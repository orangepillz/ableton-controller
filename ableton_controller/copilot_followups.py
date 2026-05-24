"""Ranked likely-follow-up predictions for copilot orchestration."""

from __future__ import annotations

from typing import Any


HABIT_FOLLOWUPS = {
    "bass-movement": ("verify movement automation", "render a resampling pass", "separate sub from mid bass"),
    "spatial-send": ("automate send throws", "cut delay tails before the drop", "verify return levels"),
    "glitch-drum": ("audition zap/perc alternatives", "verify rack chains", "tune Echo and filter movement into the synth"),
    "kick-sub": ("tighten MIDI gaps around kicks", "read sidechain controls", "verify kick/sub phase fit"),
    "mix-bus": ("check Utility gain", "read limiter settings", "verify bus routing"),
}


def likely_followups(matches: list[dict[str, Any]], workflow_habits: list[dict[str, Any]] | None = None, limit: int = 6) -> list[dict[str, Any]]:
    """Return confidence-ranked follow-up moves from matched intent and workflow memory."""
    predictions: list[dict[str, Any]] = []
    seen = set()
    order = 0
    for match in matches[:3]:
        matched_followups = set(_as_strings(match.get("matched_likely_followups")))
        for label in _as_strings(match.get("likely_followups")):
            if label in seen:
                continue
            seen.add(label)
            predictions.append(_prediction(match, label, label in matched_followups, order))
            order += 1
    for habit in (workflow_habits or [])[:4]:
        for label in _habit_followups(str(habit.get("label", ""))):
            if label in seen:
                continue
            seen.add(label)
            predictions.append(_habit_prediction(habit, label, order))
            order += 1
    ranked = sorted(
        predictions,
        key=lambda item: (
            item["priority_rank"],
            -float(item["confidence"]),
            item["source_order"],
        ),
    )[:limit]
    return [_public_prediction(rank + 1, item) for rank, item in enumerate(ranked)]


def _prediction(match: dict[str, Any], label: str, matched_current_query: bool, order: int) -> dict[str, Any]:
    intent_id = str(match.get("id", ""))
    confidence = _followup_confidence(match, matched_current_query)
    priority = _priority(confidence, matched_current_query)
    return {
        "intent_id": intent_id,
        "intent_title": str(match.get("title", "")),
        "label": label,
        "matched_current_query": matched_current_query,
        "matched_terms": [label] if matched_current_query else [],
        "confidence": confidence,
        "source_score": _float(match.get("score", 0)),
        "source_confidence": _float(match.get("confidence", 0)),
        "priority": priority,
        "priority_rank": _priority_rank(priority),
        "source_order": order,
        "why": _why(intent_id, matched_current_query),
    }


def _habit_prediction(habit: dict[str, Any], label: str, order: int) -> dict[str, Any]:
    confidence = round(min(1.0, _float(habit.get("confidence", 0)) * 0.75 + 0.12), 3)
    return {
        "intent_id": str(habit.get("id", "")),
        "intent_title": str(habit.get("label", "")),
        "label": label,
        "matched_current_query": False,
        "matched_terms": _as_strings(habit.get("matched_terms")),
        "confidence": confidence,
        "source_score": 0.0,
        "source_confidence": _float(habit.get("confidence", 0)),
        "priority": "workflow-habit",
        "priority_rank": _priority_rank("workflow-habit"),
        "source_order": order,
        "why": f"Historically likely after matched workflow habit {habit.get('label')}.",
    }


def _public_prediction(rank: int, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": rank,
        "intent_id": item["intent_id"],
        "label": item["label"],
        "matched_current_query": item["matched_current_query"],
        "confidence": item["confidence"],
        "priority": item["priority"],
        "source_score": item["source_score"],
        "matched_terms": item["matched_terms"],
        "why": item["why"],
    }


def _followup_confidence(match: dict[str, Any], matched_current_query: bool) -> float:
    source_score = _float(match.get("score", 0))
    source_confidence = _float(match.get("confidence", 0))
    direct_bonus = 0.18 if matched_current_query else 0.0
    return round(min(1.0, source_score * 0.55 + source_confidence * 0.35 + direct_bonus), 3)


def _priority(confidence: float, matched_current_query: bool) -> str:
    if matched_current_query:
        return "current-request"
    if confidence >= 0.55:
        return "probable-next"
    return "contextual"


def _priority_rank(priority: str) -> int:
    ranks = {"current-request": 0, "workflow-habit": 1, "probable-next": 2, "contextual": 3}
    return ranks.get(priority, 3)


def _habit_followups(label: str) -> tuple[str, ...]:
    for prefix, followups in HABIT_FOLLOWUPS.items():
        if label.startswith(prefix):
            return followups
    return ()


def _why(intent_id: str, matched_current_query: bool) -> str:
    if matched_current_query:
        return f"Current query directly names a learned follow-up for {intent_id}."
    return f"Historically likely after matched intent {intent_id}."


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]
