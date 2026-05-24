import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotExecutionPlanTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_safe_alias_work_stages_inspect_execute_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten BD against SC Trigger", self.write_alias_memory(tmp))
            plan = result["orchestration"]["execution_plan"]
            phases = {phase["id"]: phase for phase in plan["phases"]}

            self.assertEqual(plan["mode"], "verify-then-act")
            self.assertFalse(plan["requires_approval"])
            self.assertIn("session-snapshot", phases["inspect-context"]["commands"])
            self.assertEqual(phases["verify-assumptions"]["status"], "before-asking")
            self.assertEqual(phases["execute-edits"]["status"], "ready")
            self.assertEqual(plan["next_phase"]["id"], "inspect-context")
            self.assertEqual(plan["next_gate_phase"]["id"], "verify-assumptions")
            steps = result["orchestration"]["planning_steps"]
            self.assertTrue(any("Start with execution phase: ready: inspect-context" in step for step in steps))
            self.assertIn("workflow-macro render kick-sub-separation", phases["render-reusable-plans"]["commands"])
            self.assertTrue(any("Follow staged execution phases" in step for step in result["orchestration"]["planning_steps"]))

    def test_marker_naming_has_preview_gate_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            plan = result["orchestration"]["execution_plan"]
            phases = {phase["id"]: phase for phase in plan["phases"]}

            self.assertTrue(plan["requires_preview"])
            self.assertEqual(phases["preview-gate"]["status"], "review-required")
            self.assertIn("locator-renaming-review", phases["preview-gate"]["why"])
            self.assertEqual(plan["next_gate_summary"], "before-asking: verify-assumptions -> locators")
            self.assertIn("workflow-macro render arrangement-marker-naming", phases["render-reusable-plans"]["commands"])
            self.assertIn("locators", phases["verify-readback"]["commands"])

    def test_resampling_has_approval_gate_and_after_approval_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            plan = result["orchestration"]["execution_plan"]
            phases = {phase["id"]: phase for phase in plan["phases"]}

            self.assertTrue(plan["requires_approval"])
            self.assertEqual(plan["mode"], "ask-before-execution")
            self.assertEqual(phases["approval-gate"]["status"], "approval-required")
            self.assertEqual(phases["execute-edits"]["status"], "after-approval")
            self.assertEqual(plan["next_gate_phase"]["id"], "preview-gate")
            self.assertIn("workflow-macro render bass-resampling-pass", phases["render-reusable-plans"]["commands"])

    def test_macro_placeholder_inputs_gate_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch drum transition with zap samples", self.write_glitch_memory(tmp))
            plan = result["orchestration"]["execution_plan"]
            phases = {phase["id"]: phase for phase in plan["phases"]}

            self.assertTrue(plan["requires_inputs"])
            self.assertFalse(plan["requires_approval"])
            self.assertEqual(phases["macro-input-gate"]["status"], "inputs-required")
            self.assertEqual(phases["macro-input-gate"]["commands"], ["browser-search zap", "browser-search perc"])
            self.assertEqual(plan["next_gate_summary"], "inputs-required: macro-input-gate -> browser-search zap, browser-search perc")
            steps = result["orchestration"]["planning_steps"]
            self.assertTrue(any("Respect next execution gate: inputs-required: macro-input-gate" in step for step in steps))
            self.assertIn("glitch-drum-transition", phases["macro-input-gate"]["why"])
            self.assertIn("samples/<zap-1>", phases["macro-input-gate"]["why"])
            self.assertEqual(phases["execute-edits"]["status"], "after-inputs")

    def test_playbook_context_verification_gates_learned_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add liquid bass movement", self.write_playbook_memory(tmp))
            plan = result["orchestration"]["execution_plan"]
            phases = {phase["id"]: phase for phase in plan["phases"]}

            self.assertEqual(phases["verify-playbook-context"]["status"], "before-execution")
            self.assertEqual(phases["verify-playbook-context"]["commands"], ["device-tree"])
            self.assertIn("verify-playbook-device-context", phases["verify-playbook-context"]["why"])
            self.assertEqual(phases["execute-edits"]["status"], "after-verification")
            self.assertEqual(plan["next_gate_phase"]["id"], "verify-playbook-context")
            self.assertEqual(plan["next_gate_summary"], "before-execution: verify-playbook-context -> device-tree")

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
                            "recommended_commands": [
                                "workflow-macro render bass-resampling-pass",
                                "set-routing",
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

    def write_playbook_memory(self, tmp):
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
                            "triggers": ["bass", "movement"],
                            "query_terms": ["bass", "movement"],
                            "recommended_commands": ["workflow-macro render bass-movement", "clip-stock-automation-set"],
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
                    "signals": [
                        {
                            "id": "project.workflow.bass-movement",
                            "category": "project.workflow",
                            "label": "bass-movement-project-workflow",
                            "confidence": 0.62,
                            "evidence_count": 4,
                        }
                    ],
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
