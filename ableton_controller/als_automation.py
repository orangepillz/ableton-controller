"""Saved Live Set arrangement automation editing."""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .als_xml import (
    attr_float as _attr_float,
    child_value as _child_value,
    ensure_path as _ensure_path,
    format_float as _format_float,
    matches_text as _matches_text,
    next_child_id as _next_child_id,
    next_event_id as _next_event_id,
    norm as _norm,
    range_contains as _range_contains,
    read_tree as _read_tree,
    same_float as _same_float,
    write_tree as _write_tree,
)

TRACK_TAGS = {"AudioTrack", "MidiTrack", "GroupTrack", "ReturnTrack", "MainTrack"}
CLIP_TAGS = {"AudioClip", "MidiClip"}
CURVE_ATTRS = ("CurveControl1X", "CurveControl1Y", "CurveControl2X", "CurveControl2Y")


def arrangement_file_get(path: Path, track_ref: int | str, start: float, device_ref: str, param_ref: str) -> dict[str, Any]:
    tree = _read_tree(path)
    root = tree.getroot()
    track = _find_track(root, track_ref)
    clip = _find_arrangement_clip(track, start, None)
    parameter = _find_parameter(_find_device(track, device_ref), param_ref)
    envelope = _find_envelope(track, _automation_target_id(parameter))
    return _lane_result(path, track, clip, parameter, envelope)


def arrangement_file_set(path: Path, args: Any, events: list[dict[str, Any]]) -> dict[str, Any]:
    if len(events) < 2:
        raise ValueError("Saved-set automation curve writes need at least two events.")
    tree = _read_tree(path)
    root = tree.getroot()
    track = _find_track(root, args.track)
    clip = _find_arrangement_clip(track, args.arrangement_start, getattr(args, "clip_name", None))
    device = _find_device(track, args.device)
    parameter = _find_parameter(device, args.param)
    envelope = _find_or_create_envelope(track, parameter)
    inserted = _replace_events(
        envelope,
        parameter,
        events,
        float(_attr_float(clip, "Time", args.arrangement_start)),
        bool(getattr(args, "preserve_boundaries", True)),
    )
    if not getattr(args, "dry_run", False):
        if getattr(args, "backup", True):
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        _write_tree(path, tree)
    result = _lane_result(path, track, clip, parameter, envelope)
    result.update({"inserted": inserted, "dry_run": bool(getattr(args, "dry_run", False)), "done": True})
    return result


def _find_track(root: ET.Element, track_ref: int | str) -> ET.Element:
    tracks_root = root.find("./LiveSet/Tracks")
    if tracks_root is None:
        raise ValueError("Live Set has no Tracks section.")
    tracks = [child for child in list(tracks_root) if child.tag in TRACK_TAGS]
    if isinstance(track_ref, int):
        try:
            return tracks[track_ref]
        except IndexError as exc:
            raise ValueError("Track index %s was not found in the saved set." % track_ref) from exc
    matches = [track for track in tracks if _matches_text(track_ref, _track_names(track))]
    if not matches:
        raise ValueError("Track %r was not found in the saved set." % track_ref)
    if len(matches) > 1:
        raise ValueError("Track %r matched more than one saved-set track." % track_ref)
    return matches[0]


def _track_names(track: ET.Element) -> list[str]:
    names = [track.tag]
    for path in ("./Name/EffectiveName", "./Name/UserName", "./Name/MemorizedFirstClipName"):
        value = _child_value(track, path)
        if value:
            names.append(value)
    return names


def _find_arrangement_clip(track: ET.Element, start: float, clip_name: str | None) -> ET.Element:
    clips = [item for item in track.iter() if item.tag in CLIP_TAGS and _same_float(_attr_float(item, "Time", None), start)]
    if clip_name:
        clips = [clip for clip in clips if _matches_text(clip_name, [_child_value(clip, "./Name") or ""])]
    if not clips:
        raise ValueError("Arrangement clip at %.6g was not found on track %s." % (start, _track_names(track)[0]))
    if len(clips) > 1:
        raise ValueError("Arrangement clip at %.6g matched more than one clip; pass --clip-name." % start)
    return clips[0]


def _find_device(track: ET.Element, device_ref: str) -> ET.Element:
    matches = [item for item in track.iter() if _has_device_parameters(item) and _matches_text(device_ref, _device_names(item))]
    if not matches:
        raise ValueError("Device %r was not found on track %s." % (device_ref, _track_names(track)[0]))
    if len(matches) > 1:
        raise ValueError("Device %r matched more than one saved-set device." % device_ref)
    return matches[0]


def _has_device_parameters(device: ET.Element) -> bool:
    return any(_automation_target_id(child, required=False) is not None for child in list(device))


def _device_names(device: ET.Element) -> list[str]:
    names = [device.tag, device.tag.rstrip("0123456789")]
    for item in device.iter("DeviceId"):
        name = item.attrib.get("Name")
        if name:
            names.extend([name, name.rstrip("0123456789")])
    user_name = _child_value(device, "./UserName")
    if user_name:
        names.append(user_name)
    return names


def _find_parameter(device: ET.Element, param_ref: str) -> ET.Element:
    aliases = {"cutoff": "frequency"}
    query = aliases.get(_norm(param_ref), _norm(param_ref))
    matches = []
    for child in list(device):
        if _automation_target_id(child, required=False) is None:
            continue
        names = [child.tag, child.tag.split("_")[-1], child.tag.replace("_", " ")]
        if query in [_norm(name) for name in names]:
            matches.append(child)
    if not matches:
        raise ValueError("Parameter %r was not found on device %s." % (param_ref, device.tag))
    if len(matches) > 1:
        preferred = [match for match in matches if _norm(match.tag).startswith("filter")]
        if len(preferred) == 1:
            return preferred[0]
        raise ValueError("Parameter %r matched more than one saved-set parameter." % param_ref)
    return matches[0]


def _automation_target_id(parameter: ET.Element, *, required: bool = True) -> str | None:
    target = parameter.find("./AutomationTarget")
    value = target.attrib.get("Id") if target is not None else None
    if value is None and required:
        raise ValueError("Parameter %s has no AutomationTarget Id." % parameter.tag)
    return value


def _find_envelope(track: ET.Element, target_id: str) -> ET.Element | None:
    for envelope in track.findall("./AutomationEnvelopes/Envelopes/AutomationEnvelope"):
        if _child_value(envelope, "./EnvelopeTarget/PointeeId") == str(target_id):
            return envelope
    return None


def _find_or_create_envelope(track: ET.Element, parameter: ET.Element) -> ET.Element:
    target_id = _automation_target_id(parameter)
    envelope = _find_envelope(track, target_id)
    if envelope is not None:
        return envelope
    envelopes = _ensure_path(track, ("AutomationEnvelopes", "Envelopes"))
    envelope = ET.SubElement(envelopes, "AutomationEnvelope", {"Id": str(_next_child_id(envelopes, "AutomationEnvelope"))})
    target = ET.SubElement(envelope, "EnvelopeTarget")
    ET.SubElement(target, "PointeeId", {"Value": str(target_id)})
    automation = ET.SubElement(envelope, "Automation")
    events = ET.SubElement(automation, "Events")
    ET.SubElement(events, "FloatEvent", {"Id": "0", "Time": "-63072000", "Value": _child_value(parameter, "./Manual") or "0"})
    view = ET.SubElement(automation, "AutomationTransformViewState")
    ET.SubElement(view, "IsTransformPending", {"Value": "false"})
    ET.SubElement(view, "TimeAndValueTransforms")
    return envelope


def _replace_events(envelope: ET.Element, parameter: ET.Element, events: list[dict[str, Any]], clip_start: float, preserve: bool) -> list[dict[str, Any]]:
    events_el = envelope.find("./Automation/Events")
    if events_el is None:
        raise ValueError("AutomationEnvelope has no Events container.")
    existing = list(events_el)
    event_range_start = clip_start + min(float(event["time"]) for event in events)
    event_range_end = clip_start + max(float(event["time"]) for event in events)
    old_float_events = [child for child in existing if child.tag == "FloatEvent"]
    default_tail = next((child.tail for child in old_float_events if child.tail), "\n")
    kept = [
        child
        for child in existing
        if child.tag != "FloatEvent" or not _range_contains(event_range_start, event_range_end, _attr_float(child, "Time", 0.0))
    ]
    next_id = _next_event_id(old_float_events)
    new_events = []
    if preserve:
        pre_value = _value_before(old_float_events, event_range_start, _child_value(parameter, "./Manual") or "0")
        post_value = _value_after(old_float_events, event_range_end, _child_value(parameter, "./Manual") or "0")
        new_events.append(_float_event(next_id, event_range_start, float(pre_value), None, default_tail))
        next_id += 1
    inserted = []
    for event in events:
        value = _event_value(parameter, event)
        coefficients = event.get("curve_coefficients") or event.get("control_coefficients")
        absolute_time = clip_start + float(event["time"])
        new_events.append(_float_event(next_id, absolute_time, value, coefficients, default_tail))
        inserted.append({"time": float(event["time"]), "absolute_time": absolute_time, "value": value, "control_coefficients": coefficients})
        next_id += 1
    if preserve:
        new_events.append(_float_event(next_id, event_range_end, float(post_value), None, default_tail))
    for child in existing:
        events_el.remove(child)
    for child in sorted(kept + new_events, key=lambda item: (_attr_float(item, "Time", 0.0), kept.index(item) if item in kept else len(kept))):
        events_el.append(child)
    return inserted


def _float_event(event_id: int, time_value: float, value: float, coefficients: dict[str, Any] | None, tail: str) -> ET.Element:
    attrs = {"Id": str(event_id), "Time": _format_float(time_value), "Value": _format_float(value)}
    if coefficients is not None:
        attrs.update(
            {
                "CurveControl1X": _format_float(float(coefficients["x1"])),
                "CurveControl1Y": _format_float(float(coefficients["y1"])),
                "CurveControl2X": _format_float(float(coefficients["x2"])),
                "CurveControl2Y": _format_float(float(coefficients["y2"])),
            }
        )
    element = ET.Element("FloatEvent", attrs)
    element.tail = tail
    return element


def _lane_result(path: Path, track: ET.Element, clip: ET.Element, parameter: ET.Element, envelope: ET.Element | None) -> dict[str, Any]:
    clip_start = _attr_float(clip, "Time", 0.0)
    return {
        "set_file": str(path),
        "track": {"tag": track.tag, "name": _track_names(track)[1] if len(_track_names(track)) > 1 else _track_names(track)[0]},
        "clip": {"tag": clip.tag, "name": _child_value(clip, "./Name"), "start": clip_start},
        "parameter": {"tag": parameter.tag, "automation_target_id": _automation_target_id(parameter)},
        "has_envelope": envelope is not None,
        "events": _events_info(envelope, clip_start) if envelope is not None else [],
    }


def _events_info(envelope: ET.Element, clip_start: float) -> list[dict[str, Any]]:
    events_el = envelope.find("./Automation/Events")
    if events_el is None:
        return []
    result = []
    for event in events_el.findall("./FloatEvent"):
        absolute = _attr_float(event, "Time", 0.0)
        item = {
            "id": event.attrib.get("Id"),
            "time": absolute - clip_start,
            "absolute_time": absolute,
            "value": _attr_float(event, "Value", 0.0),
        }
        if all(name in event.attrib for name in CURVE_ATTRS):
            item["control_coefficients"] = {
                "x1": _attr_float(event, "CurveControl1X", 0.0),
                "y1": _attr_float(event, "CurveControl1Y", 0.0),
                "x2": _attr_float(event, "CurveControl2X", 0.0),
                "y2": _attr_float(event, "CurveControl2Y", 0.0),
            }
        result.append(item)
    return result


def _event_value(parameter: ET.Element, event: dict[str, Any]) -> float:
    if "value" in event:
        return float(event["value"])
    if "normalized" not in event:
        raise ValueError("Automation event needs value or normalized.")
    normalized = min(1.0, max(0.0, float(event["normalized"])))
    minimum = float(_child_value(parameter, "./MidiControllerRange/Min") or 0.0)
    maximum = float(_child_value(parameter, "./MidiControllerRange/Max") or 1.0)
    if minimum > 0 and maximum > minimum and "frequency" in _norm(parameter.tag):
        return minimum * ((maximum / minimum) ** normalized)
    return minimum + ((maximum - minimum) * normalized)


def _value_before(events: list[ET.Element], time_value: float, default: str) -> str:
    before = [event for event in events if _attr_float(event, "Time", 0.0) < time_value]
    if before:
        return before[-1].attrib.get("Value", default)
    at_time = [event for event in events if _same_float(_attr_float(event, "Time", 0.0), time_value)]
    return at_time[0].attrib.get("Value", default) if at_time else default


def _value_after(events: list[ET.Element], time_value: float, default: str) -> str:
    after = [event for event in events if _attr_float(event, "Time", 0.0) > time_value]
    if after:
        return after[0].attrib.get("Value", default)
    at_time = [event for event in events if _same_float(_attr_float(event, "Time", 0.0), time_value)]
    return at_time[-1].attrib.get("Value", default) if at_time else default

