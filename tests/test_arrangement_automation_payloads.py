import unittest

from ableton_controller.parser import build_parser
from ableton_controller.payloads import command_payload


class ArrangementAutomationPayloadTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def payload_for(self, *argv):
        return command_payload(self.parser.parse_args(list(argv)))

    def test_arrangement_automation_set_builds_stepped_ramp_payload(self):
        payload = self.payload_for(
            "arrangement-automation-set", "--track", "Build Bus", "--arrangement-start", "48",
            "--device", "Auto Filter", "--param", "Frequency", "--duration", "16",
            "--from-normalized", "0.2", "--to-normalized", "0.8", "--steps", "4", "--clear",
        )

        self.assertEqual(payload["command"], "arrangement_automation_set")
        self.assertEqual(payload["track"], "Build Bus")
        self.assertEqual(payload["arrangement_start"], 48.0)
        self.assertEqual(payload["device"], "Auto Filter")
        self.assertEqual(
            payload["steps"],
            [
                {"time": 0.0, "duration": 4.0, "normalized": 0.2},
                {"time": 4.0, "duration": 4.0, "normalized": 0.4},
                {"time": 8.0, "duration": 4.0, "normalized": 0.6},
                {"time": 12.0, "duration": 4.0, "normalized": 0.8},
            ],
        )
        self.assertIs(payload["clear"], True)

    def test_arrangement_automation_set_builds_hold_payload(self):
        payload = self.payload_for(
            "arrangement-automation-set", "--track", "FX", "--arrangement-start", "64",
            "--device-path", "song.tracks[0].devices[0]", "--param", "Dry/Wet",
            "--duration", "2", "--from-value", "0.5",
        )

        self.assertEqual(payload["steps"], [{"time": 0.0, "duration": 2.0, "value": 0.5}])

    def test_arrangement_automation_set_builds_curved_event_payload(self):
        payload = self.payload_for(
            "arrangement-automation-set", "--track", "Build Bus", "--arrangement-start", "48",
            "--device", "Auto Filter", "--param", "Frequency", "--duration", "16",
            "--from-normalized", "0.2", "--to-normalized", "0.95", "--curve", "ease-in-out", "--clear",
        )

        self.assertNotIn("steps", payload)
        self.assertEqual(
            payload["events"],
            [
                {"time": 0.0, "normalized": 0.2, "curve_coefficients": {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0}},
                {"time": 16.0, "normalized": 0.95},
            ],
        )

    def test_arrangement_automation_get_payload(self):
        payload = self.payload_for(
            "arrangement-automation-get", "--track", "Build Bus", "--arrangement-start", "48",
            "--device", "Auto Filter", "--param", "Frequency", "--times", "0,4,8",
        )

        self.assertEqual(
            payload,
            {
                "command": "arrangement_automation_get",
                "track": "Build Bus",
                "arrangement_start": 48.0,
                "device": "Auto Filter",
                "param": "Frequency",
                "times": [0.0, 4.0, 8.0],
            },
        )

    def test_arrangement_automation_device_track_does_not_replace_clip_track(self):
        payload = self.payload_for(
            "arrangement-automation-get", "--track", "Build Bus", "--arrangement-start", "48",
            "--device-track", "Filter Rack", "--device", "Auto Filter", "--param", "Frequency",
        )

        self.assertEqual(payload["track"], "Build Bus")
        self.assertEqual(payload["device_track"], "Filter Rack")

    def test_arrangement_automation_set_many_payload(self):
        payload = self.payload_for(
            "arrangement-automation-set-many", "--track", "Build Bus", "--arrangement-start", "48",
            "--device", "Auto Filter", "--lanes",
            (
                '[{"param":"Frequency","duration":16,"from_normalized":0.2,'
                '"to_normalized":0.95,"steps":4,"clear":true},'
                '{"param":"Resonance","steps":[{"time":0,"duration":16,"normalized":0.3}],"clear":true}]'
            ),
        )

        self.assertEqual(payload["command"], "arrangement_automation_set_many")
        self.assertEqual(payload["track"], "Build Bus")
        self.assertEqual(payload["arrangement_start"], 48.0)
        self.assertEqual(payload["device"], "Auto Filter")
        self.assertEqual(
            payload["lanes"][0]["steps"],
            [
                {"time": 0.0, "duration": 4.0, "normalized": 0.2},
                {"time": 4.0, "duration": 4.0, "normalized": 0.45},
                {"time": 8.0, "duration": 4.0, "normalized": 0.7},
                {"time": 12.0, "duration": 4.0, "normalized": 0.95},
            ],
        )
        self.assertEqual(payload["lanes"][1]["steps"], [{"time": 0, "duration": 16, "normalized": 0.3}])

    def test_arrangement_automation_set_many_curved_lane_payload(self):
        payload = self.payload_for(
            "arrangement-automation-set-many", "--track", "Build Bus", "--arrangement-start", "48",
            "--device", "Auto Filter", "--lanes",
            '[{"param":"Frequency","duration":16,"from_normalized":0.2,"to_normalized":0.95,"curve":"ease-out","clear":true}]',
        )

        self.assertEqual(payload["lanes"][0]["events"][0]["curve_coefficients"], {"x1": 0.0, "y1": 0.0, "x2": 0.58, "y2": 1.0})
        self.assertEqual(payload["lanes"][0]["events"][1], {"time": 16.0, "normalized": 0.95})

    def test_arrangement_automation_rejects_mixed_value_types(self):
        with self.assertRaises(SystemExit):
            self.payload_for(
                "arrangement-automation-set", "--track", "FX", "--arrangement-start", "64",
                "--device", "Auto Filter", "--param", "Frequency", "--duration", "2",
                "--from-normalized", "0.2", "--to-value", "800",
            )


if __name__ == "__main__":
    unittest.main()
