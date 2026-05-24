"""Personalized workflow-macro helpers backed by copilot memory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .arrangement_labels import load_memory
from .target_aliases import target_aliases


DEVICE_PATHS = {
    "Delay": "audio_effects/Delay",
    "Echo": "audio_effects/Echo",
    "Reverb": "audio_effects/Reverb",
    "Hybrid Reverb": "audio_effects/Hybrid Reverb",
    "AutoFilter": "audio_effects/Auto Filter",
    "Saturator": "audio_effects/Saturator",
    "Utility": "audio_effects/Utility",
}


def load_macro_memory(memory_path: Path | None) -> dict[str, Any] | None:
    return load_memory(memory_path)


def personalized_macro_track(current: str | int, default: str, role: str, memory: dict[str, Any] | None) -> str | int:
    if current != default or not memory:
        return current
    for alias in target_aliases(memory):
        if alias.get("role") == role and alias.get("aliases"):
            return alias["aliases"][0]
    return current


def personalized_target_source(memory: dict[str, Any] | None) -> str:
    if not memory:
        return "No personalized target-alias memory was loaded; default track names are used."
    return "Default target names may be replaced with learned personal aliases when available."


def has_refinement(memory: dict[str, Any] | None, label: str) -> bool:
    if not memory:
        return False
    return any(
        signal.get("category") == "chat.refinement" and signal.get("label") == label
        for signal in memory.get("signals", [])
    )


def space_chain_from_memory(memory_path: Path | None) -> tuple[list[str], str]:
    memory = load_memory(memory_path)
    signals = memory.get("signals", []) if memory else []
    ranked = sorted(
        [signal for signal in signals if signal.get("category") == "project.device-chain"],
        key=lambda signal: (-float(signal.get("confidence", 0)), -int(signal.get("evidence_count", 0)), str(signal.get("label", ""))),
    )
    for signal in ranked:
        devices = _devices_from_chain_label(str(signal.get("label", "")))
        if "Delay" in devices and "Reverb" in devices:
            return devices, f"Using learned device-chain signal `{signal.get('id', '')}`."
    return ["Delay", "Reverb"], "No learned Delay > Reverb chain was found, so the macro uses the default personalized space-chain seed."


def _devices_from_chain_label(label: str) -> list[str]:
    if ":" not in label:
        return []
    _track, chain = label.split(":", 1)
    return [part.strip() for part in chain.split(">") if part.strip()]
