"""LomResolver mixins for the Codex_AI Ableton bridge."""

import re


class LomResolverMixin(object):
    def _resolve_lom_path(self, path):
        if path is None or path == "" or path == "song":
            return self.song()
        if isinstance(path, list):
            parts = path
        else:
            text = str(path).strip()
            if text in ("song", "live_set"):
                return self.song()
            if text == "application":
                return self.application()
            parts = text.split(".")

        if not parts:
            return self.song()

        first = parts[0]
        if first in ("song", "live_set"):
            obj = self.song()
            parts = parts[1:]
        elif first == "application":
            obj = self.application()
            parts = parts[1:]
        else:
            obj = self.song()

        for part in parts:
            obj = self._resolve_lom_part(obj, part)
        return obj

    def _resolve_lom_part(self, obj, part):
        if isinstance(part, dict):
            obj = getattr(obj, part["attr"]) if "attr" in part else obj
            if "index" in part:
                obj = obj[int(part["index"])]
            return obj
        text = str(part)
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(.+)\])?$", text)
        if not match:
            raise ValueError("Invalid LOM path segment: %r" % text)
        attr, index = match.groups()
        obj = getattr(obj, attr)
        if index is None:
            return obj
        key = index.strip().strip("\"'")
        if key == "selected":
            return self.song().view.selected_track
        try:
            return obj[int(key)]
        except ValueError:
            normalized = self._normalize_name(key)
            matches = [item for item in obj if normalized in self._normalize_name(getattr(item, "name", ""))]
            if len(matches) == 1:
                return matches[0]
            if matches:
                raise ValueError("Ambiguous collection lookup %r: %s" % (key, [getattr(item, "name", "") for item in matches]))
            raise ValueError("No collection item named %r" % key)

    def _split_lom_attribute(self, path):
        if not path:
            raise ValueError("path is required")
        if isinstance(path, list):
            return path[:-1], path[-1]
        text = str(path)
        if "." not in text:
            raise ValueError("set path must include an attribute, e.g. song.tempo")
        target, attribute = text.rsplit(".", 1)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", attribute):
            raise ValueError("Invalid set attribute: %r" % attribute)
        return target, attribute

    def _coerce_like(self, value, current):
        if isinstance(current, bool):
            return bool(value)
        if isinstance(current, int) and not isinstance(current, bool):
            return int(value)
        if isinstance(current, float):
            return float(value)
        return value
