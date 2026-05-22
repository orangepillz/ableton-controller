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

from .local_automation import applescript_string, run_applescript, run_hotkey, run_menu_search
from .payload_helpers import clip_automation_device_ref_payload, clip_ref_payload, device_ref_payload
from .stock_cli import resolve_stock_control, stock_device_listing, stock_device_query_text, stock_value_payload
from .transport import send

def send_local_bridge_command(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    response = send(payload, args.host, args.port, args.timeout)
    return response.get("result", response)


def run_local_command(args: argparse.Namespace) -> dict[str, Any]:
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
        _registry, device, control = resolve_stock_control(args)
        payload = {
            "command": "clip_automation_set",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": control_parameter_name(control),
            "steps": args.steps,
            "clear": args.clear,
        }
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
