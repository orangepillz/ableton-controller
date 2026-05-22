import importlib.util
import unittest
from pathlib import Path


def load_plan_module():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "skills" / "ableton-producer" / "scripts" / "ableton_plan.py"
    spec = importlib.util.spec_from_file_location("ableton_plan", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AbletonProducerPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_plan_module()

    def test_render_plan_quotes_commands(self):
        plan = {
            "summary": "Create a bass clip.",
            "commands": [
                {"why": "Create track.", "args": ["create-track", "--type", "midi", "--name", "Drop Bass"]},
                {
                    "why": "Add notes.",
                    "args": [
                        "midi-add-notes",
                        "--track",
                        "Drop Bass",
                        "--slot",
                        0,
                        "--notes",
                        '[{"pitch":36,"start_time":0,"duration":1,"velocity":110}]',
                    ],
                },
            ],
        }

        rendered = self.module.render_plan(plan, Path("/tmp/abletonctl.py"), "python3")

        self.assertIn("Summary: Create a bass clip.", rendered)
        self.assertIn("python3 /tmp/abletonctl.py create-track --type midi --name 'Drop Bass'", rendered)
        self.assertIn("midi-add-notes", rendered)

    def test_unknown_command_is_error(self):
        _, errors, _ = self.module.validate_plan({"commands": [{"args": ["make-drop-huge"]}]})

        self.assertEqual(errors, ["step 1: unknown abletonctl command 'make-drop-huge'"])

    def test_destructive_command_warns(self):
        _, errors, warnings = self.module.validate_plan({"commands": [{"args": ["clip-delete", "--track", "Bass"]}]})

        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["step 1: potentially destructive command 'clip-delete'"])

    def test_command_shorthand_rejects_non_list_flags(self):
        _, errors, _ = self.module.validate_plan({"commands": [{"command": "status", "flags": "--bad"}]})

        self.assertEqual(errors, ["step 1: step flags must be a list when command shorthand is used"])


if __name__ == "__main__":
    unittest.main()
