"""Payload builders for clip commands."""

from .payload_helpers import add_if_not_none, clip_automation_device_ref_payload, clip_range_payload, clip_ref_payload

def build_clip_payload(args):
    command = args.command
    if command == "clips":
        return {"command": "clips", "track": args.track}
    if command == "clip-create-midi":
        payload = {"command": "clip_create_midi", "track": args.track, **clip_range_payload(args)}
        add_if_not_none(payload, "slot", args.slot)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "color", args.color)
        add_if_not_none(payload, "color_index", args.color_index)
        if args.replace:
            payload["replace"] = True
        if "slot" not in payload and not any(key in payload for key in ("start", "end", "length", "from_loop")):
            raise SystemExit("Arrangement clip-create-midi needs --start/--length, --start/--end, or --from-loop.")
        if "slot" in payload and not any(key in payload for key in ("end", "length", "from_loop")):
            raise SystemExit("Session clip-create-midi needs --length or --from-loop.")
        return payload
    if command == "clip-create-audio":
        payload = {"command": "clip_create_audio", "track": args.track, "file": args.file, **clip_range_payload(args)}
        add_if_not_none(payload, "slot", args.slot)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "color", args.color)
        add_if_not_none(payload, "color_index", args.color_index)
        add_if_not_none(payload, "warping", args.warping)
        add_if_not_none(payload, "warp_mode", args.warp_mode)
        if args.replace:
            payload["replace"] = True
        if "slot" not in payload and "start" not in payload and not payload.get("from_loop", False):
            raise SystemExit("Arrangement clip-create-audio needs --start or --from-loop.")
        return payload
    if command == "clip-set":
        payload = {"command": "clip_set", **clip_ref_payload(args)}
        for name in (
            "name",
            "color",
            "color_index",
            "muted",
            "looping",
            "loop_start",
            "loop_end",
            "start_marker",
            "end_marker",
            "position",
            "launch_mode",
            "launch_quantization",
            "legato",
            "velocity_amount",
            "signature_numerator",
            "signature_denominator",
            "gain",
            "pitch_coarse",
            "pitch_fine",
            "ram_mode",
            "warping",
            "warp_mode",
        ):
            add_if_not_none(payload, name, getattr(args, name))
        if len(payload) == 1 + len(clip_ref_payload(args)):
            raise SystemExit("clip-set needs at least one property to set.")
        return payload
    if command == "clip-warp":
        payload = {"command": "clip_warp", **clip_ref_payload(args)}
        for name in ("warping", "warp_mode", "gain", "pitch_coarse", "pitch_fine", "ram_mode"):
            add_if_not_none(payload, name, getattr(args, name))
        return payload
    if command == "clip-warp-marker-add":
        payload = {"command": "clip_warp_marker_add", **clip_ref_payload(args), "beat_time": args.beat_time}
        add_if_not_none(payload, "sample_time", args.sample_time)
        return payload
    if command == "clip-warp-marker-move":
        payload = {"command": "clip_warp_marker_move", **clip_ref_payload(args), "beat_time": args.beat_time}
        if args.to_beat is not None:
            payload["to_beat"] = args.to_beat
        else:
            payload["distance"] = args.distance
        return payload
    if command == "clip-warp-marker-remove":
        return {"command": "clip_warp_marker_remove", **clip_ref_payload(args), "beat_time": args.beat_time}
    if command == "clip-automation-get":
        payload = {
            "command": "clip_automation_get",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": args.param,
        }
        add_if_not_none(payload, "times", args.times)
        return payload
    if command == "clip-automation-set":
        if not isinstance(args.steps, list):
            raise SystemExit("clip-automation-set --steps must be a JSON list.")
        return {
            "command": "clip_automation_set",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": args.param,
            "steps": args.steps,
            "clear": args.clear,
        }
    if command == "clip-automation-clear":
        payload = {"command": "clip_automation_clear", **clip_ref_payload(args)}
        if args.all:
            payload["all"] = True
        else:
            if args.param is None:
                raise SystemExit("clip-automation-clear needs --param or --all.")
            payload.update(clip_automation_device_ref_payload(args))
            payload["param"] = args.param
        return payload
    if command == "clip-delete":
        return {"command": "clip_delete", **clip_ref_payload(args)}
    if command in {"clip-copy", "clip-move"}:
        payload = {
            "command": "clip_copy" if command == "clip-copy" else "clip_move",
            **clip_ref_payload(args, "source"),
        }
        add_if_not_none(payload, "dest_track", args.dest_track)
        add_if_not_none(payload, "dest_slot", args.dest_slot)
        add_if_not_none(payload, "dest_start", args.dest_start)
        add_if_not_none(payload, "dest_end", args.dest_end)
        add_if_not_none(payload, "length", args.length)
        if args.dest_from_loop:
            payload["dest_from_loop"] = True
        if args.replace:
            payload["replace"] = True
        if args.dest_slot is None and args.dest_start is None and args.dest_end is None and not args.dest_from_loop:
            raise SystemExit("%s needs --dest-slot, --dest-start/--dest-end, or --dest-from-loop." % command)
        return payload
    if command == "clip-split":
        return {"command": "clip_split", **clip_ref_payload(args), "time": args.time, "relative": args.relative}

    if command == "clip-slots":
        return {"command": "clip_slots", "track": args.track}
    if command == "fire-clip":
        return {"command": "fire_clip", "track": args.track, "slot": args.slot}
    if command == "stop-track-clips":
        return {"command": "stop_track_clips", "track": args.track}
    return None
