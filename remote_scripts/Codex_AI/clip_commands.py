"""ClipCommand mixins for the Codex_AI Ableton bridge."""

import os


class ClipCommandMixin(object):
    def _clip_slots(self, payload):
        track = self._resolve_track(payload.get("track"))
        slots = []
        for index, slot in enumerate(track.clip_slots):
            info = {
                "index": index,
                "has_clip": slot.has_clip,
                "is_playing": slot.is_playing,
                "is_recording": slot.is_recording,
                "will_record_on_start": slot.will_record_on_start,
            }
            if slot.has_clip:
                info["clip"] = self._clip_info(slot.clip)
            slots.append(info)
        return {"track": track.name, "clip_slots": slots}

    def _fire_clip(self, payload):
        track = self._resolve_track(payload.get("track"))
        slot_index = int(payload.get("slot", 0))
        slot = self._resolve_clip_slot(track, slot_index)
        slot.fire()
        return {"track": track.name, "slot": slot_index, "done": True}

    def _clips(self, payload):
        track = self._resolve_track(payload.get("track"))
        arrangement = []
        for index, clip in enumerate(track.arrangement_clips):
            arrangement.append({"index": index, "clip": self._clip_info(clip)})
        slots = []
        for index, slot in enumerate(track.clip_slots):
            info = {
                "index": index,
                "has_clip": slot.has_clip,
                "is_playing": slot.is_playing,
                "is_recording": slot.is_recording,
                "will_record_on_start": slot.will_record_on_start,
            }
            if slot.has_clip:
                info["clip"] = self._clip_info(slot.clip)
            slots.append(info)
        return {"track": track.name, "arrangement_clips": arrangement, "clip_slots": slots}

    def _clip_create_midi(self, payload):
        track = self._resolve_track(payload.get("track"))
        self._ensure_midi_track(track)
        name = payload.get("name")
        color = payload.get("color")
        color_index = payload.get("color_index")
        if "slot" in payload:
            slot_index = int(payload.get("slot"))
            slot = self._resolve_clip_slot(track, slot_index)
            if slot.has_clip:
                if payload.get("replace", False):
                    slot.delete_clip()
                else:
                    raise ValueError("Clip slot %s on %s already has a clip" % (slot_index, track.name))
            length = self._clip_length_from_payload(payload, None)
            slot.create_clip(length)
            clip = slot.clip
            location = {"kind": "session", "track": track.name, "slot": slot_index}
        else:
            start, length = self._arrangement_range_from_payload(payload, 0.0, 4.0)
            clip = track.create_midi_clip(start, length)
            if clip is None:
                clip = self._find_arrangement_clip(track, start, length)
            location = {"kind": "arrangement", "track": track.name, "start": start, "length": length}
        self._set_optional_clip_property(clip, "name", name)
        self._set_optional_clip_property(clip, "color", color)
        self._set_optional_clip_property(clip, "color_index", color_index)
        try:
            self.song().view.selected_track = track
            self.song().view.detail_clip = clip
        except Exception:
            pass
        return {"location": location, "clip": self._clip_info(clip)}

    def _clip_create_audio(self, payload):
        track = self._resolve_track(payload.get("track"))
        self._ensure_audio_track(track)
        file_path = str(payload.get("file") or payload.get("file_path") or "").strip()
        if not file_path:
            raise ValueError("file is required")
        if not os.path.isabs(file_path):
            raise ValueError("Audio file path must be absolute")
        if not os.path.exists(file_path):
            raise ValueError("Audio file does not exist: %s" % file_path)
        name = payload.get("name")
        color = payload.get("color")
        color_index = payload.get("color_index")
        if "slot" in payload:
            slot_index = int(payload.get("slot"))
            slot = self._resolve_clip_slot(track, slot_index)
            if slot.has_clip:
                if payload.get("replace", False):
                    slot.delete_clip()
                else:
                    raise ValueError("Clip slot %s on %s already has a clip" % (slot_index, track.name))
            clip = slot.create_audio_clip(file_path)
            if clip is None:
                clip = slot.clip
            location = {"kind": "session", "track": track.name, "slot": slot_index}
        else:
            if payload.get("from_loop", False):
                start = float(self.song().loop_start)
            else:
                start = float(payload.get("start", 0.0))
            clip = track.create_audio_clip(file_path, start)
            if clip is None:
                clip = self._find_arrangement_clip_at(track, start)
            location = {"kind": "arrangement", "track": track.name, "start": start}
        self._set_optional_clip_property(clip, "name", name)
        self._set_optional_clip_property(clip, "color", color)
        self._set_optional_clip_property(clip, "color_index", color_index)
        if "warping" in payload:
            clip.warping = bool(payload["warping"])
        if "warp_mode" in payload:
            clip.warp_mode = int(payload["warp_mode"])
        try:
            self.song().view.selected_track = track
            self.song().view.detail_clip = clip
        except Exception:
            pass
        return {"location": location, "clip": self._clip_info(clip), "warp_markers": self._warp_marker_infos(clip)}

    def _clip_set(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        changed = {}
        for key, attr in (
            ("name", "name"),
            ("color", "color"),
            ("color_index", "color_index"),
            ("muted", "muted"),
            ("looping", "looping"),
            ("launch_mode", "launch_mode"),
            ("launch_quantization", "launch_quantization"),
            ("legato", "legato"),
            ("velocity_amount", "velocity_amount"),
            ("signature_numerator", "signature_numerator"),
            ("signature_denominator", "signature_denominator"),
            ("position", "position"),
            ("loop_start", "loop_start"),
            ("loop_end", "loop_end"),
            ("start_marker", "start_marker"),
            ("end_marker", "end_marker"),
            ("gain", "gain"),
            ("pitch_coarse", "pitch_coarse"),
            ("pitch_fine", "pitch_fine"),
            ("ram_mode", "ram_mode"),
            ("warping", "warping"),
            ("warp_mode", "warp_mode"),
        ):
            if key in payload:
                setattr(clip, attr, payload[key])
                changed[attr] = self._safe_get(clip, attr)
        return {"location": self._clip_ref_info(ref), "changed": changed, "clip": self._clip_info(clip)}

    def _clip_delete(self, payload):
        ref = self._resolve_clip_ref(payload)
        info = self._clip_info(ref["clip"])
        location = self._clip_ref_info(ref)
        self._delete_clip_ref(ref)
        return {"location": location, "deleted_clip": info, "done": True}

    def _clip_copy_or_move(self, payload, move):
        source = self._resolve_clip_ref(payload, "source")
        source_clip = source["clip"]
        if not self._safe_get(source_clip, "is_midi_clip", False):
            raise ValueError("Only MIDI clip copy/move is implemented")
        source_info = self._clip_ref_info(source)
        target = self._create_midi_clip_destination(payload, source)
        self._copy_midi_clip_contents(source_clip, target["clip"])
        if move:
            self._delete_clip_ref(source)
        return {
            "source": source_info,
            "target": self._clip_ref_info(target),
            "clip": self._clip_info(target["clip"]),
            "moved": move,
            "done": True,
        }

    def _clip_split(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Only MIDI clips can be split by this command")
        if not self._safe_get(clip, "is_arrangement_clip", False):
            raise ValueError("clip-split currently supports Arrangement clips; copy Session clips to slots first")
        track = ref.get("track")
        if track is None:
            raise ValueError("Could not resolve Arrangement clip track")
        split_time = float(payload.get("time"))
        relative = bool(payload.get("relative", False))
        clip_start = float(self._safe_get(clip, "start_time", 0.0))
        clip_length = float(self._safe_get(clip, "length", 0.0))
        split_offset = split_time if relative else split_time - clip_start
        if split_offset <= 0.0 or split_offset >= clip_length:
            raise ValueError("Split time must be inside the clip range")
        original_info = self._clip_info(clip)
        original_name = self._safe_get(clip, "name", "")
        source_info = self._clip_ref_info(ref)
        notes = self._midi_note_dicts(clip)
        left_notes, right_notes = self._split_note_dicts(notes, split_offset)
        self._delete_clip_ref(ref)
        left = track.create_midi_clip(clip_start, split_offset)
        if left is None:
            left = self._find_arrangement_clip(track, clip_start, split_offset)
        right_start = clip_start + split_offset
        right_length = clip_length - split_offset
        right = track.create_midi_clip(right_start, right_length)
        if right is None:
            right = self._find_arrangement_clip(track, right_start, right_length)
        self._apply_clip_look(original_info, left, original_name)
        self._apply_clip_look(original_info, right, (original_name + " Split").strip())
        self._add_note_dicts(left, left_notes)
        self._add_note_dicts(right, right_notes)
        return {
            "source": source_info,
            "split_time": split_time,
            "split_offset": split_offset,
            "left": self._clip_info(left),
            "right": self._clip_info(right),
            "done": True,
        }
