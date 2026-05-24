"""Clip envelope discovery and focus helpers for the Codex_AI bridge."""


class ClipEnvelopeCommandMixin(object):
    def _clip_focus(self, payload):
        ref = self._resolve_clip_ref(payload)
        self._focus_clip_detail(ref)
        return {"location": self._clip_ref_info(ref), "clip": self._clip_info(ref["clip"]), "done": True}

    def _clip_envelope_targets(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._focus_clip_detail(ref)
        return {
            "location": self._clip_ref_info(ref),
            "clip": self._clip_info(clip),
            "clip_type": self._clip_type(clip),
            "has_envelopes": self._safe_get(clip, "has_envelopes"),
        }

    def _focus_clip_detail(self, ref):
        clip = ref["clip"]
        track = ref.get("track")
        if track is None:
            track = self._track_for_clip(clip)
        try:
            if track is not None:
                self.song().view.selected_track = track
            if ref.get("kind") == "session" and ref.get("slot") is not None:
                self.song().view.highlighted_clip_slot = ref["slot"]
            self.song().view.detail_clip = clip
        except Exception:
            pass
        try:
            self.application().view.show_view("Detail")
            self.application().view.show_view("Detail/Clip")
        except Exception:
            pass

    def _track_for_clip(self, clip):
        parent = self._safe_get(clip, "canonical_parent")
        if parent is None:
            return None
        if hasattr(parent, "clip_slots") and hasattr(parent, "mixer_device"):
            return parent
        return self._safe_get(parent, "canonical_parent")

    def _clip_type(self, clip):
        if self._safe_get(clip, "is_audio_clip", False):
            return "audio"
        if self._safe_get(clip, "is_midi_clip", False):
            return "midi"
        return "unknown"
