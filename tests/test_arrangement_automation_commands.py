import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "automation_commands.py"
SPEC = importlib.util.spec_from_file_location("automation_commands", MODULE_PATH)
automation_commands = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(automation_commands)
AutomationCommandMixin = automation_commands.AutomationCommandMixin

CLIP_MODULE_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "clip_automation_commands.py"
CLIP_SPEC = importlib.util.spec_from_file_location("clip_automation_commands", CLIP_MODULE_PATH)
clip_automation_commands = importlib.util.module_from_spec(CLIP_SPEC)
assert CLIP_SPEC is not None and CLIP_SPEC.loader is not None
CLIP_SPEC.loader.exec_module(clip_automation_commands)
ClipAutomationCommandMixin = clip_automation_commands.ClipAutomationCommandMixin

HELPER_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "automation_helpers.py"
HELPER_SPEC = importlib.util.spec_from_file_location("automation_helpers", HELPER_PATH)
automation_helpers = importlib.util.module_from_spec(HELPER_SPEC)
assert HELPER_SPEC is not None and HELPER_SPEC.loader is not None
HELPER_SPEC.loader.exec_module(automation_helpers)
AutomationHelperMixin = automation_helpers.AutomationHelperMixin


class ArrangementAutomationCommandTests(unittest.TestCase):
    def test_arrangement_automation_set_edits_existing_lane_in_place(self):
        deleted_ranges = []
        inserted_steps = []
        envelope = SimpleNamespace(
            parameter=None,
            delete_events_in_range=lambda start, end: deleted_ranges.append((start, end)),
            insert_step=lambda time, duration, value: inserted_steps.append((time, duration, value)),
            value_at_time=lambda time: 0.8,
        )
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)
        envelope.parameter = parameter
        track = SimpleNamespace(name="Build Bus")
        clip = SimpleNamespace(
            is_arrangement_clip=True,
            is_midi_clip=True,
            length=8.0,
            canonical_parent=track,
            automation_envelopes=[envelope],
        )
        bridge = _Bridge(SimpleNamespace(view=SimpleNamespace(selected_track=None, detail_clip=None)))
        bridge._resolve_clip_ref = lambda payload: {"kind": "arrangement", "track": track, "clip": clip}
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: envelope
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._arrangement_automation_set(
            {"steps": [{"time": 0, "duration": 1, "normalized": 0.8}], "clear": True}
        )

        self.assertEqual(deleted_ranges, [(0.0, 1576800.0)])
        self.assertEqual(inserted_steps, [(0.0, 1.0, 0.8)])
        self.assertFalse(result["materialized_from_session_clip"])
        self.assertTrue(result["done"])

    def test_arrangement_automation_set_materializes_new_midi_lane(self):
        undo_calls = []
        song = SimpleNamespace(
            view=SimpleNamespace(selected_track=None, detail_clip=None),
            begin_undo_step=lambda: undo_calls.append("begin"),
            end_undo_step=lambda: undo_calls.append("end"),
        )
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)
        source_clip = SimpleNamespace(
            is_arrangement_clip=True,
            is_midi_clip=True,
            length=4.0,
            start_time=8.0,
            name="Noise Rise",
            automation_envelopes=[],
        )
        temp_clip = SimpleNamespace(is_arrangement_clip=False, is_midi_clip=True, name="")
        new_clip = SimpleNamespace(is_arrangement_clip=True, is_midi_clip=True, name="Noise Rise")
        slot = SimpleNamespace(has_clip=False)
        slot.create_clip = lambda length: (setattr(slot, "clip", temp_clip), setattr(slot, "has_clip", True))
        slot.delete_clip = lambda: setattr(slot, "has_clip", False)
        duplicates = []
        track = SimpleNamespace(
            name="Build Bus",
            clip_slots=[slot],
            duplicate_clip_to_arrangement=lambda clip, start: duplicates.append((clip, start)),
        )
        source_clip.canonical_parent = track
        inserted_steps = []
        temp_envelope = SimpleNamespace(
            parameter=parameter,
            insert_step=lambda time, duration, value: inserted_steps.append((time, duration, value)),
            value_at_time=lambda time: 0.25,
        )
        new_envelope = SimpleNamespace(parameter=parameter, value_at_time=lambda time: 0.25)

        bridge = _Bridge(song)
        bridge._resolve_clip_ref = lambda payload: {"kind": "arrangement", "track": track, "clip": source_clip}
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: temp_envelope if clip is temp_clip else new_envelope if clip is new_clip else None
        bridge._copy_midi_clip_contents = lambda source, target: setattr(target, "copied_from", source)
        bridge._delete_clip_ref = lambda ref: setattr(ref["clip"], "deleted", True)
        bridge._find_arrangement_clip = lambda track, start, length: new_clip
        bridge._clip_ref_from_clip = lambda clip: {"kind": "arrangement", "track": track, "clip": clip}
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": clip.name}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._arrangement_automation_set(
            {"steps": [{"time": 0, "duration": 1, "normalized": 0.25}], "clear": False}
        )

        self.assertEqual(undo_calls, ["begin", "end"])
        self.assertTrue(source_clip.deleted)
        self.assertIs(temp_clip.copied_from, source_clip)
        self.assertEqual(duplicates, [(temp_clip, 8.0)])
        self.assertEqual(inserted_steps, [(0.0, 1.0, 0.25)])
        self.assertFalse(slot.has_clip)
        self.assertTrue(result["materialized_from_session_clip"])

    def test_arrangement_automation_set_many_materializes_missing_lane_with_existing_target_lane(self):
        undo_calls = []
        song = SimpleNamespace(
            view=SimpleNamespace(selected_track=None, detail_clip=None),
            begin_undo_step=lambda: undo_calls.append("begin"),
            end_undo_step=lambda: undo_calls.append("end"),
        )
        frequency = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)
        resonance = SimpleNamespace(name="Resonance", min=0.0, max=1.0, value=0.0)
        existing_frequency_envelope = SimpleNamespace(parameter=frequency)
        source_clip = SimpleNamespace(
            is_arrangement_clip=True,
            is_midi_clip=True,
            length=4.0,
            start_time=8.0,
            name="Noise Rise",
            automation_envelopes=[existing_frequency_envelope],
        )
        temp_clip = SimpleNamespace(is_arrangement_clip=False, is_midi_clip=True, name="")
        new_clip = SimpleNamespace(is_arrangement_clip=True, is_midi_clip=True, name="Noise Rise")
        slot = SimpleNamespace(has_clip=False)
        slot.create_clip = lambda length: (setattr(slot, "clip", temp_clip), setattr(slot, "has_clip", True))
        slot.delete_clip = lambda: setattr(slot, "has_clip", False)
        duplicates = []
        track = SimpleNamespace(
            name="Build Bus",
            clip_slots=[slot],
            duplicate_clip_to_arrangement=lambda clip, start: duplicates.append((clip, start)),
        )
        source_clip.canonical_parent = track
        inserted_steps = []
        temp_frequency = _envelope("Frequency", frequency, inserted_steps)
        temp_resonance = _envelope("Resonance", resonance, inserted_steps)
        new_frequency = SimpleNamespace(parameter=frequency, value_at_time=lambda time: 0.5)
        new_resonance = SimpleNamespace(parameter=resonance, value_at_time=lambda time: 0.5)

        bridge = _Bridge(song)
        bridge._resolve_clip_ref = lambda payload: {"kind": "arrangement", "track": track, "clip": source_clip}
        bridge._resolve_parameter_ref = lambda payload: {"Frequency": frequency, "Resonance": resonance}[payload["param"]]
        bridge._automation_envelope = lambda clip, parameter, create: (
            existing_frequency_envelope if clip is source_clip and parameter is frequency else
            temp_frequency if clip is temp_clip and parameter is frequency else
            temp_resonance if clip is temp_clip and parameter is resonance else
            new_frequency if clip is new_clip and parameter is frequency else
            new_resonance if clip is new_clip and parameter is resonance else
            None
        )
        bridge._copy_midi_clip_contents = lambda source, target: setattr(target, "copied_from", source)
        bridge._delete_clip_ref = lambda ref: setattr(ref["clip"], "deleted", True)
        bridge._find_arrangement_clip = lambda track, start, length: new_clip
        bridge._clip_ref_from_clip = lambda clip: {"kind": "arrangement", "track": track, "clip": clip}
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": clip.name}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._arrangement_automation_set_many(
            {
                "device": "Auto Filter",
                "lanes": [
                    {"param": "Frequency", "steps": [{"time": 0, "duration": 1, "normalized": 0.8}], "clear": True},
                    {"param": "Resonance", "steps": [{"time": 0, "duration": 1, "normalized": 0.3}], "clear": True},
                ],
            }
        )

        self.assertEqual(undo_calls, ["begin", "end"])
        self.assertTrue(source_clip.deleted)
        self.assertEqual(duplicates, [(temp_clip, 8.0)])
        self.assertEqual(inserted_steps, [("Frequency", 0.0, 1.0, 0.8), ("Resonance", 0.0, 1.0, 0.3)])
        self.assertFalse(slot.has_clip)
        self.assertTrue(result["materialized_from_session_clip"])
        self.assertEqual([lane["parameter"]["name"] for lane in result["lanes"]], ["Frequency", "Resonance"])

    def test_arrangement_automation_get_marks_hidden_arrangement_automation(self):
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.0, automation_state=1)
        song = SimpleNamespace(view=SimpleNamespace(selected_track=None, detail_clip=None))
        track = SimpleNamespace(name="Build Bus")
        clip = SimpleNamespace(is_arrangement_clip=True, length=8.0, start_time=48.0, canonical_parent=track)

        bridge = _Bridge(song)
        bridge._resolve_clip_ref = lambda payload: {"kind": "arrangement", "track": track, "clip": clip}
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: None
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._arrangement_automation_get({"times": [0, 4, 7.5]})

        self.assertTrue(result["has_automation"])
        self.assertFalse(result["has_envelope"])
        self.assertIsNone(result["read_source"])
        self.assertEqual(result["values"], [])


def _envelope(name, parameter, inserted_steps):
    return SimpleNamespace(
        parameter=parameter,
        insert_step=lambda time, duration, value: inserted_steps.append((name, time, duration, value)),
        value_at_time=lambda time: 0.5,
    )


class _Bridge(AutomationHelperMixin, ClipAutomationCommandMixin, AutomationCommandMixin):
    def __init__(self, song, application=None):
        self._song = song
        self._application = application or SimpleNamespace(view=SimpleNamespace(show_view=lambda name: None))

    def song(self):
        return self._song

    def application(self):
        return self._application

    def _safe_get(self, obj, attr, default=None):
        return getattr(obj, attr, default)

    def _clamp_float(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def _set_optional_clip_property(self, clip, attr, value):
        if value is not None:
            setattr(clip, attr, value)

    def _serialize(self, value):
        return value


if __name__ == "__main__":
    unittest.main()
