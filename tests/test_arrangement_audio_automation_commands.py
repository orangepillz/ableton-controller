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

CLIP_REFS_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "clip_refs.py"
CLIP_REFS_SPEC = importlib.util.spec_from_file_location("clip_refs", CLIP_REFS_PATH)
clip_refs = importlib.util.module_from_spec(CLIP_REFS_SPEC)
assert CLIP_REFS_SPEC is not None and CLIP_REFS_SPEC.loader is not None
CLIP_REFS_SPEC.loader.exec_module(clip_refs)
ClipReferenceMixin = clip_refs.ClipReferenceMixin


class ArrangementAudioAutomationCommandTests(unittest.TestCase):
    def test_arrangement_automation_set_materializes_new_audio_lane(self):
        undo_calls = []
        song = SimpleNamespace(
            view=SimpleNamespace(selected_track=None, detail_clip=None),
            begin_undo_step=lambda: undo_calls.append("begin"),
            end_undo_step=lambda: undo_calls.append("end"),
        )
        parameter = SimpleNamespace(name="Frequency", min=0.0, max=1.0, value=0.5)
        source_clip = SimpleNamespace(
            is_arrangement_clip=True,
            is_audio_clip=True,
            is_midi_clip=False,
            length=4.0,
            start_time=16.0,
            name="Riser",
            file_path="/Samples/riser.wav",
            automation_envelopes=[],
        )
        temp_clip = SimpleNamespace(is_arrangement_clip=False, is_audio_clip=True, is_midi_clip=False, name="")
        new_clip = SimpleNamespace(is_arrangement_clip=True, is_audio_clip=True, is_midi_clip=False, name="Riser")
        created_audio = []
        slot = SimpleNamespace(has_clip=False)

        def create_audio_clip(file_path):
            created_audio.append(file_path)
            setattr(slot, "clip", temp_clip)
            setattr(slot, "has_clip", True)
            return temp_clip

        slot.create_audio_clip = create_audio_clip
        slot.delete_clip = lambda: setattr(slot, "has_clip", False)
        duplicates = []
        track = SimpleNamespace(
            name="FX",
            clip_slots=[slot],
            duplicate_clip_to_arrangement=lambda clip, start: duplicates.append((clip, start)),
        )
        source_clip.canonical_parent = track
        inserted_steps = []
        temp_envelope = SimpleNamespace(
            parameter=parameter,
            insert_step=lambda time, duration, value: inserted_steps.append((time, duration, value)),
            value_at_time=lambda time: 0.45,
        )
        new_envelope = SimpleNamespace(parameter=parameter, value_at_time=lambda time: 0.45)

        bridge = _Bridge(song)
        bridge._resolve_clip_ref = lambda payload: {"kind": "arrangement", "track": track, "clip": source_clip}
        bridge._resolve_parameter_ref = lambda payload: parameter
        bridge._automation_envelope = lambda clip, parameter, create: (
            temp_envelope if clip is temp_clip else new_envelope if clip is new_clip else None
        )
        bridge._copy_audio_clip_contents = lambda source, target: setattr(target, "copied_audio_from", source)
        bridge._delete_clip_ref = lambda ref: setattr(ref["clip"], "deleted", True)
        bridge._find_arrangement_clip = lambda track, start, length: new_clip
        bridge._clip_ref_from_clip = lambda clip: {"kind": "arrangement", "track": track, "clip": clip}
        bridge._clip_ref_info = lambda ref: {"kind": ref["kind"]}
        bridge._clip_info = lambda clip: {"name": clip.name}
        bridge._parameter_info = lambda parameter: {"name": parameter.name}

        result = bridge._arrangement_automation_set(
            {"steps": [{"time": 0, "duration": 1, "normalized": 0.45}], "clear": False}
        )

        self.assertEqual(undo_calls, ["begin", "end"])
        self.assertEqual(created_audio, ["/Samples/riser.wav"])
        self.assertIs(temp_clip.copied_audio_from, source_clip)
        self.assertTrue(source_clip.deleted)
        self.assertEqual(duplicates, [(temp_clip, 16.0)])
        self.assertEqual(inserted_steps, [(0.0, 1.0, 0.45)])
        self.assertFalse(slot.has_clip)
        self.assertTrue(result["materialized_from_session_clip"])
        self.assertTrue(result["done"])

    def test_copy_audio_clip_contents_preserves_playback_properties(self):
        source = SimpleNamespace(
            name="Vocal Chop",
            color=123,
            color_index=7,
            muted=False,
            looping=True,
            signature_numerator=4,
            signature_denominator=4,
            is_audio_clip=True,
            length=4.0,
            warping=True,
            warp_mode=6,
            gain=0.72,
            pitch_coarse=-7,
            pitch_fine=0.25,
            ram_mode=True,
            start_marker=1.0,
            end_marker=5.0,
            loop_start=1.0,
            loop_end=5.0,
            markers=[{"beat_time": 1.0, "sample_time": 0.5}, {"beat_time": 5.0, "sample_time": 2.5}],
        )
        target = SimpleNamespace()
        bridge = _ClipRefBridge()

        bridge._copy_audio_clip_contents(source, target)

        self.assertEqual(target.name, "Vocal Chop")
        self.assertEqual(target.gain, 0.72)
        self.assertEqual(target.pitch_coarse, -7)
        self.assertTrue(target.warping)
        self.assertEqual(target.warp_mode, 6)
        self.assertEqual(target.start_marker, 1.0)
        self.assertEqual(target.end_marker, 5.0)
        self.assertEqual(bridge.replaced_markers, [(1.0, 0.5), (5.0, 2.5)])


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


class _ClipRefBridge(ClipReferenceMixin):
    def __init__(self):
        self.replaced_markers = []

    def _safe_get(self, obj, attr, default=None):
        return getattr(obj, attr, default)

    def _clip_info(self, clip):
        return {
            "name": clip.name,
            "color": clip.color,
            "color_index": clip.color_index,
            "muted": clip.muted,
            "looping": clip.looping,
            "signature_numerator": clip.signature_numerator,
            "signature_denominator": clip.signature_denominator,
            "length": clip.length,
            "warping": clip.warping,
            "warp_mode": clip.warp_mode,
            "gain": clip.gain,
            "pitch_coarse": clip.pitch_coarse,
            "pitch_fine": clip.pitch_fine,
            "ram_mode": clip.ram_mode,
            "start_marker": clip.start_marker,
            "end_marker": clip.end_marker,
            "loop_start": clip.loop_start,
            "loop_end": clip.loop_end,
        }

    def _warp_marker_infos(self, clip):
        return clip.markers

    def _replace_audio_warp_marker(self, clip, beat_time, sample_time):
        self.replaced_markers.append((float(beat_time), sample_time))


if __name__ == "__main__":
    unittest.main()
