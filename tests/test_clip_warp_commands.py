import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

COMMANDS_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "clip_warp_commands.py"
COMMANDS_SPEC = importlib.util.spec_from_file_location("clip_warp_commands", COMMANDS_PATH)
commands = importlib.util.module_from_spec(COMMANDS_SPEC)
assert COMMANDS_SPEC is not None and COMMANDS_SPEC.loader is not None
COMMANDS_SPEC.loader.exec_module(commands)
ClipWarpCommandMixin = commands.ClipWarpCommandMixin

SERIALIZATION_PATH = Path(__file__).resolve().parents[1] / "remote_scripts" / "Codex_AI" / "serialization.py"
SERIALIZATION_SPEC = importlib.util.spec_from_file_location("serialization", SERIALIZATION_PATH)
serialization = importlib.util.module_from_spec(SERIALIZATION_SPEC)
assert SERIALIZATION_SPEC is not None and SERIALIZATION_SPEC.loader is not None
SERIALIZATION_SPEC.loader.exec_module(serialization)
SerializationMixin = serialization.SerializationMixin


class ClipWarpCommandTests(unittest.TestCase):
    def test_clip_warp_sets_segment_bpm_with_warp_marker(self):
        clip = SimpleNamespace(
            name="Loop",
            is_audio_clip=True,
            warping=True,
            sample_length=48000.0 * 4.0,
            sample_rate=48000.0,
            length=8.0,
            beat_to_sample_time=lambda beat: beat * 0.5,
        )
        bridge = _Bridge(clip)

        result = bridge._clip_warp({"clip_bpm": 120})

        self.assertEqual(bridge.added_markers, [(1.0, 0.5)])
        self.assertEqual(result["changed"]["clip_bpm"]["requested"], 120.0)
        self.assertEqual(result["changed"]["clip_bpm"]["actual"], 120.0)


class _Bridge(ClipWarpCommandMixin, SerializationMixin):
    def __init__(self, clip):
        self.clip = clip
        self.added_markers = []

    def _resolve_clip_ref(self, payload):
        return {"kind": "session", "clip": self.clip}

    def _clip_ref_info(self, ref):
        return {"kind": ref["kind"]}

    def _ensure_audio_clip(self, clip):
        if not getattr(clip, "is_audio_clip", False):
            raise ValueError("Clip is not an audio clip")

    def _ensure_warped_audio_clip(self, clip):
        self._ensure_audio_clip(clip)
        if not getattr(clip, "warping", False):
            raise ValueError("Clip warping must be enabled before editing warp markers")

    def _find_warp_marker(self, clip, beat_time):
        return None

    def _add_warp_marker(self, clip, beat_time, sample_time):
        self.added_markers.append((beat_time, sample_time))
        return {"beat_time": beat_time, "sample_time": sample_time}

    def _warp_marker_infos(self, clip):
        return []

    def _safe_get(self, obj, attr, default=None):
        return getattr(obj, attr, default)

    def _is_indexable_vector(self, value):
        return hasattr(value, "__len__") and hasattr(value, "__getitem__") and not isinstance(value, (str, bytes))


if __name__ == "__main__":
    unittest.main()
