"""Local clip-envelope and audio-clip convenience commands."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from stock_device_controls import control_parameter_name

from .clip_envelopes import (
    CC_CONTROL_DEVICE,
    CC_CONTROL_DEVICE_PATH,
    CC_CONTROL_ROOT,
    cc_control_parameter_name,
    clip_envelope_catalog,
    native_clip_envelope_error,
)
from .local_automation import run_menu_search
from .payload_helpers import clip_automation_device_ref_payload, clip_ref_payload
from .stock_cli import resolve_stock_control, stock_device_listing

SendCommand = Callable[[argparse.Namespace, dict[str, Any]], dict[str, Any]]


def clip_envelope_targets(args: argparse.Namespace, send_command: SendCommand) -> dict[str, Any]:
    ref_payload = _optional_clip_ref_payload(args)
    if not ref_payload:
        return clip_envelope_catalog()
    result = send_command(args, {"command": "clip_envelope_targets", **ref_payload})
    result["catalog"] = clip_envelope_catalog(result.get("clip_type"))
    return result


def clip_envelope_get(args: argparse.Namespace, send_command: SendCommand) -> dict[str, Any]:
    lane, stock_device, stock_control = _target_parameter_payload(args)
    payload = {"command": "clip_automation_get", **clip_ref_payload(args), **lane, "times": args.times or []}
    result = send_command(args, payload)
    return _with_envelope_metadata(result, args, stock_device, stock_control)


def clip_envelope_set(args: argparse.Namespace, send_command: SendCommand) -> dict[str, Any]:
    _ensure_midi_cc_device(args, send_command)
    lane, stock_device, stock_control = _target_parameter_payload(args)
    payload = {"command": "clip_automation_set", **clip_ref_payload(args), **lane, **_automation_payload_values(args)}
    result = send_command(args, payload)
    return _with_envelope_metadata(result, args, stock_device, stock_control)


def clip_envelope_clear(args: argparse.Namespace, send_command: SendCommand) -> dict[str, Any]:
    payload = {"command": "clip_automation_clear", **clip_ref_payload(args)}
    stock_device = None
    stock_control = None
    if args.all:
        payload["all"] = True
    else:
        lane, stock_device, stock_control = _target_parameter_payload(args)
        payload.update(lane)
    result = send_command(args, payload)
    return _with_envelope_metadata(result, args, stock_device, stock_control)


def clip_audio_set(args: argparse.Namespace, send_command: SendCommand) -> dict[str, Any]:
    ref_payload = clip_ref_payload(args)
    payload = {"command": "clip_warp", **ref_payload}
    for name in ("warping", "warp_mode", "gain", "pitch_coarse", "pitch_fine", "ram_mode", "clip_bpm"):
        value = getattr(args, name, None)
        if value is not None:
            payload[name] = value
    if len(payload) == 1 + len(ref_payload) and not args.reverse:
        raise SystemExit("clip-audio-set needs an audio property or --reverse.")
    result: dict[str, Any] = {}
    if len(payload) > 1 + len(ref_payload):
        result = send_command(args, payload)
    if args.reverse:
        focus = send_command(args, {"command": "clip_focus", **ref_payload})
        run_menu_search(args.app, "Reverse Sample", args.delay, 0.35)
        result = {"focus": focus, **result, "reverse_menu_action": "Reverse Sample", "done": True}
    return result


def _automation_payload_values(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "steps", None) is not None and getattr(args, "events", None) is not None:
        raise SystemExit("Use only one of --steps or --events.")
    if getattr(args, "steps", None) is None and getattr(args, "events", None) is None:
        raise SystemExit("%s needs --steps or --events." % args.command)
    if getattr(args, "steps", None) is not None and not isinstance(args.steps, list):
        raise SystemExit("%s --steps must be a JSON list." % args.command)
    if getattr(args, "events", None) is not None and not isinstance(args.events, list):
        raise SystemExit("%s --events must be a JSON list." % args.command)
    payload: dict[str, Any] = {"clear": bool(getattr(args, "clear", False))}
    if getattr(args, "steps", None) is not None:
        payload["steps"] = args.steps
    if getattr(args, "events", None) is not None:
        payload["events"] = args.events
    return payload


def _optional_clip_ref_payload(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return clip_ref_payload(args)
    except SystemExit:
        return {}


def _target_parameter_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    if args.target == "native":
        raise SystemExit(native_clip_envelope_error(args.control or args.param or "requested target"))
    if args.target == "device":
        if args.param is None:
            raise SystemExit("%s --target device needs --param." % args.command)
        return {**clip_automation_device_ref_payload(args), "param": args.param}, None, None
    if args.target == "stock":
        if not args.control:
            raise SystemExit("%s --target stock needs --control." % args.command)
        _registry, stock_device, stock_control = resolve_stock_control(args)
        return {**clip_automation_device_ref_payload(args), "param": control_parameter_name(stock_control)}, stock_device, stock_control
    if args.target == "midi-cc":
        cc_args = _cc_control_args(args)
        _registry, stock_device, stock_control = resolve_stock_control(cc_args)
        lane = {**clip_automation_device_ref_payload(cc_args), "param": control_parameter_name(stock_control)}
        return lane, stock_device, stock_control
    raise SystemExit("Unknown clip envelope target: %s" % args.target)


def _cc_control_args(args: argparse.Namespace) -> SimpleNamespace:
    control = args.midi_control or args.control or args.param
    if control is None:
        raise SystemExit("clip-envelope %s with --target midi-cc needs --midi-control, --control, or --param." % args.command.split("-")[-1])
    try:
        control = cc_control_parameter_name(control)
    except ValueError as exc:
        raise SystemExit(str(exc))
    return SimpleNamespace(
        registry=args.registry,
        root=CC_CONTROL_ROOT,
        stock_device=CC_CONTROL_DEVICE_PATH,
        track=getattr(args, "track", None),
        device_track=getattr(args, "device_track", None),
        device_path=getattr(args, "device_path", None),
        device=args.device or CC_CONTROL_DEVICE,
        control=control,
    )


def _ensure_midi_cc_device(args: argparse.Namespace, send_command: SendCommand) -> None:
    if args.target != "midi-cc" or not getattr(args, "ensure_midi_cc_device", False):
        return
    target_track = getattr(args, "track", None)
    if target_track is None:
        raise SystemExit("--ensure-midi-cc-device needs --track on the clip reference.")
    devices = send_command(args, {"command": "devices", "track": target_track}).get("devices", [])
    if any(str(device.get("name", "")).lower() == CC_CONTROL_DEVICE.lower() for device in devices):
        return
    send_command(
        args,
        {
            "command": "device_add_stock",
            "target_track": target_track,
            "path": CC_CONTROL_DEVICE_PATH,
            "root": CC_CONTROL_ROOT,
            "allow_presets": False,
        },
    )


def _with_envelope_metadata(
    result: dict[str, Any],
    args: argparse.Namespace,
    stock_device: dict[str, Any] | None,
    stock_control: dict[str, Any] | None,
) -> dict[str, Any]:
    result["clip_envelope_target"] = args.target
    if stock_device is not None:
        result["stock_device"] = stock_device_listing(stock_device, False)
    if stock_control is not None:
        result["stock_control"] = stock_control
    return result
