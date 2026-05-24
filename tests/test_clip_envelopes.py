import unittest
from unittest.mock import patch

from ableton_controller.clip_envelopes import cc_control_parameter_name, clip_envelope_catalog
from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class ClipEnvelopeCliTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def args(self, *argv):
        return self.parser.parse_args(list(argv))

    def test_catalog_lists_direct_cc_control_and_native_cc_targets(self):
        catalog = clip_envelope_catalog("midi")
        midi_targets = {target["id"]: target for target in catalog["midi_controls"]["targets"]}
        self.assertEqual(midi_targets["pitch_bend"]["support"], "cc_control_device_parameter")
        self.assertEqual(midi_targets["cc_127"]["support"], "native_midi_ctrl_ui_only")
        self.assertEqual(cc_control_parameter_name("cc1"), "Mod Wheel")

    def test_clip_envelope_set_midi_cc_routes_to_cc_control(self):
        args = self.args(
            "clip-envelope-set",
            "--track",
            "Synth",
            "--slot",
            "0",
            "--target",
            "midi-cc",
            "--midi-control",
            "pitch-bend",
            "--events",
            '[{"time":0,"value":0},{"time":4,"value":12}]',
            "--clear",
        )
        with patch("ableton_controller.local_commands.send_local_bridge_command", return_value={"done": True}) as send:
            result = run_local_command(args)

        payload = send.call_args.args[1]
        self.assertEqual(payload["command"], "clip_automation_set")
        self.assertEqual(payload["track"], "Synth")
        self.assertEqual(payload["device"], "CC Control")
        self.assertEqual(payload["param"], "Pitch Bend")
        self.assertEqual(payload["events"], [{"time": 0, "value": 0}, {"time": 4, "value": 12}])
        self.assertTrue(payload["clear"])
        self.assertEqual(result["clip_envelope_target"], "midi-cc")

    def test_clip_envelope_native_target_fails_with_lom_limit(self):
        args = self.args(
            "clip-envelope-set",
            "--track",
            "Audio",
            "--slot",
            "0",
            "--target",
            "native",
            "--control",
            "Transposition",
            "--events",
            '[{"time":0,"value":0}]',
        )
        with self.assertRaises(SystemExit) as raised:
            run_local_command(args)
        self.assertIn("public Live Object Model", str(raised.exception))

    def test_clip_audio_set_sends_audio_properties(self):
        args = self.args("clip-audio-set", "--track", "Audio", "--slot", "0", "--gain", "0.5", "--clip-bpm", "128")
        with patch("ableton_controller.local_commands.send_local_bridge_command", return_value={"done": True}) as send:
            run_local_command(args)

        self.assertEqual(
            send.call_args.args[1],
            {"command": "clip_warp", "track": "Audio", "slot": 0, "gain": 0.5, "clip_bpm": 128.0},
        )


if __name__ == "__main__":
    unittest.main()
