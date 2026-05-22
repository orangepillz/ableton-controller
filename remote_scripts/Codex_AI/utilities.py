"""Utility mixins for the Codex_AI Ableton bridge."""


class UtilityMixin(object):
    def _clamp_int(self, value, minimum, maximum):
        return max(minimum, min(maximum, int(value)))

    def _clamp_float(self, value, minimum, maximum):
        return max(minimum, min(maximum, float(value)))

    def _normalize_name(self, value):
        return "".join(character.lower() for character in str(value) if character.isalnum())

    def _safe_get(self, obj, name, default=None):
        try:
            return getattr(obj, name)
        except Exception:
            return default

    def _is_indexable_vector(self, value):
        if isinstance(value, (bytes, str)):
            return False
        return hasattr(value, "__len__") and hasattr(value, "__getitem__")
