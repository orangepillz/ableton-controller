import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.copilot_macro_preview_cues import macro_action_plan, macro_preview_planning_steps
from ableton_controller.copilot_macro_query_overrides import query_macro_overrides
from ableton_controller.copilot_macro_preview import macro_plan_previews
from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotMacroPreviewTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["copilot-intent", *argv]))

    def test_intent_includes_side_effect_free_riser_macro_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("make a shimmer riser that inhales before the drop", "--memory", str(memory_path))
            orchestration = result["orchestration"]
            preview = orchestration["macro_plan_previews"][0]

            self.assertEqual(preview["macro"], "riser-transition")
            self.assertTrue(preview["preview_only"])
            self.assertEqual(preview["command_count"], 12)
            self.assertEqual(preview["command_sequence_preview"][0]["head"], "session-snapshot")
            self.assertTrue(preview["command_sequence_preview"][0]["read_only"])
            self.assertEqual(preview["command_sequence_preview"][1]["head"], "create-track")
            self.assertFalse(preview["command_sequence_preview"][1]["read_only"])
            self.assertIn("clip-stock-automation-set", preview["mutating_command_heads"])
            self.assertIn("clip-stock-automation-get", preview["verification_heads"])
            self.assertFalse(preview["approval_required"])
            self.assertFalse(preview["review_required"])
            self.assertEqual(preview["execution_status"]["status"], "ready-to-adapt")
            self.assertTrue(preview["execution_status"]["can_adapt_without_extra_input"])
            self.assertEqual(preview["recommended_action"]["type"], "adapt-plan")
            self.assertIn("create-track", preview["recommended_action"]["command_heads"])
            self.assertIn("workflow-macro render riser-transition", orchestration["ordered_commands"])
            self.assertTrue(any("Preview macro plan shape" in step for step in orchestration["planning_steps"]))

    def test_macro_preview_ignores_non_macro_and_unknown_commands(self):
        previews = macro_plan_previews(["session-snapshot", "workflow-macro render missing-macro"])

        self.assertEqual(previews, [])

    def test_macro_preview_uses_memory_path_for_personalized_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {
                                "id": "project.name.drums",
                                "category": "project.name",
                                "label": "Drums",
                                "confidence": 0.44,
                                "evidence_count": 8,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            preview = macro_plan_previews(["workflow-macro render drum-punch-bus"], memory_path=memory_path)[0]

            self.assertIn("Drum bus track is 'Drums'", preview["assumptions"])
            self.assertIn("device-add-stock", preview["mutating_command_heads"])

    def test_resampling_preview_marks_approval_and_routing_gates(self):
        preview = macro_plan_previews(["workflow-macro render bass-resampling-pass"])[0]

        self.assertTrue(preview["approval_required"])
        self.assertTrue(preview["review_required"])
        self.assertIn("resampling-approval", preview["risk_labels"])
        self.assertIn("routing-change-review", preview["risk_labels"])
        self.assertIn("arrangement-automation-range", preview["risk_labels"])
        self.assertIn("explicit approval", preview["next_action"])
        self.assertEqual(preview["execution_status"]["status"], "approval-required")
        self.assertFalse(preview["execution_status"]["can_adapt_without_extra_input"])
        self.assertIn("resampling-approval", preview["execution_status"]["blocking_reasons"])
        self.assertEqual(preview["recommended_action"]["type"], "ask-approval")
        self.assertEqual(preview["recommended_action"]["priority"], "high")
        self.assertIn("resampling-approval", preview["recommended_action"]["gate_labels"])
        gate_levels = {gate["label"]: gate["level"] for gate in preview["recommended_action"]["gate_details"]}
        self.assertEqual(gate_levels["resampling-approval"], "approval-required")
        self.assertEqual(gate_levels["routing-change-review"], "plan-first")

    def test_locator_preview_marks_review_without_approval(self):
        preview = macro_plan_previews(["workflow-macro render arrangement-marker-naming"])[0]

        self.assertFalse(preview["approval_required"])
        self.assertTrue(preview["review_required"])
        self.assertEqual(preview["risk_labels"], ["locator-renaming-review"])
        self.assertEqual(preview["execution_status"]["status"], "review-required")
        self.assertIn("locator-renaming-review", preview["execution_status"]["blocking_reasons"])
        self.assertEqual(preview["recommended_action"]["type"], "review-plan")
        self.assertIn("locator-renaming-review", preview["recommended_action"]["gate_labels"])
        self.assertEqual(preview["recommended_action"]["gate_details"][0]["level"], "review-before-execute")
        self.assertIn("Review", preview["next_action"])

    def test_placeholder_sample_loads_are_review_gated(self):
        preview = macro_plan_previews(["workflow-macro render glitch-drum-transition"])[0]

        self.assertFalse(preview["approval_required"])
        self.assertTrue(preview["review_required"])
        self.assertIn("placeholder-sample-selection", preview["risk_labels"])
        self.assertTrue(preview["unresolved_placeholders"])
        self.assertEqual(preview["unresolved_placeholders"][0]["head"], "drum-pad-load")
        self.assertEqual(preview["unresolved_placeholders"][0]["resolve_with"][0]["query"], "zap")
        self.assertEqual(preview["required_inputs"][0]["source"], "browser-search-result")
        self.assertEqual(preview["required_inputs"][0]["search_query"], "zap")
        self.assertEqual(preview["required_inputs"][0]["resolution_command"], "browser-search zap")
        self.assertEqual(preview["required_inputs"][2]["search_query"], "perc")
        self.assertEqual(preview["required_inputs"][2]["resolution_command"], "browser-search perc")
        self.assertEqual(preview["execution_status"]["status"], "inputs-required")
        self.assertIn("samples/<zap-1>", preview["execution_status"]["blocking_reasons"])
        self.assertEqual(preview["recommended_action"]["type"], "collect-inputs")
        self.assertIn("samples/<zap-1>", preview["recommended_action"]["required_inputs"])
        self.assertEqual(preview["recommended_action"]["required_input_details"][0]["search_query"], "zap")
        self.assertEqual(preview["recommended_action"]["required_input_details"][0]["resolution_command"], "browser-search zap")
        self.assertEqual(preview["recommended_action"]["input_resolution_commands"], ["browser-search zap", "browser-search perc"])
        self.assertIn("placeholder inputs", preview["next_action"])

    def test_query_overrides_shape_macro_preview_defaults(self):
        preview = macro_plan_previews(
            ["workflow-macro render riser-transition"],
            query='make a 16-beat riser on track "Drop Riser" in slot 2 starting at beat 32',
        )[0]

        self.assertIn("Riser MIDI track is 'Drop Riser'", preview["assumptions"])
        self.assertIn("Riser clip length is 16 beats", preview["assumptions"])
        self.assertEqual(preview["query_overrides"]["track"], "Drop Riser")
        self.assertEqual(preview["query_overrides"]["length"], 16.0)
        self.assertEqual(preview["query_overrides"]["slot"], 2)
        self.assertEqual(preview["query_overrides"]["start"], 32.0)

    def test_intent_planning_steps_include_macro_override_cues(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result(
                'make a 16-beat riser on track "Drop Riser" in slot 2 starting at beat 32 before the drop',
                "--memory",
                str(memory_path),
            )
            steps = result["orchestration"]["planning_steps"]

            self.assertTrue(any("Apply explicit macro preview override" in step and "track=Drop Riser" in step for step in steps))
            self.assertTrue(any("Use macro sequence preview" in step and "create-track" in step for step in steps))

    def test_explicit_macro_flags_override_query_defaults(self):
        preview = macro_plan_previews(
            ["workflow-macro render riser-transition --length 4"],
            query="make a 16-beat riser",
        )[0]

        self.assertIn("Riser clip length is 4 beats", preview["assumptions"])
        self.assertNotIn("length", preview["query_overrides"])

    def test_query_override_parser_keeps_only_explicit_constraints(self):
        self.assertEqual(query_macro_overrides("make the transition breathe before the drop"), {})
        self.assertEqual(query_macro_overrides('build a 2-bar loop on track "FX Bus" slot 3'), {"length": 8.0, "slot": 3, "track": "FX Bus"})

    def test_sequence_preview_bounds_large_json_arguments(self):
        preview = macro_plan_previews(["workflow-macro render riser-transition"])[0]
        automation_step = next(step for step in preview["command_sequence_preview"] if step["head"] == "clip-stock-automation-set")

        self.assertTrue(any(str(arg).startswith("<json:") for arg in automation_step["args"]))
        self.assertLessEqual(len(automation_step["args"][-1]), 20)

    def test_macro_preview_planning_steps_surface_gates_and_required_inputs(self):
        previews = macro_plan_previews(["workflow-macro render glitch-drum-transition"])
        steps = macro_preview_planning_steps(previews)

        self.assertTrue(any("inputs-required" in step and "samples/<zap-1>" in step for step in steps))
        self.assertTrue(any("placeholder-sample-selection" in step for step in steps))
        self.assertTrue(any("samples/<zap-1>" in step for step in steps))
        self.assertTrue(any("browser-search" in step and "drum-pad-load" in step for step in steps))

    def test_macro_preview_planning_steps_classify_mixed_readiness(self):
        previews = macro_plan_previews(
            [
                "workflow-macro render bass-movement",
                "workflow-macro render bass-resampling-pass",
                "workflow-macro render glitch-drum-transition",
            ]
        )
        steps = macro_preview_planning_steps(previews)
        readiness_step = next(step for step in steps if step.startswith("Classify macro execution readiness"))
        action_step = next(step for step in steps if step.startswith("Prioritize macro recommended action"))

        self.assertIn("bass-movement ready-to-adapt", readiness_step)
        self.assertIn("bass-resampling-pass approval-required", readiness_step)
        self.assertIn("glitch-drum-transition inputs-required", readiness_step)
        self.assertIn("bass-movement adapt-plan", action_step)
        self.assertIn("bass-resampling-pass ask-approval", action_step)
        self.assertIn("glitch-drum-transition collect-inputs", action_step)
        self.assertIn("samples/<zap-1>", action_step)
        self.assertLess(action_step.index("bass-resampling-pass ask-approval"), action_step.index("glitch-drum-transition collect-inputs"))
        self.assertLess(action_step.index("glitch-drum-transition collect-inputs"), action_step.index("bass-movement adapt-plan"))

    def test_macro_action_plan_sorts_blockers_before_adapt_actions(self):
        previews = macro_plan_previews(
            [
                "workflow-macro render bass-movement",
                "workflow-macro render bass-resampling-pass",
                "workflow-macro render glitch-drum-transition",
            ]
        )
        plan = macro_action_plan(previews)

        self.assertEqual([action["type"] for action in plan["actions"]], ["ask-approval", "collect-inputs", "adapt-plan"])
        self.assertEqual(plan["next_action"], "ask-approval")
        self.assertEqual(plan["next_macro"], "bass-resampling-pass")
        self.assertTrue(plan["blocked"])
        self.assertTrue(plan["needs_approval"])
        self.assertTrue(plan["needs_inputs"])
        self.assertFalse(plan["needs_review"])
        self.assertEqual(plan["blocked_count"], 2)
        self.assertEqual(plan["ready_count"], 1)
        self.assertEqual(plan["first_blocking_reason"], "resampling-approval")
        self.assertEqual(plan["input_resolution_commands"], ["browser-search zap", "browser-search perc"])
        self.assertEqual(plan["blocking_macros"], ["bass-resampling-pass", "glitch-drum-transition"])
        self.assertEqual(plan["ready_macros"], ["bass-movement"])

    def test_intent_exposes_structured_macro_action_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("make a shimmer riser that inhales before the drop", "--memory", str(memory_path))
            plan = result["orchestration"]["macro_action_plan"]

            self.assertEqual(plan["next_action"], "adapt-plan")
            self.assertEqual(plan["next_macro"], "riser-transition")
            self.assertFalse(plan["blocked"])
            self.assertFalse(plan["needs_approval"])
            self.assertFalse(plan["needs_inputs"])
            self.assertFalse(plan["needs_review"])
            self.assertEqual(plan["blocked_count"], 0)
            self.assertEqual(plan["ready_count"], 1)
            self.assertIsNone(plan["first_blocking_reason"])
            self.assertEqual(plan["input_resolution_commands"], [])
            self.assertEqual(plan["ready_macros"], ["riser-transition"])

    def test_intent_planning_steps_include_macro_action_cues(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_memory(tmp)

            result = self.local_result("make a shimmer riser that inhales before the drop", "--memory", str(memory_path))
            steps = result["orchestration"]["planning_steps"]

            self.assertTrue(any("Prioritize macro recommended action" in step and "riser-transition adapt-plan" in step for step in steps))

    def write_memory(self, tmp):
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
        return memory_path


if __name__ == "__main__":
    unittest.main()
