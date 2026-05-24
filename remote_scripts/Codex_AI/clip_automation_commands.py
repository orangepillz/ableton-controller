"""Clip automation command mixins for the Codex_AI Ableton bridge."""


class ClipAutomationCommandMixin(object):
    def _focus_clip_for_automation(self, clip):
        if not self._safe_get(clip, "is_arrangement_clip", False):
            return
        try:
            self.song().view.selected_track = clip.canonical_parent
            self.song().view.detail_clip = clip
            self.application().view.show_view("Detail")
            self.application().view.show_view("Detail/Clip")
        except Exception:
            pass

    def _show_clip_envelope(self, clip, parameter):
        view = self._safe_get(clip, "view")
        if view is None:
            return
        for method_name in ("show_envelope", "show_envelope_for_parameter", "select_envelope"):
            method = getattr(view, method_name, None)
            if callable(method):
                try:
                    method(parameter)
                except TypeError:
                    try:
                        method()
                    except Exception:
                        pass
                except Exception:
                    pass
                return

    def _clip_automation_get(self, payload):
        clip = self._resolve_clip(payload)
        self._focus_clip_for_automation(clip)
        parameter = self._resolve_parameter_ref(payload)
        self._show_clip_envelope(clip, parameter)
        envelope = self._automation_envelope(clip, parameter, False)
        values = []
        if envelope is not None:
            for time_value in payload.get("times", []):
                values.append({"time": float(time_value), "value": self._automation_value_at_time(envelope, float(time_value))})
        return {
            "clip": self._clip_info(clip),
            "parameter": self._parameter_info(parameter),
            "has_envelope": envelope is not None,
            "envelope": self._automation_envelope_info(envelope),
            "events": self._automation_events_info(envelope, 0.0, self._safe_get(clip, "length", 1576800.0)) if envelope is not None else [],
            "values": values,
        }

    def _clip_automation_set(self, payload):
        clip = self._resolve_clip(payload)
        self._focus_clip_for_automation(clip)
        parameter = self._resolve_parameter_ref(payload)
        self._show_clip_envelope(clip, parameter)
        events = self._automation_events_from_payload(payload)
        steps = None if events is not None else self._automation_steps_from_payload(payload)
        if payload.get("clear", False):
            self._clear_parameter_envelope(clip, parameter)
        envelope = self._automation_envelope(clip, parameter, True)
        inserted = (
            self._insert_automation_events(envelope, parameter, events)
            if events is not None
            else self._insert_automation_steps(envelope, parameter, steps)
        )
        return {
            "clip": self._clip_info(clip),
            "parameter": self._parameter_info(parameter),
            "inserted": inserted,
            "write_mode": "events" if events is not None else "steps",
            "envelope": self._automation_envelope_info(envelope),
            "values": [{"time": item["time"], "value": self._automation_value_at_time(envelope, item["time"])} for item in inserted],
            "done": True,
        }

    def _clip_automation_set_many(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        self._focus_clip_for_automation(clip)
        lanes = payload.get("lanes", [])
        if not isinstance(lanes, list):
            raise ValueError("clip_automation_set_many lanes must be a list")
        items = [self._clip_lane_item(lane, clip, payload) for lane in lanes]
        self._ensure_clip_lane_items(items)
        for item in items:
            self._show_clip_envelope(clip, item["parameter"])
        results = []
        for item in items:
            envelope = self._write_clip_envelope(clip, item)
            inserted = (
                self._insert_automation_events(envelope, item["parameter"], item["events"])
                if item["events"] is not None
                else self._insert_automation_steps(envelope, item["parameter"], item["steps"])
            )
            results.append(self._clip_automation_lane_result(clip, item, inserted, envelope))
        return {"location": self._clip_ref_info(ref), "clip": self._clip_info(clip), "lanes": results, "done": True}

    def _clip_automation_clear(self, payload):
        clip = self._resolve_clip(payload)
        self._focus_clip_for_automation(clip)
        if payload.get("all", False):
            clip.clear_all_envelopes()
            return {"clip": self._clip_info(clip), "cleared": "all", "done": True}
        parameter = self._resolve_parameter_ref(payload)
        self._show_clip_envelope(clip, parameter)
        self._clear_parameter_envelope(clip, parameter)
        return {"clip": self._clip_info(clip), "parameter": self._parameter_info(parameter), "cleared": "parameter", "done": True}

    def _clip_lane_item(self, payload, clip, defaults=None):
        lane_payload = dict(defaults or {})
        lane_payload.update(payload)
        parameter = self._resolve_parameter_ref(lane_payload)
        events = self._automation_events_from_payload(lane_payload)
        steps = None if events is not None else self._automation_steps_from_payload(lane_payload)
        if events is not None:
            self._validate_clip_event_range(clip, events)
        else:
            self._validate_clip_step_range(clip, steps)
        return {
            "parameter": parameter,
            "steps": steps,
            "events": events,
            "clear": bool(lane_payload.get("clear", False)),
            "envelope": self._automation_envelope(clip, parameter, False),
        }

    def _ensure_clip_lane_items(self, items):
        if not items:
            raise ValueError("clip_automation_set_many needs at least one lane")
        seen = []
        for item in items:
            parameter = item["parameter"]
            if any(parameter == existing for existing in seen):
                raise ValueError("clip_automation_set_many received duplicate parameter lanes")
            seen.append(parameter)

    def _write_clip_envelope(self, clip, item):
        envelope = item["envelope"]
        if item["clear"]:
            self._clear_parameter_envelope(clip, item["parameter"])
            envelope = None
        if envelope is None:
            envelope = self._automation_envelope(clip, item["parameter"], True)
        if envelope is None:
            name = self._safe_get(item["parameter"], "name", "parameter")
            raise ValueError("Could not create clip automation envelope for %s" % name)
        return envelope

    def _validate_clip_step_range(self, clip, steps):
        clip_length = float(self._safe_get(clip, "length", 0.0))
        for _step, time_value, duration in steps:
            if time_value < 0.0 or time_value + duration > clip_length + 0.0001:
                raise ValueError("Clip automation steps must stay within the clip length")

    def _validate_clip_event_range(self, clip, events):
        clip_length = float(self._safe_get(clip, "length", 0.0))
        for _event, time_value in events:
            if time_value < 0.0 or time_value > clip_length + 0.0001:
                raise ValueError("Clip automation events must stay within the clip length")

    def _clip_automation_lane_result(self, clip, item, inserted, envelope):
        result = {
            "parameter": self._parameter_info(item["parameter"]),
            "inserted": inserted,
            "write_mode": "events" if item["events"] is not None else "steps",
            "envelope": self._automation_envelope_info(envelope),
            "values": [{"time": entry["time"], "value": self._automation_value_at_time(envelope, entry["time"])} for entry in inserted],
        }
        if envelope is not None:
            result["events"] = self._automation_events_info(envelope, 0.0, float(self._safe_get(clip, "length", 1576800.0)))
        return result
