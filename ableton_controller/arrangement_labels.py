"""Derived arrangement section label proposals from copilot memory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_MARKER_SECTION_NAMES = (
    (0.0, "01 Intro - Setup"),
    (64.0, "02 Main Drop - Impact"),
    (160.0, "03 Break - Fakeout Space"),
    (192.0, "04 Re-Drop - Variation"),
    (256.0, "05 Late Groove - Expansion"),
    (320.0, "06 Reset - Transition"),
    (448.0, "07 Final Return"),
    (480.0, "08 Outro - Tail"),
)
MARKER_PATTERN = re.compile(r"^locator-(?P<marker>.+)-at-(?P<beat>[0-9]+(?:\.[0-9]+)?)-beats$")
PHASE_PREFIXES = ("early-arrangement-phase-", "main-section-phase-", "late-arrangement-phase-")
ROLE_PREFIXES = ("early-arrangement-role-", "main-section-role-", "late-arrangement-role-")


def default_memory_path(start: Path | None = None) -> Path:
    root = (start or Path.cwd()).resolve()
    for candidate in (root, *root.parents):
        path = candidate / ".ableton-copilot" / "memory.json"
        if path.exists():
            return path
    return root / ".ableton-copilot" / "memory.json"


def load_memory(path: Path | None = None) -> dict[str, Any] | None:
    try:
        memory = json.loads((path or default_memory_path()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return memory if isinstance(memory, dict) else None


def marker_label_proposals(memory: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not memory:
        return []
    markers = _marker_signals(memory)
    if not markers:
        return []
    role_phrases = _role_phrases(memory)
    exact_default_map = _matches_default_beats(markers)
    return [
        {
            "beat": marker["beat"],
            "name": _section_name(marker, index, len(markers), role_phrases, exact_default_map),
            "confidence": _proposal_confidence(marker["confidence"], role_phrases),
            "evidence_signal_ids": [marker["id"], *role_phrases.get("evidence", [])[:3]],
            "marker_label": marker["label"],
        }
        for index, marker in enumerate(markers)
    ]


def fallback_marker_label_proposals() -> list[dict[str, Any]]:
    return [
        {
            "beat": beat,
            "name": name,
            "confidence": 0.2,
            "evidence_signal_ids": [],
            "marker_label": "",
        }
        for beat, name in DEFAULT_MARKER_SECTION_NAMES
    ]


def _marker_signals(memory: dict[str, Any]) -> list[dict[str, Any]]:
    markers = []
    for signal in memory.get("signals", []):
        if signal.get("category") != "project.arrangement-marker":
            continue
        marker = _marker_from_signal(signal)
        if marker:
            markers.append(marker)
    return sorted(markers, key=lambda marker: (marker["beat"], -marker["confidence"], marker["label"]))


def _marker_from_signal(signal: dict[str, Any]) -> dict[str, Any] | None:
    label = str(signal.get("label", ""))
    match = MARKER_PATTERN.match(label)
    if not match:
        return None
    try:
        beat = float(match.group("beat"))
        confidence = float(signal.get("confidence", 0.0))
    except ValueError:
        return None
    marker_text = match.group("marker")
    return {
        "beat": beat,
        "confidence": confidence,
        "label": label,
        "id": str(signal.get("id", "")),
        "marker_number": _marker_number(marker_text),
    }


def _matches_default_beats(markers: list[dict[str, Any]]) -> bool:
    if len(markers) != len(DEFAULT_MARKER_SECTION_NAMES):
        return False
    defaults = [beat for beat, _name in DEFAULT_MARKER_SECTION_NAMES]
    return all(abs(float(marker["beat"]) - beat) < 0.01 for marker, beat in zip(markers, defaults))


def _role_phrases(memory: dict[str, Any]) -> dict[str, Any]:
    buckets: dict[str, set[str]] = {}
    evidence: dict[str, list[str]] = {}
    for signal in memory.get("signals", []):
        label = str(signal.get("label", ""))
        if signal.get("category") == "project.arrangement-phase":
            _collect_prefixed_roles(label, PHASE_PREFIXES, "-phase-", signal, buckets, evidence)
        if signal.get("category") == "project.arrangement-role":
            _collect_prefixed_roles(label, ROLE_PREFIXES, "-role-", signal, buckets, evidence)
    phrases: dict[str, Any] = {"evidence": []}
    for bucket, roles in buckets.items():
        phrases[bucket] = _role_phrase("-".join(sorted(roles)))
        phrases["evidence"].extend(evidence.get(bucket, []))
    return phrases


def _collect_prefixed_roles(
    label: str,
    prefixes: tuple[str, ...],
    suffix: str,
    signal: dict[str, Any],
    buckets: dict[str, set[str]],
    evidence: dict[str, list[str]],
) -> None:
    for prefix in prefixes:
        if not label.startswith(prefix):
            continue
        bucket = prefix.removesuffix(suffix)
        roles = {role for role in label.removeprefix(prefix).split("-") if role}
        if roles:
            buckets.setdefault(bucket, set()).update(roles)
            evidence.setdefault(bucket, []).append(str(signal.get("id", "")))


def _section_name(marker: dict[str, Any], index: int, total: int, roles: dict[str, Any], exact_default_map: bool) -> str:
    main_roles = roles.get("main-section", "")
    late_roles = roles.get("late-arrangement", main_roles)
    if exact_default_map:
        names = list(DEFAULT_MARKER_SECTION_NAMES)
        if main_roles:
            names[1] = (names[1][0], f"02 Main Drop - {main_roles} Impact")
            names[3] = (names[3][0], f"04 Re-Drop - {main_roles} Variation")
        if late_roles:
            names[4] = (names[4][0], f"05 Late Groove - {late_roles} Expansion")
        return names[index][1]

    number = marker.get("marker_number") or index + 1
    role_index = min(int(number), len(DEFAULT_MARKER_SECTION_NAMES)) - 1
    label = str(marker["label"])
    if role_index == 0:
        role = "Intro - Setup"
    elif role_index == 1:
        role = f"Main Drop - {main_roles} Impact" if main_roles else "Main Drop - Impact"
    elif role_index == 2:
        role = "Break - Fakeout Space"
    elif role_index == 3:
        role = f"Re-Drop - {main_roles} Variation" if main_roles else "Re-Drop - Variation"
    elif role_index == 4:
        role = f"Late Groove - {late_roles} Expansion" if late_roles else "Late Groove - Expansion"
    elif role_index == 5:
        role = "Reset - Transition"
    elif role_index == 6:
        role = "Final Return"
    else:
        role = "Outro - Tail"
    return f"{number:02d} {role} ({_readable_marker(label)})"


def _role_phrase(raw: str) -> str:
    roles = [_readable_role(role) for role in raw.split("-") if role]
    return " ".join(roles)


def _readable_role(role: str) -> str:
    names = {"drums": "Drum", "fx": "FX"}
    return names.get(role, role.replace("-", " ").title())


def _readable_marker(label: str) -> str:
    match = MARKER_PATTERN.match(label)
    if not match:
        return label
    return match.group("marker").replace("-", " ")


def _marker_number(marker_text: str) -> int | None:
    match = re.search(r"\d+", marker_text)
    return int(match.group(0)) if match else None


def _proposal_confidence(marker_confidence: float, roles: dict[str, Any]) -> float:
    role_bonus = 0.05 if roles.get("evidence") else 0.0
    return round(max(0.2, min(0.9, marker_confidence + role_bonus)), 3)
