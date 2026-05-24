"""Arrangement feature extraction helpers for Ableton project scans."""

from __future__ import annotations

import re
from collections import Counter


NON_MUSICAL_MARKER_LABELS = {"true", "false", "on", "off", "lane", "straight", "s-shaped"}
ROLE_RULES = (
    ("drums", ("drum", "break", "impulse", "tr8s", "perc")),
    ("kick", ("kick", "bd", "808")),
    ("bass", ("bass", "sub")),
    ("fill", ("fill", "roll")),
    ("fx", ("fx", "hit", "siren", "riser", "impact", "noise")),
    ("melodic", ("horn", "flute", "lead", "synth", "wavetable", "chord", "pad")),
)


def arrangement_shape(scenes: int, locators: int, clip_times: list[float], clip_lengths: list[float]) -> Counter[str]:
    shape: Counter[str] = Counter()
    if scenes:
        shape[f"scene-count-{scenes}"] += 1
    shape[f"locator-count-{locators}"] += 1
    arrangement_starts = [time for time in clip_times if time > 0]
    if arrangement_starts:
        shape[_count_bucket("arrangement-clips", len(arrangement_starts))] += 1
        grid = _dominant_grid(arrangement_starts)
        if grid:
            shape[f"arrangement-start-grid-{grid}-beats"] += 1
        shape[_span_bucket(max(arrangement_starts) + (max(clip_lengths) if clip_lengths else 0))] += 1
    for length, count in Counter(_round_beats(length) for length in clip_lengths if length > 0).most_common(3):
        shape[f"common-clip-length-{length}-beats"] += count
    return shape


def arrangement_roles(clips: list[tuple[float, str]]) -> Counter[str]:
    roles: Counter[str] = Counter()
    for time, name in clips:
        if time <= 0:
            continue
        for role in _roles_for_name(name):
            roles[f"clip-role-{role}"] += 1
            roles[f"{_time_bucket(time)}-role-{role}"] += 1
    return roles


def arrangement_phase_signatures(clips: list[tuple[float, str]]) -> Counter[str]:
    roles_by_bucket: dict[str, set[str]] = {}
    for time, name in clips:
        if time <= 0:
            continue
        roles = _roles_for_name(name)
        if not roles:
            continue
        bucket = _time_bucket(time)
        roles_by_bucket.setdefault(bucket, set()).update(roles)
    signatures: Counter[str] = Counter()
    for bucket, roles in roles_by_bucket.items():
        if len(roles) >= 2:
            signatures[f"{bucket}-phase-{'-'.join(sorted(roles))}"] += 1
    return signatures


def locator_marker_label(name: str | None, time: float | None) -> str | None:
    if name is None or time is None or not _looks_marker_label(name):
        return None
    cleaned_name = name.strip()
    if not any(char.isalpha() for char in cleaned_name):
        cleaned_name = f"marker {cleaned_name}"
    return f"locator-{_slug_label(cleaned_name)}-at-{_beat_label(time)}-beats"


def _looks_marker_label(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(value and normalized not in NON_MUSICAL_MARKER_LABELS)


def _roles_for_name(name: str) -> list[str]:
    normalized = name.lower()
    return [role for role, terms in ROLE_RULES if any(term in normalized for term in terms)]


def _time_bucket(time: float) -> str:
    if time < 32:
        return "early-arrangement"
    if time < 96:
        return "main-section"
    return "late-arrangement"


def _dominant_grid(starts: list[float]) -> int | None:
    for grid in (32, 16, 8, 4):
        aligned = sum(1 for value in starts if abs(value % grid) < 0.01 or abs((value % grid) - grid) < 0.01)
        if aligned / len(starts) >= 0.55:
            return grid
    return None


def _round_beats(value: float) -> str:
    rounded = round(value)
    return str(rounded if abs(value - rounded) < 0.01 else round(value, 2))


def _slug_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "marker"


def _beat_label(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.01:
        return str(int(rounded))
    return str(round(value, 2)).rstrip("0").rstrip(".")


def _count_bucket(prefix: str, count: int) -> str:
    if count <= 16:
        bucket = "1-16"
    elif count <= 64:
        bucket = "17-64"
    else:
        bucket = "65-plus"
    return f"{prefix}-{bucket}"


def _span_bucket(span: float) -> str:
    if span < 64:
        bucket = "under-64"
    elif span < 128:
        bucket = "64-128"
    elif span < 256:
        bucket = "128-256"
    else:
        bucket = "256-plus"
    return f"timeline-span-{bucket}-beats"
