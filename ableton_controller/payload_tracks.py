"""Payload builders for track_scene commands."""

def build_track_scene_payload(args):
    command = args.command
    if command == "create-track":
        payload = {"command": "create_track", "type": args.type}
        if args.index is not None:
            payload["index"] = args.index
        if args.name:
            payload["name"] = args.name
        return payload
    if command == "delete-track":
        return {"command": "delete_track", "track": args.track}
    if command == "duplicate-track":
        return {"command": "duplicate_track", "track": args.track}
    if command == "create-scene":
        payload = {"command": "create_scene"}
        if args.index is not None:
            payload["index"] = args.index
        if args.name:
            payload["name"] = args.name
        return payload
    if command == "delete-scene":
        return {"command": "delete_scene", "scene": args.scene}
    if command == "duplicate-scene":
        return {"command": "duplicate_scene", "scene": args.scene}
    if command == "fire-scene":
        return {"command": "fire_scene", "scene": args.scene}
    if command == "set-routing":
        if args.type is None and args.channel is None:
            raise SystemExit("set-routing needs --type, --channel, or both.")
        payload = {"command": "set_routing", "track": args.track, "direction": args.direction}
        if args.type is not None:
            payload["type"] = args.type
        if args.channel is not None:
            payload["channel"] = args.channel
        return payload
    return None
