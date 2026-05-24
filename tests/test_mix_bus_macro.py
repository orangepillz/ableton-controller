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


class MixBusMacroTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.plan_module = load_plan_module()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["workflow-macro", *argv]))

    def test_mix_bus_macro_prepares_conservative_preview_chain(self):
        plan = self.local_result("render", "mix-bus-control", "--track", "Master")
        commands = [step["args"] for step in plan["commands"] if step["args"]]
        command_names = [args[0] for args in commands]
        _steps, errors, warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertFalse(warnings)
        self.assertEqual(plan["macro"], "mix-bus-control")
        self.assertEqual(commands[0], ["session-snapshot", "--track", "Master", "--device-tree-depth", 6])
        self.assertIn(["device-add-stock", "--target-track", "Master", "--path", "audio_effects/Utility"], commands)
        self.assertIn(["device-add-stock", "--target-track", "Master", "--path", "audio_effects/Limiter"], commands)
        self.assertIn(["stock-controls", "--device", "Limiter"], commands)
        self.assertNotIn("set-stock-control", command_names)
        self.assertNotIn("save", command_names)

    def test_mix_bus_macro_mentions_learned_master_evidence_when_memory_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {"id": "project.name.master", "category": "project.name", "label": "Master", "confidence": 0.3},
                            {"id": "project.device.limiter", "category": "project.device", "label": "Limiter", "confidence": 0.35},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result("render", "mix-bus-control", "--memory", str(memory_path))

            self.assertIn("Mix/master target is 'Master'", plan["assumptions"])
            self.assertIn("Historical project evidence includes a Master track naming signal.", plan["assumptions"])


if __name__ == "__main__":
    unittest.main()
