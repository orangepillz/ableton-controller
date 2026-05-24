"""Personal workflow playbooks derived from learned workflow habits."""

from __future__ import annotations

from typing import Any


PLAYBOOKS = {
    "bass-movement": {
        "title": "Bass movement and resampling",
        "first_move": "Probe bass/sub devices, keep the sub stable, then add mid-bass filter or distortion motion.",
        "follow_through": "Verify movement automation, separate sub from mid bass, and treat resampling as an approval-gated follow-up.",
    },
    "spatial-send": {
        "title": "Spatial send throws",
        "first_move": "Prefer return/send movement for delay and reverb space before adding inserts to many tracks.",
        "follow_through": "Automate send throws, check return levels, and cut delay tails before high-impact drops.",
    },
    "glitch-drum": {
        "title": "Glitch drum transition",
        "first_move": "Resolve zap/perc samples, map them to distinct pads, then shape timing before the transition.",
        "follow_through": "Verify rack chains, audition alternate hits, and tune Echo/filter movement into the next synth or drop.",
    },
    "kick-sub": {
        "title": "Kick/sub separation",
        "first_move": "Read current kick, sub, and sidechain context before changing low-end routing or dynamics.",
        "follow_through": "Tighten MIDI gaps, inspect sidechain controls, and verify kick/sub phase fit after edits.",
    },
    "mix-bus": {
        "title": "Conservative mix-bus polish",
        "first_move": "Inspect Utility, limiter, and routing before making loudness or master-bus changes.",
        "follow_through": "Check gain staging, read limiter settings, and keep destructive loudness moves approval-gated.",
    },
    "arrangement-transition": {
        "title": "Arrangement transition flow",
        "first_move": "Use locator and section evidence before writing dense arrangement automation or transition edits.",
        "follow_through": "Name/verify sections, place transition FX, and confirm automation ranges before mutation.",
    },
    "riser-transition": {
        "title": "Riser and swell transition",
        "first_move": "Render the non-destructive riser plan before choosing detailed synth or FX tuning.",
        "follow_through": "Tune filter dips, add noise texture only when useful, and shorten reverb tails before the drop.",
    },
}


def playbook_key(label: str) -> str | None:
    for key in PLAYBOOKS:
        if label.startswith(key):
            return key
    return None


def workflow_playbooks_from_habits(workflow_habits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return runtime playbook guidance for already-matched workflow habits."""
    grouped: dict[str, dict[str, Any]] = {}
    for habit in workflow_habits:
        entry = _runtime_entry(habit)
        if not entry:
            continue
        existing = grouped.setdefault(entry["id"], entry)
        if existing is entry:
            continue
        existing["confidence"] = max(float(existing["confidence"]), float(entry["confidence"]))
        existing["matched_terms"] = _dedupe(_as_strings(existing.get("matched_terms")) + _as_strings(entry.get("matched_terms")))
        existing["evidence_signal_ids"].extend(entry.get("evidence_signal_ids", []))
        existing["source_label"] = ", ".join(_dedupe([existing.get("source_label", ""), entry.get("source_label", "")]))
    return sorted(grouped.values(), key=lambda item: (-float(item["confidence"]), item["id"]))


def workflow_playbooks_from_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return profile playbook guidance from persisted chat/project workflow signals."""
    grouped: dict[str, dict[str, Any]] = {}
    for signal in signals:
        if signal.get("category") not in {"project.workflow", "chat.workflow"}:
            continue
        key = playbook_key(str(signal.get("label", "")))
        if not key:
            continue
        item = grouped.setdefault(key, _base_entry(key))
        item["confidence"] = max(float(item["confidence"]), float(signal.get("confidence", 0)))
        item["evidence_count"] += int(signal.get("evidence_count", 0) or 0)
        item["evidence_signal_ids"].append(str(signal.get("id", "")))
    for item in grouped.values():
        item["confidence"] = round(min(0.95, float(item["confidence"]) + min(0.08, item["evidence_count"] * 0.01)), 3)
    return sorted(grouped.values(), key=lambda item: (-float(item["confidence"]), item["id"]))


def _runtime_entry(habit: dict[str, Any]) -> dict[str, Any] | None:
    key = playbook_key(str(habit.get("label", "")))
    if not key:
        return None
    entry = _base_entry(key)
    entry["confidence"] = round(min(0.95, float(habit.get("confidence", 0)) * 0.85 + 0.08), 3)
    entry["matched_terms"] = _as_strings(habit.get("matched_terms"))
    entry["evidence_signal_ids"] = [str(habit.get("id", ""))]
    entry["source_label"] = str(habit.get("label", ""))
    return entry


def _base_entry(key: str) -> dict[str, Any]:
    definition = PLAYBOOKS[key]
    return {
        "id": key,
        "title": definition["title"],
        "first_move": definition["first_move"],
        "follow_through": definition["follow_through"],
        "confidence": 0.0,
        "evidence_count": 0,
        "evidence_signal_ids": [],
    }


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
