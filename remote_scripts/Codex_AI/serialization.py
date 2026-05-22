"""Serialization mixins for the Codex_AI Ableton bridge."""


class SerializationMixin(object):
    def _track_info(self, track, index, kind="track"):
        mixer = track.mixer_device
        info = {
            "kind": kind,
            "index": index,
            "name": track.name,
            "volume": self._parameter_info(mixer.volume),
            "pan": self._parameter_info(mixer.panning),
            "mute": self._safe_get(track, "mute"),
            "solo": self._safe_get(track, "solo"),
            "arm": self._safe_get(track, "arm"),
            "device_count": len(track.devices),
            "send_count": len(mixer.sends),
        }
        return info

    def _device_infos(self, track):
        return [self._device_info(device, index) for index, device in enumerate(track.devices)]

    def _device_info(self, device, index):
        return {
            "index": index,
            "name": device.name,
            "class_name": device.class_name,
            "can_have_chains": getattr(device, "can_have_chains", False),
            "parameter_count": len(device.parameters),
        }

    def _clip_info(self, clip):
        return {
            "name": clip.name,
            "color": self._safe_get(clip, "color"),
            "color_index": self._safe_get(clip, "color_index"),
            "is_audio_clip": self._safe_get(clip, "is_audio_clip"),
            "is_midi_clip": self._safe_get(clip, "is_midi_clip"),
            "is_session_clip": self._safe_get(clip, "is_session_clip"),
            "is_arrangement_clip": self._safe_get(clip, "is_arrangement_clip"),
            "length": self._safe_get(clip, "length"),
            "start_time": self._safe_get(clip, "start_time"),
            "end_time": self._safe_get(clip, "end_time"),
            "looping": self._safe_get(clip, "looping"),
            "loop_start": self._safe_get(clip, "loop_start"),
            "loop_end": self._safe_get(clip, "loop_end"),
            "start_marker": self._safe_get(clip, "start_marker"),
            "end_marker": self._safe_get(clip, "end_marker"),
            "muted": self._safe_get(clip, "muted"),
            "launch_mode": self._safe_get(clip, "launch_mode"),
            "launch_quantization": self._safe_get(clip, "launch_quantization"),
            "legato": self._safe_get(clip, "legato"),
            "signature_numerator": self._safe_get(clip, "signature_numerator"),
            "signature_denominator": self._safe_get(clip, "signature_denominator"),
            "velocity_amount": self._safe_get(clip, "velocity_amount"),
            "gain": self._safe_get(clip, "gain"),
            "gain_display_string": self._safe_get(clip, "gain_display_string"),
            "file_path": self._safe_get(clip, "file_path"),
            "pitch_coarse": self._safe_get(clip, "pitch_coarse"),
            "pitch_fine": self._safe_get(clip, "pitch_fine"),
            "ram_mode": self._safe_get(clip, "ram_mode"),
            "sample_length": self._safe_get(clip, "sample_length"),
            "sample_rate": self._safe_get(clip, "sample_rate"),
            "warp_mode": self._safe_get(clip, "warp_mode"),
            "warping": self._safe_get(clip, "warping"),
        }

    def _scene_info(self, scene, index):
        return {
            "index": index,
            "name": scene.name,
            "color": self._safe_get(scene, "color"),
            "color_index": self._safe_get(scene, "color_index"),
            "is_empty": self._safe_get(scene, "is_empty"),
            "is_triggered": self._safe_get(scene, "is_triggered"),
            "tempo": self._safe_get(scene, "tempo"),
            "tempo_enabled": self._safe_get(scene, "tempo_enabled"),
            "time_signature_enabled": self._safe_get(scene, "time_signature_enabled"),
            "time_signature_numerator": self._safe_get(scene, "time_signature_numerator"),
            "time_signature_denominator": self._safe_get(scene, "time_signature_denominator"),
        }

    def _parameter_infos(self, device):
        return [self._parameter_info(parameter, index) for index, parameter in enumerate(device.parameters)]

    def _parameter_info(self, parameter, index=None):
        try:
            display_value = parameter.str_for_value(parameter.value)
        except Exception:
            display_value = str(parameter.value)
        info = {
            "name": parameter.name,
            "value": parameter.value,
            "min": parameter.min,
            "max": parameter.max,
            "display_value": display_value,
            "is_enabled": getattr(parameter, "is_enabled", True),
            "is_quantized": getattr(parameter, "is_quantized", False),
            "automation_state": self._safe_get(parameter, "automation_state"),
            "state": self._safe_get(parameter, "state"),
            "default_value": self._safe_get(parameter, "default_value"),
            "original_name": self._safe_get(parameter, "original_name"),
        }
        value_items = self._safe_get(parameter, "value_items")
        if value_items is not None:
            info["value_items"] = self._serialize(value_items)
        if index is not None:
            info["index"] = index
        return info

    def _serialize(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, dict):
            return {str(key): self._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize(item) for item in list(value)[:512]]
        if self._is_indexable_vector(value):
            length = len(value)
            return {
                "type": type(value).__name__,
                "length": length,
                "items": [self._serialize(value[index]) for index in range(min(length, 512))],
                "truncated": length > 512,
            }
        if hasattr(value, "min") and hasattr(value, "max") and hasattr(value, "value"):
            return self._parameter_info(value)
        if hasattr(value, "clip_slots") and hasattr(value, "mixer_device"):
            return self._track_info(value, self._track_index(value), self._track_kind(value))
        if hasattr(value, "parameters") and hasattr(value, "class_name"):
            return self._device_info(value, -1)
        if hasattr(value, "is_audio_clip") or hasattr(value, "is_midi_clip"):
            return self._clip_info(value)
        if hasattr(value, "is_loadable") and hasattr(value, "children"):
            return {"type": type(value).__name__, "item": self._browser_item_info(value)}
        if hasattr(value, "sample_time") and hasattr(value, "beat_time"):
            return self._warp_marker_info(value)
        if hasattr(value, "insert_step") and hasattr(value, "value_at_time"):
            return self._automation_envelope_info(value)
        if hasattr(value, "pitch") and hasattr(value, "start_time"):
            return self._note_info(value)
        return {"type": type(value).__name__, "summary": self._summary(value)}

    def _note_info(self, note):
        keys = (
            "note_id",
            "pitch",
            "start_time",
            "duration",
            "velocity",
            "velocity_deviation",
            "release_velocity",
            "probability",
            "mute",
        )
        return {key: self._safe_get(note, key) for key in keys if self._safe_get(note, key) is not None}

    def _summary(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return {"type": type(value).__name__, "length": len(value)}
        if self._is_indexable_vector(value):
            return {"type": type(value).__name__, "length": len(value)}
        name = self._safe_get(value, "name")
        class_name = self._safe_get(value, "class_name")
        summary = {"type": type(value).__name__}
        if name is not None:
            summary["name"] = name
        if class_name is not None:
            summary["class_name"] = class_name
        return summary

    def _track_index(self, track):
        for index, candidate in enumerate(self.song().tracks):
            if candidate == track:
                return index
        for index, candidate in enumerate(self.song().return_tracks):
            if candidate == track:
                return index
        return 0

    def _track_kind(self, track):
        if track == self.song().master_track:
            return "master"
        if track in list(self.song().return_tracks):
            return "return"
        return "track"

    def _resolve_scene(self, identifier):
        scenes = list(self.song().scenes)
        if isinstance(identifier, int):
            if 0 <= identifier < len(scenes):
                return scenes[identifier]
            raise ValueError("Scene index out of range: %s" % identifier)
        text = str(identifier).strip()
        if text.isdigit():
            return self._resolve_scene(int(text))
        normalized = self._normalize_name(text)
        matches = [scene for scene in scenes if normalized in self._normalize_name(scene.name)]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Scene %r is ambiguous: %s" % (identifier, [scene.name for scene in matches]))
        raise ValueError("Unknown scene: %r" % identifier)

    def _scene_index(self, scene):
        for index, candidate in enumerate(self.song().scenes):
            if candidate == scene:
                return index
        return 0
