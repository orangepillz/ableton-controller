import unittest

from ableton_controller.copilot_followups import likely_followups


class CopilotFollowupTests(unittest.TestCase):
    def test_workflow_habits_add_followup_predictions(self):
        followups = likely_followups(
            [
                {
                    "id": "bass-movement",
                    "title": "Bass Movement",
                    "confidence": 0.5,
                    "score": 0.5,
                    "likely_followups": ["render a resampling pass"],
                }
            ],
            [
                {
                    "id": "project.workflow.spatial-send-project-workflow",
                    "label": "spatial-send-project-workflow",
                    "confidence": 0.4,
                    "matched_terms": ["delay", "space"],
                }
            ],
        )
        labels = [item["label"] for item in followups]
        habit = next(item for item in followups if item["label"] == "automate send throws")

        self.assertIn("render a resampling pass", labels)
        self.assertEqual(habit["priority"], "workflow-habit")
        self.assertEqual(habit["matched_terms"], ["delay", "space"])
        self.assertIn("spatial-send-project-workflow", habit["why"])


if __name__ == "__main__":
    unittest.main()
