import unittest

from stock_device_controls import find_control, find_device, registry_summary, verify_registry


class StockDeviceControlTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "schema_version": 1,
            "generated_at": "test",
            "live_version": "12",
            "failures": [],
            "devices": [
                {
                    "root": "audio_effects",
                    "path": "audio_effects/Auto Filter",
                    "name": "Auto Filter",
                    "slug": "auto_filter",
                    "class_name": "AutoFilter",
                    "loaded_name": "Auto Filter",
                    "controls": [
                        {
                            "index": 1,
                            "name": "Frequency",
                            "slug": "frequency",
                            "aliases": ["freq"],
                            "parameter": {"name": "Frequency"},
                        }
                    ],
                }
            ],
        }

    def test_find_device_matches_path_slug_and_partial_text(self):
        self.assertEqual(find_device(self.registry, "auto_filter")["name"], "Auto Filter")
        self.assertEqual(find_device(self.registry, "audio_effects/Auto Filter")["class_name"], "AutoFilter")
        self.assertEqual(find_device(self.registry, "filter")["path"], "audio_effects/Auto Filter")

    def test_find_control_matches_index_alias_and_parameter_name(self):
        device = find_device(self.registry, "Auto Filter")
        self.assertEqual(find_control(device, 1)["name"], "Frequency")
        self.assertEqual(find_control(device, "freq")["index"], 1)
        self.assertEqual(find_control(device, "Frequency")["slug"], "frequency")

    def test_summary_and_verification(self):
        self.assertEqual(registry_summary(self.registry)["parameter_count"], 1)
        self.assertTrue(verify_registry(self.registry)["ok"])


if __name__ == "__main__":
    unittest.main()
