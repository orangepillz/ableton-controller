import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotReadinessPhaseGateTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_playbook_context_gate_prevents_immediate_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("polish the mix bus", self.write_mix_playbook_memory(tmp))
            readiness = result["orchestration"]["readiness"]
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["verification-before-execution"]

            self.assertEqual(readiness["status"], "verify-execution-context")
            self.assertFalse(readiness["can_execute_mutations_now"])
            self.assertEqual(
                readiness["next_required_summary"],
                "verify-before-execution: verify-playbook-context via stock-controls",
            )
            self.assertIn("verify-playbook-context", readiness["gate_labels"])
            self.assertEqual(gap["evidence"]["required_labels"], ["verify-playbook-context"])
            self.assertEqual(gap["evidence"]["readback_commands"], ["stock-controls"])

    def write_mix_playbook_memory(self, tmp):
        payload = {
            "intent_mappings": [
                {
                    "id": "mix-bus-control",
                    "title": "Mix Bus",
                    "confidence": 0.7,
                    "status": "active",
                    "triggers": ["mix", "bus"],
                    "query_terms": ["mix", "bus"],
                    "recommended_commands": ["workflow-macro render mix-bus-control", "stock-controls", "set-stock-control"],
                }
            ],
            "workflow_macros": [
                {
                    "id": "workflow-macro.mix-bus-control",
                    "name": "mix-bus-control",
                    "description": "Prepare conservative mix-bus controls.",
                    "confidence": 0.7,
                    "tags": ["mixing"],
                    "linked_intent_ids": ["mix-bus-control"],
                    "status": "active",
                }
            ],
            "signals": [
                {
                    "id": "project.workflow.mix-bus",
                    "category": "project.workflow",
                    "label": "mix-bus-project-workflow",
                    "confidence": 0.5,
                }
            ],
        }
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
