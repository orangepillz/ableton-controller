import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotOrchestrationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_resampling_and_arrangement_automation_add_safety_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_memory(tmp))
            checks = {check["label"]: check for check in result["orchestration"]["safety_checks"]}

            self.assertEqual(checks["resampling-approval"]["level"], "approval-required")
            self.assertEqual(checks["arrangement-automation-range"]["level"], "plan-first")
            self.assertTrue(any("Apply safety checks" in step for step in result["orchestration"]["planning_steps"]))

    def test_arrangement_marker_naming_adds_locator_review_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_memory(tmp))
            labels = [check["label"] for check in result["orchestration"]["safety_checks"]]

            self.assertIn("locator-renaming-review", labels)
            self.assertNotIn("arrangement-automation-range", labels)
            self.assertNotIn("copilot-intent", result["orchestration"]["ordered_commands"])
            self.assertNotIn("arrangement-automation-set", result["orchestration"]["ordered_commands"])

    def test_build_automation_adds_range_check_without_marker_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add build automation into the drop", self.write_memory(tmp))
            labels = [check["label"] for check in result["orchestration"]["safety_checks"]]

            self.assertIn("arrangement-automation-range", labels)
            self.assertNotIn("locator-renaming-review", labels)
            self.assertIn("arrangement-automation-set", result["orchestration"]["ordered_commands"])
            self.assertNotIn("workflow-macro render arrangement-marker-naming", result["orchestration"]["ordered_commands"])

    def test_small_drum_request_has_no_extra_safety_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_memory(tmp))

            self.assertEqual(result["orchestration"]["safety_checks"], [])

    def write_memory(self, tmp):
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
                            "triggers": ["bass", "resampling", "movement"],
                            "query_terms": ["bass", "resampling", "movement"],
                            "recommended_commands": [
                                "workflow-macro render bass-resampling-pass",
                                "arrangement-automation-set",
                            ],
                        },
                        {
                            "id": "arrangement-flow",
                            "title": "Arrangement Flow",
                            "confidence": 0.6,
                            "status": "active",
                            "triggers": ["arrangement", "marker", "automation", "build", "drop"],
                            "query_terms": ["arrangement", "marker", "name", "automation", "build", "drop"],
                            "recommended_commands": [
                                "workflow-macro render arrangement-marker-naming",
                                "copilot-intent",
                                "arrangement-automation-set",
                            ],
                        },
                        {
                            "id": "drum-kit-building",
                            "title": "Drum Kit Building",
                            "confidence": 0.6,
                            "status": "active",
                            "triggers": ["drums"],
                            "query_terms": ["drums"],
                            "recommended_commands": ["workflow-macro render drum-punch-bus"],
                        },
                    ],
                    "signals": [],
                    "workflow_macros": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
