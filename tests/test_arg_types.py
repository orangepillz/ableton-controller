import argparse
import unittest

from ableton_controller.arg_types import (
    bool_arg,
    float_list_arg,
    int_list_arg,
    scalar_value,
    track_value,
    warp_mode_value,
)


class ArgTypeTests(unittest.TestCase):
    def test_bool_arg_accepts_common_values(self):
        self.assertIs(bool_arg("yes"), True)
        self.assertIs(bool_arg("0"), False)
        with self.assertRaises(argparse.ArgumentTypeError):
            bool_arg("maybe")

    def test_track_value_coerces_numeric_identifiers(self):
        self.assertEqual(track_value("4"), 4)
        self.assertEqual(track_value("Synth"), "Synth")

    def test_list_args_accept_csv_and_json(self):
        self.assertEqual(int_list_arg("1, 2,3"), [1, 2, 3])
        self.assertEqual(int_list_arg("[4, 5]"), [4, 5])
        self.assertEqual(float_list_arg("0, 1.25"), [0.0, 1.25])
        self.assertEqual(float_list_arg("[2, 3.5]"), [2.0, 3.5])

    def test_warp_mode_names_and_indexes(self):
        self.assertEqual(warp_mode_value("complex-pro"), 6)
        self.assertEqual(warp_mode_value("3"), 3)
        with self.assertRaises(argparse.ArgumentTypeError):
            warp_mode_value("9")

    def test_scalar_value_preserves_strings_after_simple_types(self):
        self.assertIs(scalar_value("true"), True)
        self.assertIsNone(scalar_value("none"))
        self.assertEqual(scalar_value("42"), 42)
        self.assertEqual(scalar_value("3.5"), 3.5)
        self.assertEqual(scalar_value("Auto Filter"), "Auto Filter")


if __name__ == "__main__":
    unittest.main()
