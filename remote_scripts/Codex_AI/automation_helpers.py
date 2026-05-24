"""AutomationHelper mixins for the Codex_AI Ableton bridge."""


class AutomationHelperMixin(object):
    def _automation_envelope(self, clip, parameter, create):
        envelope = None
        try:
            envelope = clip.automation_envelope(parameter)
        except Exception:
            envelope = None
        if envelope is None and create:
            envelope = self._create_automation_envelope(clip, parameter)
        return envelope

    def _create_automation_envelope(self, clip, parameter):
        for _ in range(2):
            try:
                envelope = clip.create_automation_envelope(parameter)
            except Exception:
                envelope = None
            if envelope is not None:
                return envelope
            try:
                envelope = clip.automation_envelope(parameter)
            except Exception:
                envelope = None
            if envelope is not None:
                return envelope
            self._show_clip_envelope(clip, parameter)
        return None

    def _clear_parameter_envelope(self, clip, parameter):
        try:
            clip.clear_envelope(parameter)
        except Exception:
            envelope = self._automation_envelope(clip, parameter, False)
            if envelope is not None:
                self._clear_automation_envelope_steps(envelope)

    def _clear_automation_envelope_steps(self, envelope):
        method = getattr(envelope, "delete_events_in_range", None)
        if callable(method):
            method(0.0, 1576800.0)
            return
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

    def _insert_automation_event(self, envelope, time_value, value, coefficients):
        method = getattr(envelope, "create_event", None)
        if not callable(method):
            raise ValueError("Automation envelope does not support create_event")
        module = self._live_envelope_module()
        event = module.EnvelopeEvent(time=float(time_value), value=float(value))
        if coefficients is not None:
            event.control_coefficients = module.EnvelopeEventControlCoefficients(**coefficients)
        method(event)
        if coefficients is not None:
            self._set_stored_automation_event_coefficients(envelope, time_value, value, coefficients)

    def _set_stored_automation_event_coefficients(self, envelope, time_value, value, coefficients):
        events_in_range = getattr(envelope, "events_in_range", None)
        if not callable(events_in_range):
            return
        events = list(events_in_range(float(time_value) - 0.0001, float(time_value) + 0.0001))
        if not events:
            return
        event = min(events, key=lambda item: abs(float(self._safe_get(item, "time", time_value)) - float(time_value)))
        try:
            event.value = float(value)
        except Exception:
            pass
        event.control_coefficients = self._live_envelope_module().EnvelopeEventControlCoefficients(**coefficients)
        create_event = getattr(envelope, "create_event", None)
        if callable(create_event):
            create_event(event)

    def _automation_value_at_time(self, envelope, time_value):
        method = getattr(envelope, "value_at_time", None)
        if not callable(method):
            return None
        return method(float(time_value))

    def _automation_steps_from_payload(self, payload):
        steps = payload.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("steps must be a list")
        normalized = []
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Each automation step must be an object")
            time_value = float(step.get("time", step.get("start", 0.0)))
            duration = float(step.get("duration", step.get("length", 0.0)))
            if duration <= 0.0:
                raise ValueError("Automation step duration must be greater than 0")
            normalized.append((step, time_value, duration))
        return normalized

    def _automation_events_from_payload(self, payload):
        events = payload.get("events")
        if events is None:
            return None
        if not isinstance(events, list) or not events:
            raise ValueError("events must be a non-empty list")
        normalized = []
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("Each automation event must be an object")
            if "time" not in event:
                raise ValueError("Automation event needs time")
            normalized.append((event, float(event["time"])))
        return normalized

    def _insert_automation_steps(self, envelope, parameter, steps):
        inserted = []
        for step, time_value, duration in steps:
            value = self._automation_step_value(parameter, step)
            self._insert_automation_step(envelope, time_value, duration, value)
            inserted.append({"time": time_value, "duration": duration, "value": value})
        return inserted

    def _insert_automation_events(self, envelope, parameter, events):
        inserted = []
        for event, time_value in events:
            value = self._automation_step_value(parameter, event)
            coefficients = self._automation_event_coefficients(event)
            self._insert_automation_event(envelope, time_value, value, coefficients)
            item = {"time": time_value, "value": value}
            if coefficients is not None:
                item["control_coefficients"] = coefficients
            inserted.append(item)
        return inserted

    def _automation_event_coefficients(self, event):
        coefficients = event.get("curve_coefficients")
        if coefficients is None:
            coefficients = event.get("control_coefficients")
        if coefficients is None:
            return None
        if not isinstance(coefficients, dict):
            raise ValueError("Automation event curve_coefficients must be an object")
        return {key: float(coefficients[key]) for key in ("x1", "y1", "x2", "y2")}

    def _automation_events_info(self, envelope, start, end):
        method = getattr(envelope, "events_in_range", None)
        if not callable(method):
            return []
        return [self._automation_event_info(event) for event in method(float(start), float(end))]

    def _automation_event_info(self, event):
        info = {
            "time": self._safe_get(event, "time"),
            "value": self._safe_get(event, "value"),
        }
        coefficients = self._safe_get(event, "control_coefficients")
        if coefficients is not None:
            info["control_coefficients"] = {
                "x1": self._safe_get(coefficients, "x1"),
                "y1": self._safe_get(coefficients, "y1"),
                "x2": self._safe_get(coefficients, "x2"),
                "y2": self._safe_get(coefficients, "y2"),
            }
        return info

    def _live_envelope_module(self):
        import Live
        return Live.Envelope

    def _automation_envelope_info(self, envelope):
        if envelope is None:
            return None
        return {
            "type": type(envelope).__name__,
            "parameter": self._parameter_info(self._safe_get(envelope, "parameter")) if self._safe_get(envelope, "parameter") is not None else None,
            "points": self._serialize(self._safe_get(envelope, "points")),
            "step_count": self._safe_get(envelope, "step_count"),
        }
