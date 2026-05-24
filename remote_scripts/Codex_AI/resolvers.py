"""Resolver mixins for the Codex_AI Ableton bridge."""


class ResolverMixin(object):
    def _resolve_track(self, identifier):
        song = self.song()
        if identifier is None:
            return song.view.selected_track
        if isinstance(identifier, int):
            tracks = list(song.tracks)
            if 0 <= identifier < len(tracks):
                return tracks[identifier]
            raise ValueError("Track index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        if lowered == "selected":
            return song.view.selected_track
        if lowered == "master":
            return song.master_track
        if lowered.startswith("return:"):
            return self._resolve_return_track(text.split(":", 1)[1])
        for track in list(song.tracks) + list(song.return_tracks) + [song.master_track]:
            if track.name.lower() == lowered:
                return track
        normalized = self._normalize_name(text)
        matches = [
            track
            for track in list(song.tracks) + list(song.return_tracks) + [song.master_track]
            if normalized in self._normalize_name(track.name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Track %r is ambiguous: %s" % (identifier, [track.name for track in matches]))
        raise ValueError("Unknown track: %r" % (identifier,))

    def _resolve_return_track(self, identifier):
        returns = list(self.song().return_tracks)
        text = str(identifier).strip()
        if text.isdigit():
            index = int(text)
            if 0 <= index < len(returns):
                return returns[index]
        if len(text) == 1 and text.isalpha():
            index = ord(text.upper()) - ord("A")
            if 0 <= index < len(returns):
                return returns[index]
        lowered = text.lower()
        for track in returns:
            if track.name.lower() == lowered:
                return track
        raise ValueError("Unknown return track: %r" % identifier)

    def _resolve_device_ref(self, payload, prefix=""):
        info = self._resolve_device_ref_info(payload, prefix)
        return info["device"]

    def _resolve_device_ref_info(self, payload, prefix=""):
        device_path = self._prefixed(payload, prefix, "device_path", None)
        if device_path:
            device = self._resolve_lom_path(device_path)
            if not hasattr(device, "parameters") or not hasattr(device, "class_name"):
                raise ValueError("Path did not resolve to a device")
            container = self._device_container(device)
            return {"device": device, "container": container, "index": self._device_index(device, container)}

        track_identifier = self._prefixed(payload, prefix, "device_track", None)
        if track_identifier is None:
            track_identifier = self._prefixed(payload, prefix, "track")
        track = self._resolve_track(track_identifier)
        device = self._resolve_device(track, self._prefixed(payload, prefix, "device"))
        return {"device": device, "container": track, "index": self._device_index(device, track)}

    def _resolve_parameter_ref(self, payload):
        device = self._resolve_device_ref(payload)
        return self._resolve_parameter(device, payload.get("param"))

    def _resolve_container_ref(self, payload, prefix="target"):
        path = self._prefixed(payload, prefix, "path", None)
        if path:
            container = self._resolve_lom_path(path)
            self._ensure_device_container(container)
            return container
        track_identifier = self._prefixed(payload, prefix, "track", None)
        return self._resolve_track(track_identifier)

    def _ensure_device_container(self, container):
        if not hasattr(container, "devices"):
            raise ValueError("Target must be a Track or Rack Chain with devices")

    def _track_for_container(self, container):
        current = container
        while current is not None:
            if hasattr(current, "clip_slots") and hasattr(current, "mixer_device"):
                return current
            current = self._safe_get(current, "canonical_parent")
        raise ValueError("Could not resolve the owning track for target container")

    def _device_container(self, device):
        container = self._safe_get(device, "canonical_parent")
        self._ensure_device_container(container)
        return container

    def _device_index(self, device, container=None):
        if container is None:
            try:
                container = self._device_container(device)
            except Exception:
                return -1
        for index, candidate in enumerate(container.devices):
            if candidate == device:
                return index
        return -1

    def _device_at(self, container, index):
        devices = list(container.devices)
        if not devices:
            raise ValueError("Target has no devices")
        index = self._clamp_int(index, 0, len(devices) - 1)
        return devices[index]

    def _device_identity_set(self, container):
        return list(container.devices)

    def _new_or_last_device(self, container, before):
        devices = list(container.devices)
        for device in devices:
            if not any(device == candidate for candidate in before):
                return device
        if devices:
            return devices[-1]
        raise ValueError("Device was not added")

    def _container_device_infos(self, container):
        return [self._device_info(device, index) for index, device in enumerate(container.devices)]

    def _reorder_container_devices(self, container, ordered_devices):
        for index, device in enumerate(ordered_devices):
            if self._device_index(device, container) != index:
                self.song().move_device(device, container, index)

    def _container_info(self, container):
        info = {"type": type(container).__name__, "device_count": len(container.devices)}
        name = self._safe_get(container, "name")
        if name is not None:
            info["name"] = name
        if hasattr(container, "clip_slots") and hasattr(container, "mixer_device"):
            info["kind"] = "track"
            info["track_index"] = self._track_index(container)
            info["path"] = self._track_path(container)
        else:
            info["kind"] = "chain"
            info["path"] = self._chain_path(container)
        return info

    def _track_path(self, track):
        kind = self._track_kind(track)
        if kind == "master":
            return "song.master_track"
        if kind == "return":
            return "song.return_tracks[%s]" % self._track_index(track)
        return "song.tracks[%s]" % self._track_index(track)

    def _chain_path(self, chain):
        path = self._path_for_object(chain)
        return path or ""

    def _path_for_object(self, target):
        for track in list(self.song().tracks) + list(self.song().return_tracks) + [self.song().master_track]:
            track_path = self._track_path(track)
            if target == track:
                return track_path
            found = self._path_for_object_in_devices(target, list(track.devices), track_path)
            if found:
                return found
        return None

    def _path_for_object_in_devices(self, target, devices, parent_path):
        for index, device in enumerate(devices):
            device_path = "%s.devices[%s]" % (parent_path, index)
            if target == device:
                return device_path
            for chain_attr in ("chains", "return_chains"):
                chains = self._safe_get(device, chain_attr)
                if not self._is_indexable_vector(chains):
                    continue
                for chain_index, chain in enumerate(chains):
                    chain_path = "%s.%s[%s]" % (device_path, chain_attr, chain_index)
                    if target == chain:
                        return chain_path
                    found = self._path_for_object_in_devices(target, list(chain.devices), chain_path)
                    if found:
                        return found
        return None

    def _device_tree_devices(self, container, parent_path, depth):
        devices = []
        for index, device in enumerate(container.devices):
            path = "%s.devices[%s]" % (parent_path, index)
            info = self._device_info(device, index)
            info["path"] = path
            if depth > 0:
                chains = self._device_tree_chains(device, path, depth - 1)
                if chains:
                    info["chains"] = chains
            devices.append(info)
        return devices

    def _device_tree_chains(self, device, device_path, depth):
        chains = []
        for chain_attr in ("chains", "return_chains"):
            chain_values = self._safe_get(device, chain_attr)
            if not self._is_indexable_vector(chain_values):
                continue
            for index, chain in enumerate(chain_values):
                path = "%s.%s[%s]" % (device_path, chain_attr, index)
                chains.append({
                    "kind": chain_attr,
                    "index": index,
                    "name": self._safe_get(chain, "name"),
                    "path": path,
                    "devices": self._device_tree_devices(chain, path, depth) if depth > 0 else [],
                })
        return chains

    def _resolve_device(self, track, identifier):
        devices = list(track.devices)
        if isinstance(identifier, int):
            if 0 <= identifier < len(devices):
                return devices[identifier]
            raise ValueError("Device index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        for device in devices:
            if device.name.lower() == lowered or device.class_name.lower() == lowered:
                return device
        normalized = self._normalize_name(text)
        matches = [
            device
            for device in devices
            if normalized in self._normalize_name(device.name)
            or normalized in self._normalize_name(device.class_name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Device %r is ambiguous: %s" % (identifier, [device.name for device in matches]))
        raise ValueError("Unknown device %r on track %s" % (identifier, track.name))

    def _resolve_parameter(self, device, identifier):
        parameters = list(device.parameters)
        if isinstance(identifier, int):
            if 0 <= identifier < len(parameters):
                return parameters[identifier]
            raise ValueError("Parameter index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        for parameter in parameters:
            if parameter.name.lower() == lowered:
                return parameter
        normalized = self._normalize_name(text)
        matches = [
            parameter
            for parameter in parameters
            if normalized in self._normalize_name(parameter.name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Parameter %r is ambiguous: %s" % (identifier, [parameter.name for parameter in matches]))
        raise ValueError("Unknown parameter %r on device %s" % (identifier, device.name))
