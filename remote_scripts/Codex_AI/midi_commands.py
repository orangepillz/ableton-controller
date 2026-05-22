"""MidiCommand mixins for the Codex_AI Ableton bridge."""

try:
    from .live_api import Live
except ImportError:
    from live_api import Live


class MidiCommandMixin(object):
    def _midi_get_notes(self, payload):
        clip = self._resolve_clip(payload)
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")
        if self._has_note_region(payload):
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
            notes = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)
        else:
            try:
                notes = clip.get_all_notes_extended()
            except TypeError:
                notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
        return {"clip": self._clip_info(clip), "notes": self._serialize(notes)}

    def _midi_add_notes(self, payload):
        if Live is None:
            raise ValueError("Live module is not available")
        clip = self._resolve_clip(payload)
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")
        notes = payload.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("notes must be a list")
        self._add_note_dicts(clip, notes)
        return self._midi_get_notes(payload)

    def _midi_replace_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        notes = payload.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("notes must be a list")
        self._remove_notes_region(clip, 0, 128, 0.0, max(float(self._safe_get(clip, "length", 0.0)), 1576800.0))
        self._add_note_dicts(clip, notes)
        return self._midi_get_notes(payload)

    def _midi_update_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        updates = payload.get("notes", [])
        if not isinstance(updates, list):
            raise ValueError("notes must be a list")
        existing = {}
        for note in self._midi_note_dicts(clip):
            note_id = note.get("note_id")
            if note_id is not None:
                existing[int(note_id)] = note
        modified = []
        for update in updates:
            if not isinstance(update, dict) or "note_id" not in update:
                raise ValueError("Each update note must include note_id")
            note_id = int(update["note_id"])
            if note_id not in existing:
                raise ValueError("No note with note_id %s" % note_id)
            data = dict(existing[note_id])
            data.update(update)
            modified.append(data)
        if modified:
            self._replace_notes_by_id(clip, modified)
        return self._midi_get_notes(payload)

    def _midi_remove_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        ids = payload.get("note_ids")
        if ids:
            clip.remove_notes_by_id(tuple(int(note_id) for note_id in ids))
        else:
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
            self._remove_notes_region(clip, from_pitch, pitch_span, from_time, time_span)
        return self._midi_get_notes(payload)

    def _midi_clear_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        if self._has_note_region(payload):
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
        else:
            from_pitch, pitch_span, from_time, time_span = (0, 128, 0.0, max(float(self._safe_get(clip, "length", 0.0)), 1576800.0))
        self._remove_notes_region(clip, from_pitch, pitch_span, from_time, time_span)
        return self._midi_get_notes(payload)

    def _midi_transform_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        notes = self._midi_note_dicts(clip, payload if self._has_note_region(payload) else None)
        modified = []
        transpose = int(payload.get("transpose", 0))
        time_delta = float(payload.get("time_delta", 0.0))
        duration_scale = float(payload.get("duration_scale", 1.0))
        duration_delta = float(payload.get("duration_delta", 0.0))
        velocity_scale = float(payload.get("velocity_scale", 1.0))
        velocity_delta = float(payload.get("velocity_delta", 0.0))
        for note in notes:
            data = dict(note)
            data["pitch"] = self._clamp_int(int(data.get("pitch", 0)) + transpose, 0, 127)
            data["start_time"] = max(0.0, float(data.get("start_time", 0.0)) + time_delta)
            data["duration"] = max(0.0001, float(data.get("duration", 0.0)) * duration_scale + duration_delta)
            data["velocity"] = self._clamp_float(float(data.get("velocity", 100.0)) * velocity_scale + velocity_delta, 0.0, 127.0)
            if "probability" in payload:
                data["probability"] = self._clamp_float(float(payload["probability"]), 0.0, 1.0)
            if "velocity_deviation" in payload:
                data["velocity_deviation"] = self._clamp_float(float(payload["velocity_deviation"]), -127.0, 127.0)
            if "release_velocity" in payload:
                data["release_velocity"] = self._clamp_float(float(payload["release_velocity"]), 0.0, 127.0)
            if "mute" in payload:
                data["mute"] = bool(payload["mute"])
            modified.append(data)
        if modified:
            self._replace_notes_by_id(clip, modified)
        return self._midi_get_notes(payload)

    def _midi_duplicate_region(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        region_start = float(payload.get("start", 0.0))
        if "length" in payload:
            region_length = float(payload.get("length"))
        elif "end" in payload:
            region_length = float(payload.get("end")) - region_start
        else:
            raise ValueError("midi-duplicate-region needs --length or --end")
        destination_time = float(payload.get("destination_time"))
        pitch = int(payload.get("pitch", -1))
        transposition = int(payload.get("transpose", 0))
        try:
            clip.duplicate_region(region_start, region_length, destination_time, pitch, transposition)
        except TypeError:
            if pitch != -1 or transposition != 0:
                clip.duplicate_region(region_start, region_length, destination_time, pitch, transposition)
            else:
                clip.duplicate_region(region_start, region_length, destination_time)
        result_payload = dict(payload)
        for key in ("start", "end", "length", "pitch_min", "pitch_max"):
            result_payload.pop(key, None)
        return self._midi_get_notes(result_payload)

    def _midi_note_spec(self, note, include_note_id=False):
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object")
        data = {
            "pitch": int(note["pitch"]),
            "start_time": float(note.get("start_time", note.get("start", 0.0))),
            "duration": float(note.get("duration", 1.0)),
            "velocity": float(note.get("velocity", 100.0)),
            "mute": bool(note.get("mute", False)),
            "probability": float(note.get("probability", 1.0)),
            "velocity_deviation": float(note.get("velocity_deviation", 0.0)),
            "release_velocity": float(note.get("release_velocity", 64.0)),
        }
        if include_note_id and "note_id" in note:
            data["note_id"] = int(note["note_id"])
        spec_class = Live.Clip.MidiNoteSpecification
        try:
            return spec_class(**data)
        except TypeError:
            spec = spec_class()
            for key, value in data.items():
                setattr(spec, key, value)
            return spec
