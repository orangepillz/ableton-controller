import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotRecoveryPlanTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_safe_alias_plan_has_checkpoints_and_failure_readbacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten BD against SC Trigger", self.write_alias_memory(tmp))
            recovery = result["orchestration"]["recovery_plan"]

            self.assertIn("session-snapshot", recovery["checkpoint_commands"])
            self.assertIn("stock-controls", recovery["checkpoint_commands"])
            self.assertIn("device-tree", recovery["post_failure_readbacks"])
            self.assertEqual(recovery["stop_conditions"][0]["label"], "verification-failed")
            self.assertEqual(recovery["next_stop_condition"]["label"], "verification-failed")
            self.assertEqual(recovery["next_stop_summary"], "stop-and-readback: verification-failed")
            self.assertTrue(any("Capture recovery checkpoints" in step for step in result["orchestration"]["planning_steps"]))

    def test_marker_review_plan_checkpoints_locators(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            recovery = result["orchestration"]["recovery_plan"]
            conditions = {condition["label"]: condition for condition in recovery["stop_conditions"]}

            self.assertIn("locators", recovery["checkpoint_commands"])
            self.assertIn("locator-renaming-review", conditions)
            self.assertEqual(conditions["locator-renaming-review"]["level"], "review-before-execute")
            self.assertEqual(recovery["next_stop_condition"]["label"], "locator-renaming-review")
            self.assertEqual(recovery["next_stop_summary"], "review-before-execute: locator-renaming-review")
            self.assertTrue(any(step["label"] == "review-recovery" for step in recovery["manual_recovery_steps"]))

    def test_resampling_plan_has_approval_recovery_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            recovery = result["orchestration"]["recovery_plan"]
            conditions = {condition["label"]: condition for condition in recovery["stop_conditions"]}

            self.assertIn("resampling-approval", conditions)
            self.assertEqual(conditions["resampling-approval"]["level"], "approval-required")
            self.assertEqual(conditions["arrangement-automation-range"]["level"], "plan-first")
            self.assertEqual(conditions["routing-change-review"]["level"], "plan-first")
            self.assertEqual([condition["label"] for condition in recovery["stop_conditions"]].count("resampling-approval"), 1)
            self.assertIn("session-snapshot", recovery["post_failure_readbacks"])
            self.assertEqual(recovery["next_stop_condition"]["label"], "resampling-approval")
            self.assertEqual(recovery["next_stop_summary"], "approval-required: resampling-approval")
            steps = result["orchestration"]["planning_steps"]
            self.assertTrue(any("Use recovery stop priority: approval-required: resampling-approval" in step for step in steps))
            self.assertTrue(any(step["label"] == "approval-recovery" for step in recovery["manual_recovery_steps"]))

    def test_macro_placeholder_inputs_have_recovery_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch drum transition with zap samples", self.write_glitch_memory(tmp))
            recovery = result["orchestration"]["recovery_plan"]
            conditions = {condition["label"]: condition for condition in recovery["stop_conditions"]}

            self.assertIn("samples/<zap-1>", conditions)
            self.assertEqual(conditions["samples/<zap-1>"]["level"], "inputs-required")
            self.assertEqual(conditions["samples/<zap-1>"]["macro"], "glitch-drum-transition")
            self.assertEqual(conditions["samples/<zap-1>"]["search_query"], "zap")
            self.assertEqual(conditions["samples/<zap-1>"]["resolution_command"], "browser-search zap")
            self.assertEqual(conditions["samples/<perc-1>"]["search_query"], "perc")
            self.assertEqual(conditions["samples/<perc-1>"]["resolution_command"], "browser-search perc")
            self.assertEqual(recovery["next_stop_condition"]["label"], "samples/<zap-1>")
            self.assertEqual(recovery["next_stop_summary"], "inputs-required: samples/<zap-1> via browser-search zap")
            self.assertEqual(recovery["input_resolution_commands"], ["browser-search zap", "browser-search perc"])
            input_step = next(step for step in recovery["manual_recovery_steps"] if step["label"] == "input-recovery")
            self.assertIn("browser-search zap", input_step["why"])

    def write_alias_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "kick-sub-sidechain",
                            "title": "Kick/Sub",
                            "confidence": 0.7,
                            "status": "active",
                            "triggers": ["bd", "sc trigger"],
                            "query_terms": ["bd", "sc trigger"],
                            "recommended_commands": [
                                "workflow-macro render kick-sub-separation",
                                "device-tree",
                                "set-stock-control",
                            ],
                        }
                    ],
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

    def write_glitch_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "glitch-drum-transition",
                            "title": "Glitch Drum Transition",
                            "confidence": 0.7,
                            "status": "active",
                            "triggers": ["glitch", "zap", "transition"],
                            "query_terms": ["glitch", "zap", "transition"],
                            "recommended_commands": [
                                "workflow-macro render glitch-drum-transition",
                                "browser-search",
                                "drum-pad-load",
                            ],
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
