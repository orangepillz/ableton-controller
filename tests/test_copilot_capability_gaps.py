import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotCapabilityGapTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_unknown_request_creates_missing_intent_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a velvet crystalline texture that slowly blooms", self.write_empty_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}

            self.assertIn("missing-personal-intent", gaps)
            self.assertEqual(gaps["missing-personal-intent"]["type"], "personalization-gap")
            self.assertEqual(gaps["missing-personal-intent"]["priority"], "high")
            self.assertIn("candidate chat evidence", gaps["missing-personal-intent"]["next_action"])
            self.assertTrue(any("Track request-level capability gaps" in step for step in result["orchestration"]["planning_steps"]))

    def test_suppressed_learned_command_creates_query_support_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make it G Jones energy", self.write_empty_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["suppressed-command-workflow-macro-render-bass-resampling-pass"]

            self.assertEqual(gap["type"], "query-support-gap")
            self.assertEqual(gap["priority"], "medium")
            self.assertEqual(gap["evidence"]["reason"], "query-mismatch")
            self.assertEqual(gap["evidence"]["source_types"], ["artist_inspiration"])
            self.assertIn("focused clarification", gap["next_action"])

    def test_macro_only_plan_tracks_render_before_execution_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drums punchier", self.write_drum_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["macro-render-before-execution"]

            self.assertEqual(gap["type"], "workflow-orchestration-gap")
            self.assertEqual(gap["priority"], "low")
            self.assertEqual(gap["evidence"]["macro_commands"], ["workflow-macro render drum-punch-bus"])
            self.assertIn("Render the macro plan", gap["next_action"])

    def test_revision_readback_is_not_missing_intent_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("not quite, make it less busy", self.write_empty_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["verification-before-execution"]

            self.assertNotIn("missing-personal-intent", gaps)
            self.assertEqual(gap["type"], "current-set-evidence-gap")
            self.assertEqual(gap["priority"], "medium")
            self.assertEqual(gap["evidence"]["required_labels"], ["preserve-current-plan-context"])
            self.assertEqual(gap["evidence"]["readback_commands"], ["session-snapshot"])
            self.assertIn("required readback", gap["next_action"])

    def test_macro_placeholder_inputs_create_resolution_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch drum transition with zap samples", self.write_glitch_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["macro-inputs-before-execution"]

            self.assertEqual(gap["type"], "workflow-input-gap")
            self.assertEqual(gap["priority"], "high")
            self.assertEqual(gap["evidence"]["search_queries"], ["zap", "perc"])
            self.assertEqual(gap["evidence"]["resolution_commands"], ["browser-search zap", "browser-search perc"])
            self.assertIn("samples/<zap-1>", gap["evidence"]["required_inputs"])
            self.assertIn("required macro inputs", gap["next_action"])

    def test_approval_gate_creates_safety_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a bass resampling pass", self.write_resampling_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["approval-before-execution"]

            self.assertEqual(gap["type"], "execution-safety-gap")
            self.assertEqual(gap["priority"], "high")
            self.assertIn("resampling-approval", gap["evidence"]["required_labels"])
            self.assertIn("approval-required", gap["evidence"]["required_levels"])
            self.assertIn("explicit approval", gap["next_action"])

    def test_preview_gate_creates_review_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("name the arrangement markers", self.write_arrangement_memory(tmp))
            gaps = {gap["id"]: gap for gap in result["orchestration"]["capability_gaps"]}
            gap = gaps["preview-before-execution"]

            self.assertEqual(gap["type"], "execution-review-gap")
            self.assertEqual(gap["priority"], "medium")
            self.assertEqual(gap["evidence"]["required_labels"], ["locator-renaming-review"])
            self.assertEqual(gap["evidence"]["next_required_summary"], "review-before-execute: locator-renaming-review")
            self.assertIn("preview gate", gap["next_action"])

    def test_weak_generic_suppressions_are_not_capability_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a shimmer riser that inhales before the drop", self.write_drop_overlap_memory(tmp))
            gap_ids = [gap["id"] for gap in result["orchestration"]["capability_gaps"]]

            self.assertEqual(gap_ids, ["macro-render-before-execution"])
            self.assertTrue(
                any(item["reason"] == "weak-generic-match" for item in result["orchestration"]["suppressed_commands"])
            )

    def write_empty_memory(self, tmp):
        return self.write_memory(tmp, {"intent_mappings": [], "workflow_macros": [], "signals": []})

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

    def write_drop_overlap_memory(self, tmp):
        return self.write_memory(
            tmp,
            {
                "intent_mappings": [
                    {
                        "id": "bass-movement",
                        "title": "Bass Movement",
                        "confidence": 0.53,
                        "status": "active",
                        "triggers": ["bass", "movement", "drop"],
                        "query_terms": ["bass", "movement", "drop"],
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
                "signals": [],
            },
        )

    def write_memory(self, tmp, payload):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(json.dumps(payload), encoding="utf-8")
        return memory_path


if __name__ == "__main__":
    unittest.main()
