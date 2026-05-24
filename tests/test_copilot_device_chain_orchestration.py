import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotDeviceChainOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path), "--min-score", "0"]))

    def test_matched_device_chain_preferences_are_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add delay reverb movement", self.write_memory(tmp))
            chains = result["orchestration"]["device_chain_preferences"]

            self.assertEqual(chains[0]["label"], "Midi track: Delay > Reverb")
            self.assertIn("Delay", chains[0]["matched_terms"])
            self.assertIn("Reverb", chains[0]["matched_terms"])
            self.assertTrue(any("learned device-chain preferences" in step for step in result["orchestration"]["planning_steps"]))

    def test_unmatched_device_chain_preferences_are_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_memory(tmp))

            self.assertEqual(result["orchestration"]["device_chain_preferences"], [])
            self.assertFalse(any("learned device-chain preferences" in step for step in result["orchestration"]["planning_steps"]))

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [],
                    "signals": [
                        {
                            "id": "project.device-chain.midi-track-delay-reverb",
                            "category": "project.device-chain",
                            "label": "Midi track: Delay > Reverb",
                            "confidence": 0.3,
                            "evidence_count": 2,
                        },
                        {
                            "id": "project.device-chain.midi-track-originalsimpler-reverb",
                            "category": "project.device-chain",
                            "label": "Midi track: OriginalSimpler > Reverb",
                            "confidence": 0.24,
                            "evidence_count": 1,
                        },
                    ],
                    "workflow_macros": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
