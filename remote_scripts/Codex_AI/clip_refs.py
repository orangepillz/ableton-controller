"""ClipReference mixins for the Codex_AI Ableton bridge."""


class ClipReferenceMixin(object):
    def _resolve_clip(self, payload):
        return self._resolve_clip_ref(payload)["clip"]

    def _ensure_midi_track(self, track):
        if not self._safe_get(track, "has_midi_input", False):
            raise ValueError("Track %s is not a MIDI track" % track.name)

    def _ensure_audio_track(self, track):
        if not self._safe_get(track, "has_audio_input", False):
            raise ValueError("Track %s is not an audio track" % track.name)

    def _ensure_midi_clip(self, clip):
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")

    def _ensure_audio_clip(self, clip):
        if not self._safe_get(clip, "is_audio_clip", False):
            raise ValueError("Clip is not an audio clip")

    def _ensure_warped_audio_clip(self, clip):
        self._ensure_audio_clip(clip)
        if not self._safe_get(clip, "warping", False):
            raise ValueError("Clip warping must be enabled before editing warp markers")

    def _resolve_clip_slot(self, track, slot_index):
        slots = list(track.clip_slots)
        if slot_index < 0 or slot_index >= len(slots):
            raise ValueError("Clip slot index out of range: %s" % slot_index)
        return slots[slot_index]

    def _resolve_clip_ref(self, payload, prefix=""):
        path = self._prefixed(payload, prefix, "path")
        if path:
            clip = self._resolve_lom_path(path)
            if not hasattr(clip, "is_audio_clip") and not hasattr(clip, "is_midi_clip"):
                raise ValueError("Path did not resolve to a clip")
            return self._clip_ref_from_clip(clip)

        track = self._resolve_track(self._prefixed(payload, prefix, "track"))
        arrangement_index = self._prefixed(payload, prefix, "arrangement_index", None)
        if arrangement_index is not None:
            clips = list(track.arrangement_clips)
            index = int(arrangement_index)
            if index < 0 or index >= len(clips):
                raise ValueError("Arrangement clip index out of range: %s" % index)
            return {"kind": "arrangement", "track": track, "arrangement_index": index, "clip": clips[index]}

        arrangement_start = self._prefixed(payload, prefix, "arrangement_start", None)
        if arrangement_start is not None:
            clip = self._find_arrangement_clip_at(track, float(arrangement_start))
            return self._clip_ref_from_clip(clip)

        slot_index = int(self._prefixed(payload, prefix, "slot", 0))
        slot = self._resolve_clip_slot(track, slot_index)
        if not slot.has_clip:
            raise ValueError("Clip slot %s on %s has no clip" % (slot_index, track.name))
        return {"kind": "session", "track": track, "slot": slot, "slot_index": slot_index, "clip": slot.clip}

    def _clip_ref_from_clip(self, clip):
        ref = {"kind": "path", "clip": clip}
        try:
            if self._safe_get(clip, "is_session_clip", False):
                slot = clip.canonical_parent
                track = slot.canonical_parent
                ref.update({"kind": "session", "track": track, "slot": slot, "slot_index": self._slot_index(track, slot)})
            elif self._safe_get(clip, "is_arrangement_clip", False):
                track = clip.canonical_parent
                ref.update({"kind": "arrangement", "track": track, "arrangement_index": self._arrangement_clip_index(track, clip)})
        except Exception:
            pass
        return ref

    def _delete_clip_ref(self, ref):
        if ref.get("kind") == "session" and ref.get("slot") is not None:
            ref["slot"].delete_clip()
            return
        track = ref.get("track")
        if track is None:
            track = ref["clip"].canonical_parent
        track.delete_clip(ref["clip"])

    def _clip_ref_info(self, ref):
        info = {"kind": ref.get("kind")}
        track = ref.get("track")
        if track is not None:
            info["track"] = track.name
            info["track_index"] = self._track_index(track)
        if "slot_index" in ref:
            info["slot"] = ref["slot_index"]
        if "arrangement_index" in ref:
            info["arrangement_index"] = ref["arrangement_index"]
        clip = ref.get("clip")
        if clip is not None:
            if self._safe_get(clip, "is_arrangement_clip", False):
                info["start_time"] = self._safe_get(clip, "start_time")
                info["end_time"] = self._safe_get(clip, "end_time")
            info["clip"] = self._clip_info(clip)
        return info

    def _prefixed(self, payload, prefix, key, default=None):
        if prefix:
            return payload.get("%s_%s" % (prefix, key), default)
        return payload.get(key, default)

    def _clip_length_from_payload(self, payload, fallback):
        if payload.get("from_loop", False):
            return float(self.song().loop_length)
        if "length" in payload:
            return float(payload.get("length"))
        if "end" in payload:
            start = float(payload.get("start", 0.0))
            return float(payload.get("end")) - start
        if fallback is not None:
            return float(fallback)
        return 4.0

    def _arrangement_range_from_payload(self, payload, fallback_start, fallback_length):
        if payload.get("from_loop", False):
            start = float(self.song().loop_start)
            length = float(self.song().loop_length)
        else:
            start = float(payload.get("start", fallback_start))
            length = self._clip_length_from_payload(payload, fallback_length)
        if "end" in payload:
            end = float(payload.get("end"))
            length = end - start
        if length <= 0.0:
            raise ValueError("Clip length must be greater than 0")
        return start, length

    def _create_midi_clip_destination(self, payload, source_ref):
        source_clip = source_ref["clip"]
        source_track = source_ref.get("track")
        target_track = self._resolve_track(payload.get("dest_track", source_track.name if source_track is not None else None))
        self._ensure_midi_track(target_track)
        length = self._clip_length_from_payload(payload, self._safe_get(source_clip, "length", 4.0))
        dest_slot = payload.get("dest_slot")
        if dest_slot is not None:
            slot_index = int(dest_slot)
            slot = self._resolve_clip_slot(target_track, slot_index)
            if slot.has_clip:
                if payload.get("replace", False):
                    slot.delete_clip()
                else:
                    raise ValueError("Destination clip slot %s on %s already has a clip" % (slot_index, target_track.name))
            slot.create_clip(length)
            return {"kind": "session", "track": target_track, "slot": slot, "slot_index": slot_index, "clip": slot.clip}

        if payload.get("dest_from_loop", False):
            start = float(self.song().loop_start)
        elif "dest_start" in payload:
            start = float(payload.get("dest_start"))
        elif "start" in payload:
            start = float(payload.get("start"))
        else:
            start = float(self._safe_get(source_clip, "start_time", 0.0))
        if "dest_end" in payload:
            length = float(payload.get("dest_end")) - start
        if length <= 0.0:
            raise ValueError("Destination clip length must be greater than 0")
        clip = target_track.create_midi_clip(start, length)
        if clip is None:
            clip = self._find_arrangement_clip(target_track, start, length)
        return self._clip_ref_from_clip(clip)

    def _find_arrangement_clip(self, track, start, length):
        target_end = start + length
        for clip in track.arrangement_clips:
            clip_start = float(self._safe_get(clip, "start_time", -1.0))
            clip_end = float(self._safe_get(clip, "end_time", -1.0))
            if abs(clip_start - start) < 0.0001 and abs(clip_end - target_end) < 0.0001:
                return clip
        raise ValueError("Could not find newly-created Arrangement clip")

    def _find_arrangement_clip_at(self, track, start):
        matches = []
        for clip in track.arrangement_clips:
            clip_start = float(self._safe_get(clip, "start_time", -1.0))
            clip_end = float(self._safe_get(clip, "end_time", -1.0))
            if abs(clip_start - start) < 0.0001 or (clip_start <= start < clip_end):
                matches.append(clip)
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Arrangement time %s matches multiple clips" % start)
        raise ValueError("No Arrangement clip at %s on %s" % (start, track.name))

    def _slot_index(self, track, slot):
        for index, candidate in enumerate(track.clip_slots):
            if candidate == slot:
                return index
        return -1

    def _arrangement_clip_index(self, track, clip):
        for index, candidate in enumerate(track.arrangement_clips):
            if candidate == clip:
                return index
        return -1

    def _copy_midi_clip_contents(self, source, target):
        self._apply_clip_look(self._clip_info(source), target, self._safe_get(source, "name", ""))
        self._add_note_dicts(target, self._midi_note_dicts(source))

    def _copy_audio_clip_contents(self, source, target):
        source_info = self._clip_info(source)
        self._apply_clip_look(source_info, target, self._safe_get(source, "name", ""))
        for attr in (
            "warping",
            "warp_mode",
            "gain",
            "pitch_coarse",
            "pitch_fine",
            "ram_mode",
        ):
            self._set_optional_clip_property(target, attr, source_info.get(attr))
        self._copy_audio_marker_properties(source_info, target)
        self._copy_audio_warp_markers(source, target)

    def _copy_audio_marker_properties(self, source_info, target):
        end_marker = source_info.get("end_marker")
        if end_marker is None and source_info.get("length") is not None:
            start_marker = source_info.get("start_marker") or 0.0
            try:
                end_marker = float(start_marker) + float(source_info["length"])
            except Exception:
                end_marker = None
        marker_values = {
            "end_marker": end_marker,
            "start_marker": source_info.get("start_marker"),
            "loop_end": source_info.get("loop_end"),
            "loop_start": source_info.get("loop_start"),
        }
        for attr in ("end_marker", "start_marker", "loop_end", "loop_start"):
            self._set_optional_clip_property(target, attr, marker_values.get(attr))

    def _copy_audio_warp_markers(self, source, target):
        if not self._safe_get(source, "warping", False):
            return
        for marker in self._warp_marker_infos(source):
            beat_time = marker.get("beat_time")
            if beat_time is None:
                continue
            self._replace_audio_warp_marker(target, beat_time, marker.get("sample_time"))

    def _replace_audio_warp_marker(self, clip, beat_time, sample_time):
        existing = self._find_warp_marker(clip, beat_time)
        if existing is not None:
            try:
                clip.remove_warp_marker(float(existing.get("beat_time", beat_time)))
            except Exception:
                pass
        self._add_warp_marker(clip, float(beat_time), sample_time)

    def _apply_clip_look(self, info, clip, name):
        self._set_optional_clip_property(clip, "name", name)
        self._set_optional_clip_property(clip, "color", info.get("color"))
        self._set_optional_clip_property(clip, "color_index", info.get("color_index"))
        self._set_optional_clip_property(clip, "muted", info.get("muted"))
        self._set_optional_clip_property(clip, "looping", info.get("looping"))
        self._set_optional_clip_property(clip, "signature_numerator", info.get("signature_numerator"))
        self._set_optional_clip_property(clip, "signature_denominator", info.get("signature_denominator"))

    def _set_optional_clip_property(self, clip, attr, value):
        if value is None:
            return
        try:
            setattr(clip, attr, value)
        except Exception:
            pass
