"""AutomationHelper mixins for the Codex_AI Ableton bridge."""


class AutomationHelperMixin(object):
    def _automation_envelope(self, clip, parameter, create):
        envelope = None
        try:
            envelope = clip.automation_envelope(parameter)
        except Exception:
            envelope = None
        if envelope is None and create:
            envelope = clip.create_automation_envelope(parameter)
        return envelope

    def _clear_parameter_envelope(self, clip, parameter):
        try:
            clip.clear_envelope(parameter)
        except Exception:
            envelope = self._automation_envelope(clip, parameter, False)
            if envelope is not None:
                self._clear_automation_envelope_steps(envelope)

    def _clear_automation_envelope_steps(self, envelope):
        for name in ("clear_all_steps", "clear"):
            method = getattr(envelope, name, None)
            if callable(method):
                method()
                return
        length = 1576800.0
        method = getattr(envelope, "clear_steps", None)
        if callable(method):
            method(0.0, length)
            return
        raise ValueError("Automation envelope cannot be cleared by this Live API")

    def _automation_step_value(self, parameter, step):
        if "normalized" in step:
            normalized = self._clamp_float(float(step["normalized"]), 0.0, 1.0)
            return float(parameter.min) + (float(parameter.max) - float(parameter.min)) * normalized
        if "value" not in step:
            raise ValueError("Automation step needs value or normalized")
        return self._clamp_float(float(step["value"]), float(parameter.min), float(parameter.max))

    def _insert_automation_step(self, envelope, time_value, duration, value):
        method = getattr(envelope, "insert_step", None)
        if not callable(method):
            raise ValueError("Automation envelope does not support insert_step")
        method(float(time_value), float(duration), float(value))

    def _automation_value_at_time(self, envelope, time_value):
        method = getattr(envelope, "value_at_time", None)
        if not callable(method):
            return None
        return method(float(time_value))

    def _automation_envelope_info(self, envelope):
        if envelope is None:
            return None
        return {
            "type": type(envelope).__name__,
            "points": self._serialize(self._safe_get(envelope, "points")),
            "step_count": self._safe_get(envelope, "step_count"),
        }
