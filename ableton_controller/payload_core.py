"""Payload builders for core commands."""

import json

from .arg_types import scalar_value
from .payload_helpers import device_ref_payload

def build_core_payload(args):
    command = args.command
    if command == "ping":
        return {"command": "ping"}
    if command == "status":
        return {"command": "status"}
    if command == "tracks":
        return {"command": "tracks"}
    if command == "selected":
        return {"command": "selected", "devices": args.devices}
    if command == "select-track":
        return {"command": "select_track", "track": args.track}

    if command == "set-track":
        fields = {
            key: getattr(args, key)
            for key in ("volume", "pan", "mute", "solo", "arm")
            if getattr(args, key) is not None
        }
        if not fields:
            raise SystemExit("set-track needs at least one of --volume, --pan, --mute, --solo, --arm.")
        return {"command": "set_track", "track": args.track, **fields}
    if command == "set-send":
        return {"command": "set_send", "track": args.track, "send": args.send, "value": args.value}
    if command == "set-param":
        payload = {
            "command": "set_param",
            **device_ref_payload(args),
            "param": args.param,
        }
        if args.value is not None:
            payload["value"] = args.value
        elif args.normalized is not None:
            payload["normalized"] = args.normalized
        else:
            payload["delta"] = args.delta
        return payload
    if command == "tempo":
        payload = {"command": "tempo"}
        if args.set is not None:
            payload["value"] = args.set
        return payload
    if command in {"play", "stop", "continue", "undo", "redo"}:
        return {"command": command}
    if command == "lom-get":
        return {"command": "lom_get", "path": args.path}
    if command == "lom-set":
        if args.json:
            try:
                value = json.loads(args.value)
            except ValueError as exc:
                raise SystemExit(f"Invalid JSON value: {exc}")
        else:
            value = scalar_value(args.value)
        return {"command": "lom_set", "path": args.path, "value": value}
    if command == "lom-call":
        try:
            call_args = json.loads(args.args)
            call_kwargs = json.loads(args.kwargs)
        except ValueError as exc:
            raise SystemExit(f"Invalid call JSON: {exc}")
        return {"command": "lom_call", "path": args.path, "args": call_args, "kwargs": call_kwargs}
    if command == "lom-inspect":
        return {"command": "lom_inspect", "path": args.path}
    if command in {"show-view", "hide-view", "focus-view"}:
        return {"command": "view", "action": command.split("-", 1)[0], "view": args.view}
    if command == "toggle-browse":
        return {"command": "view", "action": "toggle-browse"}
    return None
