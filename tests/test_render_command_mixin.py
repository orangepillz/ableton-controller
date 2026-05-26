from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

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


class FakeRouting:
    def __init__(self, name: str):
        self.name = name
        self.display_name = name


class FakeClip:
    file_path = "/tmp/fake-render.aif"


class FakeClipSlot:
    def __init__(self):
        self.has_clip = False
        self.clip = None
        self.fired_length = None

    def fire(self, length):
        self.fired_length = length
        self.has_clip = True
        self.clip = FakeClip()


class FakeTrack:
    def __init__(self, name: str, can_arm: bool = True):
        self.name = name
        self.mute = False
        self.solo = False
        self.arm = False
        self.clip_slots = [FakeClipSlot()]
        self.available_input_routing_types = [FakeRouting("Ext. In"), FakeRouting("Resampling")]
        self.input_routing_type = self.available_input_routing_types[0]
        self.current_monitoring_state = 0
        self.can_be_armed = can_arm


class FakeSong:
    def __init__(self):
        self.tracks = [FakeTrack("Kick"), FakeTrack("Bass")]
        self.return_tracks = [FakeTrack("A-Reverb", can_arm=False)]
        self.master_track = FakeTrack("Master", can_arm=False)
        self.view = FakeView(self.tracks[1])
        self.signature_numerator = 4
        self.tempo = 120
        self.file_path = "/tmp/test_set.als"
        self.is_playing = True
        self.current_song_time = 12.0
        self.loop = False
        self.loop_start = 8.0
        self.loop_length = 4.0

    def stop_playing(self):
        self.is_playing = False

    def start_playing(self):
        self.is_playing = True

    def create_audio_track(self, index):
        track = FakeTrack("New Audio")
        self.tracks.insert(index, track)
        return track

    def delete_track(self, index):
        del self.tracks[index]


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

    def _track_index(self, track):
        return self._song.tracks.index(track)

    def _track_kind(self, track):
        return "return" if track in self._song.return_tracks else "track"

    def _match_routing(self, values, requested):
        for value in values:
            if value.name == requested:
                return value
        raise ValueError(requested)


class RenderCommandMixinTests(unittest.TestCase):
    def test_resampling_prepare_and_finish_restore_state(self):
        song = FakeSong()
        song.tracks[0].mute = True
        song.tracks[1].solo = True
        bridge = FakeBridge(song)
        prepared = bridge._render_audio_prepare(
            {
                "start_bar": 3,
                "bars": 2,
                "solo_tracks": ["Kick"],
                "muted_tracks": ["Bass"],
                "include_returns": False,
                "restore_state": True,
            }
        )
        temp_track = song.tracks[-1]
        self.assertEqual(temp_track.input_routing_type.name, "Resampling")
        self.assertEqual(temp_track.clip_slots[0].fired_length, 8.0)
        finished = bridge._render_audio_finish({"state_id": prepared["state_id"]})
        self.assertEqual(finished["source_file"], "/tmp/fake-render.aif")
        self.assertTrue(finished["restored_state"])
        self.assertEqual([track.name for track in song.tracks], ["Kick", "Bass"])
        self.assertTrue(song.tracks[0].mute)
        self.assertTrue(song.tracks[1].solo)
        self.assertEqual(song.loop_start, 8.0)
        self.assertEqual(song.loop_length, 4.0)
        self.assertTrue(song.is_playing)

    def test_cancel_deletes_temp_track_and_restores_state(self):
        song = FakeSong()
        bridge = FakeBridge(song)
        prepared = bridge._render_audio_prepare(
            {
                "start_bar": 1,
                "bars": 1,
                "solo_tracks": ["Kick"],
                "muted_tracks": [],
                "include_returns": True,
                "restore_state": True,
            }
        )
        self.assertEqual(len(song.tracks), 3)
        cancelled = bridge._render_audio_cancel({"state_id": prepared["state_id"]})
        self.assertTrue(cancelled["restored_state"])
        self.assertEqual([track.name for track in song.tracks], ["Kick", "Bass"])
        self.assertTrue(song.is_playing)

    def test_delete_stale_temp_track_does_not_delete_real_track(self):
        song = FakeSong()
        bridge = FakeBridge(song)
        bridge._delete_track_object(FakeTrack("stale"))
        self.assertEqual([track.name for track in song.tracks], ["Kick", "Bass"])


if __name__ == "__main__":
    unittest.main()
