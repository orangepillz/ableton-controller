import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPERS = REPO_ROOT / "scripts" / "stock_device_generator_lib.py"
SPEC = importlib.util.spec_from_file_location("stock_device_generator_lib", HELPERS)
stock_device_generator_lib = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stock_device_generator_lib)
build_controls = stock_device_generator_lib.build_controls
track_kind = stock_device_generator_lib.track_kind
unique_strings = stock_device_generator_lib.unique_strings


class StockDeviceGeneratorLibTests(unittest.TestCase):
    def test_build_controls_preserves_aliases_and_disambiguates_slugs(self):
        controls = build_controls(
            [
                {"index": 0, "name": "Frequency", "original_name": "Freq", "min": 0, "max": 1},
                {"index": 1, "name": "Frequency", "original_name": None, "min": 0, "max": 1},
            ]
        )

        self.assertEqual(controls[0]["slug"], "frequency")
        self.assertEqual(controls[1]["slug"], "frequency_1")
        self.assertIn("Freq", controls[0]["aliases"])
        self.assertEqual(controls[0]["parameter"]["name"], "Frequency")

    def test_track_kind_classifies_audio_effects(self):
        self.assertEqual(track_kind("audio_effects"), "audio")
        self.assertEqual(track_kind({"root": "max_for_live", "path": "max_for_live/Max Audio Effect/Foo"}), "audio")
        self.assertEqual(track_kind("instruments"), "midi")

    def test_unique_strings_keeps_order(self):
        self.assertEqual(unique_strings(["A", "B", "A", None, 2]), ["A", "B", "2"])


if __name__ == "__main__":
    unittest.main()
