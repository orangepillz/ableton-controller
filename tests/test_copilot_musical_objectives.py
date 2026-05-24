import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotMusicalObjectivesTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_bass_movement_surfaces_musical_success_criteria(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add liquid bass movement", self.write_bass_memory(tmp))
            objectives = {item["id"]: item for item in result["orchestration"]["musical_objectives"]}
            objective = objectives["bass-motion"]

            self.assertEqual(objective["rank"], 1)
            self.assertIn("low-end clarity", objective["focus_axes"])
            self.assertIn("workflow-macro render bass-movement", objective["evidence"]["commands"])
            self.assertEqual(objective["evidence"]["workflow_habits"][0]["label"], "bass-movement-project-workflow")
            self.assertGreaterEqual(objective["confidence"], 0.75)
            self.assertTrue(any("automation" in item for item in objective["success_criteria"]))
            self.assertTrue(any("matched bass movement habit" in item for item in objective["success_criteria"]))
            self.assertTrue(any("explicit musical objective" in step for step in result["orchestration"]["planning_steps"]))

    def test_resampling_objective_carries_approval_and_range_criteria(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            objectives = {item["id"]: item for item in result["orchestration"]["musical_objectives"]}
            objective = objectives["resampling-readiness"]

            self.assertIn("resampling-approval", objective["evidence"]["safety_labels"])
            self.assertIn("arrangement-automation-range", objective["evidence"]["safety_labels"])
            self.assertTrue(any("approval" in item for item in objective["success_criteria"]))
            self.assertTrue(any("beat range" in item for item in objective["success_criteria"]))
            self.assertTrue(any("Do not record" in item for item in objective["constraints"]))

    def test_arrangement_objective_uses_learned_section_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            objectives = {item["id"]: item for item in result["orchestration"]["musical_objectives"]}
            objective = objectives["arrangement-flow"]

            self.assertIn("tension/release", objective["focus_axes"])
            self.assertIn("locator-renaming-review", objective["evidence"]["safety_labels"])
            self.assertTrue(any("learned early/main/late flow" in item for item in objective["success_criteria"]))
            self.assertTrue(any("reviewable preview" in item for item in objective["constraints"]))

    def write_bass_memory(self, tmp):
        return self.write_memory(
            tmp,
            {
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
                "signals": [
                    {
                        "id": "project.workflow.bass-movement",
                        "category": "project.workflow",
                        "label": "bass-movement-project-workflow",
                        "confidence": 0.62,
                        "evidence_count": 4,
                    }
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
                        "recommended_commands": [
                            "workflow-macro render bass-resampling-pass",
                            "arrangement-automation-set",
                        ],
                    }
                ],
                "workflow_macros": [],
                "signals": [],
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
                        "query_terms": ["arrangement", "marker", "name"],
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
                    {
                        "id": "project.arrangement-marker.1",
                        "category": "project.arrangement-marker",
                        "label": "locator-marker-1-at-0-beats",
                        "confidence": 0.3,
                    },
                    {
                        "id": "project.arrangement-marker.2",
                        "category": "project.arrangement-marker",
                        "label": "locator-marker-2-at-64-beats",
                        "confidence": 0.3,
                    },
                    {
                        "id": "project.arrangement-phase.main",
                        "category": "project.arrangement-phase",
                        "label": "main-section-phase-drums-bass",
                        "confidence": 0.4,
                    },
                ],
            },
        )

    def write_memory(self, tmp, payload):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
