import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    path = REPO_ROOT / "remote_scripts" / "Codex_AI" / ("%s.py" % name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BrowserCommandMixin = load_module("browser_commands").BrowserCommandMixin
ClipReferenceMixin = load_module("clip_refs").ClipReferenceMixin
DeviceCommandMixin = load_module("device_commands").DeviceCommandMixin
ResolverMixin = load_module("resolvers").ResolverMixin
SerializationMixin = load_module("serialization").SerializationMixin
SerumCommandMixin = load_module("serum_commands").SerumCommandMixin
TrackCommandMixin = load_module("track_commands").TrackCommandMixin
UtilityMixin = load_module("utilities").UtilityMixin


class FakeParameter:
    def __init__(self, name, value=0.0, minimum=0.0, maximum=1.0):
        self.name = name
        self.value = value
        self.min = minimum
        self.max = maximum

    def str_for_value(self, value):
        return str(value)


class FakeDevice:
    def __init__(self, name, parameters=None, class_name="PluginDevice", parameter_names=None):
        self.name = name
        self.class_name = class_name
        self.parameters = parameters or []
        self.parameter_names = parameter_names or []
        self.stored_bank = None
        self.can_have_chains = False
        self.canonical_parent = None

    def get_parameter_names(self, start=0, end=-1):
        names = self.parameter_names
        if end < 0:
            return names[start:]
        return names[start:end]


class FakeTrack:
    def __init__(self, name, devices=None, has_midi_input=True):
        self.name = name
        self.devices = []
        self.has_midi_input = has_midi_input
        self.clip_slots = []
        self.mixer_device = SimpleNamespace(
            volume=FakeParameter("Volume", 0.85),
            panning=FakeParameter("Pan", 0.0, -1.0, 1.0),
            sends=[],
        )
        for device in devices or []:
            self.add_device(device)

    def add_device(self, device):
        device.canonical_parent = self
        self.devices.append(device)


class FakeBrowserItem:
    def __init__(self, name, source="", uri="", is_loadable=False, is_device=True, children=None):
        self.name = name
        self.source = source
        self.uri = uri
        self.is_loadable = is_loadable
        self.is_device = is_device
        self.is_folder = bool(children)
        self.is_selected = False
        self.children = children or []


class FakeBrowser:
    def __init__(self, song, plugins):
        self.song = song
        self.plugins = plugins
        self.loaded = None

    def load_item(self, item):
        self.loaded = item
        self.song.view.selected_track.add_device(FakeDevice(item.name, [FakeParameter("Filter Cutoff", 0.0, 0.0, 1000.0)]))


class FakeSong:
    def __init__(self, tracks):
        self.tracks = tracks
        self.return_tracks = []
        self.master_track = FakeTrack("Master")
        self.view = SimpleNamespace(selected_track=tracks[0])
        self.scenes = []

    def move_device(self, device, target, index):
        source = device.canonical_parent
        source.devices.remove(device)
        insert_index = max(0, min(int(index), len(target.devices)))
        target.devices.insert(insert_index, device)
        device.canonical_parent = target
        return insert_index


class FakeBridge(
    SerumCommandMixin,
    DeviceCommandMixin,
    BrowserCommandMixin,
    TrackCommandMixin,
    ClipReferenceMixin,
    ResolverMixin,
    SerializationMixin,
    UtilityMixin,
):
    def __init__(self, tracks, plugins):
        self._song = FakeSong(tracks)
        self.browser = FakeBrowser(self._song, plugins)

    def song(self):
        return self._song

    def application(self):
        return SimpleNamespace(browser=self.browser)

    def instance_identifier(self):
        return 1234


def serum_plugins_root():
    vst2 = FakeBrowserItem("Serum", source="VST", uri="vst://xfer/serum", is_loadable=True, is_device=False)
    vst3 = FakeBrowserItem("Serum", source="VST3", uri="vst3://xfer/serum", is_loadable=True, is_device=False)
    audio_unit = FakeBrowserItem("Serum", source="Audio Unit", uri="au://xfer/serum", is_loadable=True, is_device=False)
    return FakeBrowserItem(
        "Plugins",
        children=[
            FakeBrowserItem("VST", children=[vst2]),
            FakeBrowserItem("VST3", children=[vst3]),
            FakeBrowserItem("Audio Units", children=[audio_unit]),
        ],
    )


class SerumCommandTests(unittest.TestCase):
    def test_serum_add_prefers_vst3_and_honors_target_index(self):
        utility = FakeDevice("Utility", [])
        track = FakeTrack("Lead", [utility])
        bridge = FakeBridge([track], serum_plugins_root())

        result = bridge._serum_add({"target_track": "Lead", "format": "vst", "target_index": 0})

        self.assertEqual(track.devices[0].name, "Serum")
        self.assertIs(track.devices[1], utility)
        self.assertEqual(bridge.browser.loaded.source, "VST3")
        self.assertEqual(result["device"]["name"], "Serum")

    def test_serum_add_requires_midi_track(self):
        track = FakeTrack("Audio", has_midi_input=False)
        bridge = FakeBridge([track], serum_plugins_root())

        with self.assertRaisesRegex(ValueError, "MIDI track"):
            bridge._serum_add({"target_track": "Audio", "format": "vst"})

    def test_serum_names_reads_hidden_plugin_parameter_names(self):
        serum = FakeDevice("Serum", [FakeParameter("Device On", 1.0)], parameter_names=["MasterVol", "A Vol", "A Pan"])
        track = FakeTrack("Lead", [serum])
        bridge = FakeBridge([track], serum_plugins_root())

        result = bridge._serum_names({"track": "Lead", "start": 1, "end": 3})

        self.assertEqual(result["names"], ["A Vol", "A Pan"])
        self.assertEqual(result["length"], 2)

    def test_serum_set_targets_selected_instance(self):
        first = FakeDevice("Serum", [FakeParameter("Filter Cutoff", 100.0, 0.0, 1000.0)])
        second = FakeDevice("Serum Bass", [FakeParameter("Filter Cutoff", 100.0, 0.0, 1000.0)])
        track = FakeTrack("Lead", [first, second])
        bridge = FakeBridge([track], serum_plugins_root())

        result = bridge._serum_set_param({"track": "Lead", "instance": 1, "param": "Filter Cutoff", "normalized": 0.5})

        self.assertEqual(first.parameters[0].value, 100.0)
        self.assertEqual(second.parameters[0].value, 500.0)
        self.assertEqual(result["parameter"]["value"], 500.0)

    def test_serum_control_requires_instance_when_ambiguous(self):
        track = FakeTrack("Lead", [FakeDevice("Serum"), FakeDevice("Serum Bass")])
        bridge = FakeBridge([track], serum_plugins_root())

        with self.assertRaisesRegex(ValueError, "Multiple Serum instances"):
            bridge._serum_params({"track": "Lead"})

    def test_serum_set_many_applies_each_control(self):
        cutoff = FakeParameter("Filter Cutoff", 100.0, 0.0, 1000.0)
        wt_pos = FakeParameter("WT Pos", 0.2, 0.0, 1.0)
        track = FakeTrack("Lead", [FakeDevice("Serum", [cutoff, wt_pos])])
        bridge = FakeBridge([track], serum_plugins_root())

        result = bridge._serum_set_many(
            {
                "track": "Lead",
                "controls": [
                    {"param": "Filter Cutoff", "normalized": 0.25},
                    {"param": "WT Pos", "delta": 0.1},
                ],
            }
        )

        self.assertEqual(cutoff.value, 250.0)
        self.assertAlmostEqual(wt_pos.value, 0.3)
        self.assertTrue(result["done"])


if __name__ == "__main__":
    unittest.main()
