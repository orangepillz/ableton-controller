"""Rendered-audio export support for the Codex_AI bridge."""

import json
import os
import time
from datetime import datetime


class RenderCommandMixin(object):
    def _render_audio(self, payload):
        song = self.song()
        output_abs = str(payload.get("output_file_abs") or payload.get("output_file"))
        if not output_abs:
            raise ValueError("render_audio requires output_file")
        output_dir = os.path.dirname(output_abs)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        beats_per_bar = float(self._safe_get(song, "signature_numerator", 4) or 4)
        start_bar = float(payload.get("start_bar", 1.0))
        bars = float(payload.get("bars", 1.0))
        start_beat = max(0.0, (start_bar - 1.0) * beats_per_bar)
        length_beats = max(0.0, bars * beats_per_bar)
        if length_beats <= 0.0:
            raise ValueError("render_audio requires --bars greater than zero")
        state = self._capture_render_state() if payload.get("restore_state", True) else None
        restored = False
        try:
            self._prepare_render_range(start_beat, length_beats)
            self._apply_render_track_state(payload)
            self._call_export_audio(song, output_abs, start_beat, length_beats, payload)
            self._verify_rendered_wav(output_abs)
            manifest_path = None
            if payload.get("create_manifest", True):
                manifest_path = self._write_render_manifest(payload, output_abs, start_beat, length_beats)
            return {
                "done": True,
                "output_file": payload.get("output_file"),
                "output_file_abs": output_abs,
                "manifest": manifest_path,
                "restored_state": bool(payload.get("restore_state", True)),
            }
        finally:
            if state is not None:
                self._restore_render_state(state)
                restored = True
            if payload.get("restore_state", True) and not restored:
                raise ValueError("render_audio could not restore Live state")

    def _capture_render_state(self):
        song = self.song()
        tracks = list(song.tracks) + list(song.return_tracks)
        return {
            "tracks": [(track, self._safe_get(track, "mute"), self._safe_get(track, "solo")) for track in tracks],
            "selected_track": self._safe_get(song.view, "selected_track"),
            "is_playing": self._safe_get(song, "is_playing", False),
            "current_song_time": self._safe_get(song, "current_song_time"),
            "loop": self._safe_get(song, "loop"),
            "loop_start": self._safe_get(song, "loop_start"),
            "loop_length": self._safe_get(song, "loop_length"),
        }

    def _restore_render_state(self, state):
        song = self.song()
        for track, mute, solo in state["tracks"]:
            if mute is not None:
                try:
                    track.mute = mute
                except Exception:
                    pass
            if solo is not None:
                try:
                    track.solo = solo
                except Exception:
                    pass
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

    def _resolve_render_tracks(self, identifiers):
        tracks = []
        for identifier in identifiers or []:
            tracks.append(self._resolve_track(identifier))
        return tracks

    def _set_track_bool(self, track, name, value):
        try:
            setattr(track, name, bool(value))
        except Exception:
            pass

    def _call_export_audio(self, song, output_abs, start_beat, length_beats, payload):
        method = None
        for name in ("export_audio", "export_audio_file", "render_audio"):
            candidate = self._safe_get(song, name)
            if callable(candidate):
                method = candidate
                break
        if method is None:
            raise ValueError("This Live version does not expose an audio export method to the bridge")
        settings = {
            "sample_rate": int(payload.get("sample_rate", 48000)),
            "bit_depth": int(payload.get("bit_depth", 24)),
            "normalize": bool(payload.get("normalize", False)),
        }
        attempts = (
            (output_abs, start_beat, length_beats, settings),
            (output_abs, start_beat, length_beats),
            (output_abs,),
        )
        last_error = None
        for args in attempts:
            try:
                method(*args)
                return
            except TypeError as error:
                last_error = error
        raise ValueError("Live audio export call failed: %s" % (last_error,))

    def _verify_rendered_wav(self, output_abs):
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if os.path.exists(output_abs) and os.path.getsize(output_abs) > 44:
                with open(output_abs, "rb") as handle:
                    header = handle.read(12)
                if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
                    return
            time.sleep(0.1)
        raise ValueError("Render did not produce a readable WAV file: %s" % output_abs)

    def _write_render_manifest(self, payload, output_abs, start_beat, length_beats):
        base, _extension = os.path.splitext(output_abs)
        manifest_path = base + ".manifest.json"
        song = self.song()
        manifest = {
            "render_id": os.path.splitext(os.path.basename(output_abs))[0],
            "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "set_name": os.path.basename(str(self._safe_get(song, "file_path", "") or "unsaved_live_set")),
            "tempo_bpm": self._safe_get(song, "tempo"),
            "start_bar": payload.get("start_bar"),
            "start_beat": start_beat,
            "bars": payload.get("bars"),
            "length_beats": length_beats,
            "output_file": payload.get("output_file"),
            "output_file_abs": output_abs,
            "sample_rate": int(payload.get("sample_rate", 48000)),
            "bit_depth": int(payload.get("bit_depth", 24)),
            "normalize": bool(payload.get("normalize", False)),
            "solo_tracks": list(payload.get("solo_tracks", [])),
            "solo_groups": list(payload.get("solo_groups", [])),
            "muted_tracks": list(payload.get("muted_tracks", [])),
            "muted_groups": list(payload.get("muted_groups", [])),
            "include_returns": bool(payload.get("include_returns", True)),
            "restored_state": bool(payload.get("restore_state", True)),
        }
        with open(manifest_path, "w") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return manifest_path
