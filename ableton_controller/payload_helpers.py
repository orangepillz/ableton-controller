"""Shared payload construction helpers."""

import argparse
from typing import Any

def add_if_not_none(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value


def clip_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    names = ("path", "track", "slot", "arrangement_index", "arrangement_start")
    found = False
    for name in names:
        value = getattr(args, ("%s_%s" % (prefix, name)) if prefix else name, None)
        if value is not None:
            payload[("%s_%s" % (prefix, name)) if prefix else name] = value
            found = True
    if not found:
        label = "%s " % prefix if prefix else ""
        raise SystemExit("Command needs a %sclip reference: --path, --track/--slot, --track/--arrangement-index, or --track/--arrangement-start." % label)
    return payload


def device_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    names = ("device_path", "track", "device")
    found = False
    for name in names:
        arg_name = ("%s_%s" % (prefix, name)) if prefix else name
        value = getattr(args, arg_name, None)
        if value is not None:
            payload[arg_name] = value
            found = True
    if not found:
        label = "%s " % prefix if prefix else ""
        raise SystemExit("Command needs a %sdevice reference: --device-path or --track/--device." % label)
    return payload


def optional_device_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    try:
        return device_ref_payload(args, prefix)
    except SystemExit:
        return {}


def clip_automation_device_ref_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if getattr(args, "device_path", None) is not None:
        payload["device_path"] = args.device_path
    if getattr(args, "device_track", None) is not None:
        payload["device_track"] = args.device_track
    elif getattr(args, "track", None) is not None:
        payload["track"] = args.track
    if getattr(args, "device", None) is not None:
        payload["device"] = args.device
    if "device_path" not in payload and "device" not in payload:
        raise SystemExit("Command needs --device-path or --device.")
    return payload


def container_ref_payload(args: argparse.Namespace, prefix: str = "target") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("path", "track"):
        arg_name = "%s_%s" % (prefix, name)
        value = getattr(args, arg_name, None)
        if value is not None:
            payload[arg_name] = value
    if not payload:
        raise SystemExit("Command needs a %s container reference: --%s-path or --%s-track." % (prefix, prefix, prefix))
    return payload


def note_region_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("start", "end", "length", "pitch_min", "pitch_max"):
        add_if_not_none(payload, name, getattr(args, name, None))
    return payload


def clip_range_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("start", "end", "length"):
        add_if_not_none(payload, name, getattr(args, name, None))
    if getattr(args, "from_loop", False):
        payload["from_loop"] = True
    return payload
