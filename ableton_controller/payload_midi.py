"""Payload builders for midi commands."""

import json

from .payload_helpers import add_if_not_none, clip_ref_payload, note_region_payload

def build_midi_payload(args):
    command = args.command
    if command == "midi-get-notes":
        if not args.path and args.track is None:
            raise SystemExit("midi-get-notes needs --path or --track.")
        payload = {"command": "midi_get_notes", "slot": args.slot, **note_region_payload(args)}
        if args.path:
            payload["path"] = args.path
        if args.track is not None:
            payload["track"] = args.track
        add_if_not_none(payload, "arrangement_index", args.arrangement_index)
        add_if_not_none(payload, "arrangement_start", args.arrangement_start)
        return payload
    if command == "midi-add-notes":
        if not args.path and args.track is None:
            raise SystemExit("midi-add-notes needs --path or --track.")
        try:
            notes = json.loads(args.notes)
        except ValueError as exc:
            raise SystemExit(f"Invalid notes JSON: {exc}")
        payload = {"command": "midi_add_notes", "slot": args.slot, "notes": notes}
        if args.path:
            payload["path"] = args.path
        if args.track is not None:
            payload["track"] = args.track
        add_if_not_none(payload, "arrangement_index", args.arrangement_index)
        add_if_not_none(payload, "arrangement_start", args.arrangement_start)
        return payload
    if command == "midi-replace-notes":
        return {"command": "midi_replace_notes", **clip_ref_payload(args), "notes": args.notes}
    if command == "midi-update-notes":
        return {"command": "midi_update_notes", **clip_ref_payload(args), "notes": args.notes}
    if command == "midi-remove-notes":
        payload = {"command": "midi_remove_notes", **clip_ref_payload(args), **note_region_payload(args)}
        add_if_not_none(payload, "note_ids", args.note_ids)
        if "note_ids" not in payload and not any(key in payload for key in ("start", "end", "length", "pitch_min", "pitch_max")):
            raise SystemExit("midi-remove-notes needs --note-ids or a region/pitch filter.")
        return payload
    if command == "midi-clear-notes":
        return {"command": "midi_clear_notes", **clip_ref_payload(args), **note_region_payload(args)}
    if command == "midi-transform-notes":
        payload = {"command": "midi_transform_notes", **clip_ref_payload(args), **note_region_payload(args)}
        for name in (
            "transpose",
            "time_delta",
            "duration_scale",
            "duration_delta",
            "velocity_scale",
            "velocity_delta",
            "probability",
            "velocity_deviation",
            "release_velocity",
            "mute",
        ):
            add_if_not_none(payload, name, getattr(args, name))
        if not any(key in payload for key in ("transpose", "time_delta", "duration_scale", "duration_delta", "velocity_scale", "velocity_delta", "probability", "velocity_deviation", "release_velocity", "mute")):
            raise SystemExit("midi-transform-notes needs at least one transform option.")
        return payload
    if command == "midi-duplicate-region":
        payload = {
            "command": "midi_duplicate_region",
            **clip_ref_payload(args),
            "start": args.start,
            "destination_time": args.destination_time,
            "pitch": args.pitch,
            "transpose": args.transpose,
        }
        add_if_not_none(payload, "end", args.end)
        add_if_not_none(payload, "length", args.length)
        return payload
    return None
