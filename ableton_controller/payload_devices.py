"""Payload builders for device commands."""

from .payload_helpers import add_if_not_none, container_ref_payload, device_ref_payload

def build_device_payload(args):
    command = args.command
    if command == "devices":
        return {"command": "devices", "track": args.track}
    if command == "device-tree":
        return {"command": "device_tree", "track": args.track, "depth": args.depth}
    if command == "device-add-stock":
        payload = {"command": "device_add_stock", **container_ref_payload(args, "target")}
        add_if_not_none(payload, "path", args.path)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "root", args.root)
        add_if_not_none(payload, "target_index", args.target_index)
        if args.allow_presets:
            payload["allow_presets"] = True
        return payload
    if command == "device-move":
        return {
            "command": "device_move",
            **device_ref_payload(args, "source"),
            **container_ref_payload(args, "target"),
            "target_index": args.target_index,
        }
    if command == "device-delete":
        return {"command": "device_delete", **device_ref_payload(args)}
    if command == "drum-pad-load":
        payload = {
            "command": "drum_pad_load",
            "device": args.device,
            "pad": args.pad,
            "item": args.item,
            "clear": args.clear,
        }
        add_if_not_none(payload, "track", args.track)
        add_if_not_none(payload, "device_path", args.device_path)
        return payload
    if command == "params":
        return {"command": "params", **device_ref_payload(args)}
    return None
