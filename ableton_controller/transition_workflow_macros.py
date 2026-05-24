"""Transition-focused workflow macro renderers."""

from __future__ import annotations

import argparse
import json
from typing import Any


def riser_transition(args: argparse.Namespace) -> dict[str, Any]:
    """Create a deterministic MIDI riser sketch with filter and space movement."""
    track = args.track if args.track is not None else "Inhale Riser"
    length = float(args.length)
    clip_name = args.name or "Inhale Riser Into Drop"
    notes = [{"pitch": 72, "start_time": 0, "duration": length, "velocity": 92}]
    filter_steps = [
        {"time": 0, "duration": length * 0.35, "normalized": 0.18},
        {"time": length * 0.35, "duration": length * 0.35, "normalized": 0.58},
        {"time": length * 0.7, "duration": length * 0.22, "normalized": 0.86},
        {"time": length * 0.92, "duration": length * 0.08, "normalized": 0.24},
    ]
    wet_steps = [
        {"time": 0, "duration": length * 0.5, "normalized": 0.22},
        {"time": length * 0.5, "duration": length * 0.35, "normalized": 0.48},
        {"time": length * 0.85, "duration": length * 0.15, "normalized": 0.68},
    ]
    return {
        "summary": "Create a non-destructive inhale riser sketch with a long tone, opening filter, and swelling space before the drop.",
        "assumptions": [
            f"Riser MIDI track is {track!r}",
            f"Riser clip length is {length:g} beats",
            "The final filter dip leaves room for the drop transient instead of washing through it.",
        ],
        "commands": [
            {"why": "Read current context before adding a transition layer.", "args": ["session-snapshot", "--device-tree-depth", 3]},
            {"why": "Create a dedicated editable MIDI riser track.", "args": ["create-track", "--type", "midi", "--name", track]},
            {"why": "Use Operator as a deterministic stock tone source.", "args": ["device-add-stock", "--target-track", track, "--path", "instruments/Operator"]},
            {"why": "Add filter movement for the inhale shape.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Auto Filter"]},
            {"why": "Add controlled space for the swell tail.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Reverb"]},
            {"why": "Create the riser clip container.", "args": ["clip-create-midi", "--track", track, "--slot", args.slot, "--length", length, "--name", clip_name]},
            {"why": "Write a sustained tone that can be shaped by automation.", "args": ["midi-add-notes", "--track", track, "--slot", args.slot, "--notes", _json(notes)]},
            {"why": "Write the inhale filter arc with a final pre-drop dip.", "args": ["clip-stock-automation-set", "--track", track, "--slot", args.slot, "--device", "Auto Filter", "--stock-device", "Auto Filter", "--control", "frequency", "--clear", "--steps", _json(filter_steps)]},
            {"why": "Swell reverb into the transition without committing to a final mix value.", "args": ["clip-stock-automation-set", "--track", track, "--slot", args.slot, "--device", "Reverb", "--stock-device", "Reverb", "--control", "dry_wet", "--clear", "--steps", _json(wet_steps)]},
            {"why": "Verify the riser notes.", "args": ["midi-get-notes", "--track", track, "--slot", args.slot]},
            {"why": "Verify the filter automation samples.", "args": ["clip-stock-automation-get", "--track", track, "--slot", args.slot, "--device", "Auto Filter", "--stock-device", "Auto Filter", "--control", "frequency", "--times", f"0,{length * 0.5:g},{length * 0.9:g}"]},
            {"why": "Verify the resulting riser chain.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 5]},
        ],
    }


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))
