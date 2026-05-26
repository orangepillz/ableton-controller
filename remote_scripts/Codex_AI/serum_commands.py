"""Serum plug-in command mixins for the Codex_AI Ableton bridge."""


class SerumCommandMixin(object):
    def _serum_add(self, payload):
        container = self._resolve_container_ref(payload, "target")
        self._ensure_serum_target(container)
        item = self._resolve_serum_plugin_item(payload)
        return self._load_device_item_to_container(container, item, payload.get("target_index", None))

    def _serum_params(self, payload):
        device = self._resolve_serum_device(payload)
        return {"device": self._device_info(device, self._device_index(device)), "parameters": self._parameter_infos(device)}

    def _serum_names(self, payload):
        device = self._resolve_serum_device(payload)
        get_names = getattr(device, "get_parameter_names", None)
        if not callable(get_names):
            raise ValueError("Serum device does not expose get_parameter_names")
        start = max(0, int(payload.get("start", 0)))
        end = int(payload.get("end", -1))
        names = list(get_names(start, end))
        return {
            "device": self._device_info(device, self._device_index(device)),
            "start": start,
            "end": end,
            "length": len(names),
            "names": names,
        }

    def _serum_set_param(self, payload):
        device = self._resolve_serum_device(payload)
        parameter = self._apply_serum_control(device, payload)
        return {
            "device": self._device_info(device, self._device_index(device)),
            "parameter": self._parameter_info(parameter),
        }

    def _serum_set_many(self, payload):
        device = self._resolve_serum_device(payload)
        controls = payload.get("controls", [])
        if not isinstance(controls, list):
            raise ValueError("controls must be a list")
        parameters = [self._parameter_info(self._apply_serum_control(device, control)) for control in controls]
        return {
            "device": self._device_info(device, self._device_index(device)),
            "parameters": parameters,
            "done": True,
        }

    def _ensure_serum_target(self, container):
        track = self._track_for_container(container)
        if self._safe_get(track, "has_midi_input", True) is False:
            raise ValueError("Serum must be added to a MIDI track or one of its rack chains")

    def _resolve_serum_plugin_item(self, payload):
        plugin_format = str(payload.get("format", "vst")).lower()
        path = payload.get("path")
        if path:
            item = self._resolve_browser_item(path)
            self._validate_serum_plugin_item(item, path, plugin_format)
            return item

        name = payload.get("name") or "Serum"
        root = self.application().browser.plugins
        matches = []
        self._find_serum_plugin_items(root, "plugins", name, plugin_format, matches, 0, 8, 8000)
        if not matches:
            raise ValueError("No Serum %s plug-in found in the Live Plugins browser" % plugin_format.upper())

        ranked = sorted(matches, key=lambda match: self._serum_plugin_rank(match, name, plugin_format))
        best_rank = self._serum_plugin_rank(ranked[0], name, plugin_format)
        tied = [match for match in ranked if self._serum_plugin_rank(match, name, plugin_format) == best_rank]
        if len(tied) > 1:
            raise ValueError("Ambiguous Serum plug-in: %s" % [match["path"] for match in tied[:12]])
        return ranked[0]["item"]

    def _validate_serum_plugin_item(self, item, path, plugin_format):
        if not self._safe_get(item, "is_loadable", False):
            raise ValueError("Serum browser item is not loadable: %s" % path)
        haystack = self._serum_item_haystack(item, path)
        if "serum" not in self._normalize_name(haystack):
            raise ValueError("Browser item does not look like Serum: %s" % path)
        if not self._serum_format_matches(item, path, plugin_format):
            raise ValueError("Browser item does not match requested Serum plug-in format %s: %s" % (plugin_format, path))

    def _find_serum_plugin_items(self, item, path, name, plugin_format, matches, depth, max_depth, max_items):
        if max_items <= 0 or depth > max_depth:
            return max_items
        max_items -= 1
        haystack = self._serum_item_haystack(item, path)
        normalized_name = self._normalize_name(name)
        if (
            normalized_name in self._normalize_name(haystack)
            and self._safe_get(item, "is_loadable", False)
            and self._serum_format_matches(item, path, plugin_format)
        ):
            matches.append({"item": item, "path": path})
        for child in self._browser_item_children(item):
            if max_items <= 0:
                break
            child_path = self._browser_child_path(path, child)
            max_items = self._find_serum_plugin_items(child, child_path, name, plugin_format, matches, depth + 1, max_depth, max_items)
        return max_items

    def _serum_plugin_rank(self, match, name, plugin_format):
        item = match["item"]
        path = match["path"]
        item_name = self._normalize_name(self._safe_get(item, "name", ""))
        query = self._normalize_name(name)
        exact_rank = 0 if item_name == query else 1
        format_rank = self._serum_format_rank(item, path, plugin_format)
        return (exact_rank, format_rank, len(path))

    def _serum_format_rank(self, item, path, plugin_format):
        normalized = self._normalize_name(self._serum_item_haystack(item, path))
        if plugin_format == "vst":
            if "vst3" in normalized:
                return 0
            if "vst2" in normalized:
                return 1
            return 2
        if plugin_format == "vst3":
            return 0 if "vst3" in normalized else 1
        if plugin_format == "vst2":
            return 0 if "vst2" in normalized else 1
        if plugin_format == "au":
            return 0 if "audiounit" in normalized or "au" in normalized else 1
        return 0

    def _serum_format_matches(self, item, path, plugin_format):
        normalized = self._normalize_name(self._serum_item_haystack(item, path))
        if plugin_format == "any":
            return True
        if plugin_format == "vst":
            return "vst" in normalized
        if plugin_format == "vst3":
            return "vst3" in normalized
        if plugin_format == "vst2":
            return "vst2" in normalized or ("vst" in normalized and "vst3" not in normalized)
        if plugin_format == "au":
            return "audiounit" in normalized or "au" in normalized
        raise ValueError("Unknown Serum plug-in format: %r" % plugin_format)

    def _serum_item_haystack(self, item, path):
        return "%s %s %s %s" % (
            self._safe_get(item, "name", ""),
            self._safe_get(item, "source", ""),
            self._safe_get(item, "uri", ""),
            path,
        )

    def _resolve_serum_device(self, payload):
        device_path = payload.get("device_path")
        if device_path:
            device = self._resolve_lom_path(device_path)
            self._ensure_serum_device(device)
            return device

        track = self._resolve_track(payload.get("track"))
        if payload.get("device") is not None:
            device = self._resolve_device(track, payload.get("device"))
            self._ensure_serum_device(device)
            return device

        devices = [device for device in track.devices if self._is_serum_device(device)]
        if "instance" in payload:
            index = int(payload.get("instance"))
            if 0 <= index < len(devices):
                return devices[index]
            raise ValueError("Serum instance index out of range on track %s: %s" % (track.name, index))
        if len(devices) == 1:
            return devices[0]
        if devices:
            raise ValueError("Multiple Serum instances on track %s; use --instance, --device, or --device-path" % track.name)
        raise ValueError("No Serum instance found on track %s" % track.name)

    def _ensure_serum_device(self, device):
        if not hasattr(device, "parameters") or not hasattr(device, "class_name"):
            raise ValueError("Path did not resolve to a device")
        if not self._is_serum_device(device):
            raise ValueError("Device is not a Serum instance: %s" % self._safe_get(device, "name", ""))

    def _is_serum_device(self, device):
        return "serum" in self._normalize_name(
            "%s %s %s" % (
                self._safe_get(device, "name", ""),
                self._safe_get(device, "class_name", ""),
                self._safe_get(device, "original_name", ""),
            )
        )

    def _apply_serum_control(self, device, control):
        if "param" not in control:
            raise ValueError("Serum control needs param")
        parameter = self._resolve_parameter(device, control.get("param"))
        if "normalized" in control:
            self._set_parameter(parameter, normalized=float(control["normalized"]))
        elif "delta" in control:
            self._set_parameter(parameter, value=parameter.value + float(control["delta"]))
        elif "value" in control:
            self._set_parameter(parameter, value=float(control["value"]))
        else:
            raise ValueError("Serum control requires value, normalized, or delta")
        return parameter
