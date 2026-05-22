"""MidiHelper mixins for the Codex_AI Ableton bridge."""


class MidiHelperMixin(object):
    def _add_note_dicts(self, clip, notes):
        if not notes:
            return
        clip.add_new_notes(tuple(self._midi_note_spec(note) for note in notes))

    def _replace_notes_by_id(self, clip, notes):
        ids = [int(note["note_id"]) for note in notes if "note_id" in note]
        if ids:
            clip.remove_notes_by_id(tuple(ids))
        self._add_note_dicts(clip, notes)

    def _midi_note_dicts(self, clip, region_payload=None):
        self._ensure_midi_clip(clip)
        if region_payload is not None:
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(region_payload, clip)
            notes = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)
        else:
            try:
                notes = clip.get_all_notes_extended()
            except TypeError:
                notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
        serialized = self._serialize(notes)
        if isinstance(serialized, dict) and "items" in serialized:
            return serialized["items"]
        if isinstance(serialized, list):
            return serialized
        return []

    def _remove_notes_region(self, clip, from_pitch, pitch_span, from_time, time_span):
        try:
            clip.remove_notes_extended(int(from_pitch), int(pitch_span), float(from_time), float(time_span))
        except TypeError:
            clip.remove_notes(float(from_time), int(from_pitch), float(time_span), int(pitch_span))

    def _midi_region_args(self, payload, clip):
        from_pitch = self._clamp_int(int(payload.get("pitch_min", 0)), 0, 127)
        pitch_max = self._clamp_int(int(payload.get("pitch_max", 127)), from_pitch, 127)
        pitch_span = pitch_max - from_pitch + 1
        from_time = max(0.0, float(payload.get("start", 0.0)))
        if "end" in payload:
            time_span = float(payload.get("end")) - from_time
        elif "length" in payload:
            time_span = float(payload.get("length"))
        else:
            time_span = max(float(self._safe_get(clip, "length", 0.0)) - from_time, 0.0)
        if time_span < 0.0:
            raise ValueError("MIDI note region end must be after start")
        return from_pitch, pitch_span, from_time, time_span

    def _has_note_region(self, payload):
        return any(key in payload for key in ("start", "end", "length", "pitch_min", "pitch_max"))

    def _split_note_dicts(self, notes, split_offset):
        left = []
        right = []
        for note in notes:
            start = float(note.get("start_time", 0.0))
            duration = float(note.get("duration", 0.0))
            end = start + duration
            if start < split_offset:
                left_duration = min(end, split_offset) - start
                if left_duration > 0.0001:
                    data = dict(note)
                    data["duration"] = left_duration
                    left.append(data)
            if end > split_offset:
                right_start = max(start, split_offset) - split_offset
                right_duration = end - max(start, split_offset)
                if right_duration > 0.0001:
                    data = dict(note)
                    data["start_time"] = right_start
                    data["duration"] = right_duration
                    right.append(data)
        return left, right
