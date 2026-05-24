import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotRevisionHintTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_actually_more_request_surfaces_revision_without_intent_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("actually make it more intense", memory_path)
            labels = [hint["label"] for hint in result["profile_hints"]["revision_requests"]]

            self.assertEqual(result["matches"], [])
            self.assertIn("correction-actually", labels)
            self.assertIn("increase-intensity-more", labels)

    def test_instead_pad_request_marks_plan_redirection(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("instead use the other pad", memory_path)
            hints = result["profile_hints"]["revision_requests"]
            labels = [hint["label"] for hint in hints]

            self.assertIn("correction-instead-of", labels)
            self.assertIn("pad-mapping-correction", labels)
            self.assertTrue(any("current plan" in hint["hint"] or "existing plan" in hint["hint"] for hint in hints))

    def test_not_quite_less_request_marks_negative_subtractive_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("not quite, make it less busy", memory_path)
            labels = [hint["label"] for hint in result["profile_hints"]["revision_requests"]]

            self.assertIn("negative-revision-not-quite", labels)
            self.assertIn("reduce-intensity-less", labels)

    def test_historical_refinement_patterns_shape_revision_strategy(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("not quite, make it less busy", self.write_revision_memory(tmp))
            orchestration = result["orchestration"]
            strategy = orchestration["refinement_strategy"]

            self.assertEqual(strategy["mode"], "revise-current-plan")
            self.assertIn("negative-revision-not-quite", [item["label"] for item in strategy["historical_patterns"]])
            self.assertTrue(any("failed assumption" in item for item in strategy["planning_biases"]))
            self.assertTrue(any("subtractive" in item for item in strategy["planning_biases"]))
            self.assertTrue(orchestration["clarification_policy"]["can_reduce_clarification"])
            self.assertIn("learned revision context", orchestration["clarification_policy"]["why"])
            self.assertIn("session-snapshot", orchestration["clarification_policy"]["readback_commands"])
            phases = {phase["id"]: phase for phase in orchestration["execution_plan"]["phases"]}
            self.assertEqual(phases["verify-refinement-context"]["status"], "before-asking")
            self.assertEqual(phases["verify-refinement-context"]["commands"], ["session-snapshot"])
            self.assertIn("preserve-current-plan-context", phases["verify-refinement-context"]["why"])
            readiness = orchestration["readiness"]
            self.assertEqual(readiness["status"], "verify-assumptions")
            self.assertIn("preserve-current-plan-context", readiness["gate_labels"])
            self.assertEqual(readiness["next_required_summary"], "verify-before-execution: preserve-current-plan-context via session-snapshot")
            self.assertEqual(readiness["supporting_signals"]["refinement_verification_labels"], ["preserve-current-plan-context"])
            recovery = orchestration["recovery_plan"]
            conditions = {item["label"]: item for item in recovery["stop_conditions"]}
            self.assertEqual(conditions["preserve-current-plan-context"]["level"], "verify-before-execution")
            self.assertEqual(conditions["preserve-current-plan-context"]["verify_with"], "session-snapshot")
            self.assertTrue(any(step["label"] == "verification-gate-recovery" for step in recovery["manual_recovery_steps"]))
            self.assertTrue(any("Apply learned refinement strategy" in step for step in orchestration["planning_steps"]))

    def test_pad_mapping_memory_adds_refinement_verification_bias(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch zap transition", self.write_pad_memory(tmp))
            strategy = result["orchestration"]["refinement_strategy"]

            self.assertIn("pad-mapping-correction", [item["label"] for item in strategy["historical_patterns"]])
            self.assertEqual(strategy["verification_biases"][0]["label"], "verify-drum-pad-mapping")
            self.assertEqual(strategy["verification_biases"][0]["command"], "device-tree")
            phases = {phase["id"]: phase for phase in result["orchestration"]["execution_plan"]["phases"]}
            self.assertIn("device-tree", phases["verify-refinement-context"]["commands"])
            self.assertIn("device-tree", result["orchestration"]["recovery_plan"]["checkpoint_commands"])
            readiness = result["orchestration"]["readiness"]
            self.assertIn("verify-drum-pad-mapping", readiness["gate_labels"])
            self.assertIn("verify-drum-pad-mapping", readiness["supporting_signals"]["refinement_verification_labels"])
            conditions = {item["label"]: item for item in result["orchestration"]["recovery_plan"]["stop_conditions"]}
            self.assertEqual(conditions["verify-drum-pad-mapping"]["verify_with"], "device-tree")
            self.assertTrue(any("Apply refinement verification bias" in step for step in result["orchestration"]["planning_steps"]))

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps({"intent_mappings": [], "signals": [], "workflow_macros": []}),
            encoding="utf-8",
        )
        return memory_path

    def write_revision_memory(self, tmp):
        return self.write_payload(
            tmp,
            {
                "intent_mappings": [],
                "workflow_macros": [],
                "signals": [
                    {
                        "id": "chat.refinement.negative",
                        "category": "chat.refinement",
                        "label": "negative-revision-not-quite",
                        "confidence": 0.42,
                        "evidence_count": 2,
                    },
                    {
                        "id": "chat.refinement.less",
                        "category": "chat.refinement",
                        "label": "reduce-intensity-less",
                        "confidence": 0.39,
                        "evidence_count": 2,
                    },
                ],
            },
        )

    def write_pad_memory(self, tmp):
        return self.write_payload(
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
                        "recommended_commands": ["workflow-macro render glitch-drum-transition"],
                    }
                ],
                "workflow_macros": [
                    {
                        "id": "workflow-macro.glitch-drum-transition",
                        "name": "glitch-drum-transition",
                        "description": "Sketch zap/perc Drum Racks with stutters.",
                        "confidence": 0.7,
                        "tags": ["drums", "transition", "glitch"],
                        "linked_intent_ids": ["glitch-drum-transition"],
                        "status": "active",
                    }
                ],
                "signals": [
                    {
                        "id": "chat.refinement.pad",
                        "category": "chat.refinement",
                        "label": "pad-mapping-correction",
                        "confidence": 0.34,
                        "evidence_count": 1,
                    }
                ],
            },
        )

    def write_payload(self, tmp, payload):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
