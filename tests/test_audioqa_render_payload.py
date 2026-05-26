from __future__ import annotations

import unittest
from pathlib import Path

from ableton_controller.config import LOCAL_COMMANDS
from ableton_controller.parser import build_parser
from ableton_controller.render_audio import _prepare_payload


class RenderAudioLocalCommandTests(unittest.TestCase):
    def test_render_audio_is_local_command_and_prepare_payload_has_targets(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "render-audio",
                "--start-bar",
                "65",
                "--bars",
                "4",
                "--solo-track",
                "Kick",
                "--solo-tracks",
                "BASS,Snare",
                "--mute-group",
                "FX",
                "--output",
                ".ableton-audits/renders/drop_1_kick.wav",
            ]
        )
        self.assertIn(args.command, LOCAL_COMMANDS)
        payload = _prepare_payload(args, Path(args.output).resolve())
        self.assertEqual(payload["command"], "render_audio_prepare")
        self.assertEqual(payload["start_bar"], 65.0)
        self.assertEqual(payload["bars"], 4.0)
        self.assertEqual(payload["solo_tracks"], ["Kick", "BASS", "Snare"])
        self.assertEqual(payload["muted_groups"], ["FX"])
        self.assertEqual(payload["sample_rate"], 48000)
        self.assertEqual(payload["bit_depth"], 24)
        self.assertFalse(payload["normalize"])
        self.assertTrue(payload["restore_state"])
        self.assertIn("output_file_abs", payload)


if __name__ == "__main__":
    unittest.main()
