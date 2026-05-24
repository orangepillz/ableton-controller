import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace


DRUM_PAD_COMMANDS = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "drum_pad_commands.py"
SPEC = importlib.util.spec_from_file_location("drum_pad_commands", DRUM_PAD_COMMANDS)
drum_pad_commands = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(drum_pad_commands)
DrumPadCommandMixin = drum_pad_commands.DrumPadCommandMixin


class FakeChain:
    name = "Pad Chain"
    devices = []


class FakePad:
    def __init__(self, chains):
        self.name = "Kick"
        self.note = 36
        self.mute = False
        self.solo = False
        self.chains = chains
        self.clear_called = False

    def delete_all_chains(self):
        self.clear_called = True
        self.chains = []


class FakeRack:
    def __init__(self, pad):
        self.name = "Drum Rack"
        self.class_name = "DrumGroupDevice"
        self.parameters = []
        self.drum_pads = [pad]
        self.view = SimpleNamespace(selected_drum_pad=None)


class FakeTrack:
    def __init__(self, rack):
        self.name = "Drums"
        self.devices = [rack]
        self.view = SimpleNamespace(selected_device=None)


class FakeBrowser:
    def __init__(self, pad):
        self.pad = pad
        self.loaded = None

    def load_item(self, item):
        self.loaded = item
        self.pad.chains = [FakeChain()]


class FakeBridge(DrumPadCommandMixin):
    def __init__(self, pad):
        self.pad = pad
        self.rack = FakeRack(pad)
        self.track = FakeTrack(self.rack)
        self.item = SimpleNamespace(name="Kick.wav", is_loadable=True)
        self.browser = FakeBrowser(pad)
        self.song_view = SimpleNamespace(selected_track=None)
        self.app_view = SimpleNamespace(show_view=lambda _view: None)

    def _safe_get(self, obj, name, default=None):
        return getattr(obj, name, default)

    def _is_indexable_vector(self, value):
        return hasattr(value, "__len__") and hasattr(value, "__getitem__")

    def _resolve_track(self, identifier):
        return self.track

    def _resolve_device(self, track, identifier):
        return self.rack

    def _resolve_browser_item(self, identifier):
        return self.item

    def _track_info(self, track, index, kind="track"):
        return {"name": track.name, "index": index, "kind": kind}

    def _track_index(self, track):
        return 0

    def _track_kind(self, track):
        return "track"

    def _device_info(self, device, index):
        return {"name": device.name, "index": index}

    def _device_index(self, device):
        return 0

    def _browser_item_info(self, item):
        return {"name": item.name, "is_loadable": item.is_loadable}

    def _container_device_infos(self, container):
        return []

    def song(self):
        return SimpleNamespace(view=self.song_view)

    def application(self):
        return SimpleNamespace(browser=self.browser, view=self.app_view)


class DrumPadCommandTests(unittest.TestCase):
    def test_load_refuses_existing_pad_without_clear(self):
        pad = FakePad([FakeChain()])
        bridge = FakeBridge(pad)

        with self.assertRaises(ValueError):
            bridge._drum_pad_load({"track": "Drums", "pad": 36, "item": "samples/Kick.wav"})

        self.assertIsNone(bridge.browser.loaded)
        self.assertFalse(pad.clear_called)

    def test_load_clears_and_verifies_pad(self):
        pad = FakePad([FakeChain()])
        bridge = FakeBridge(pad)

        response = bridge._drum_pad_load({"track": "Drums", "pad": 36, "item": "samples/Kick.wav", "clear": True})

        self.assertTrue(response["done"])
        self.assertTrue(pad.clear_called)
        self.assertEqual(response["pad"]["before"]["chain_count"], 1)
        self.assertEqual(response["pad"]["after"]["chain_count"], 1)
        self.assertEqual(bridge.browser.loaded.name, "Kick.wav")
        self.assertIs(bridge.rack.view.selected_drum_pad, pad)


if __name__ == "__main__":
    unittest.main()
