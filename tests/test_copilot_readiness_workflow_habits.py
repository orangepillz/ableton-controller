import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotReadinessWorkflowHabitTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_workflow_habits_strengthen_readiness_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            without_habit = self.local_result("add liquid bass movement", self.write_memory(tmp, []))
            with_habit = self.local_result(
                "add liquid bass movement",
                self.write_memory(
                    tmp,
                    [
                        {
                            "id": "project.workflow.bass-movement",
                            "category": "project.workflow",
                            "label": "bass-movement-project-workflow",
                            "confidence": 0.62,
                            "evidence_count": 4,
                        },
                        {
                            "id": "chat.workflow.bass-movement",
                            "category": "chat.workflow",
                            "label": "bass-movement-workflow",
                            "confidence": 0.25,
                            "evidence_count": 1,
                        },
                    ],
                    "with-habit.json",
                ),
            )

            plain_readiness = without_habit["orchestration"]["readiness"]
            habit_readiness = with_habit["orchestration"]["readiness"]
            playbook = with_habit["orchestration"]["workflow_playbooks"][0]
            verification = {step["label"]: step for step in with_habit["orchestration"]["verification_steps"]}
            recovery = with_habit["orchestration"]["recovery_plan"]
            signals = habit_readiness["supporting_signals"]

            self.assertGreater(habit_readiness["score"], plain_readiness["score"])
            self.assertEqual(playbook["id"], "bass-movement")
            self.assertIn("Probe bass/sub devices", playbook["first_move"])
            self.assertEqual(len(with_habit["orchestration"]["workflow_playbooks"]), 1)
            self.assertEqual(verification["verify-playbook-device-context"]["command"], "device-tree")
            self.assertIn("device-tree", recovery["checkpoint_commands"])
            self.assertEqual(signals["workflow_habit_count"], 2)
            self.assertEqual(signals["workflow_playbook_count"], 1)
            self.assertEqual(signals["workflow_playbooks"][0]["id"], "bass-movement")
            self.assertIn("approval-gated follow-up", signals["workflow_playbooks"][0]["follow_through"])
            self.assertEqual(signals["workflow_habits"][0]["label"], "bass-movement-project-workflow")
            self.assertEqual(signals["workflow_habits"][0]["confidence"], 0.62)
            self.assertTrue(
                any(
                    "Treat readiness confidence as personalized by workflow habit evidence" in step
                    for step in with_habit["orchestration"]["planning_steps"]
                )
            )
            self.assertTrue(
                any(
                    "Apply personalized workflow playbook bass-movement" in step
                    for step in with_habit["orchestration"]["planning_steps"]
                )
            )

    def write_memory(self, tmp, signals, filename="memory.json"):
        payload = {
            "intent_mappings": [
                {
                    "id": "bass-movement",
                    "title": "Bass Movement",
                    "confidence": 0.7,
                    "status": "active",
                    "triggers": ["bass", "movement"],
                    "query_terms": ["bass", "movement"],
                    "recommended_commands": ["workflow-macro render bass-movement"],
                }
            ],
            "workflow_macros": [
                {
                    "id": "workflow-macro.bass-movement",
                    "name": "bass-movement",
                    "description": "Add deterministic mid-bass filter movement.",
                    "confidence": 0.7,
                    "tags": ["sound-design", "automation"],
                    "linked_intent_ids": ["bass-movement"],
                    "status": "active",
                }
            ],
            "signals": signals,
        }
        memory_path = Path(tmp) / filename
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
