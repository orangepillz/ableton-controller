import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotArrangementHintTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_arrangement_request_surfaces_section_label_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_memory(tmp))
            labels = result["profile_hints"]["section_label_proposals"]

            self.assertEqual(labels[0]["beat"], 0.0)
            self.assertEqual(labels[1]["beat"], 64.0)
            self.assertIn("Main Drop - Drum FX Kick Impact", labels[1]["label"])
            self.assertIn("project.arrangement-phase.main-section-phase-drums-fx-kick", labels[1]["evidence_signal_ids"])
            self.assertTrue(any("section label proposals" in step for step in result["orchestration"]["planning_steps"]))

    def test_unrelated_request_does_not_surface_section_label_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_memory(tmp))

            self.assertNotIn("section_label_proposals", result["profile_hints"])

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "arrangement-flow",
                            "title": "Arrangement Flow",
                            "confidence": 0.5,
                            "status": "active",
                            "triggers": ["arrangement", "marker", "locator", "section"],
                            "query_terms": ["arrangement", "marker", "locator", "section", "name"],
                            "recommended_commands": ["workflow-macro render arrangement-marker-naming"],
                            "planning_bias": "Create or use explicit section labels before dense edits.",
                        },
                        {
                            "id": "drum-kit-building",
                            "title": "Drum Kit Building",
                            "confidence": 0.5,
                            "status": "active",
                            "triggers": ["drums"],
                            "query_terms": ["drums"],
                        },
                    ],
                    "signals": [
                        {
                            "id": "project.arrangement-marker.locator-marker-1-at-0-beats",
                            "category": "project.arrangement-marker",
                            "label": "locator-marker-1-at-0-beats",
                            "confidence": 0.25,
                            "evidence_count": 2,
                        },
                        {
                            "id": "project.arrangement-marker.locator-marker-2-at-64-beats",
                            "category": "project.arrangement-marker",
                            "label": "locator-marker-2-at-64-beats",
                            "confidence": 0.3,
                            "evidence_count": 2,
                        },
                        {
                            "id": "project.arrangement-phase.main-section-phase-drums-fx-kick",
                            "category": "project.arrangement-phase",
                            "label": "main-section-phase-drums-fx-kick",
                            "confidence": 0.23,
                            "evidence_count": 1,
                        },
                    ],
                    "workflow_macros": [
                        {
                            "id": "workflow-macro.arrangement-marker-naming",
                            "name": "arrangement-marker-naming",
                            "description": "Rename numbered locators into musical section anchors.",
                            "confidence": 0.62,
                            "tags": ["arrangement", "personalized"],
                            "linked_intent_ids": ["arrangement-flow"],
                            "status": "active",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
