"""Helpers for arrangement clip automation payloads."""

from __future__ import annotations

import argparse
from types import SimpleNamespace
from typing import Any


def _mapping_value(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in mapping:
        return mapping[key]
    return mapping.get(key.replace("_", "-"), default)


CURVE_PRESETS = ("linear", "ease-in", "ease-out", "ease-in-out")


def _automation_value_key(args: argparse.Namespace, prefix: str) -> tuple[str, float]:
    normalized = getattr(args, f"{prefix}_normalized")
    value = getattr(args, f"{prefix}_value")
    if normalized is not None:
        return "normalized", float(normalized)
    if value is not None:
        return "value", float(value)
    raise SystemExit(f"arrangement-automation-set needs --{prefix.replace('_', '-')}-normalized or --{prefix.replace('_', '-')}-value.")


def _curve_coefficients_preset(name: str | None) -> dict[str, float]:
    preset = (name or "linear").replace("_", "-").lower()
    if preset == "linear":
        return {"x1": 0.333333, "y1": 0.333333, "x2": 0.666667, "y2": 0.666667}
    if preset == "ease-in":
        return {"x1": 0.42, "y1": 0.0, "x2": 1.0, "y2": 1.0}
    if preset == "ease-out":
        return {"x1": 0.0, "y1": 0.0, "x2": 0.58, "y2": 1.0}
    if preset == "ease-in-out":
        return {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0}
    raise SystemExit("Arrangement automation curve must be one of: %s." % ", ".join(CURVE_PRESETS))


def _curve_coefficients(mapping: dict[str, Any]) -> dict[str, float] | None:
    preset = _mapping_value(mapping, "curve")
    explicit = _mapping_value(mapping, "curve_coefficients")
    if explicit is None:
        explicit = _mapping_value(mapping, "control_coefficients")
    if preset is not None and explicit is not None:
        raise SystemExit("Use only one of curve or curve_coefficients for an automation event.")
    if preset is not None:
        return _curve_coefficients_preset(str(preset))
    if explicit is None and all(_mapping_value(mapping, key) is None for key in ("x1", "y1", "x2", "y2")):
        return None
    source = explicit if explicit is not None else mapping
    if not isinstance(source, dict):
        raise SystemExit("Automation curve_coefficients must be an object with x1, y1, x2, y2.")
    coefficients: dict[str, float] = {}
    for key in ("x1", "y1", "x2", "y2"):
        value = _mapping_value(source, key)
        if value is None:
            raise SystemExit("Automation curve_coefficients needs x1, y1, x2, y2.")
        coefficients[key] = float(value)
    return coefficients


def _interpolate(start: float, end: float, index: int, total: int) -> float:
    if total <= 1:
        return end
    return start + ((end - start) * (index / (total - 1)))


def arrangement_automation_steps(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.duration is None:
        raise SystemExit("arrangement-automation-set needs --duration when --events or --curve is not used.")
    if args.duration <= 0:
        raise SystemExit("arrangement-automation-set --duration must be greater than 0.")
    if args.steps < 1:
        raise SystemExit("arrangement-automation-set --steps must be at least 1.")

    value_key, start_value = _automation_value_key(args, "from")
    to_normalized = args.to_normalized
    to_value = args.to_value
    if to_normalized is not None and to_value is not None:
        raise SystemExit("Use only one of --to-normalized or --to-value.")
    if to_normalized is None and to_value is None:
        return [{"time": 0.0, "duration": float(args.duration), value_key: start_value}]

    end_key = "normalized" if to_normalized is not None else "value"
    end_value = float(to_normalized if to_normalized is not None else to_value)
    if end_key != value_key:
        raise SystemExit("Use matching value types: normalized-to-normalized or value-to-value.")

    step_count = int(args.steps)
    step_duration = float(args.duration) / step_count
    steps: list[dict[str, Any]] = []
    for index in range(step_count):
        steps.append(
            {
                "time": round(index * step_duration, 6),
                "duration": round(step_duration, 6),
                value_key: round(_interpolate(start_value, end_value, index, step_count), 6),
            }
        )
    return steps


def arrangement_automation_events(args: argparse.Namespace) -> list[dict[str, Any]]:
    if getattr(args, "events", None) is not None:
        return _automation_events(args.events, "arrangement-automation-set --events")
    if args.duration is None:
        raise SystemExit("arrangement-automation-set needs --duration when generating curved events.")
    if args.duration <= 0:
        raise SystemExit("arrangement-automation-set --duration must be greater than 0.")
    value_key, start_value = _automation_value_key(args, "from")
    to_normalized = args.to_normalized
    to_value = args.to_value
    if to_normalized is not None and to_value is not None:
        raise SystemExit("Use only one of --to-normalized or --to-value.")
    if to_normalized is None and to_value is None:
        raise SystemExit("Curved automation needs --to-normalized or --to-value.")
    end_key = "normalized" if to_normalized is not None else "value"
    end_value = float(to_normalized if to_normalized is not None else to_value)
    if end_key != value_key:
        raise SystemExit("Use matching value types: normalized-to-normalized or value-to-value.")
    curve_mapping = {
        "curve": getattr(args, "curve", None),
        "curve_coefficients": getattr(args, "curve_coefficients", None),
    }
    event = {"time": 0.0, value_key: start_value}
    coefficients = _curve_coefficients(curve_mapping)
    if coefficients is not None:
        event["curve_coefficients"] = coefficients
    return [event, {"time": float(args.duration), value_key: end_value}]


def _automation_events(events: Any, source_name: str) -> list[dict[str, Any]]:
    if not isinstance(events, list) or not events:
        raise SystemExit("%s must be a non-empty JSON list." % source_name)
    payload_events: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise SystemExit("%s event %s must be an object." % (source_name, index))
        time_value = _mapping_value(event, "time")
        if time_value is None:
            raise SystemExit("%s event %s needs time." % (source_name, index))
        value_key = "normalized" if _mapping_value(event, "normalized") is not None else "value"
        value = _mapping_value(event, value_key)
        if value is None:
            raise SystemExit("%s event %s needs value or normalized." % (source_name, index))
        payload: dict[str, Any] = {"time": float(time_value), value_key: float(value)}
        coefficients = _curve_coefficients(event)
        if coefficients is not None:
            payload["curve_coefficients"] = coefficients
        payload_events.append(payload)
    return payload_events


def _lane_steps(lane: dict[str, Any], index: int) -> list[dict[str, Any]]:
    steps = _mapping_value(lane, "steps")
    if isinstance(steps, list):
        return steps
    duration = _mapping_value(lane, "duration")
    if duration is None:
        raise SystemExit("arrangement-automation-set-many lane %s needs duration or step objects." % index)
    args = SimpleNamespace(
        duration=float(duration),
        steps=int(steps if steps is not None else 8),
        from_normalized=_mapping_value(lane, "from_normalized"),
        from_value=_mapping_value(lane, "from_value"),
        to_normalized=_mapping_value(lane, "to_normalized"),
        to_value=_mapping_value(lane, "to_value"),
    )
    return arrangement_automation_steps(args)


def _lane_events(lane: dict[str, Any], index: int) -> list[dict[str, Any]]:
    events = _mapping_value(lane, "events")
    if events is not None:
        return _automation_events(events, "arrangement-automation-set-many lane %s events" % index)
    duration = _mapping_value(lane, "duration")
    if duration is None:
        raise SystemExit("arrangement-automation-set-many lane %s needs duration for curved automation." % index)
    args = SimpleNamespace(
        events=None,
        duration=float(duration),
        from_normalized=_mapping_value(lane, "from_normalized"),
        from_value=_mapping_value(lane, "from_value"),
        to_normalized=_mapping_value(lane, "to_normalized"),
        to_value=_mapping_value(lane, "to_value"),
        curve=_mapping_value(lane, "curve"),
        curve_coefficients=_mapping_value(lane, "curve_coefficients"),
    )
    return arrangement_automation_events(args)


def arrangement_automation_lanes(lanes: Any) -> list[dict[str, Any]]:
    if not isinstance(lanes, list) or not lanes:
        raise SystemExit("arrangement-automation-set-many --lanes must be a non-empty JSON list.")
    payload_lanes: list[dict[str, Any]] = []
    for index, lane in enumerate(lanes):
        if not isinstance(lane, dict):
            raise SystemExit("arrangement-automation-set-many lane %s must be an object." % index)
        param = _mapping_value(lane, "param")
        if param is None:
            raise SystemExit("arrangement-automation-set-many lane %s needs param." % index)
        payload: dict[str, Any] = {"param": param}
        if _mapping_value(lane, "events") is not None or _mapping_value(lane, "curve") is not None or _mapping_value(lane, "curve_coefficients") is not None:
            payload["events"] = _lane_events(lane, index)
        else:
            payload["steps"] = _lane_steps(lane, index)
        for key in ("device_path", "device_track", "device"):
            value = _mapping_value(lane, key)
            if value is not None:
                payload[key] = value
        if _mapping_value(lane, "clear", False):
            payload["clear"] = True
        payload_lanes.append(payload)
    return payload_lanes
