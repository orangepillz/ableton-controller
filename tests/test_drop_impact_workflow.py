import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class DropImpactWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        args = self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)])
        return run_local_command(args)

    def test_drop_hit_harder_routes_to_impact_plan_not_generic_drop_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make the drop hit harder", self.write_overlap_memory(tmp))
            orchestration = result["orchestration"]
            ordered = orchestration["ordered_commands"]
            suppressed = {item["command"]: item for item in orchestration["suppressed_commands"]}
            objective = orchestration["musical_objectives"][0]

            self.assertEqual(result["matches"][0]["id"], "drop-impact")
            self.assertIn("hit harder", result["matches"][0]["matched_query_terms"])
            self.assertIn("workflow-macro render kick-sub-separation", ordered)
            self.assertIn("workflow-macro render drum-punch-bus", ordered)
            self.assertIn("workflow-macro render bass-movement", ordered)
            self.assertIn("workflow-macro render mix-bus-control", ordered)
            self.assertNotIn("workflow-macro render arrangement-phase-scaffold", ordered)
            self.assertNotIn("workflow-macro render riser-transition", ordered)
            self.assertEqual(suppressed["workflow-macro render arrangement-phase-scaffold"]["reason"], "weak-generic-match")
            self.assertEqual(objective["id"], "drop-impact")
            self.assertTrue(any("master loudness" in item for item in objective["constraints"]))

    def test_drop_slam_with_mix_context_keeps_impact_above_mix_only_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make this drop slam without wrecking the mix", self.write_overlap_memory(tmp))
            ordered = result["orchestration"]["ordered_commands"]
            objectives = [item["id"] for item in result["orchestration"]["musical_objectives"]]

            self.assertEqual(result["matches"][0]["id"], "drop-impact")
            self.assertIn("slam", result["matches"][0]["matched_query_terms"])
            self.assertLess(objectives.index("drop-impact"), objectives.index("mix-translation"))
            self.assertIn("stock-controls", ordered)
            self.assertIn("workflow-macro render mix-bus-control", ordered)

    def write_overlap_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps(
                {
                    "intent_mappings": [
                        {
                            "id": "bass-movement",
                            "title": "Bass Movement",
                            "confidence": 0.54,
                            "status": "active",
                            "triggers": ["bass", "drop"],
                            "query_terms": ["bass", "movement", "drop"],
                            "recommended_commands": ["workflow-macro render bass-movement"],
                        },
                        {
                            "id": "arrangement-flow",
                            "title": "Arrangement Flow",
                            "confidence": 0.45,
                            "status": "active",
                            "triggers": ["arrangement", "drop"],
                            "query_terms": ["arrangement", "section", "drop"],
                            "recommended_commands": ["workflow-macro render arrangement-phase-scaffold"],
                        },
                        {
                            "id": "riser-transition",
                            "title": "Riser Transition",
                            "confidence": 0.32,
                            "status": "active",
                            "triggers": ["drop"],
                            "query_terms": ["riser", "build", "drop"],
                            "recommended_commands": ["workflow-macro render riser-transition"],
                        },
                        {
                            "id": "mix-bus-control",
                            "title": "Mix Bus Control",
                            "confidence": 0.75,
                            "status": "active",
                            "triggers": ["mix", "master"],
                            "query_terms": ["mix", "master", "loudness"],
                            "recommended_commands": ["workflow-macro render mix-bus-control", "stock-controls"],
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
                        {
                            "id": "workflow-macro.mix-bus-control",
                            "name": "mix-bus-control",
                            "description": "Prepare a conservative mix/master preview chain.",
                            "confidence": 0.62,
                            "tags": ["mixing", "mastering"],
                            "linked_intent_ids": ["mix-bus-control"],
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
