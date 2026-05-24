import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


track_commands = load_module("track_commands", REPO_ROOT / "remote_scripts" / "Codex_AI" / "track_commands.py")
utilities = load_module("utilities", REPO_ROOT / "remote_scripts" / "Codex_AI" / "utilities.py")
TrackCommandMixin = track_commands.TrackCommandMixin
UtilityMixin = utilities.UtilityMixin


class FakeLocator:
    def __init__(self, name, time):
        self.name = name
        self.time = time
        self.is_song_start = time == 0


class FakeSong:
    def __init__(self, cue_points):
        self.cue_points = cue_points


class FakeBridge(TrackCommandMixin, UtilityMixin):
    def __init__(self, cue_points):
        self._song = FakeSong(cue_points)

    def song(self):
        return self._song


class LocatorCommandTests(unittest.TestCase):
    def test_lists_locator_cue_points(self):
        bridge = FakeBridge([FakeLocator("1", 0), FakeLocator("2", 64)])

        result = bridge._locators()

        self.assertEqual(result["locators"][0]["name"], "1")
        self.assertEqual(result["locators"][1]["time"], 64)

    def test_set_locator_renames_by_time(self):
        bridge = FakeBridge([FakeLocator("1", 0), FakeLocator("2", 64)])

        result = bridge._set_locator({"time": 64, "name": "02 Main Drop"})

        self.assertEqual(result["old_name"], "2")
        self.assertEqual(result["locator"]["name"], "02 Main Drop")
        self.assertEqual(bridge.song().cue_points[1].name, "02 Main Drop")

    def test_set_locator_renames_by_index(self):
        bridge = FakeBridge([FakeLocator("Intro", 0), FakeLocator("Break", 96)])

        result = bridge._set_locator({"locator": 1, "name": "03 Fakeout"})

        self.assertEqual(result["old_name"], "Break")
        self.assertEqual(result["locator"]["index"], 1)
        self.assertEqual(result["locator"]["name"], "03 Fakeout")


if __name__ == "__main__":
    unittest.main()
