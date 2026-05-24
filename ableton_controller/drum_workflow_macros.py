"""Drum-focused reusable workflow macro renderers."""

from __future__ import annotations

import argparse
from typing import Any

from .workflow_personalization import load_macro_memory, personalized_macro_track, personalized_target_source


def drum_punch_bus(args: argparse.Namespace) -> dict[str, Any]:
    memory = load_macro_memory(getattr(args, "memory", None))
    track = personalized_macro_track(_track(args, "Drum Bus"), "Drum Bus", "drums", memory)
    return {
        "summary": "Prepare a punchier drum bus chain with transient and glue controls visible for tuning.",
        "assumptions": [f"Drum bus track is {track!r}", personalized_target_source(memory)],
        "commands": [
            {"why": "Read drum bus context before adding processing.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 3]},
            {"why": "Add transient and saturation control.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Drum Buss"]},
            {"why": "Add gentle bus cohesion control.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Glue Compressor"]},
            {"why": "Read exact Drum Buss controls for follow-up tuning.", "args": ["stock-controls", "--device", "Drum Buss"]},
            {"why": "Read exact Glue Compressor controls for follow-up tuning.", "args": ["stock-controls", "--device", "Glue Compressor"]},
        ],
    }


def hat_humanize(args: argparse.Namespace) -> dict[str, Any]:
    memory = load_macro_memory(getattr(args, "memory", None))
    track = personalized_macro_track(_track(args, "Hats"), "Hats", "hats", memory)
    start, end = _range(args)
    return {
        "summary": "Humanize an existing hat clip with controlled velocity and probability variation.",
        "assumptions": [
            f"Hat track is {track!r}",
            f"Session clip slot {args.slot} covers the hat pattern.",
            "Hat pitches default to MIDI 42-46 for closed/open hat lanes.",
            personalized_target_source(memory),
        ],
        "commands": [
            {"why": "Read hat clip and chain context before changing the groove.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 3]},
            {"why": "Inspect hat notes before applying variation.", "args": ["midi-get-notes", "--track", track, "--slot", args.slot, "--start", start, "--end", end, "--pitch-min", 42, "--pitch-max", 46]},
            {
                "why": "Add subtle velocity/probability variation while keeping the grid anchors intact.",
                "args": [
                    "midi-transform-notes",
                    "--track",
                    track,
                    "--slot",
                    args.slot,
                    "--start",
                    start,
                    "--end",
                    end,
                    "--pitch-min",
                    42,
                    "--pitch-max",
                    46,
                    "--velocity-deviation",
                    8,
                    "--probability",
                    0.94,
                ],
            },
            {"why": "Read back hat notes after humanization.", "args": ["midi-get-notes", "--track", track, "--slot", args.slot, "--start", start, "--end", end, "--pitch-min", 42, "--pitch-max", 46]},
        ],
    }


def _track(args: argparse.Namespace, default: str) -> str | int:
    return args.track if args.track is not None else default


def _range(args: argparse.Namespace) -> tuple[float, float]:
    start = float(args.start)
    end = float(args.end) if args.end is not None else start + float(args.length)
    return start, end
