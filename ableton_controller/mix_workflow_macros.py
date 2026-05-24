"""Mix and master-prep workflow macro renderers."""

from __future__ import annotations

import argparse
from typing import Any

from .workflow_personalization import load_macro_memory, personalized_target_source


MIX_BUS_DEVICE_PATHS = (
    ("Utility", "audio_effects/Utility"),
    ("EQ Eight", "audio_effects/EQ Eight"),
    ("Glue Compressor", "audio_effects/Glue Compressor"),
    ("Limiter", "audio_effects/Limiter"),
    ("Spectrum", "audio_effects/Spectrum"),
)


def mix_bus_control(args: argparse.Namespace) -> dict[str, Any]:
    memory = load_macro_memory(getattr(args, "memory", None))
    target = _mix_target(args, memory)
    commands: list[dict[str, Any]] = [
        {"why": "Read the mix/master target before adding preview-chain devices.", "args": ["session-snapshot", "--track", target, "--device-tree-depth", 6]},
    ]
    for device, path in MIX_BUS_DEVICE_PATHS:
        commands.append(
            {"why": f"Add {device} for conservative mix-bus inspection and preview control if missing.", "args": ["device-add-stock", "--target-track", target, "--path", path]}
        )
    for device, _path in MIX_BUS_DEVICE_PATHS:
        commands.append(
            {"why": f"Read {device} controls before any gain, EQ, dynamics, or loudness decisions.", "args": ["stock-controls", "--device", device]}
        )
    commands.append(
        {"why": "Verify the resulting mix-bus chain without changing loudness or saving the set.", "args": ["session-snapshot", "--track", target, "--device-tree-depth", 6]}
    )
    return {
        "summary": "Prepare a conservative mix/master preview chain with readbacks before any gain or loudness decisions.",
        "assumptions": [
            f"Mix/master target is {target!r}",
            _mix_target_source(memory),
            "The macro only prepares inspection and control devices; exact settings still depend on reference, destination, and current headroom.",
        ],
        "commands": commands,
    }


def _mix_target(args: argparse.Namespace, memory: dict[str, Any] | None) -> str | int:
    if args.track is not None:
        return args.track
    if _has_master_name(memory):
        return "Master"
    return "Master"


def _mix_target_source(memory: dict[str, Any] | None) -> str:
    if _has_master_name(memory):
        return "Historical project evidence includes a Master track naming signal."
    return personalized_target_source(memory)


def _has_master_name(memory: dict[str, Any] | None) -> bool:
    if not memory:
        return False
    return any(
        signal.get("category") == "project.name" and str(signal.get("label", "")).lower() == "master"
        for signal in memory.get("signals", [])
    )
