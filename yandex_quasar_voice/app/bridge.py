"""Pure command parsing and HA/Music Assistant adapter logic."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen


COMMAND = re.compile(
    r"^(?:алиса[,.]?\s*)?(?:включи|поставь|сыграй)\s+"
    r"(?:(?:песню|трек|группу)\s+)?(?P<query>.+)$",
    re.I,
)
DEVICE = re.compile(r"\b(?:свет|ламп|телевизор|чайник|пылесос|кондиционер|штор|розетк)\w*\b", re.I)


@dataclass(frozen=True)
class Settings:
    station_adb_serial: str
    ma_player_entity: str
    ma_config_entry_id: str
    youtube_provider: str = "ytmusic"
    command_prefix: str = ""


def parse_query(text: str, prefix: str = "") -> str:
    normalized = " ".join(text.strip().split())
    if not normalized or len(normalized) > 512 or DEVICE.search(normalized):
        raise ValueError("not a music command")
    if prefix:
        expected = prefix.casefold() + " "
        if not normalized.casefold().startswith(expected):
            raise ValueError("prefix mismatch")
        normalized = normalized[len(expected):]
    match = COMMAND.match(normalized)
    if not match:
        raise ValueError("not a music command")
    query = match.group("query").strip(" .,!?:;\"'«»")
    if not query:
        raise ValueError("empty query")
    return query


class HomeAssistant:
    def __init__(self, token: str, base_url: str = "http://supervisor/core/api"):
        if not token:
            raise ValueError("SUPERVISOR_TOKEN is unavailable")
        self.base_url = base_url.rstrip("/")
        self.token = token

    def call(self, path: str, payload: dict, *, response: bool = False):
        suffix = "?return_response" if response else ""
        request = Request(
            self.base_url + path + suffix,
            data=json.dumps(payload).encode(),
            method="POST",
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=15) as result:
                return json.load(result)
        except HTTPError as exc:
            raise RuntimeError(f"Home Assistant returned HTTP {exc.code}") from exc

    def search_and_play(self, query: str, settings: Settings) -> str:
        result = self.call("/services/music_assistant/search", {
            "config_entry_id": settings.ma_config_entry_id,
            "name": query,
            "media_type": ["track"],
            "limit": 25,
            "library_only": False,
        }, response=True)
        tracks = (result.get("service_response") or {}).get("tracks") or []
        track = next((item for item in tracks if self._is_youtube_track(item, settings.youtube_provider)), None)
        if not track:
            raise RuntimeError("YouTube Music track not found")
        self.call("/services/music_assistant/play_media", {
            "entity_id": settings.ma_player_entity,
            "media_id": track["uri"],
            "media_type": "track",
            "enqueue": "replace",
            "radio_mode": False,
        })
        return str(track.get("name") or query)

    @staticmethod
    def _is_youtube_track(item: object, provider: str) -> bool:
        if not isinstance(item, dict):
            return False
        uri = item.get("uri")
        return isinstance(uri, str) and uri.startswith(provider + "://track/")
