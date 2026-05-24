import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotTargetAliasOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path), "--min-score", "0"]))

    def test_matched_target_aliases_are_promoted_into_orchestration(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten BD against SC Trigger", self.write_memory(tmp))
            aliases = result["orchestration"]["target_aliases"]
            roles = [alias["role"] for alias in aliases]

            self.assertIn("kick", roles)
            self.assertIn("sidechain", roles)
            self.assertIn("BD", aliases[0]["matched_terms"])
            alias_step = next(
                step for step in result["orchestration"]["planning_steps"] if "Resolve matched personal target aliases" in step
            )
            self.assertIn('session-snapshot --track "BD" --track "SC Trigger" --device-tree-depth 3', alias_step)

    def test_unmatched_alias_hints_are_not_promoted_into_orchestration(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the groove punchier", self.write_memory(tmp))

            self.assertEqual(result["orchestration"]["target_aliases"], [])
            self.assertFalse(any("Resolve matched personal target aliases" in step for step in result["orchestration"]["planning_steps"]))

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [],
                    "signals": [
                        {
                            "id": "project.name.bd",
                            "category": "project.name",
                            "label": "BD",
                            "confidence": 0.44,
                            "evidence_count": 8,
                        },
                        {
                            "id": "project.name.kicks",
                            "category": "project.name",
                            "label": "Kicks",
                            "confidence": 0.4,
                            "evidence_count": 5,
                        },
                        {
                            "id": "project.name.sc-trigger",
                            "category": "project.name",
                            "label": "SC Trigger",
                            "confidence": 0.4,
                            "evidence_count": 6,
                        },
                        {
                            "id": "project.name.tr8s",
                            "category": "project.name",
                            "label": "TR8S",
                            "confidence": 0.4,
                            "evidence_count": 4,
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
