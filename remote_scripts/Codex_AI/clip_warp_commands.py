"""ClipWarpCommand mixins for the Codex_AI Ableton bridge."""


class ClipWarpCommandMixin(object):
    def _clip_warp(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._ensure_audio_clip(clip)
        changed = {}
        for key, attr in (
            ("warping", "warping"),
            ("warp_mode", "warp_mode"),
            ("gain", "gain"),
            ("pitch_coarse", "pitch_coarse"),
            ("pitch_fine", "pitch_fine"),
            ("ram_mode", "ram_mode"),
        ):
            if key in payload:
                setattr(clip, attr, payload[key])
                changed[attr] = self._safe_get(clip, attr)
        if "clip_bpm" in payload:
            changed["clip_bpm"] = self._set_clip_segment_bpm(clip, float(payload["clip_bpm"]))
        return self._clip_warp_info(ref, changed)

    def _clip_warp_marker_add(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._ensure_warped_audio_clip(clip)
        beat_time = float(payload.get("beat_time"))
        sample_time = payload.get("sample_time", None)
        marker = self._add_warp_marker(clip, beat_time, sample_time)
        return self._clip_warp_info(ref, {"added_marker": marker})

    def _clip_warp_marker_move(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._ensure_warped_audio_clip(clip)
        beat_time = float(payload.get("beat_time"))
        if "to_beat" in payload:
            distance = float(payload.get("to_beat")) - beat_time
        else:
            distance = float(payload.get("distance"))
        clip.move_warp_marker(beat_time, distance)
        return self._clip_warp_info(ref, {"moved_marker": {"beat_time": beat_time, "distance": distance}})

    def _clip_warp_marker_remove(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._ensure_warped_audio_clip(clip)
        beat_time = float(payload.get("beat_time"))
        clip.remove_warp_marker(beat_time)
        return self._clip_warp_info(ref, {"removed_marker": {"beat_time": beat_time}})

    def _clip_warp_info(self, ref, changed=None):
        clip = ref["clip"]
        return {
            "location": self._clip_ref_info(ref),
            "changed": changed or {},
            "clip": self._clip_info(clip),
            "warp_markers": self._warp_marker_infos(clip),
        }

    def _set_clip_segment_bpm(self, clip, bpm):
        self._ensure_warped_audio_clip(clip)
        if bpm <= 0.0:
            raise ValueError("clip_bpm must be greater than 0")
        beat_time = 1.0
        sample_time = 60.0 / bpm
        sample_duration = self._audio_sample_duration(clip)
        if sample_duration is not None and sample_duration > 0.0:
            sample_time = max(0.0, min(sample_time, sample_duration))
        existing = self._find_warp_marker(clip, beat_time)
        if existing is not None:
            try:
                clip.remove_warp_marker(float(existing.get("beat_time", beat_time)))
            except Exception:
                pass
        marker = self._add_warp_marker(clip, beat_time, sample_time)
        return {
            "requested": bpm,
            "actual": self._clip_segment_bpm(clip),
            "beat_time": beat_time,
            "sample_time": sample_time,
            "marker": marker,
        }
