import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotRiserWorkflowHintTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["copilot-intent", *argv]))

    def test_inhale_build_query_surfaces_learned_riser_workflow_habit(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "riser-transition",
                                "title": "Riser/Swell Transition Into Drop",
                                "confidence": 0.62,
                                "status": "active",
                                "triggers": ["riser", "swell"],
                                "query_terms": ["riser", "swell", "inhale", "drop"],
                                "recommended_commands": ["workflow-macro render riser-transition"],
                            }
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.riser-transition",
                                "name": "riser-transition",
                                "description": "Create an inhale riser with filter and space automation before a drop.",
                                "confidence": 0.72,
                                "tags": ["transition", "sound-design", "automation"],
                                "linked_intent_ids": ["riser-transition"],
                                "status": "active",
                            }
                        ],
                        "signals": [
                            {
                                "id": "chat.workflow.riser-transition-workflow",
                                "category": "chat.workflow",
                                "label": "riser-transition-workflow",
                                "confidence": 0.25,
                                "evidence_count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("build tension before the drop with an inhale", "--memory", str(memory_path))
            orchestration = result["orchestration"]

            self.assertEqual(orchestration["workflow_habits"][0]["label"], "riser-transition-workflow")
            self.assertIn("inhale", orchestration["workflow_habits"][0]["matched_terms"])
            self.assertIn("Historical workflow habit: riser transitions build tension", orchestration["workflow_habits"][0]["hint"])
            self.assertEqual(orchestration["workflow_playbooks"][0]["id"], "riser-transition")
            self.assertIn("workflow-macro render riser-transition", orchestration["ordered_commands"])


if __name__ == "__main__":
    unittest.main()
