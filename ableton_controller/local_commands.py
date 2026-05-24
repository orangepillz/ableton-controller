"""Local commands that do not map directly to one bridge payload."""

import argparse
import time
from typing import Any

from stock_device_controls import (
    control_parameter_name,
    find_control,
    find_device,
    iter_devices,
    load_registry,
    normalize,
    registry_summary,
    verify_registry,
)

from .als_automation import arrangement_file_get, arrangement_file_set
from .arrangement_automation import arrangement_automation_events
from .local_clip_envelopes import (
    clip_audio_set,
    clip_envelope_clear,
    clip_envelope_get,
    clip_envelope_set,
    clip_envelope_targets,
)
from .copilot_intent import match_copilot_intent
from .local_automation import applescript_string, run_applescript, run_hotkey, run_menu_search
from .payload_helpers import clip_automation_device_ref_payload, clip_ref_payload, device_ref_payload
from .session_snapshot import collect_session_snapshot
from .stock_cli import resolve_stock_control, stock_device_listing, stock_device_query_text, stock_value_payload
from .transport import send
from .workflow_macros import list_workflow_macros, render_workflow_macro

def send_local_bridge_command(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    response = send(payload, args.host, args.port, args.timeout)
    return response.get("result", response)


def arrangement_automation_get(args: argparse.Namespace) -> dict[str, Any]:
    payload = {
        "command": "arrangement_automation_get",
        "track": args.track,
        "arrangement_start": args.arrangement_start,
        **clip_automation_device_ref_payload(args),
        "param": args.param,
        "times": args.times or [],
    }
    result = send_local_bridge_command(args, payload)
    if result.get("has_automation") and not result.get("has_envelope") and payload["times"]:
        result["values"] = sample_arrangement_automation_values(args, payload, result)
        result["read_source"] = "client_playhead_sample"
    return result


def sample_arrangement_automation_values(args: argparse.Namespace, payload: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    original_time = send_local_bridge_command(args, {"command": "lom_get", "path": "song.current_song_time"})
    location = result.get("location") if isinstance(result.get("location"), dict) else {}
    clip_start = float(location.get("start_time", payload["arrangement_start"]))
    sample_payload = dict(payload)
    sample_payload["times"] = []
    values = []
    try:
        for time_value in payload["times"]:
            relative_time = float(time_value)
            send_local_bridge_command(
                args,
                {"command": "lom_set", "path": "song.current_song_time", "value": clip_start + relative_time},
            )
            time.sleep(0.02)
            sample = send_local_bridge_command(args, sample_payload)
            parameter = sample.get("parameter") if isinstance(sample.get("parameter"), dict) else {}
            values.append({"time": relative_time, "value": parameter.get("value")})
    finally:
        if original_time is not None:
            send_local_bridge_command(args, {"command": "lom_set", "path": "song.current_song_time", "value": original_time})
    return values


def run_local_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "copilot-intent":
        return match_copilot_intent(
            args.query,
            memory_path=args.memory,
            limit=args.limit,
            min_score=args.min_score,
            include_inactive=args.include_inactive,
        )
    if args.command == "session-snapshot":
        return collect_session_snapshot(args, lambda payload: send_local_bridge_command(args, payload))
    if args.command == "workflow-macro":
        if args.action == "list":
            return list_workflow_macros()
        return render_workflow_macro(args)
    if args.command == "arrangement-automation-file-get":
        return arrangement_file_get(args.set_file, args.track, args.arrangement_start, args.device, args.param)
    if args.command == "arrangement-automation-file-set":
        return arrangement_file_set(args.set_file, args, arrangement_automation_events(args))
    if args.command == "clip-envelope-targets":
        return clip_envelope_targets(args, send_local_bridge_command)
    if args.command == "clip-envelope-get":
        return clip_envelope_get(args, send_local_bridge_command)
    if args.command == "clip-envelope-set":
        return clip_envelope_set(args, send_local_bridge_command)
    if args.command == "clip-envelope-clear":
        return clip_envelope_clear(args, send_local_bridge_command)
    if args.command == "clip-audio-set":
        return clip_audio_set(args, send_local_bridge_command)
    if args.command == "stock-devices":
        registry = load_registry(args.registry)
        if args.summary:
            return registry_summary(registry)
        devices = iter_devices(registry, args.root)
        if args.query:
            needle = normalize(args.query)
            devices = [device for device in devices if needle in stock_device_query_text(device)]
        return {
            "summary": registry_summary(registry),
            "count": len(devices),
            "devices": [stock_device_listing(device, args.controls) for device in devices],
        }
    if args.command == "stock-controls":
        registry = load_registry(args.registry)
        device = find_device(registry, args.device, args.root)
        if args.control:
            control = find_control(device, args.control)
            return {"device": stock_device_listing(device, False), "control": control}
        return {"device": stock_device_listing(device, False), "controls": device.get("controls", [])}
    if args.command == "stock-coverage":
        return verify_registry(load_registry(args.registry))
    if args.command == "set-stock-control":
        _registry, device, control = resolve_stock_control(args)
        payload = {
            "command": "set_param",
            **device_ref_payload(args),
            "param": control_parameter_name(control),
            **stock_value_payload(args),
        }
        result = send_local_bridge_command(args, payload)
        result["stock_device"] = stock_device_listing(device, False)
        result["stock_control"] = control
        return result
    if args.command == "arrangement-automation-get":
        return arrangement_automation_get(args)
    if args.command == "clip-stock-automation-get":
        _registry, device, control = resolve_stock_control(args)
        payload = {
            "command": "clip_automation_get",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": control_parameter_name(control),
            "times": args.times or [],
        }
        result = send_local_bridge_command(args, payload)
        result["stock_device"] = stock_device_listing(device, False)
        result["stock_control"] = control
        return result
    if args.command == "clip-stock-automation-set":
        if args.steps is not None and args.events is not None:
            raise SystemExit("Use only one of clip-stock-automation-set --steps or --events.")
        if args.steps is None and args.events is None:
            raise SystemExit("clip-stock-automation-set needs --steps or --events.")
        _registry, device, control = resolve_stock_control(args)
        payload = {
            "command": "clip_automation_set",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": control_parameter_name(control),
            "clear": args.clear,
        }
        if args.steps is not None:
            payload["steps"] = args.steps
        if args.events is not None:
            payload["events"] = args.events
        result = send_local_bridge_command(args, payload)
        result["stock_device"] = stock_device_listing(device, False)
        result["stock_control"] = control
        return result
    if args.command == "clip-stock-automation-clear":
        payload = {"command": "clip_automation_clear", **clip_ref_payload(args)}
        if args.all:
            payload["all"] = True
            return send_local_bridge_command(args, payload)
        if not args.control:
            raise SystemExit("clip-stock-automation-clear needs --control or --all.")
        _registry, device, control = resolve_stock_control(args)
        payload.update({**clip_automation_device_ref_payload(args), "param": control_parameter_name(control)})
        result = send_local_bridge_command(args, payload)
        result["stock_device"] = stock_device_listing(device, False)
        result["stock_control"] = control
        return result
    if args.command == "save":
        run_hotkey(args.app, "cmd+s", args.delay)
        return {"command": "save", "app": args.app, "hotkey": "cmd+s", "done": True}
    if args.command == "hotkey":
        run_hotkey(args.app, args.combo, args.delay)
        return {"command": "hotkey", "app": args.app, "combo": args.combo, "done": True}
    if args.command == "key-sequence":
        for index, combo in enumerate(args.combos):
            run_hotkey(args.app, combo, args.delay if index == 0 else 0.0)
            if index < len(args.combos) - 1:
                time.sleep(max(0.0, args.between))
        return {"command": "key-sequence", "app": args.app, "combos": args.combos, "done": True}
    if args.command == "type-text":
        run_applescript(
            [
                'tell application %s to activate' % applescript_string(args.app),
                "delay %.3f" % max(0.0, args.delay),
                "tell application \"System Events\"",
                "  keystroke %s" % applescript_string(args.text),
                "end tell",
            ]
        )
        return {"command": "type-text", "app": args.app, "characters": len(args.text), "done": True}
    if args.command == "menu-search":
        run_menu_search(args.app, args.query, args.delay, args.search_delay)
        return {"command": "menu-search", "app": args.app, "query": args.query, "done": True}
    raise SystemExit(f"Unknown local command: {args.command}")
