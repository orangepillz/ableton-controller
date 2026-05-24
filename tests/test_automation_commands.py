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


class AutomationCommandTests(unittest.TestCase):
    def test_focus_clip_for_automation_only_selects_arrangement_clips(self):
        view = SimpleNamespace(selected_track=None, detail_clip=None)
        app_view_calls = []
        app_view = SimpleNamespace(show_view=lambda name: app_view_calls.append(name))
        app = SimpleNamespace(view=app_view)
        song = SimpleNamespace(view=view)
        track = SimpleNamespace(name="Build Bus")
        arrangement_clip = SimpleNamespace(is_arrangement_clip=True, canonical_parent=track)
        session_clip = SimpleNamespace(is_arrangement_clip=False, canonical_parent=track)

        bridge = _Bridge(song, app)
        bridge._focus_clip_for_automation(arrangement_clip)
        self.assertIs(view.selected_track, track)
        self.assertIs(view.detail_clip, arrangement_clip)
        self.assertEqual(app_view_calls, ["Detail", "Detail/Clip"])

        view.selected_track = None
        view.detail_clip = None
        app_view_calls[:] = []
        bridge._focus_clip_for_automation(session_clip)
        self.assertIsNone(view.selected_track)
        self.assertIsNone(view.detail_clip)
        self.assertEqual(app_view_calls, [])

    def test_clip_automation_set_focuses_arrangement_clip_before_writing(self):
        view = SimpleNamespace(selected_track=None, detail_clip=None)
        app_view_calls = []
        app_view = SimpleNamespace(show_view=lambda name: app_view_calls.append(name))
        app = SimpleNamespace(view=app_view)
        song = SimpleNamespace(view=view)
        track = SimpleNamespace(name="Build Bus")
        clip_view_calls = []
        clip = SimpleNamespace(is_arrangement_clip=True, canonical_parent=track, view=SimpleNamespace(show_envelope=lambda parameter: clip_view_calls.append(parameter)))
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)
        envelope = SimpleNamespace(points=[], step_count=1)

        bridge = _Bridge(song, app)
        bridge._resolve_clip = lambda payload: clip
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: envelope
        bridge._automation_step_value = lambda parameter, step: 0.75
        calls = []
        bridge._insert_automation_step = lambda envelope, time_value, duration, value: calls.append((time_value, duration, value))
        bridge._automation_envelope_info = lambda envelope: {"step_count": 1}
        bridge._automation_value_at_time = lambda envelope, time_value: 0.75
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": "Frequency"}

        result = bridge._clip_automation_set({"steps": [{"time": 0, "duration": 1, "value": 0.75}]})

        self.assertIs(view.selected_track, track)
        self.assertIs(view.detail_clip, clip)
        self.assertEqual(app_view_calls, ["Detail", "Detail/Clip"])
        self.assertEqual(clip_view_calls, [parameter])
        self.assertEqual(calls, [(0.0, 1.0, 0.75)])
        self.assertTrue(result["done"])

    def test_clip_automation_clear_focuses_arrangement_clip_before_clearing(self):
        view = SimpleNamespace(selected_track=None, detail_clip=None)
        app_view_calls = []
        app_view = SimpleNamespace(show_view=lambda name: app_view_calls.append(name))
        app = SimpleNamespace(view=app_view)
        song = SimpleNamespace(view=view)
        track = SimpleNamespace(name="Build Bus")
        clip = SimpleNamespace(is_arrangement_clip=True, canonical_parent=track)
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)

        bridge = _Bridge(song, app)
        bridge._resolve_clip = lambda payload: clip
        bridge._resolve_parameter_ref = lambda payload: parameter
        cleared = []
        bridge._clear_parameter_envelope = lambda clip, parameter: cleared.append((clip, parameter))
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": "Frequency"}

        result = bridge._clip_automation_clear({"clear": False})

        self.assertIs(view.selected_track, track)
        self.assertIs(view.detail_clip, clip)
        self.assertEqual(app_view_calls, ["Detail", "Detail/Clip"])
        self.assertEqual(cleared, [(clip, parameter)])
        self.assertEqual(result["cleared"], "parameter")

    def test_clip_automation_get_shows_target_envelope(self):
        view = SimpleNamespace(selected_track=None, detail_clip=None)
        app_view_calls = []
        app_view = SimpleNamespace(show_view=lambda name: app_view_calls.append(name))
        app = SimpleNamespace(view=app_view)
        song = SimpleNamespace(view=view)
        track = SimpleNamespace(name="Build Bus")
        clip_view_calls = []
        clip = SimpleNamespace(is_arrangement_clip=True, canonical_parent=track, view=SimpleNamespace(show_envelope=lambda parameter: clip_view_calls.append(parameter)))
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)

        bridge = _Bridge(song, app)
        bridge._resolve_clip = lambda payload: clip
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: None
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": "Frequency"}
        bridge._automation_envelope_info = lambda envelope: None

        result = bridge._clip_automation_get({"times": []})

        self.assertIs(view.selected_track, track)
        self.assertIs(view.detail_clip, clip)
        self.assertEqual(app_view_calls, ["Detail", "Detail/Clip"])
        self.assertEqual(clip_view_calls, [parameter])
        self.assertFalse(result["has_envelope"])

    def test_clip_automation_set_many_writes_multiple_lanes(self):
        song = SimpleNamespace(view=SimpleNamespace(selected_track=None, detail_clip=None))
        track = SimpleNamespace(name="Synth")
        clip = SimpleNamespace(is_arrangement_clip=False, length=4.0, canonical_parent=track)
        frequency = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.0)
        resonance = SimpleNamespace(name="Resonance", min=0.0, max=1.0, value=0.0)
        inserted = []
        envelopes = {}

        def automation_envelope(_clip, parameter, create):
            parameter_key = id(parameter)
            if parameter_key in envelopes:
                return envelopes[parameter_key]
            if not create:
                return None
            envelope = SimpleNamespace(
                parameter=parameter,
                insert_step=lambda time, duration, value, name=parameter.name: inserted.append((name, time, duration, value)),
                value_at_time=lambda time: 0.5,
            )
            envelopes[parameter_key] = envelope
            return envelope

        bridge = _Bridge(song)
        bridge._resolve_clip_ref = lambda payload: {"kind": "session", "track": track, "clip": clip}
        bridge._resolve_parameter_ref = lambda payload: {"Frequency": frequency, "Resonance": resonance}[payload["param"]]
        bridge._automation_envelope = automation_envelope
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": "clip"}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._clip_automation_set_many(
            {
                "device": "Auto Filter",
                "lanes": [
                    {"param": "Frequency", "steps": [{"time": 0, "duration": 1, "normalized": 0.25}]},
                    {"param": "Resonance", "steps": [{"time": 1, "duration": 1, "normalized": 0.75}]},
                ],
            }
        )

        self.assertEqual(inserted, [("Frequency", 0.0, 1.0, 0.25), ("Resonance", 1.0, 1.0, 0.75)])
        self.assertEqual([lane["parameter"]["name"] for lane in result["lanes"]], ["Frequency", "Resonance"])
        self.assertTrue(result["done"])

    def test_automation_envelope_creation_retries_after_showing_envelope(self):
        song = SimpleNamespace(view=SimpleNamespace(selected_track=None, detail_clip=None))
        app_view_calls = []
        app = SimpleNamespace(view=SimpleNamespace(show_view=lambda name: app_view_calls.append(name)))
        track = SimpleNamespace(name="Build Bus")
        clip_view_calls = []
        clip = SimpleNamespace(
            is_arrangement_clip=True,
            canonical_parent=track,
            view=SimpleNamespace(show_envelope=lambda parameter: clip_view_calls.append(parameter)),
        )
        parameter = SimpleNamespace(name="Frequency")
        create_attempts = []
        envelope_queries = []

        bridge = _Bridge(song, app)
        clip.create_automation_envelope = lambda parameter: create_attempts.append(parameter) or ({"created": True} if len(create_attempts) >= 2 else None)
        clip.automation_envelope = lambda parameter: envelope_queries.append(parameter) or None

        envelope = bridge._create_automation_envelope(clip, parameter)

        self.assertEqual(create_attempts, [parameter, parameter])
        self.assertEqual(envelope_queries, [parameter])
        self.assertIsNotNone(envelope)
        self.assertEqual(clip_view_calls, [parameter])
        self.assertEqual(app_view_calls, [])


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
