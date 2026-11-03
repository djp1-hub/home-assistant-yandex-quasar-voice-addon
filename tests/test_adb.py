import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "yandex_quasar_voice" / "app"))
from main import adb_lines


class AdbTests(unittest.TestCase):
    def test_connect_timeout_yields_boundary_and_retries(self):
        with patch("main.subprocess.run", side_effect=[
            subprocess.TimeoutExpired(["adb", "connect"], 10),
            KeyboardInterrupt(),
        ]), patch("main.time.sleep"):
            lines = adb_lines("station:5555", delay=0)
            self.assertIsNone(next(lines))
            with self.assertRaises(KeyboardInterrupt):
                next(lines)


if __name__ == "__main__":
    unittest.main()
