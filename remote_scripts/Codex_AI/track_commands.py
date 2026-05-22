"""TrackCommand mixins for the Codex_AI Ableton bridge."""


class TrackCommandMixin(object):
    def _create_track(self, payload):
        kind = str(payload.get("type", "midi")).lower()
        index = payload.get("index")
        args = [] if index is None else [int(index)]
        if kind == "audio":
            track = self.song().create_audio_track(*args)
        elif kind == "midi":
            track = self.song().create_midi_track(*args)
        elif kind == "return":
            track = self.song().create_return_track(*args)
        else:
            raise ValueError("Track type must be audio, midi, or return")
        if payload.get("name"):
            track.name = str(payload.get("name"))
        return self._track_info(track, self._track_index(track), self._track_kind(track))

    def _create_scene(self, payload):
        index = payload.get("index")
        scene = self.song().create_scene() if index is None else self.song().create_scene(int(index))
        if payload.get("name"):
            scene.name = str(payload.get("name"))
        return self._scene_info(scene, self._scene_index(scene))

    def _set_routing(self, payload):
        track = self._resolve_track(payload.get("track"))
        direction = str(payload.get("direction", "input")).lower()
        if direction not in ("input", "output"):
            raise ValueError("direction must be input or output")
        result = {"track": track.name, "direction": direction}
        route_type = payload.get("type")
        route_channel = payload.get("channel")
        if route_type is not None:
            setattr(track, "%s_routing_type" % direction, self._match_routing(getattr(track, "available_%s_routing_types" % direction), route_type))
            result["type"] = self._safe_get(track, "current_%s_routing" % direction)
        if route_channel is not None:
            setattr(track, "%s_routing_channel" % direction, self._match_routing(getattr(track, "available_%s_routing_channels" % direction), route_channel))
            result["channel"] = self._safe_get(track, "current_%s_sub_routing" % direction)
        return result

    def _match_routing(self, values, requested):
        normalized = self._normalize_name(requested)
        matches = [value for value in list(values) if normalized in self._normalize_name(self._routing_name(value))]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Ambiguous routing %r: %s" % (requested, [self._routing_name(value) for value in matches]))
        raise ValueError("No routing option named %r. Available: %s" % (requested, [self._routing_name(value) for value in list(values)]))

    def _routing_name(self, value):
        for name in ("display_name", "name", "identifier"):
            found = self._safe_get(value, name)
            if found:
                return found
        return str(value)

    def _status(self):
        song = self.song()
        return {
            "tempo": song.tempo,
            "is_playing": song.is_playing,
            "selected_track": song.view.selected_track.name,
            "track_count": len(song.tracks),
            "return_count": len(song.return_tracks),
            "tracks": [self._track_info(track, index) for index, track in enumerate(song.tracks)],
        }

    def _selected(self, include_devices):
        track = self.song().view.selected_track
        info = self._track_info(track, self._track_index(track), self._track_kind(track))
        if include_devices:
            info["devices"] = self._device_infos(track)
        return info

    def _set_track(self, payload):
        track = self._resolve_track(payload.get("track"))
        mixer = track.mixer_device
        changed = {}
        if "volume" in payload:
            self._set_parameter(mixer.volume, value=float(payload["volume"]))
            changed["volume"] = self._parameter_info(mixer.volume)
        if "pan" in payload:
            self._set_parameter(mixer.panning, value=float(payload["pan"]))
            changed["pan"] = self._parameter_info(mixer.panning)
        for name in ("mute", "solo", "arm"):
            if name in payload:
                try:
                    setattr(track, name, bool(payload[name]))
                    changed[name] = getattr(track, name)
                except Exception as error:
                    raise ValueError("Track %s does not support %s: %s" % (track.name, name, error))
        return {"track": track.name, "changed": changed}

    def _set_send(self, payload):
        track = self._resolve_track(payload.get("track"))
        send = payload.get("send")
        sends = list(track.mixer_device.sends)
        if isinstance(send, int):
            index = send
        else:
            normalized = self._normalize_name(str(send))
            index = None
            for candidate_index, parameter in enumerate(sends):
                if normalized in (self._normalize_name(parameter.name), str(candidate_index)):
                    index = candidate_index
                    break
            if index is None and len(str(send)) == 1:
                possible = ord(str(send).upper()) - ord("A")
                if 0 <= possible < len(sends):
                    index = possible
        if index is None or index < 0 or index >= len(sends):
            raise ValueError("Unknown send %r on track %s" % (send, track.name))
        parameter = sends[index]
        self._set_parameter(parameter, value=float(payload["value"]))
        return {"track": track.name, "send": index, "parameter": self._parameter_info(parameter)}

    def _set_param(self, payload):
        device = self._resolve_device_ref(payload)
        parameter = self._resolve_parameter(device, payload.get("param"))
        if "normalized" in payload:
            self._set_parameter(parameter, normalized=float(payload["normalized"]))
        elif "delta" in payload:
            self._set_parameter(parameter, value=parameter.value + float(payload["delta"]))
        elif "value" in payload:
            self._set_parameter(parameter, value=float(payload["value"]))
        else:
            raise ValueError("set_param requires value, normalized, or delta")
        return {
            "device": self._device_info(device, self._device_index(device)),
            "parameter": self._parameter_info(parameter),
        }

    def _set_parameter(self, parameter, value=None, normalized=None):
        if normalized is not None:
            normalized = max(0.0, min(1.0, normalized))
            value = parameter.min + (parameter.max - parameter.min) * normalized
        value = max(parameter.min, min(parameter.max, value))
        parameter.value = value
