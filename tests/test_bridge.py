import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "yandex_quasar_voice" / "app"))
from bridge import HomeAssistant, Settings, parse_query


class BridgeTests(unittest.TestCase):
    def test_standard_phrase(self):
        self.assertEqual(parse_query("Алиса, включи Noize MC Страна дождей"),
                         "Noize MC Страна дождей")

    def test_non_music_rejected(self):
        for phrase in ("включи свет", "какая погода", "включи телевизор"):
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                parse_query(phrase)

    def test_optional_prefix(self):
        self.assertEqual(parse_query("мост включи Queen", "мост"), "Queen")
        with self.assertRaises(ValueError):
            parse_query("включи Queen", "мост")

    def test_youtube_filter_and_play_payload(self):
        settings = Settings("station:5555", "media_player.station", "entry", "ytmusic--abc")
        ha = HomeAssistant("token", "http://ha/api")
        responses = [
            {"service_response": {"tracks": [
                {"uri": "spotify://track/no", "name": "wrong"},
                {"uri": "ytmusic--abc://track/yes", "name": "right"},
            ]}},
            [],
        ]
        with patch.object(ha, "call", side_effect=responses) as call:
            self.assertEqual(ha.search_and_play("right", settings), "right")
        self.assertEqual(call.call_args_list[1].args[0], "/services/music_assistant/play_media")
        self.assertEqual(call.call_args_list[1].args[1]["radio_mode"], False)


if __name__ == "__main__":
    unittest.main()
