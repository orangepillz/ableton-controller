import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotOrchestrationFollowupTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_orchestration_promotes_likely_followups(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add bass movement", self.write_bass_followup_memory(tmp))
            followups = result["orchestration"]["likely_followups"]

            self.assertEqual(followups[0]["label"], "render a resampling pass")
            self.assertEqual(followups[0]["intent_id"], "bass-movement")
            self.assertEqual(followups[0]["priority"], "probable-next")
            self.assertGreater(followups[0]["confidence"], 0.6)
            self.assertTrue(any("Anticipate likely follow-up operations" in step for step in result["orchestration"]["planning_steps"]))

    def test_current_query_followup_is_prioritized(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("add call and response variation to the bass movement", self.write_bass_followup_memory(tmp))
            followups = result["orchestration"]["likely_followups"]

            self.assertEqual(followups[0]["label"], "add call/response variation")
            self.assertEqual(followups[0]["priority"], "current-request")
            self.assertEqual(followups[0]["rank"], 1)
            self.assertTrue(followups[0]["matched_current_query"])
            self.assertEqual(followups[0]["matched_terms"], ["add call/response variation"])
            self.assertIn("Current query directly names", followups[0]["why"])

    def test_verification_only_followup_request_suppresses_edit_macros(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("verify return levels", self.write_space_followup_memory(tmp))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertEqual(result["matches"][0]["id"], "space-delay-rides")
            self.assertEqual(orchestration["ordered_commands"], ["session-snapshot"])
            self.assertEqual(
                suppressed["workflow-macro render personalized-space-chain"]["reason"],
                "verification-followup",
            )

    def write_bass_followup_memory(self, tmp):
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
                        "likely_followups": [
                            "render a resampling pass",
                            "add call/response variation",
                        ],
                    }
                ],
                "workflow_macros": [],
                "signals": [],
            },
        )

    def write_space_followup_memory(self, tmp):
        return self.write_memory(
            tmp,
            {
                "intent_mappings": [
                    {
                        "id": "space-delay-rides",
                        "title": "Reverb/Delay Spatial Movement",
                        "confidence": 0.62,
                        "status": "active",
                        "triggers": ["reverb", "delay", "space", "send"],
                        "query_terms": ["reverb", "delay", "space", "send"],
                        "recommended_commands": ["workflow-macro render personalized-space-chain"],
                        "likely_followups": ["verify return levels", "automate send throws"],
                    }
                ],
                "workflow_macros": [
                    {
                        "id": "workflow-macro.personalized-space-chain",
                        "name": "personalized-space-chain",
                        "description": "Add learned delay and reverb space.",
                        "confidence": 0.8,
                        "tags": ["mixing", "spatial"],
                        "linked_intent_ids": ["space-delay-rides"],
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
