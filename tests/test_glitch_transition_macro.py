import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_plan_module():
    script = REPO_ROOT / "skills" / "ableton-producer" / "scripts" / "ableton_plan.py"
    spec = importlib.util.spec_from_file_location("ableton_plan", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GlitchTransitionMacroTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.plan_module = load_plan_module()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["workflow-macro", *argv]))

    def test_adds_pad_mapping_verification_from_refinement_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {
                                "id": "chat.refinement.pad-mapping-correction",
                                "category": "chat.refinement",
                                "label": "pad-mapping-correction",
                                "confidence": 0.23,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result(
                "render",
                "glitch-drum-transition",
                "--track",
                "Zap Rack",
                "--secondary-track",
                "Perc Rack",
                "--synth-track",
                "Lead Synth",
                "--memory",
                str(memory_path),
            )
            commands = [step["args"] for step in plan["commands"] if step["args"]]
            _steps, errors, warnings = self.plan_module.validate_plan(plan)

            self.assertEqual(errors, [])
            self.assertFalse(warnings)
            self.assertTrue(any("distinct Drum Rack pads" in assumption for assumption in plan["assumptions"]))
            self.assertIn(["device-tree", "--track", "Zap Rack", "--depth", 6], commands)
            self.assertIn(["device-tree", "--track", "Perc Rack", "--depth", 6], commands)


if __name__ == "__main__":
    unittest.main()
