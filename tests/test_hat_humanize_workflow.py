import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser
from ableton_controller.target_aliases import target_aliases
from copilot_improvement.memory import default_memory, upsert_signal


class HatHumanizeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(list(argv)))

    def test_hat_humanize_macro_uses_personal_hat_alias_and_variation(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_hat_memory(tmp)
            plan = self.local_result("workflow-macro", "render", "hat-humanize", "--memory", str(memory_path))
            commands = [step["args"] for step in plan["commands"]]

            self.assertEqual(plan["macro"], "hat-humanize")
            self.assertIn("Hat track is 'CH'", plan["assumptions"])
            self.assertEqual(commands[1][:5], ["midi-get-notes", "--track", "CH", "--slot", 0])
            self.assertIn("--velocity-deviation", commands[2])
            self.assertIn("--probability", commands[2])
            self.assertEqual(commands[-1][0], "midi-get-notes")

    def test_human_hat_request_routes_to_hat_macro_not_drum_bus(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_drum_memory(tmp)
            result = self.local_result("copilot-intent", "make the hats more human", "--memory", str(memory_path))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertEqual(result["matches"][0]["id"], "hat-humanize")
            self.assertIn("workflow-macro render hat-humanize", orchestration["ordered_commands"])
            self.assertIn("midi-transform-notes", orchestration["ordered_commands"])
            self.assertNotIn("workflow-macro render drum-punch-bus", orchestration["ordered_commands"])
            self.assertEqual(suppressed["workflow-macro render drum-punch-bus"]["reason"], "weak-generic-match")
            self.assertEqual(orchestration["musical_objectives"][0]["id"], "groove-humanization")

    def test_robotic_hat_request_suppresses_target_only_drum_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_overlap_memory(tmp)
            result = self.local_result("copilot-intent", "make the hats less robotic", "--memory", str(memory_path))
            orchestration = result["orchestration"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}

            self.assertEqual(result["matches"][0]["id"], "hat-humanize")
            self.assertIn("robotic", result["matches"][0]["matched_query_terms"])
            self.assertNotIn("workflow-macro render drum-punch-bus", orchestration["ordered_commands"])
            self.assertEqual(suppressed["workflow-macro render drum-punch-bus"]["reason"], "weak-generic-match")

    def test_hat_tightening_context_suppresses_drum_and_kick_macros(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = self.write_overlap_memory(tmp)
            result = self.local_result(
                "copilot-intent",
                "tighten the hats against the kick and snare",
                "--memory",
                str(memory_path),
            )
            ordered = result["orchestration"]["ordered_commands"]

            self.assertEqual(result["matches"][0]["id"], "hat-humanize")
            self.assertIn("workflow-macro render hat-humanize", ordered)
            self.assertNotIn("workflow-macro render drum-punch-bus", ordered)
            self.assertNotIn("workflow-macro render kick-sub-separation", ordered)

    def test_project_ch_name_derives_hat_target_alias(self):
        memory = default_memory()
        upsert_signal(memory, category="project.name", label="CH", evidence="Name in set.", source="set.als")

        aliases = {alias["role"]: alias for alias in target_aliases(memory)}

        self.assertEqual(aliases["hats"]["aliases"], ["CH"])

    def write_hat_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps({"signals": [{"category": "project.name", "label": "CH", "confidence": 0.4, "evidence_count": 4}]}),
            encoding="utf-8",
        )
        return memory_path

    def write_drum_memory(self, tmp):
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
                            "triggers": ["drum", "hats"],
                            "query_terms": ["drum", "hats"],
                            "recommended_commands": ["workflow-macro render drum-punch-bus"],
                        }
                    ],
                    "workflow_macros": [
                        {
                            "id": "workflow-macro.drum-punch-bus",
                            "name": "drum-punch-bus",
                            "description": "Prepare a punch-focused drum bus chain.",
                            "confidence": 0.75,
                            "tags": ["mixing", "drums"],
                            "linked_intent_ids": ["drum-kit-building"],
                            "status": "active",
                        }
                    ],
                    "signals": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path

    def write_overlap_memory(self, tmp):
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
                            "triggers": ["drum", "hats", "kick", "snare"],
                            "query_terms": ["drum", "hats", "kick", "snare"],
                            "recommended_commands": ["workflow-macro render drum-punch-bus", "clip-create-midi"],
                        },
                        {
                            "id": "kick-sub-sidechain",
                            "title": "Kick/Sub",
                            "confidence": 0.56,
                            "status": "active",
                            "triggers": ["kick"],
                            "query_terms": ["kick"],
                            "recommended_commands": ["workflow-macro render kick-sub-separation"],
                        },
                    ],
                    "workflow_macros": [
                        {
                            "id": "workflow-macro.drum-punch-bus",
                            "name": "drum-punch-bus",
                            "description": "Prepare a punch-focused drum bus chain.",
                            "confidence": 0.75,
                            "tags": ["mixing", "drums"],
                            "linked_intent_ids": ["drum-kit-building"],
                            "status": "active",
                        },
                        {
                            "id": "workflow-macro.kick-sub-separation",
                            "name": "kick-sub-separation",
                            "description": "Tighten kick/sub timing and prepare controlled ducking.",
                            "confidence": 0.73,
                            "tags": ["mixing", "bass"],
                            "linked_intent_ids": ["kick-sub-sidechain"],
                            "status": "active",
                        },
                    ],
                    "signals": [],
                }
            ),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
