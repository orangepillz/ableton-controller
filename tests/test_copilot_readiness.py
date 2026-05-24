import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotReadinessTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_alias_work_requires_readback_before_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten BD against SC Trigger", self.write_alias_memory(tmp))
            readiness = result["orchestration"]["readiness"]

            self.assertEqual(readiness["status"], "verify-assumptions")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertIn("matched-target-aliases", readiness["gate_labels"])
            self.assertEqual(readiness["required_before_execution"][0]["verify_with"], "session-snapshot")
            self.assertTrue(any("Check execution readiness" in step for step in result["orchestration"]["planning_steps"]))

    def test_marker_naming_is_preview_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            readiness = result["orchestration"]["readiness"]

            self.assertEqual(readiness["status"], "preview-required")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertIn("locator-renaming-review", readiness["gate_labels"])
            self.assertIn("locator-renaming-review", readiness["risk_labels"])
            self.assertLess(readiness["score"], 0.7)

    def test_resampling_is_approval_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            readiness = result["orchestration"]["readiness"]

            self.assertEqual(readiness["status"], "approval-required")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertIn("resampling-approval", readiness["gate_labels"])
            self.assertEqual(readiness["required_before_execution"][0]["level"], "approval-required")
            self.assertEqual(readiness["next_required_before_execution"]["label"], "resampling-approval")
            self.assertEqual(readiness["next_required_summary"], "approval-required: resampling-approval")
            steps = result["orchestration"]["planning_steps"]
            self.assertTrue(any("Resolve next readiness requirement: approval-required: resampling-approval" in step for step in steps))
            levels = {item["label"]: item["level"] for item in readiness["required_before_execution"]}
            self.assertEqual(levels["arrangement-automation-range"], "plan-first")
            self.assertEqual(levels["routing-change-review"], "plan-first")
            self.assertEqual([item["label"] for item in readiness["required_before_execution"]].count("resampling-approval"), 1)
            self.assertIn("explicit approval", readiness["next_action"])

    def test_macro_only_plan_is_ready_to_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_drum_memory(tmp))
            readiness = result["orchestration"]["readiness"]

            self.assertEqual(readiness["status"], "ready-to-render")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertIsNone(readiness["next_required_before_execution"])
            self.assertIsNone(readiness["next_required_summary"])
            self.assertEqual(readiness["gate_labels"], [])
            self.assertIn("mix-translation", readiness["supporting_signals"]["objective_ids"])
            self.assertGreater(readiness["score"], 0.6)

    def test_macro_placeholder_inputs_block_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch drum transition with zap samples", self.write_glitch_memory(tmp))
            readiness = result["orchestration"]["readiness"]

            self.assertEqual(readiness["status"], "inputs-required")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertIn("samples/<zap-1>", readiness["gate_labels"])
            self.assertIn("samples/<zap-1>", readiness["risk_labels"])
            self.assertEqual(readiness["required_before_execution"][0]["level"], "inputs-required")
            self.assertEqual(readiness["required_before_execution"][0]["macro"], "glitch-drum-transition")
            self.assertEqual(readiness["required_before_execution"][0]["search_query"], "zap")
            self.assertEqual(readiness["required_before_execution"][0]["resolution_command"], "browser-search zap")
            self.assertEqual(readiness["next_required_before_execution"]["resolution_command"], "browser-search zap")
            self.assertEqual(readiness["next_required_summary"], "inputs-required: samples/<zap-1> via browser-search zap")
            self.assertEqual(readiness["required_before_execution"][2]["search_query"], "perc")
            self.assertEqual(readiness["required_before_execution"][2]["resolution_command"], "browser-search perc")
            self.assertEqual(readiness["input_resolution_commands"], ["browser-search zap", "browser-search perc"])
            self.assertEqual(readiness["supporting_signals"]["macro_blocked_count"], 1)
            self.assertEqual(readiness["supporting_signals"]["macro_ready_count"], 1)
            self.assertIn("placeholder inputs", readiness["next_action"])

    def write_alias_memory(self, tmp):
        return self.write_memory(
            tmp,
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
                "workflow_macros": [
                    {
                        "id": "workflow-macro.kick-sub-separation",
                        "name": "kick-sub-separation",
                        "description": "Separate kick and sub.",
                        "confidence": 0.7,
                        "tags": ["mixing", "bass"],
                        "linked_intent_ids": ["kick-sub-sidechain"],
                        "status": "active",
                    }
                ],
                "signals": [
                    {"id": "project.name.bd", "category": "project.name", "label": "BD", "confidence": 0.44},
                    {"id": "project.name.sc", "category": "project.name", "label": "SC Trigger", "confidence": 0.4},
                ],
            },
        )

    def write_arrangement_memory(self, tmp):
        return self.write_memory(
            tmp,
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
            },
        )

    def write_resampling_memory(self, tmp):
        return self.write_memory(
            tmp,
            {
                "intent_mappings": [
                    {
                        "id": "bass-movement",
                        "title": "Bass Movement",
                        "confidence": 0.7,
                        "status": "active",
                        "triggers": ["bass", "resampling"],
                        "query_terms": ["bass", "resampling"],
                        "recommended_commands": ["workflow-macro render bass-resampling-pass", "set-routing"],
                    }
                ],
                "workflow_macros": [],
                "signals": [],
            },
        )

    def write_drum_memory(self, tmp):
        return self.write_memory(
            tmp,
            {
                "intent_mappings": [
                    {
                        "id": "drum-kit-building",
                        "title": "Drum Kit Building",
                        "confidence": 0.6,
                        "status": "active",
                        "triggers": ["drums"],
                        "query_terms": ["drums"],
                        "recommended_commands": ["workflow-macro render drum-punch-bus"],
                    }
                ],
                "workflow_macros": [
                    {
                        "id": "workflow-macro.drum-punch-bus",
                        "name": "drum-punch-bus",
                        "description": "Prepare a punch-focused drum bus chain.",
                        "confidence": 0.7,
                        "tags": ["mixing", "drums"],
                        "linked_intent_ids": ["drum-kit-building"],
                        "status": "active",
                    }
                ],
                "signals": [],
            },
        )

    def write_glitch_memory(self, tmp):
        return self.write_memory(
            tmp,
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
            },
        )

    def write_memory(self, tmp, payload):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
