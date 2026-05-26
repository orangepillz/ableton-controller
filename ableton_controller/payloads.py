"""Dispatch CLI namespaces to bridge JSON payloads."""

from .payload_browser import build_browser_payload
from .payload_clips import build_clip_payload
from .payload_core import build_core_payload
from .payload_devices import build_device_payload
from .payload_midi import build_midi_payload
from .payload_raw import build_raw_payload
from .payload_serum import build_serum_payload
from .payload_tracks import build_track_scene_payload

BUILDERS = (
    build_core_payload,
    build_device_payload,
    build_serum_payload,
    build_browser_payload,
    build_track_scene_payload,
    build_clip_payload,
    build_midi_payload,
    build_raw_payload,
)


def command_payload(args):
    for builder in BUILDERS:
        payload = builder(args)
        if payload is not None:
            return payload
    raise SystemExit(f"Unknown command: {args.command}")
