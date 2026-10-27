"""Long-running read-only Quasar watcher for the HA App container."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

from bridge import HomeAssistant, Settings, parse_query


FINAL = re.compile(r"onRequestStateChanged:\s*LISTENING,\s*recognizedPhrase='([^'\r\n]{1,512})'")
IDLE = re.compile(r"onAliceStateChanged:\s*IDLE(?:\s|$)")
LOG_PATH = "/data/quasar/daemons_logs/maind.log"


def load_settings(path: str = "/data/options.json") -> Settings:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return Settings(**data)


def adb_lines(serial: str, delay: float = 5.0):
    while True:
        subprocess.run(["adb", "connect", serial], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)
        process = subprocess.Popen(
            ["adb", "-s", serial, "shell", "tail", "-n", "0", "-F", LOG_PATH],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            encoding="utf-8", errors="replace", bufsize=1,
        )
        try:
            if process.stdout:
                yield from process.stdout
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
        yield None
        time.sleep(delay)


def run(settings: Settings, ha: HomeAssistant) -> None:
    pending = None
    for line in adb_lines(settings.station_adb_serial):
        if line is None:
            pending = None
            print("ADB disconnected; reconnecting", file=sys.stderr, flush=True)
            continue
        found = FINAL.search(line)
        if found:
            pending = " ".join(found.group(1).split())
            continue
        if pending and IDLE.search(line):
            phrase, pending = pending, None
            try:
                query = parse_query(phrase, settings.command_prefix)
                played = ha.search_and_play(query, settings)
                print(json.dumps({"status": "playing", "name": played}, ensure_ascii=False), flush=True)
            except ValueError:
                continue
            except (OSError, RuntimeError) as exc:
                print(str(exc), file=sys.stderr, flush=True)


if __name__ == "__main__":
    run(load_settings(), HomeAssistant(os.environ.get("SUPERVISOR_TOKEN", "")))
