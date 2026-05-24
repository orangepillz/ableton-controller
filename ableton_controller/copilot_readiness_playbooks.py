"""Readiness helpers for personalized workflow playbooks."""

from __future__ import annotations

from typing import Any


def playbook_readiness_bonus(playbooks: list[dict[str, Any]]) -> float:
    """Return a small bounded confidence lift for actionable playbook guidance."""
    return round(min(0.04, 0.015 * len(playbook_supporting_signals(playbooks))), 3)


def playbook_supporting_signals(playbooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals = []
    seen = set()
    for playbook in playbooks:
        playbook_id = str(playbook.get("id", ""))
        if not playbook_id or playbook_id in seen:
            continue
        seen.add(playbook_id)
        signals.append(
            {
                "id": playbook_id,
                "title": str(playbook.get("title", "")),
                "confidence": playbook.get("confidence", 0),
                "first_move": str(playbook.get("first_move", "")),
                "follow_through": str(playbook.get("follow_through", "")),
            }
        )
    return signals
