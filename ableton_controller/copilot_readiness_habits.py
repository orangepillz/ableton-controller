"""Workflow habit evidence for readiness summaries."""

from __future__ import annotations

from typing import Any


def workflow_habit_signals(musical_objectives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return unique workflow habit signals surfaced by musical objectives."""
    seen = set()
    habits: list[dict[str, Any]] = []
    for objective in musical_objectives:
        evidence = objective.get("evidence", {})
        if not isinstance(evidence, dict):
            continue
        for habit in evidence.get("workflow_habits", []):
            habit_id = str(habit.get("id", ""))
            label = str(habit.get("label", ""))
            key = habit_id or label
            if not key or key in seen:
                continue
            seen.add(key)
            habits.append({"id": habit_id, "label": label, "confidence": habit.get("confidence", 0)})
    return habits
