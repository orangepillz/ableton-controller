import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

COMMANDS_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "automation_commands.py"
COMMANDS_SPEC = importlib.util.spec_from_file_location("automation_commands", COMMANDS_PATH)
commands = importlib.util.module_from_spec(COMMANDS_SPEC)
assert COMMANDS_SPEC is not None and COMMANDS_SPEC.loader is not None
COMMANDS_SPEC.loader.exec_module(commands)
AutomationCommandMixin = commands.AutomationCommandMixin

CLIP_COMMANDS_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "clip_automation_commands.py"
CLIP_COMMANDS_SPEC = importlib.util.spec_from_file_location("clip_automation_commands", CLIP_COMMANDS_PATH)
clip_commands = importlib.util.module_from_spec(CLIP_COMMANDS_SPEC)
assert CLIP_COMMANDS_SPEC is not None and CLIP_COMMANDS_SPEC.loader is not None
CLIP_COMMANDS_SPEC.loader.exec_module(clip_commands)
ClipAutomationCommandMixin = clip_commands.ClipAutomationCommandMixin

HELPERS_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "automation_helpers.py"
HELPERS_SPEC = importlib.util.spec_from_file_location("automation_helpers", HELPERS_PATH)
helpers = importlib.util.module_from_spec(HELPERS_SPEC)
assert HELPERS_SPEC is not None and HELPERS_SPEC.loader is not None
HELPERS_SPEC.loader.exec_module(helpers)
AutomationHelperMixin = helpers.AutomationHelperMixin


class ArrangementAutomationCurveCommandTests(unittest.TestCase):
    def test_arrangement_automation_set_writes_curved_events(self):
        deleted_ranges = []
        created_events = []
        create_calls = []
        envelope = SimpleNamespace(
            parameter=None,
            delete_events_in_range=lambda start, end: deleted_ranges.append((start, end)),
            create_event=_create_or_replace(created_events, create_calls),
            value_at_time=lambda time: 0.6,
            events_in_range=lambda start, end: created_events,
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
        bridge._live_envelope_module = lambda: _fake_envelope_module()

        result = bridge._arrangement_automation_set(
            {
                "events": [
                    {
                        "time": 0,
                        "normalized": 0.2,
                        "curve_coefficients": {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0},
                    },
                    {"time": 8, "normalized": 0.9},
                ],
                "clear": True,
            }
        )

        self.assertEqual(deleted_ranges, [(0.0, 1576800.0)])
        self.assertEqual(create_calls, [(8.0, 0.9), (0.0, 0.2)])
        self.assertEqual([(event.time, event.value) for event in created_events], [(0.0, 0.2), (8.0, 0.9)])
        self.assertEqual(created_events[0].control_coefficients.x1, 0.42)
        self.assertEqual(result["write_mode"], "events")
        self.assertEqual(result["inserted"][0]["control_coefficients"]["x2"], 0.58)

    def test_arrangement_automation_set_materializes_curved_events(self):
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
            length=8.0,
            start_time=48.0,
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
        created_events = []
        create_calls = []
        temp_envelope = SimpleNamespace(
            parameter=parameter,
            create_event=_create_or_replace(created_events, create_calls),
            value_at_time=lambda time: 0.7,
            events_in_range=lambda start, end: created_events,
        )
        new_envelope = SimpleNamespace(parameter=parameter, value_at_time=lambda time: 0.7)

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
        bridge._live_envelope_module = lambda: _fake_envelope_module()

        result = bridge._arrangement_automation_set(
            {
                "events": [
                    {"time": 0, "normalized": 0.2, "curve_coefficients": {"x1": 0.1, "y1": 0.0, "x2": 0.9, "y2": 1.0}},
                    {"time": 8, "normalized": 0.9},
                ],
                "clear": True,
            }
        )

        self.assertEqual(undo_calls, ["begin", "end"])
        self.assertTrue(source_clip.deleted)
        self.assertEqual(duplicates, [(temp_clip, 48.0)])
        self.assertEqual(create_calls, [(8.0, 0.9), (0.0, 0.2)])
        self.assertEqual([(event.time, event.value) for event in created_events], [(0.0, 0.2), (8.0, 0.9)])
        self.assertFalse(slot.has_clip)
        self.assertTrue(result["materialized_from_session_clip"])
        self.assertEqual(result["write_mode"], "events")
        self.assertEqual(result["inserted"][0]["control_coefficients"]["x1"], 0.1)


def _fake_envelope_module():
    class Event:
        def __init__(self, time, value):
            self.time = time
            self.value = value
            self.control_coefficients = None

    class Coefficients:
        def __init__(self, x1, y1, x2, y2):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2

    return SimpleNamespace(EnvelopeEvent=Event, EnvelopeEventControlCoefficients=Coefficients)


def _create_or_replace(events, calls=None):
    def create(event):
        if calls is not None:
            calls.append((event.time, event.value))
        stored = SimpleNamespace(time=event.time, value=event.value, control_coefficients=None)
        if event.control_coefficients is not None and any(existing.time > event.time for existing in events):
            stored.control_coefficients = event.control_coefficients
        for index, existing in enumerate(events):
            if existing.time == event.time:
                events[index] = stored
                events.sort(key=lambda item: item.time)
                return
        events.append(stored)
        events.sort(key=lambda item: item.time)
    return create


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
