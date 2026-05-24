import unittest

import ableton_controller.local_commands as local_commands
from ableton_controller.parser import build_parser


class SessionSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def snapshot_for(self, *argv):
        return self.parser.parse_args(["session-snapshot", *argv])

    def test_session_snapshot_collects_standard_and_target_probes(self):
        calls = []

        def fake_send(payload, host, port, timeout):
            calls.append(payload)
            return {"result": {"payload": payload}}

        original = local_commands.send
        local_commands.send = fake_send
        try:
            result = local_commands.run_local_command(self.snapshot_for("--track", "Bass", "--device-tree-depth", "2"))
        finally:
            local_commands.send = original

        self.assertEqual(result["command"], "session-snapshot")
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            calls,
            [
                {"command": "status"},
                {"command": "tracks"},
                {"command": "selected", "devices": True},
                {"command": "devices", "track": "selected"},
                {"command": "clips", "track": "selected"},
                {"command": "device_tree", "track": "selected", "depth": 2},
                {"command": "devices", "track": "Bass"},
                {"command": "clips", "track": "Bass"},
                {"command": "device_tree", "track": "Bass", "depth": 2},
            ],
        )
        self.assertEqual([target["track"] for target in result["targets"]], ["selected", "Bass"])

    def test_optional_target_probe_errors_are_recorded(self):
        def fake_send(payload, host, port, timeout):
            if payload["command"] == "clips":
                raise SystemExit("Ableton bridge error: no clip slots")
            return {"result": {"payload": payload}}

        original = local_commands.send
        local_commands.send = fake_send
        try:
            result = local_commands.run_local_command(self.snapshot_for())
        finally:
            local_commands.send = original

        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["probe"], "clips")
        self.assertEqual(result["targets"][0]["track"], "selected")
        self.assertIn("devices", result["targets"][0])
        self.assertNotIn("clips", result["targets"][0])


if __name__ == "__main__":
    unittest.main()

