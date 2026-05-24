"""Explicit natural-language overrides for workflow macro previews."""

from __future__ import annotations

import re
from typing import Any


def query_macro_overrides(query: str) -> dict[str, Any]:
    """Extract low-risk macro render defaults from explicit query language."""
    overrides: dict[str, Any] = {}
    length = _length_beats(query)
    if length is not None:
        overrides["length"] = length
    start = _start_beat(query)
    if start is not None:
        overrides["start"] = start
    slot = _slot(query)
    if slot is not None:
        overrides["slot"] = slot
    track = _quoted_track(query)
    if track is not None:
        overrides["track"] = track
    return overrides


def _length_beats(query: str) -> float | None:
    beat_match = re.search(r"\b(\d+(?:\.\d+)?)\s*[- ]?beats?\b", query, re.IGNORECASE)
    if beat_match:
        return float(beat_match.group(1))
    bar_match = re.search(r"\b(\d+(?:\.\d+)?)\s*[- ]?bars?\b", query, re.IGNORECASE)
    if bar_match:
        return float(bar_match.group(1)) * 4.0
    return None


def _start_beat(query: str) -> float | None:
    match = re.search(r"\b(?:start(?:ing)?\s+at|from|at)\s+beat\s+(\d+(?:\.\d+)?)\b", query, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _slot(query: str) -> int | None:
    match = re.search(r"\bslot\s+(\d+)\b", query, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _quoted_track(query: str) -> str | None:
    match = re.search(r"\b(?:on|to|for)?\s*track\s+[\"']([^\"']+)[\"']", query, re.IGNORECASE)
    if not match:
        return None
    track = match.group(1).strip()
    if not track or len(track) > 80:
        return None
    return track
