"""Temporary resampling-track support for rendered-audio probes."""

import time


class RenderCommandMixin(object):
    def _render_audio_prepare(self, payload):
        song = self.song()
        beats_per_bar = float(self._safe_get(song, "signature_numerator", 4) or 4)
        start_bar = float(payload.get("start_bar", 1.0))
        bars = float(payload.get("bars", 1.0))
        start_beat = max(0.0, (start_bar - 1.0) * beats_per_bar)
        length_beats = max(0.0, bars * beats_per_bar)
        if length_beats <= 0.0:
            raise ValueError("render-audio requires --bars greater than zero")
        store = self._render_state_store()
        state_id = "render-%s" % int(time.time() * 1000)
        state = self._capture_render_state()
        temp_track = None
        try:
            self._prepare_render_range(start_beat, length_beats)
            self._apply_render_track_state(payload)
            temp_track = self._create_resampling_track(state_id)
            slot = temp_track.clip_slots[0]
            temp_track.arm = True
            slot.fire(length_beats)
            store[state_id] = {"state": state, "track": temp_track, "slot": slot}
            tempo = float(self._safe_get(song, "tempo", 120.0) or 120.0)
            return {
                "state_id": state_id,
                "temporary_track": temp_track.name,
                "temporary_track_index": self._track_index(temp_track),
                "set_name": self._render_set_name(),
                "tempo_bpm": tempo,
                "start_beat": start_beat,
                "length_beats": length_beats,
                "wait_seconds": round((length_beats * 60.0 / tempo) + 1.25, 3),
            }
        except Exception:
            if temp_track is not None:
                self._delete_track_object(temp_track)
            self._restore_render_state(state)
            raise

    def _render_audio_finish(self, payload):
        state_id = str(payload.get("state_id"))
        store = self._render_state_store()
        if state_id not in store:
            raise ValueError("Unknown render state: %s" % state_id)
        entry = store.pop(state_id)
        source_file = ""
        try:
            try:
                self.song().stop_playing()
            except Exception:
                pass
            slot = entry["slot"]
            source_file = self._recorded_clip_source_file(slot)
            return {"source_file": source_file, "restored_state": True}
        finally:
            self._delete_track_object(entry["track"])
            self._restore_render_state(entry["state"])

    def _render_audio_cancel(self, payload):
        state_id = str(payload.get("state_id"))
        store = self._render_state_store()
        entry = store.pop(state_id, None)
        if entry is None:
            return {"done": True, "restored_state": False}
        try:
            self.song().stop_playing()
        except Exception:
            pass
        self._delete_track_object(entry["track"])
        self._restore_render_state(entry["state"])
        return {"done": True, "restored_state": True}

    def _render_state_store(self):
        if not hasattr(self, "_audio_render_states"):
            self._audio_render_states = {}
        return self._audio_render_states

    def _capture_render_state(self):
        song = self.song()
        tracks = list(song.tracks) + list(song.return_tracks)
        return {
            "tracks": [
                (track, self._safe_get(track, "mute"), self._safe_get(track, "solo"), self._safe_get(track, "arm"))
                for track in tracks
            ],
            "selected_track": self._safe_get(song.view, "selected_track"),
            "is_playing": self._safe_get(song, "is_playing", False),
            "current_song_time": self._safe_get(song, "current_song_time"),
            "loop": self._safe_get(song, "loop"),
            "loop_start": self._safe_get(song, "loop_start"),
            "loop_length": self._safe_get(song, "loop_length"),
        }

    def _restore_render_state(self, state):
        song = self.song()
        for track, mute, solo, arm in state["tracks"]:
            self._set_track_bool(track, "mute", mute)
            self._set_track_bool(track, "solo", solo)
            self._set_track_bool(track, "arm", arm)
        for name in ("loop_start", "loop_length", "loop", "current_song_time"):
            if state.get(name) is not None:
                try:
                    setattr(song, name, state[name])
                except Exception:
                    pass
        if state.get("selected_track") is not None:
            try:
                song.view.selected_track = state["selected_track"]
            except Exception:
                pass
        try:
            if state.get("is_playing"):
                song.start_playing()
            else:
                song.stop_playing()
        except Exception:
            pass

    def _prepare_render_range(self, start_beat, length_beats):
        song = self.song()
        try:
            song.stop_playing()
        except Exception:
            pass
        for name, value in (("loop_start", start_beat), ("loop_length", length_beats), ("loop", True)):
            try:
                setattr(song, name, value)
            except Exception:
                pass
        try:
            song.current_song_time = start_beat
        except Exception:
            pass

    def _apply_render_track_state(self, payload):
        tracks = list(self.song().tracks)
        returns = list(self.song().return_tracks)
        solo_targets = self._resolve_render_tracks(payload.get("solo_tracks", []))
        solo_targets.extend(self._resolve_render_tracks(payload.get("solo_groups", [])))
        muted_targets = self._resolve_render_tracks(payload.get("muted_tracks", []))
        muted_targets.extend(self._resolve_render_tracks(payload.get("muted_groups", [])))
        if solo_targets:
            for track in tracks + returns:
                self._set_track_bool(track, "solo", False)
            for track in solo_targets:
                self._set_track_bool(track, "solo", True)
        for track in muted_targets:
            self._set_track_bool(track, "mute", True)
        if not payload.get("include_returns", True):
            for track in returns:
                self._set_track_bool(track, "mute", True)

    def _create_resampling_track(self, state_id):
        song = self.song()
        track = song.create_audio_track(len(song.tracks))
        track.name = "Codex AudioQA Render %s" % state_id.rsplit("-", 1)[-1]
        track.input_routing_type = self._match_routing(track.available_input_routing_types, "Resampling")
        try:
            track.current_monitoring_state = 2
        except Exception:
            pass
        return track

    def _delete_track_object(self, track):
        try:
            tracks = list(self.song().tracks)
            if track in tracks:
                self.song().delete_track(tracks.index(track))
        except Exception:
            pass

    def _recorded_clip_source_file(self, slot):
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if self._safe_get(slot, "has_clip", False):
                clip = slot.clip
                source_file = self._safe_get(clip, "file_path", "")
                if source_file:
                    return source_file
            time.sleep(0.1)
        if not self._safe_get(slot, "has_clip", False):
            raise ValueError("Resampling did not create an audio clip")
        raise ValueError("Recorded audio clip has no file_path")

    def _resolve_render_tracks(self, identifiers):
        tracks = []
        for identifier in identifiers or []:
            tracks.append(self._resolve_track(identifier))
        return tracks

    def _set_track_bool(self, track, name, value):
        if value is None:
            return
        try:
            setattr(track, name, bool(value))
        except Exception:
            pass

    def _render_set_name(self):
        path = str(self._safe_get(self.song(), "file_path", "") or "")
        if "/" in path:
            return path.rsplit("/", 1)[-1]
        return path or "unsaved_live_set"
