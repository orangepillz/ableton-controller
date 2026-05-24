import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_artist_request_gets_ordered_commands_and_guardrail(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make it more Tipper-like with liquid bass movement", self.write_memory(tmp))
            orchestration = result["orchestration"]

            self.assertEqual(orchestration["mode"], "revise-current-plan")
            self.assertEqual(orchestration["ordered_commands"][0], "session-snapshot")
            self.assertIn("workflow-macro render bass-movement", orchestration["ordered_commands"])
            self.assertIn("low-end clarity", orchestration["focus_axes"])
            self.assertIn("do not recreate", orchestration["non_imitation"])
            self.assertTrue(any("original production constraints" in step for step in orchestration["planning_steps"]))

    def test_revision_request_switches_orchestration_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("not quite, make it less busy", self.write_memory(tmp))
            orchestration = result["orchestration"]

            self.assertEqual(orchestration["mode"], "revise-current-plan")
            self.assertEqual(orchestration["ordered_commands"], ["session-snapshot"])
            self.assertIn("negative-revision-not-quite", orchestration["planning_steps"][0])

    def test_orchestration_dedupes_match_and_macro_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
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
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("add bass movement", memory_path)
            commands = result["orchestration"]["ordered_commands"]
            sources = result["orchestration"]["command_sources"]
            bass_source = next(
                source for source in sources if source["command"] == "workflow-macro render bass-movement"
            )
            source_types = {source["type"] for source in bass_source["sources"]}

            self.assertEqual(commands.count("workflow-macro render bass-movement"), 1)
            self.assertEqual(commands[0], "session-snapshot")
            self.assertEqual(source_types, {"intent_mapping", "workflow_macro"})
            self.assertEqual(result["orchestration"]["suppressed_commands"], [])

    def test_orchestration_explains_query_suppressed_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make it G Jones energy", self.write_memory(tmp))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertNotIn("workflow-macro render bass-resampling-pass", orchestration["ordered_commands"])
            self.assertEqual(suppressed["workflow-macro render bass-resampling-pass"]["reason"], "query-mismatch")
            self.assertEqual(suppressed["workflow-macro render bass-resampling-pass"]["sources"][0]["type"], "artist_inspiration")
            self.assertTrue(any("Suppress learned commands" in step for step in orchestration["planning_steps"]))

    def test_orchestration_explains_meta_command_suppression(self):
        with tempfile.TemporaryDirectory() as tmp:
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
                                "triggers": ["bass", "movement"],
                                "query_terms": ["bass", "movement"],
                                "recommended_commands": [
                                    "copilot-intent add bass movement",
                                    "workflow-macro render bass-movement",
                                ],
                            }
                        ],
                        "workflow_macros": [],
                        "signals": [],
                    }
                ),
                encoding="utf-8",
            )

            result = self.local_result("add bass movement", memory_path)
            suppressed = {item["command"]: item for item in result["orchestration"]["suppressed_commands"]}

            self.assertNotIn("copilot-intent add bass movement", result["orchestration"]["ordered_commands"])
            self.assertEqual(suppressed["copilot-intent add bass movement"]["reason"], "meta-command")
            self.assertEqual(suppressed["copilot-intent add bass movement"]["sources"][0]["type"], "intent_mapping")

    def test_macro_render_step_omits_suppressed_macro_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
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
                                "triggers": ["bass", "movement"],
                                "query_terms": ["bass", "movement"],
                                "recommended_commands": [
                                    "workflow-macro render bass-movement",
                                    "workflow-macro render bass-resampling-pass",
                                ],
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

            result = self.local_result("add bass movement", memory_path)
            render_steps = [step for step in result["orchestration"]["planning_steps"] if step.startswith("Render and adapt")]

            self.assertEqual(
                render_steps,
                ["Render and adapt reusable macro plan(s): workflow-macro render bass-movement."],
            )
            self.assertIn(
                "workflow-macro render bass-resampling-pass",
                [item["command"] for item in result["orchestration"]["suppressed_commands"]],
            )

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps({"intent_mappings": [], "signals": [], "workflow_macros": []}),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
