"""AutomationCommand mixins for the Codex_AI Ableton bridge."""


class AutomationCommandMixin(object):
    def _arrangement_automation_get(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        if not self._safe_get(clip, "is_arrangement_clip", False):
            raise ValueError("arrangement_automation_get needs an Arrangement clip reference")
        self._focus_clip_for_automation(clip)
        parameter = self._resolve_parameter_ref(payload)
        self._show_clip_envelope(clip, parameter)
        envelope = self._automation_envelope(clip, parameter, False)
        times = payload.get("times", [])
        values = self._arrangement_automation_values(envelope, times)
        return {
            "location": self._clip_ref_info(ref),
            "clip": self._clip_info(clip),
            "parameter": self._parameter_info(parameter),
            "has_envelope": envelope is not None,
            "has_automation": envelope is not None or self._parameter_is_automated(parameter),
            "envelope": self._automation_envelope_info(envelope),
            "events": self._automation_events_info(envelope, 0.0, self._safe_get(clip, "length", 1576800.0)) if envelope is not None else [],
            "read_source": "envelope" if envelope is not None else None,
            "values": values,
        }

    def _arrangement_automation_set(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        if not self._safe_get(clip, "is_arrangement_clip", False):
            raise ValueError("arrangement_automation_set needs an Arrangement clip reference")
        self._focus_clip_for_automation(clip)
        item = self._arrangement_lane_item(payload, clip)
        self._show_clip_envelope(clip, item["parameter"])
        envelope = item["envelope"]
        if envelope is not None:
            inserted = self._write_existing_arrangement_envelope(envelope, item)
            return self._arrangement_automation_result(ref, ref["clip"], item, inserted, envelope, False)
        return self._materialize_arrangement_automation(ref, item)

    def _arrangement_automation_set_many(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        if not self._safe_get(clip, "is_arrangement_clip", False):
            raise ValueError("arrangement_automation_set_many needs an Arrangement clip reference")
        self._focus_clip_for_automation(clip)
        lanes = payload.get("lanes", [])
        if not isinstance(lanes, list):
            raise ValueError("arrangement_automation_set_many lanes must be a list")
        items = [self._arrangement_lane_item(lane, clip, payload) for lane in lanes]
        self._ensure_arrangement_lane_items(items)
        for item in items:
            self._show_clip_envelope(clip, item["parameter"])
        if all(item["envelope"] is not None for item in items):
            results = []
            for item in items:
                inserted = self._write_existing_arrangement_envelope(item["envelope"], item)
                results.append(self._arrangement_automation_lane_result(item, inserted, item["envelope"]))
            return self._arrangement_automation_many_result(ref, clip, results, False)
        return self._materialize_arrangement_automation_lanes(ref, items)

    def _arrangement_lane_item(self, payload, clip, defaults=None):
        lane_payload = dict(defaults or {})
        lane_payload.update(payload)
        parameter = self._resolve_parameter_ref(lane_payload)
        events = self._automation_events_from_payload(lane_payload)
        steps = None if events is not None else self._automation_steps_from_payload(lane_payload)
        if events is not None:
            self._validate_arrangement_event_range(clip, events)
        else:
            self._validate_arrangement_step_range(clip, steps)
        return {
            "parameter": parameter,
            "steps": steps,
            "events": events,
            "clear": bool(lane_payload.get("clear", False)),
            "envelope": self._automation_envelope(clip, parameter, False),
        }

    def _ensure_arrangement_lane_items(self, items):
        if not items:
            raise ValueError("arrangement_automation_set_many needs at least one lane")
        seen = []
        for item in items:
            parameter = item["parameter"]
            if any(parameter == existing for existing in seen):
                raise ValueError("arrangement_automation_set_many received duplicate parameter lanes")
            seen.append(parameter)

    def _write_existing_arrangement_envelope(self, envelope, item):
        if item["clear"]:
            self._clear_automation_envelope_steps(envelope)
        if item["events"] is not None:
            return self._insert_automation_events(envelope, item["parameter"], item["events"])
        return self._insert_automation_steps(envelope, item["parameter"], item["steps"])

    def _validate_arrangement_step_range(self, clip, steps):
        clip_length = float(self._safe_get(clip, "length", 0.0))
        for _step, time_value, duration in steps:
            if time_value < 0.0 or time_value + duration > clip_length + 0.0001:
                raise ValueError("Arrangement automation steps must stay within the clip length")

    def _validate_arrangement_event_range(self, clip, events):
        clip_length = float(self._safe_get(clip, "length", 0.0))
        for _event, time_value in events:
            if time_value < 0.0 or time_value > clip_length + 0.0001:
                raise ValueError("Arrangement automation events must stay within the clip length")

    def _arrangement_automation_result(self, ref, clip, item, inserted, envelope, materialized):
        return {"location": self._clip_ref_info(ref), "clip": self._clip_info(clip), **self._arrangement_automation_lane_result(item, inserted, envelope), "materialized_from_session_clip": materialized, "done": True}

    def _arrangement_automation_lane_result(self, item, inserted, envelope):
        result = {
            "parameter": self._parameter_info(item["parameter"]),
            "inserted": inserted,
            "write_mode": "events" if item["events"] is not None else "steps",
            "envelope": self._automation_envelope_info(envelope),
            "values": [{"time": item["time"], "value": self._automation_value_at_time(envelope, item["time"])} for item in inserted],
        }
        if envelope is not None:
            result["events"] = self._automation_events_info(envelope, 0.0, 1576800.0)
        return result

    def _arrangement_automation_many_result(self, ref, clip, lane_results, materialized):
        return {"location": self._clip_ref_info(ref), "clip": self._clip_info(clip), "lanes": lane_results, "materialized_from_session_clip": materialized, "done": True}

    def _arrangement_automation_values(self, envelope, times):
        if not times:
            return []
        if envelope is not None:
            return [
                {"time": float(time_value), "value": self._automation_value_at_time(envelope, float(time_value))}
                for time_value in times
            ]
        return []

    def _parameter_is_automated(self, parameter):
        try:
            return int(self._safe_get(parameter, "automation_state", 0)) != 0
        except Exception:
            return False

    def _materialize_arrangement_automation(self, ref, item):
        result = self._materialize_arrangement_automation_lanes(ref, [item])
        lane = result["lanes"][0]
        return {
            "location": result["location"],
            "clip": result["clip"],
            **lane,
            "materialized_from_session_clip": result["materialized_from_session_clip"],
            "done": True,
        }

    def _materialize_arrangement_automation_lanes(self, ref, items):
        source = ref["clip"]
        track = ref.get("track") or self._safe_get(source, "canonical_parent")
        if not self._safe_get(source, "is_midi_clip", False):
            raise ValueError("Live cannot create Arrangement envelopes in place; the safe materialization fallback supports MIDI clips only")
        self._ensure_materialization_can_replace_lanes(source, items)
        _slot_index, slot = self._empty_session_slot(track)
        clip_start = float(self._safe_get(source, "start_time", 0.0))
        clip_length = float(self._safe_get(source, "length", 0.0))
        self.song().begin_undo_step()
        created = False
        try:
            slot.create_clip(clip_length)
            temp_clip = slot.clip
            self._copy_midi_clip_contents(source, temp_clip)
            self._set_optional_clip_property(temp_clip, "name", self._safe_get(source, "name", ""))
            lane_results = []
            for item in items:
                envelope = self._automation_envelope(temp_clip, item["parameter"], True)
                if item["events"] is not None:
                    inserted = self._insert_automation_events(envelope, item["parameter"], item["events"])
                else:
                    inserted = self._insert_automation_steps(envelope, item["parameter"], item["steps"])
                lane_results.append({"item": item, "inserted": inserted})
            self._delete_clip_ref(ref)
            track.duplicate_clip_to_arrangement(temp_clip, clip_start)
            new_clip = self._find_arrangement_clip(track, clip_start, clip_length)
            new_ref = self._clip_ref_from_clip(new_clip)
            results = []
            for lane in lane_results:
                new_envelope = self._automation_envelope(new_clip, lane["item"]["parameter"], False)
                results.append(self._arrangement_automation_lane_result(lane["item"], lane["inserted"], new_envelope))
            created = True
            return self._arrangement_automation_many_result(new_ref, new_clip, results, True)
        finally:
            if created and slot.has_clip:
                slot.delete_clip()
            self.song().end_undo_step()

    def _ensure_materialization_can_replace_lanes(self, clip, items):
        envelopes = list(self._safe_get(clip, "automation_envelopes", []) or [])
        if not envelopes:
            return
        for envelope in envelopes:
            envelope_parameter = self._safe_get(envelope, "parameter")
            matches = [item for item in items if envelope_parameter == item["parameter"]]
            if not matches:
                raise ValueError("Refusing to materialize Arrangement automation because the clip has other automation envelopes")
            if not matches[0]["clear"]:
                raise ValueError("Arrangement automation lane already exists; use clear=true to replace it through materialization")

    def _empty_session_slot(self, track):
        for index, slot in enumerate(track.clip_slots):
            if not slot.has_clip:
                return index, slot
        raise ValueError("No empty Session clip slot is available for Arrangement automation materialization")
