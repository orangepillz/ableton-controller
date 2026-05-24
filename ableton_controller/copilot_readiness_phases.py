"""Execution-plan phase gates that affect readiness."""

from __future__ import annotations

from typing import Any


def staged_execution_gate_items(execution_plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return execution-plan gates that must complete before mutating commands."""
    items: list[dict[str, Any]] = []
    for phase in execution_plan.get("phases", []):
        if not isinstance(phase, dict) or phase.get("status") != "before-execution":
            continue
        commands = [str(command) for command in phase.get("commands", []) if str(command).strip()]
        items.append(
            {
                "label": str(phase.get("id", "")),
                "level": "verify-before-execution",
                "why": str(phase.get("why", "")),
                "verify_with": commands[0] if commands else "",
                "commands": commands,
            }
        )
    return items
