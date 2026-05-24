import unittest

from ableton_controller.copilot_macro_preview import macro_plan_previews
from ableton_controller.copilot_macro_preview_cues import macro_action_plan


class CopilotMacroActionPlanTests(unittest.TestCase):
    def test_resampling_action_plan_exposes_deduped_blocker_details(self):
        previews = macro_plan_previews(["workflow-macro render bass-resampling-pass"])
        plan = macro_action_plan(previews)
        details = {item["label"]: item for item in plan["blocker_details"]}

        self.assertEqual(plan["blocker_levels"], ["approval-required", "plan-first"])
        self.assertEqual(plan["next_blocker_detail"]["label"], "resampling-approval")
        self.assertEqual(plan["blocker_details"][0]["level"], "approval-required")
        self.assertEqual(details["resampling-approval"]["level"], "approval-required")
        self.assertEqual(details["arrangement-automation-range"]["level"], "plan-first")
        self.assertEqual(details["routing-change-review"]["level"], "plan-first")

    def test_placeholder_action_plan_exposes_resolution_details(self):
        previews = macro_plan_previews(["workflow-macro render glitch-drum-transition"])
        plan = macro_action_plan(previews)
        details = {item["label"]: item for item in plan["blocker_details"]}

        self.assertEqual(plan["blocker_levels"], ["inputs-required"])
        self.assertEqual(plan["next_blocker_detail"]["label"], "samples/<zap-1>")
        self.assertEqual(plan["input_resolution_commands"], ["browser-search zap", "browser-search perc"])
        self.assertEqual(details["samples/<zap-1>"]["resolution_command"], "browser-search zap")
        self.assertEqual(details["samples/<perc-1>"]["search_query"], "perc")

    def test_ready_action_plan_has_empty_blocker_details(self):
        previews = macro_plan_previews(["workflow-macro render riser-transition"])
        plan = macro_action_plan(previews)

        self.assertEqual(plan["blocker_details"], [])
        self.assertIsNone(plan["next_blocker_detail"])
        self.assertEqual(plan["blocker_levels"], [])


if __name__ == "__main__":
    unittest.main()
