import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotTransitionContextTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_delay_throws_before_drop_suppress_context_only_riser_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add delay throws before the drop", self.write_memory(tmp))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertEqual(result["matches"][0]["id"], "space-delay-rides")
            self.assertIn("workflow-macro render personalized-space-chain", orchestration["ordered_commands"])
            self.assertNotIn("workflow-macro render riser-transition", orchestration["ordered_commands"])
            self.assertEqual(suppressed["workflow-macro render riser-transition"]["reason"], "weak-generic-match")

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "space-delay-rides",
                            "title": "Reverb/Delay Spatial Movement",
                            "confidence": 0.62,
                            "status": "active",
                            "triggers": ["delay", "throw", "throws"],
                            "query_terms": ["delay", "throw", "throws"],
                            "recommended_commands": [
                                "workflow-macro render personalized-space-chain",
                                "set-send",
                                "device-add-stock",
                                "clip-stock-automation-set",
                            ],
                        },
                        {
                            "id": "riser-transition",
                            "title": "Riser/Swell Transition Into Drop",
                            "confidence": 0.32,
                            "status": "active",
                            "triggers": ["drop"],
                            "query_terms": ["before the drop", "drop"],
                            "recommended_commands": ["workflow-macro render riser-transition"],
                        },
                    ],
                    "workflow_macros": [
                        {
                            "id": "workflow-macro.personalized-space-chain",
                            "name": "personalized-space-chain",
                            "description": "Add learned delay and reverb space.",
                            "confidence": 0.78,
                            "tags": ["mixing", "spatial"],
                            "linked_intent_ids": ["space-delay-rides"],
                            "status": "active",
                        },
                        {
                            "id": "workflow-macro.riser-transition",
                            "name": "riser-transition",
                            "description": "Create an inhale riser with filter movement before a drop.",
                            "confidence": 0.72,
                            "tags": ["transition", "sound-design", "automation"],
                            "linked_intent_ids": ["riser-transition"],
                            "status": "active",
                        },
                    ],
                    "signals": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
