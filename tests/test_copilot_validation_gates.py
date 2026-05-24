import subprocess
import tempfile
import unittest
from pathlib import Path

from copilot_improvement.reports import VALIDATION_COMMANDS


REPO_ROOT = Path(__file__).resolve().parents[1]


class CopilotValidationGateTests(unittest.TestCase):
    def test_validation_commands_include_size_gate(self):
        self.assertIn("python3 scripts/copilot_size_gate.py", VALIDATION_COMMANDS)

    def test_size_gate_fails_on_oversized_python_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large.py").write_text("x = 1\n" * 300, encoding="utf-8")

            result = subprocess.run(
                ["python3", "scripts/copilot_size_gate.py", str(root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("large.py has 300 lines", result.stdout)


if __name__ == "__main__":
    unittest.main()
