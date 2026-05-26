import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "remote_scripts" / "Codex_AI" / "lom_commands.py"
SPEC = importlib.util.spec_from_file_location("lom_commands", MODULE_PATH)
lom_commands = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(lom_commands)


class FakeLomBridge(lom_commands.LomCommandMixin):
    def _resolve_lom_path(self, path):
        return lambda *args, **kwargs: {"path": path, "args": args, "kwargs": kwargs}

    def _serialize(self, value):
        return value


class LomCommandTests(unittest.TestCase):
    def test_lom_call_rejects_plugin_store_chosen_bank(self):
        bridge = FakeLomBridge()

        with self.assertRaisesRegex(ValueError, "store_chosen_bank"):
            bridge._lom_call({"path": "song.tracks[0].devices[0].store_chosen_bank", "args": [0, 0]})


if __name__ == "__main__":
    unittest.main()
