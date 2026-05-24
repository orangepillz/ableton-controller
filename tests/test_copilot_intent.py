import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotIntentTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["copilot-intent", *argv]))

    def test_matches_personalized_mapping_from_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [
                            {
                                "id": "glitch-drum-transition",
                                "title": "Glitchy Zap/Perc Drum Transition",
                                "confidence": 0.42,
                                "status": "active",
                                "triggers": ["glitchy", "transition", "zap"],
                                "query_terms": ["glitch", "glitchy", "zap", "perc", "transition", "synth"],
                                "recommended_commands": ["workflow-macro render glitch-drum-transition"],
                                "planning_bias": "Render the glitch drum transition macro.",
                                "likely_followups": ["replace placeholder sample paths"],
                                "evidence_signal_ids": ["chat.intent.glitchy"],
                            },
                            {
                                "id": "mix-bus-control",
                                "title": "Mix Bus Control",
                                "confidence": 0.8,
                                "status": "active",
                                "triggers": ["mix", "master"],
                                "query_terms": ["mix", "master", "limiter"],
                            },
                        ],
                        "workflow_macros": [
                            {
                                "id": "workflow-macro.glitch-drum-transition",
                                "name": "glitch-drum-transition",
                                "description": "Sketch zap/perc Drum Racks with stutters and a pre-bar-3 cutout.",
                                "confidence": 0.59,
                                "tags": ["drums", "transition", "glitch"],
                                "linked_intent_ids": ["glitch-drum-transition"],
                                "status": "active",
                            },
                            {
                                "id": "workflow-macro.mix-bus-control",
                                "name": "mix-bus-control",
                                "description": "Prepare a conservative mix/master preview chain.",
                                "confidence": 0.54,
                                "tags": ["mixing", "mastering"],
                                "linked_intent_ids": ["mix-bus-control"],
                                "status": "active",
                            },
                        ],
                        "signals": [
                            {
                                "id": "project.arrangement-phase.main-section-phase-bass-drums",
                                "category": "project.arrangement-phase",
                                "label": "main-section-phase-bass-drums",
                                "confidence": 0.55,
                                "evidence_count": 2,
                            },
                            {
                                "id": "project.arrangement-role.clip-role-drums",
                                "category": "project.arrangement-role",
                                "label": "clip-role-drums",
                                "confidence": 0.5,
                                "evidence_count": 4,
                            },
                            {
                                "id": "project.arrangement-shape.common-clip-length-16-beats",
                                "category": "project.arrangement-shape",
                                "label": "common-clip-length-16-beats",
                                "confidence": 0.45,
                                "evidence_count": 3,
                            },
                            {
                                "id": "project.arrangement-marker.locator-marker-2-at-64-beats",
                                "category": "project.arrangement-marker",
                                "label": "locator-marker-2-at-64-beats",
                                "confidence": 0.43,
                                "evidence_count": 2,
                            },
                            {
                                "id": "project.automation.AutomationEnvelope",
                                "category": "project.automation",
                                "label": "AutomationEnvelope",
                                "confidence": 0.4,
                                "evidence_count": 2,
                            },
                            {
                                "id": "project.device-chain.midi-track-operator-autofilter-saturator",
                                "category": "project.device-chain",
                                "label": "Midi track: Operator > AutoFilter > Saturator",
                                "confidence": 0.37,
                                "evidence_count": 1,
                            },
                            {
                                "id": "chat.refinement.pad-mapping-correction",
                                "category": "chat.refinement",
                                "label": "pad-mapping-correction",
                                "confidence": 0.34,
                                "evidence_count": 1,
                            },
                            {
                                "id": "chat.workflow.glitch-drum-transition",
                                "category": "chat.workflow",
                                "label": "glitch-drum-transition",
                                "confidence": 0.45,
                                "evidence_count": 2,
                            },
                            {
                                "id": "project.workflow.spatial-send-project-workflow",
                                "category": "project.workflow",
                                "label": "spatial-send-project-workflow",
                                "confidence": 0.42,
                                "evidence_count": 3,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("make a glitchy zap transition into the synth", "--memory", str(memory_path))
            top = result["matches"][0]

            self.assertTrue(result["memory_found"])
            self.assertEqual(top["id"], "glitch-drum-transition")
            self.assertIn("zap", top["matched_triggers"])
            self.assertIn("synth", top["matched_query_terms"])
            self.assertIn("workflow-macro render glitch-drum-transition", top["recommended_commands"])
            self.assertEqual(result["profile_hints"]["arrangement_phases"][0]["label"], "main-section-phase-bass-drums")
            self.assertIn("main sections combine bass and drum", result["profile_hints"]["arrangement_phases"][0]["hint"])
            self.assertEqual(result["profile_hints"]["arrangement_roles"][0]["label"], "clip-role-drums")
            self.assertIn("drum clips", result["profile_hints"]["arrangement_roles"][0]["hint"])
            self.assertEqual(result["profile_hints"]["arrangement_shape"][0]["label"], "common-clip-length-16-beats")
            self.assertEqual(result["profile_hints"]["arrangement_markers"][0]["label"], "locator-marker-2-at-64-beats")
            self.assertIn("locator marker 2 at beat 64", result["profile_hints"]["arrangement_markers"][0]["hint"])
            self.assertEqual(result["profile_hints"]["device_chains"][0]["label"], "Midi track: Operator > AutoFilter > Saturator")
            self.assertIn("Historical device-chain preference", result["profile_hints"]["device_chains"][0]["hint"])
            self.assertEqual(result["profile_hints"]["refinement_patterns"][0]["label"], "pad-mapping-correction")
            self.assertIn("distinct pads", result["profile_hints"]["refinement_patterns"][0]["hint"])
            self.assertEqual(result["profile_hints"]["chat_workflows"][0]["label"], "glitch-drum-transition")
            self.assertIn("glitch drum transitions", result["profile_hints"]["chat_workflows"][0]["hint"])
            self.assertEqual(result["profile_hints"]["project_workflows"][0]["label"], "spatial-send-project-workflow")
            self.assertEqual(result["orchestration"]["workflow_habits"][0]["label"], "glitch-drum-transition")
            self.assertTrue(any("historical workflow habits" in step for step in result["orchestration"]["planning_steps"]))
            self.assertIn("audition zap/perc alternatives", [item["label"] for item in result["orchestration"]["likely_followups"]])
            self.assertEqual(result["profile_hints"]["workflow_macros"][0]["label"], "glitch-drum-transition")
            self.assertEqual(result["profile_hints"]["workflow_macros"][0]["recommended_command"], "workflow-macro render glitch-drum-transition")
            self.assertNotIn("mix-bus-control", [hint["label"] for hint in result["profile_hints"]["workflow_macros"]])

    def test_missing_memory_returns_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("tighten the kick and sub", "--memory", str(Path(tmp) / "missing.json"))

            self.assertFalse(result["memory_found"])
            self.assertEqual(result["matches"], [])
            self.assertEqual(result["profile_hints"], {})
            self.assertIn("copilot_improvement.py run", result["guidance"])

    def test_built_in_fallback_handles_new_macro_language_before_memory_learns_it(self):
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
                                "triggers": ["bass", "movement", "drop"],
                                "query_terms": ["bass", "movement", "drop"],
                                "recommended_commands": ["workflow-macro render bass-movement"],
                            },
                            {
                                "id": "arrangement-flow",
                                "title": "Arrangement Flow",
                                "confidence": 0.45,
                                "status": "active",
                                "triggers": ["arrangement", "drop"],
                                "query_terms": ["arrangement", "drop"],
                                "recommended_commands": ["workflow-macro render arrangement-phase-scaffold"],
                            },
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
                            },
                            {
                                "id": "workflow-macro.arrangement-phase-scaffold",
                                "name": "arrangement-phase-scaffold",
                                "description": "Create named scenes from learned phase signatures.",
                                "confidence": 0.6,
                                "tags": ["arrangement"],
                                "linked_intent_ids": ["arrangement-flow"],
                                "status": "active",
                            },
                        ],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("make a shimmer riser that inhales before the drop", "--memory", str(memory_path))
            top = result["matches"][0]

            self.assertEqual(top["id"], "riser-transition")
            self.assertEqual(top["source"], "built-in")
            self.assertIn("workflow-macro render riser-transition", top["recommended_commands"])
            self.assertIn("workflow-macro render riser-transition", result["orchestration"]["ordered_commands"])
            self.assertNotIn("workflow-macro render bass-movement", result["orchestration"]["ordered_commands"])
            self.assertNotIn("workflow-macro render arrangement-phase-scaffold", result["orchestration"]["ordered_commands"])
            suppressed = {item["command"]: item for item in result["orchestration"]["suppressed_commands"]}
            self.assertEqual(suppressed["workflow-macro render bass-movement"]["reason"], "weak-generic-match")
            self.assertEqual(suppressed["workflow-macro render arrangement-phase-scaffold"]["reason"], "weak-generic-match")
            source_types = {
                source["type"]
                for source in result["orchestration"]["command_sources"][1]["sources"]
            }
            self.assertIn("built_in_intent", source_types)

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            self.local_result(" ")

    def test_profile_hints_include_personal_target_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "intent_mappings": [],
                        "signals": [
                            {
                                "id": "project.name.bd",
                                "category": "project.name",
                                "label": "BD",
                                "confidence": 0.44,
                                "evidence_count": 8,
                            },
                            {
                                "id": "project.name.sc-trigger",
                                "category": "project.name",
                                "label": "SC Trigger",
                                "confidence": 0.4,
                                "evidence_count": 6,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("tighten the kick sidechain", "--memory", str(memory_path), "--min-score", "0")
            hints = result["profile_hints"]["target_aliases"]

            self.assertEqual(hints[0]["label"], "kick: BD")
            self.assertIn("prefer BD", hints[0]["hint"])
            self.assertTrue(any(hint["label"] == "sidechain: SC Trigger" for hint in hints))


if __name__ == "__main__":
    unittest.main()
