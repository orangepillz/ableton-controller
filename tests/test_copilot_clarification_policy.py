import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotClarificationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_target_aliases_are_verified_before_asking(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten BD against SC Trigger", self.write_alias_memory(tmp))
            policy = result["orchestration"]["clarification_policy"]

            self.assertEqual(policy["mode"], "verify-then-act")
            self.assertTrue(policy["can_reduce_clarification"])
            self.assertEqual(policy["ask_before_execution"], [])
            self.assertEqual(policy["verify_before_asking"][0]["label"], "matched-target-aliases")
            self.assertEqual(policy["verify_before_asking"][0]["verify_with"], "session-snapshot")
            self.assertEqual(
                policy["verify_before_asking"][0]["resolution_command"],
                'session-snapshot --track "BD" --track "SC Trigger" --device-tree-depth 3',
            )
            self.assertEqual(
                policy["readback_commands"][0],
                'session-snapshot --track "BD" --track "SC Trigger" --device-tree-depth 3',
            )
            self.assertTrue(any("Verify personalized assumptions" in step for step in result["orchestration"]["planning_steps"]))

    def test_arrangement_marker_review_uses_preview_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            policy = result["orchestration"]["clarification_policy"]

            self.assertEqual(policy["mode"], "preview-before-execution")
            self.assertEqual(policy["preview_before_execution"][0]["label"], "locator-renaming-review")
            self.assertEqual(policy["verify_before_asking"][0]["label"], "derived-section-labels")
            self.assertIn("locators", policy["readback_commands"])

    def test_resampling_requires_approval_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            policy = result["orchestration"]["clarification_policy"]

            self.assertEqual(policy["mode"], "ask-before-execution")
            self.assertFalse(policy["can_reduce_clarification"])
            self.assertEqual(policy["ask_before_execution"][0]["label"], "resampling-approval")
            self.assertTrue(any("Ask only for approval-level" in step for step in result["orchestration"]["planning_steps"]))

    def write_alias_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [],
                    "workflow_macros": [],
                    "signals": [
                        {"id": "project.name.bd", "category": "project.name", "label": "BD", "confidence": 0.44},
                        {"id": "project.name.sc", "category": "project.name", "label": "SC Trigger", "confidence": 0.4},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return memory_path

    def write_arrangement_memory(self, tmp):
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
                            "query_terms": ["arrangement", "marker"],
                            "recommended_commands": ["workflow-macro render arrangement-marker-naming"],
                        }
                    ],
                    "workflow_macros": [
                        {
                            "id": "workflow-macro.arrangement-marker-naming",
                            "name": "arrangement-marker-naming",
                            "description": "Name arrangement markers from memory.",
                            "confidence": 0.6,
                            "tags": ["arrangement"],
                            "linked_intent_ids": ["arrangement-flow"],
                            "status": "active",
                        }
                    ],
                    "signals": [
                        {"category": "project.arrangement-marker", "label": "locator-marker-1-at-0-beats", "confidence": 0.3},
                        {"category": "project.arrangement-marker", "label": "locator-marker-2-at-64-beats", "confidence": 0.3},
                        {
                            "category": "project.arrangement-phase",
                            "label": "main-section-phase-drums-kick",
                            "confidence": 0.3,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        return memory_path

    def write_resampling_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "bass-movement",
                            "title": "Bass Movement",
                            "confidence": 0.7,
                            "status": "active",
                            "triggers": ["bass", "resampling"],
                            "query_terms": ["bass", "resampling"],
                            "recommended_commands": ["workflow-macro render bass-resampling-pass"],
                        }
                    ],
                    "workflow_macros": [],
                    "signals": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
