"""AutomationCommand mixins for the Codex_AI Ableton bridge."""


class AutomationCommandMixin(object):
    def _clip_automation_get(self, payload):
        clip = self._resolve_clip(payload)
        parameter = self._resolve_parameter_ref(payload)
        envelope = self._automation_envelope(clip, parameter, False)
        times = payload.get("times", [])
        values = []
        if envelope is not None:
            for time_value in times:
                values.append({"time": float(time_value), "value": self._automation_value_at_time(envelope, float(time_value))})
        return {
            "clip": self._clip_info(clip),
            "parameter": self._parameter_info(parameter),
            "has_envelope": envelope is not None,
            "envelope": self._automation_envelope_info(envelope),
            "values": values,
        }

    def _clip_automation_set(self, payload):
        clip = self._resolve_clip(payload)
        parameter = self._resolve_parameter_ref(payload)
        steps = payload.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("steps must be a list")
        if payload.get("clear", False):
            self._clear_parameter_envelope(clip, parameter)
        envelope = self._automation_envelope(clip, parameter, True)
        inserted = []
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Each automation step must be an object")
            time_value = float(step.get("time", step.get("start", 0.0)))
            duration = float(step.get("duration", step.get("length", 0.0)))
            if duration <= 0.0:
                raise ValueError("Automation step duration must be greater than 0")
            value = self._automation_step_value(parameter, step)
            self._insert_automation_step(envelope, time_value, duration, value)
            inserted.append({"time": time_value, "duration": duration, "value": value})
        return {
            "clip": self._clip_info(clip),
            "parameter": self._parameter_info(parameter),
            "inserted": inserted,
            "envelope": self._automation_envelope_info(envelope),
            "values": [{"time": item["time"], "value": self._automation_value_at_time(envelope, item["time"])} for item in inserted],
            "done": True,
        }

    def _clip_automation_clear(self, payload):
        clip = self._resolve_clip(payload)
        if payload.get("all", False):
            clip.clear_all_envelopes()
            return {"clip": self._clip_info(clip), "cleared": "all", "done": True}
        parameter = self._resolve_parameter_ref(payload)
        self._clear_parameter_envelope(clip, parameter)
        return {"clip": self._clip_info(clip), "parameter": self._parameter_info(parameter), "cleared": "parameter", "done": True}
