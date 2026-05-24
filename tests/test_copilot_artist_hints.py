import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


class CopilotArtistHintTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def local_result(self, query, memory_path):
        return run_local_command(self.parser.parse_args(["copilot-intent", query, "--memory", str(memory_path)]))

    def test_tipper_request_surfaces_non_imitative_bass_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make it more Tipper-like with liquid bass movement", self.write_memory(tmp))
            hint = result["profile_hints"]["artist_inspiration"][0]

            self.assertEqual(hint["label"], "tipper-inspired-principles")
            self.assertIn("low-end clarity", hint["focus_axes"])
            self.assertIn("workflow-macro render bass-movement", hint["recommended_commands"])
            self.assertIn("do not recreate", hint["non_imitation"])

    def test_g_jones_request_surfaces_contrast_and_resampling_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make this more G Jones with stark contrast and glitches", self.write_memory(tmp))
            hint = result["profile_hints"]["artist_inspiration"][0]

            self.assertEqual(hint["label"], "g-jones-inspired-principles")
            self.assertIn("contrast", hint["focus_axes"])
            self.assertIn("workflow-macro render bass-resampling-pass", hint["recommended_commands"])

    def test_chris_lake_request_surfaces_groove_and_kick_bass_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("give the drums a Chris Lake groove", self.write_memory(tmp))
            hint = result["profile_hints"]["artist_inspiration"][0]

            self.assertEqual(hint["label"], "chris-lake-inspired-principles")
            self.assertIn("groove", hint["focus_axes"])
            self.assertIn("workflow-macro render drum-punch-bus", hint["recommended_commands"])

    def test_generic_glitch_request_does_not_infer_named_artist(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.local_result("make a glitch transition into the drop", self.write_memory(tmp))

            self.assertNotIn("artist_inspiration", result["profile_hints"])

    def write_memory(self, tmp):
        memory_path = Path(tmp) / "memory.json"
        memory_path.write_text(
            json.dumps({"intent_mappings": [], "signals": [], "workflow_macros": []}),
            encoding="utf-8",
        )
        return memory_path


if __name__ == "__main__":
    unittest.main()
