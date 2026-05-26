from __future__ import annotations

import json
import importlib.util
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_MODULE = REPO_ROOT / "remote_scripts" / "Codex_AI" / "render_commands.py"
spec = importlib.util.spec_from_file_location("render_commands", RENDER_MODULE)
assert spec is not None and spec.loader is not None
render_commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_commands)
RenderCommandMixin = render_commands.RenderCommandMixin


class FakeView:
    def __init__(self, track):
        self.selected_track = track


class FakeTrack:
    def __init__(self, name: str):
        self.name = name
        self.mute = False
        self.solo = False


class FakeSong:
    def __init__(self):
        self.tracks = [FakeTrack("Kick"), FakeTrack("Bass")]
        self.return_tracks = [FakeTrack("A-Reverb")]
        self.master_track = FakeTrack("Master")
        self.view = FakeView(self.tracks[1])
        self.signature_numerator = 4
        self.tempo = 87
        self.file_path = "/tmp/test_set.als"
        self.is_playing = True
        self.current_song_time = 12.0
        self.loop = False
        self.loop_start = 8.0
        self.loop_length = 4.0
        self.export_calls = []

    def stop_playing(self):
        self.is_playing = False

    def start_playing(self):
        self.is_playing = True

    def export_audio(self, output, start, length, settings):
        self.export_calls.append({"output": output, "start": start, "length": length, "settings": settings})
        write_silent_wav(Path(output))


class FakeBridge(RenderCommandMixin):
    def __init__(self, song):
        self._song = song

    def song(self):
        return self._song

    def _safe_get(self, obj, name, default=None):
        return getattr(obj, name, default)

    def _resolve_track(self, identifier):
        for track in list(self._song.tracks) + list(self._song.return_tracks) + [self._song.master_track]:
            if track.name == identifier:
                return track
        raise ValueError(identifier)


class RenderCommandMixinTests(unittest.TestCase):
    def test_render_audio_writes_manifest_and_restores_state(self):
        song = FakeSong()
        song.tracks[0].mute = True
        song.tracks[1].solo = True
        bridge = FakeBridge(song)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "kick.wav"
            result = bridge._render_audio(
                {
                    "output_file": str(output),
                    "output_file_abs": str(output),
                    "start_bar": 3,
                    "bars": 2,
                    "solo_tracks": ["Kick"],
                    "muted_tracks": ["Bass"],
                    "include_returns": False,
                    "sample_rate": 48000,
                    "bit_depth": 24,
                    "normalize": False,
                    "create_manifest": True,
                    "restore_state": True,
                }
            )
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertTrue(result["done"])
        self.assertTrue(song.tracks[0].mute)
        self.assertTrue(song.tracks[1].solo)
        self.assertEqual(song.loop_start, 8.0)
        self.assertEqual(song.loop_length, 4.0)
        self.assertTrue(song.is_playing)
        self.assertEqual(song.export_calls[0]["start"], 8.0)
        self.assertEqual(song.export_calls[0]["length"], 8.0)
        self.assertEqual(manifest["render_id"], "kick")
        self.assertEqual(manifest["solo_tracks"], ["Kick"])
        self.assertTrue(manifest["restored_state"])


def write_silent_wav(path: Path) -> None:
    samples = np.zeros(256, dtype="<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(samples.tobytes())


if __name__ == "__main__":
    unittest.main()
