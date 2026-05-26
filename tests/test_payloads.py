import unittest

from ableton_controller.parser import build_parser
from ableton_controller.payloads import command_payload


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def payload_for(self, *argv):
        return command_payload(self.parser.parse_args(list(argv)))

    def test_device_add_stock_payload(self):
        self.assertEqual(
            self.payload_for(
                "device-add-stock",
                "--target-track",
                "Vox",
                "--name",
                "EQ Eight",
                "--root",
                "audio_effects",
                "--target-index",
                "0",
                "--allow-presets",
            ),
            {
                "command": "device_add_stock",
                "target_track": "Vox",
                "name": "EQ Eight",
                "root": "audio_effects",
                "target_index": 0,
                "allow_presets": True,
            },
        )

    def test_drum_pad_load_payload_accepts_note_name(self):
        self.assertEqual(
            self.payload_for(
                "drum-pad-load",
                "--track",
                "Drums",
                "--device",
                "Main Rack",
                "--pad",
                "C1",
                "--item",
                "samples/Kick.wav",
                "--clear",
            ),
            {
                "command": "drum_pad_load",
                "track": "Drums",
                "device": "Main Rack",
                "pad": 36,
                "item": "samples/Kick.wav",
                "clear": True,
            },
        )

    def test_serum_add_payload_defaults_to_vst_format(self):
        self.assertEqual(
            self.payload_for("serum-add", "--target-track", "Lead"),
            {
                "command": "serum_add",
                "target_track": "Lead",
                "format": "vst",
            },
        )

    def test_serum_set_payload_accepts_instance_selector(self):
        self.assertEqual(
            self.payload_for(
                "serum-set",
                "--track",
                "Lead",
                "--instance",
                "1",
                "--param",
                "Filter Cutoff",
                "--normalized",
                "0.45",
            ),
            {
                "command": "serum_set_param",
                "track": "Lead",
                "instance": 1,
                "param": "Filter Cutoff",
                "normalized": 0.45,
            },
        )

    def test_serum_set_many_payload_validates_controls(self):
        self.assertEqual(
            self.payload_for(
                "serum-set-many",
                "--device-path",
                "song.tracks[0].devices[2]",
                "--controls",
                '[{"param":"Filter Cutoff","normalized":0.45},{"param":"WT Pos","delta":0.05}]',
            ),
            {
                "command": "serum_set_many",
                "device_path": "song.tracks[0].devices[2]",
                "controls": [
                    {"param": "Filter Cutoff", "normalized": 0.45},
                    {"param": "WT Pos", "delta": 0.05},
                ],
            },
        )
        with self.assertRaises(SystemExit):
            self.payload_for("serum-set-many", "--track", "Lead", "--controls", '[{"param":"Cutoff"}]')

    def test_clip_create_midi_requires_length_for_session_clip(self):
        with self.assertRaises(SystemExit):
            self.payload_for("clip-create-midi", "--track", "Synth", "--slot", "0")

    def test_clip_create_midi_session_payload(self):
        self.assertEqual(
            self.payload_for("clip-create-midi", "--track", "Synth", "--slot", "0", "--length", "4", "--replace"),
            {
                "command": "clip_create_midi",
                "track": "Synth",
                "length": 4.0,
                "slot": 0,
                "replace": True,
            },
        )

    def test_clip_automation_payload(self):
        payload = self.payload_for(
            "clip-automation-set",
            "--track",
            "Synth",
            "--slot",
            "0",
            "--device",
            "Auto Filter",
            "--param",
            "Frequency",
            "--steps",
            '[{"time":0,"duration":1,"normalized":0.2}]',
            "--clear",
        )
        self.assertEqual(payload["command"], "clip_automation_set")
        self.assertEqual(payload["track"], "Synth")
        self.assertEqual(payload["device"], "Auto Filter")
        self.assertEqual(payload["steps"], [{"time": 0, "duration": 1, "normalized": 0.2}])
        self.assertIs(payload["clear"], True)

    def test_clip_automation_set_many_payload(self):
        payload = self.payload_for(
            "clip-automation-set-many",
            "--track",
            "Synth",
            "--slot",
            "0",
            "--device",
            "Auto Filter",
            "--lanes",
            '[{"param":"Frequency","duration":4,"from_normalized":0.2,"to_normalized":0.8}]',
        )
        self.assertEqual(payload["command"], "clip_automation_set_many")
        self.assertEqual(payload["track"], "Synth")
        self.assertEqual(payload["device"], "Auto Filter")
        self.assertEqual(
            payload["lanes"],
            [
                {
                    "param": "Frequency",
                    "steps": [
                        {"time": 0.0, "duration": 0.5, "normalized": 0.2},
                        {"time": 0.5, "duration": 0.5, "normalized": 0.285714},
                        {"time": 1.0, "duration": 0.5, "normalized": 0.371429},
                        {"time": 1.5, "duration": 0.5, "normalized": 0.457143},
                        {"time": 2.0, "duration": 0.5, "normalized": 0.542857},
                        {"time": 2.5, "duration": 0.5, "normalized": 0.628571},
                        {"time": 3.0, "duration": 0.5, "normalized": 0.714286},
                        {"time": 3.5, "duration": 0.5, "normalized": 0.8},
                    ],
                }
            ],
        )

    def test_clip_warp_payload_accepts_clip_bpm(self):
        self.assertEqual(
            self.payload_for("clip-warp", "--track", "Audio", "--slot", "0", "--clip-bpm", "128"),
            {"command": "clip_warp", "track": "Audio", "slot": 0, "clip_bpm": 128.0},
        )

    def test_locator_payloads(self):
        self.assertEqual(self.payload_for("locators"), {"command": "locators"})
        self.assertEqual(
            self.payload_for("set-locator", "--time", "64", "--name", "02 Main Drop"),
            {"command": "set_locator", "time": 64.0, "name": "02 Main Drop"},
        )
        self.assertEqual(
            self.payload_for("set-locator", "--locator", "2", "--name", "03 Break"),
            {"command": "set_locator", "locator": 2, "name": "03 Break"},
        )

    def test_midi_transform_requires_transform_option(self):
        with self.assertRaises(SystemExit):
            self.payload_for("midi-transform-notes", "--track", "Synth", "--slot", "0")

    def test_raw_payload_must_be_object(self):
        self.assertEqual(self.payload_for("raw", '{"command":"status"}'), {"command": "status"})
        with self.assertRaises(SystemExit):
            self.payload_for("raw", "[1, 2]")


if __name__ == "__main__":
    unittest.main()
