import unittest

from ableton_controller.target_aliases import target_alias_probe_command, target_aliases
from copilot_improvement.memory import default_memory, upsert_signal


class TargetAliasTests(unittest.TestCase):
    def test_derives_personal_target_aliases_from_project_names(self):
        memory = default_memory()
        upsert_signal(memory, category="project.name", label="BD", evidence="Name in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="Kicks", evidence="Name in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="SC Trigger", evidence="Name in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="A-Reverb", evidence="Name in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="B-Delay", evidence="Name in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="5-Maschine 2", evidence="Name in set.", source="set.als")

        aliases = target_aliases(memory)
        by_role = {alias["role"]: alias for alias in aliases}

        self.assertEqual(by_role["kick"]["aliases"][:2], ["BD", "Kicks"])
        self.assertEqual(by_role["sidechain"]["aliases"], ["SC Trigger"])
        self.assertEqual(by_role["reverb-return"]["aliases"], ["A-Reverb"])
        self.assertEqual(by_role["delay-return"]["aliases"], ["B-Delay"])
        self.assertNotIn("B-Delay", by_role["kick"]["aliases"])
        self.assertNotIn("5-Maschine 2", by_role["sidechain"]["aliases"])
        self.assertGreater(by_role["kick"]["confidence"], 0.2)

    def test_builds_concrete_probe_command_from_ranked_aliases(self):
        command = target_alias_probe_command(
            [
                {"role": "kick", "aliases": ["BD", "Kicks"]},
                {"role": "sidechain", "aliases": ["SC Trigger"]},
                {"role": "drums", "aliases": ["Drums"]},
            ]
        )

        self.assertEqual(
            command,
            'session-snapshot --track "BD" --track "SC Trigger" --track "Drums" --device-tree-depth 3',
        )


if __name__ == "__main__":
    unittest.main()
