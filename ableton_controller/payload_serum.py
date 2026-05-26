"""Payload builders for Serum plug-in commands."""

import argparse
from typing import Any

from .payload_helpers import add_if_not_none, container_ref_payload


def build_serum_payload(args):
    command = args.command
    if command == "serum-add":
        payload = {
            "command": "serum_add",
            **container_ref_payload(args, "target"),
            "format": args.format,
        }
        add_if_not_none(payload, "path", args.path)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "target_index", args.target_index)
        return payload
    if command == "serum-params":
        return {"command": "serum_params", **serum_device_ref_payload(args)}
    if command == "serum-set":
        payload = {"command": "serum_set_param", **serum_device_ref_payload(args), "param": args.param}
        add_serum_value(payload, args)
        return payload
    if command == "serum-set-many":
        return {
            "command": "serum_set_many",
            **serum_device_ref_payload(args),
            "controls": serum_controls(args.controls),
        }
    return None


def serum_device_ref_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("device_path", "track", "device", "instance"):
        add_if_not_none(payload, name, getattr(args, name, None))
    return payload


def add_serum_value(payload: dict[str, Any], args: argparse.Namespace) -> None:
    values = [name for name in ("value", "normalized", "delta") if getattr(args, name, None) is not None]
    if len(values) != 1:
        raise SystemExit("Serum control needs exactly one of --value, --normalized, or --delta.")
    key = values[0]
    payload[key] = getattr(args, key)


def serum_controls(raw_controls: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_controls, list):
        raise SystemExit("serum-set-many --controls must be a JSON list.")
    controls = []
    for index, raw_control in enumerate(raw_controls):
        if not isinstance(raw_control, dict):
            raise SystemExit("Serum control %s must be an object." % index)
        control = dict(raw_control)
        if "param" not in control:
            raise SystemExit("Serum control %s needs a param." % index)
        values = [name for name in ("value", "normalized", "delta") if name in control]
        if len(values) != 1:
            raise SystemExit("Serum control %s needs exactly one of value, normalized, or delta." % index)
        controls.append(
            {
                "param": control["param"],
                values[0]: float(control[values[0]]),
            }
        )
    return controls
