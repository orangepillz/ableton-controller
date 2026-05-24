import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotIntentWorkflowHintTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["copilot-intent", *argv]))

    def test_workflow_macro_hints_filter_unrelated_high_confidence_macros(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "drum-kit-building",
                                "title": "Drum Rack Kit Building",
                                "confidence": 0.58,
                                "status": "active",
                                "triggers": ["drum", "drums"],
                                "query_terms": ["drum", "drums", "kick", "snare"],
                                "recommended_commands": ["workflow-macro render drum-punch-bus"],
                            }
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.personalized-space-chain",
                                "name": "personalized-space-chain",
                                "description": "Add learned delay and reverb space.",
                                "confidence": 0.95,
                                "tags": ["mixing", "spatial"],
                                "linked_intent_ids": ["space-delay-rides"],
                                "status": "active",
                            },
                            {
                                "id": "workflow-macro.drum-punch-bus",
                                "name": "drum-punch-bus",
                                "description": "Prepare a punch-focused drum bus chain.",
                                "confidence": 0.75,
                                "tags": ["mixing", "drums"],
                                "linked_intent_ids": ["drum-kit-building"],
                                "status": "active",
                            },
                        ],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("make the drums punchier", "--memory", str(memory_path))
            hints = result["profile_hints"]["workflow_macros"]

            self.assertEqual([hint["label"] for hint in hints], ["drum-punch-bus"])
            self.assertEqual(hints[0]["matched_intent_ids"], ["drum-kit-building"])

    def test_likely_followup_terms_can_match_followup_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "bass-movement",
                                "title": "Bass Movement",
                                "confidence": 0.53,
                                "status": "active",
                                "triggers": ["bass", "movement"],
                                "query_terms": ["bass", "movement", "drop"],
                                "recommended_commands": ["workflow-macro render call-response-bass"],
                                "likely_followups": ["add call/response variation", "render a resampling pass"],
                            }
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.call-response-bass",
                                "name": "call-response-bass",
                                "description": "Create an editable call-and-response bass phrase.",
                                "confidence": 0.7,
                                "tags": ["composition", "bass"],
                                "linked_intent_ids": ["bass-movement"],
                                "status": "active",
                            },
                            {
                                "id": "workflow-macro.bass-resampling-pass",
                                "name": "bass-resampling-pass",
                                "description": "Prepare a movement-heavy bass resampling print pass.",
                                "confidence": 0.7,
                                "tags": ["sound-design", "resampling"],
                                "linked_intent_ids": ["bass-movement"],
                                "status": "active",
                            },
                        ],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("add call and response variation", "--memory", str(memory_path))
            top = result["matches"][0]

            self.assertEqual(top["id"], "bass-movement")
            self.assertEqual(top["matched_likely_followups"], ["add call/response variation"])
            self.assertEqual(result["profile_hints"]["workflow_macros"][0]["label"], "call-response-bass")
            self.assertIn("call-response-bass", result["profile_hints"]["workflow_macros"][0]["matched_terms"])

    def test_riser_request_promotes_riser_transition_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "riser-transition",
                                "title": "Riser/Swell Transition Into Drop",
                                "confidence": 0.62,
                                "status": "active",
                                "triggers": ["riser", "swell"],
                                "query_terms": ["riser", "swell", "inhale", "drop"],
                                "recommended_commands": ["workflow-macro render riser-transition"],
                            }
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.riser-transition",
                                "name": "riser-transition",
                                "description": "Create an inhale riser with filter and space automation before a drop.",
                                "confidence": 0.72,
                                "tags": ["transition", "sound-design", "automation"],
                                "linked_intent_ids": ["riser-transition"],
                                "status": "active",
                            }
                        ],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("make a shimmer riser that inhales before the drop", "--memory", str(memory_path))
            orchestration = result["orchestration"]

            self.assertEqual(result["matches"][0]["id"], "riser-transition")
            self.assertIn("workflow-macro render riser-transition", orchestration["ordered_commands"])
            self.assertEqual(orchestration["readiness"]["status"], "ready-to-render")
            self.assertEqual(orchestration["musical_objectives"][0]["id"], "transition-contrast")
            self.assertIn("workflow-macro render riser-transition", orchestration["capability_gaps"][0]["evidence"]["macro_commands"])

    def test_spatial_throw_target_uses_space_macro_not_drum_bus(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "drum-kit-building",
                                "title": "Drum Rack Kit Building",
                                "confidence": 0.58,
                                "status": "active",
                                "triggers": ["drum", "snare"],
                                "query_terms": ["drum", "snare"],
                                "recommended_commands": ["workflow-macro render drum-punch-bus"],
                            }
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.personalized-space-chain",
                                "name": "personalized-space-chain",
                                "description": "Add learned delay and reverb space.",
                                "confidence": 0.75,
                                "tags": ["mixing", "spatial"],
                                "linked_intent_ids": ["space-delay-rides"],
                                "status": "active",
                            },
                            {
                                "id": "workflow-macro.drum-punch-bus",
                                "name": "drum-punch-bus",
                                "description": "Prepare a punch-focused drum bus chain.",
                                "confidence": 0.75,
                                "tags": ["mixing", "drums"],
                                "linked_intent_ids": ["drum-kit-building"],
                                "status": "active",
                            },
                        ],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("add a spatial throw on the snare", "--memory", str(memory_path))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertEqual(result["matches"][0]["id"], "space-delay-rides")
            self.assertEqual(result["matches"][0]["source"], "built-in")
            self.assertIn("workflow-macro render personalized-space-chain", orchestration["ordered_commands"])
            self.assertNotIn("workflow-macro render drum-punch-bus", orchestration["ordered_commands"])
            self.assertEqual(suppressed["workflow-macro render drum-punch-bus"]["reason"], "weak-generic-match")

    def test_verification_followup_query_keeps_match_but_avoids_render_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "glitch-drum-transition",
                                "title": "Glitch Drum Transition",
                                "confidence": 0.6,
                                "status": "active",
                                "triggers": ["glitch", "zap", "transition"],
                                "query_terms": ["glitch", "zap", "transition"],
                                "recommended_commands": ["workflow-macro render glitch-drum-transition"],
                                "likely_followups": ["verify rack chains", "replace placeholder sample paths"],
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
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("verify rack chains", "--memory", str(memory_path))

            self.assertEqual(result["matches"][0]["id"], "glitch-drum-transition")
            self.assertEqual(result["matches"][0]["matched_likely_followups"], ["verify rack chains"])
            self.assertEqual(result["orchestration"]["ordered_commands"], ["session-snapshot"])
            suppressed = {item["command"]: item for item in result["orchestration"]["suppressed_commands"]}
            self.assertEqual(
                suppressed["workflow-macro render glitch-drum-transition"]["reason"],
                "verification-followup",
            )


if __name__ == "__main__":
    unittest.main()
