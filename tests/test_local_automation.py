import unittest

from ableton_controller.local_automation import applescript_key_action, parse_combo


class LocalAutomationTests(unittest.TestCase):
    def test_parse_combo_deduplicates_modifiers(self):
        self.assertEqual(parse_combo("cmd+command+s"), ("s", ["command down"]))

    def test_applescript_key_action_uses_key_codes_for_special_keys(self):
        self.assertEqual(applescript_key_action("shift+tab"), "key code 48 using {shift down}")

    def test_applescript_key_action_uses_keystroke_for_characters(self):
        self.assertEqual(applescript_key_action("cmd+s"), 'keystroke "s" using {command down}')

    def test_unknown_modifier_exits(self):
        with self.assertRaises(SystemExit):
            parse_combo("hyper+s")


if __name__ == "__main__":
    unittest.main()
