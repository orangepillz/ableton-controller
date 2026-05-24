import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotVerificationOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_arrangement_marker_request_gets_locator_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_memory(tmp))
            steps = {step["label"]: step for step in result["orchestration"]["verification_steps"]}

            self.assertEqual(steps["verify-locators"]["command"], "locators")
            self.assertTrue(any("Verify with readback probes" in step for step in result["orchestration"]["planning_steps"]))

    def test_bass_movement_request_gets_automation_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add bass movement", self.write_memory(tmp))
            commands = [step["command"] for step in result["orchestration"]["verification_steps"]]

            self.assertIn("clip-stock-automation-get", commands)

    def test_drum_request_gets_device_chain_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_memory(tmp))
            commands = [step["command"] for step in result["orchestration"]["verification_steps"]]

            self.assertIn("device-tree", commands)
            self.assertNotIn("midi-get-notes", commands)
            self.assertNotIn("drum-pad-load", result["orchestration"]["ordered_commands"])

    def test_drum_kit_request_keeps_pad_and_midi_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("build a drum rack kit and program a pattern", self.write_memory(tmp))
            commands = [step["command"] for step in result["orchestration"]["verification_steps"]]

            self.assertIn("device-tree", commands)
            self.assertIn("midi-get-notes", commands)
            self.assertIn("drum-pad-load", result["orchestration"]["ordered_commands"])

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "arrangement-flow",
                            "title": "Arrangement Flow",
                            "confidence": 0.6,
                            "status": "active",
                            "triggers": ["arrangement", "marker"],
                            "query_terms": ["arrangement", "marker", "name"],
                            "recommended_commands": ["workflow-macro render arrangement-marker-naming"],
                        },
                        {
                            "id": "bass-movement",
                            "title": "Bass Movement",
                            "confidence": 0.7,
                            "status": "active",
                            "triggers": ["bass", "movement"],
                            "query_terms": ["bass", "movement"],
                            "recommended_commands": ["workflow-macro render bass-movement"],
                        },
                        {
                            "id": "drum-kit-building",
                            "title": "Drum Kit Building",
                            "confidence": 0.6,
                            "status": "active",
                            "triggers": ["drums", "drum rack", "kit", "pattern"],
                            "query_terms": ["drums", "drum rack", "kit", "pattern"],
                            "recommended_commands": [
                                "workflow-macro render drum-punch-bus",
                                "drum-pad-load",
                                "clip-create-midi",
                                "midi-add-notes",
                            ],
                        },
                    ],
                    "signals": [],
                    "workflow_macros": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
