"""Local stock-device registry CLI helpers."""

import argparse
from typing import Any

from stock_device_controls import find_control, find_device, load_registry, normalize

def stock_device_listing(device: dict[str, Any], include_controls: bool = False) -> dict[str, Any]:
    listed = {key: value for key, value in device.items() if key != "controls"}
    listed["control_count"] = len(device.get("controls", []))
    if include_controls:
        listed["controls"] = device.get("controls", [])
    return listed


def stock_device_query_text(device: dict[str, Any]) -> str:
    fields = [
        device.get("name"),
        device.get("path"),
        device.get("slug"),
        device.get("root"),
        device.get("class_name"),
        device.get("loaded_name"),
    ]
    return normalize(" ".join(str(field) for field in fields if field))


def stock_registry_device_identifier(args: argparse.Namespace) -> Any:
    if getattr(args, "stock_device", None):
        return args.stock_device
    device = getattr(args, "device", None)
    if device is not None and not isinstance(device, int):
        return device
    raise SystemExit("Command needs --stock-device when --device is numeric or --device-path is used.")


def resolve_stock_control(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry = load_registry(args.registry)
    device = find_device(registry, stock_registry_device_identifier(args), getattr(args, "root", None))
    control = find_control(device, args.control)
    return registry, device, control


def stock_value_payload(args: argparse.Namespace) -> dict[str, float]:
    if getattr(args, "value", None) is not None:
        return {"value": args.value}
    if getattr(args, "normalized", None) is not None:
        return {"normalized": args.normalized}
    return {"delta": args.delta}
