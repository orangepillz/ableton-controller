"""Execution status classification for rendered workflow macro previews."""

from __future__ import annotations

from typing import Any


def macro_execution_status(gates: list[dict[str, str]], placeholders: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize whether a rendered macro preview needs inputs, review, or approval."""
    if _has_level(gates, "approval-required"):
        return _status(
            "approval-required",
            "Ask for explicit approval before executing the rendered macro plan.",
            _gate_labels(gates, level="approval-required"),
        )
    if placeholders:
        return _status(
            "inputs-required",
            "Resolve placeholder inputs from browser-search results before executing the rendered macro plan.",
            _placeholder_labels(placeholders),
        )
    if gates:
        return _status(
            "review-required",
            "Review the rendered macro plan and verify targets before execution.",
            _gate_labels(gates),
        )
    return _status(
        "ready-to-adapt",
        "Render or adapt the macro plan, then verify touched Ableton state.",
        [],
    )


def _status(status: str, next_action: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "status": status,
        "can_adapt_without_extra_input": status == "ready-to-adapt",
        "blocking_reasons": reasons,
        "next_action": next_action,
    }


def _has_level(gates: list[dict[str, str]], level: str) -> bool:
    return any(gate.get("level") == level for gate in gates)


def _gate_labels(gates: list[dict[str, str]], level: str | None = None) -> list[str]:
    labels = []
    for gate in gates:
        if level is not None and gate.get("level") != level:
            continue
        label = gate.get("label")
        if label:
            labels.append(label)
    return _dedupe(labels)


def _placeholder_labels(placeholders: list[dict[str, Any]]) -> list[str]:
    labels = []
    for placeholder in placeholders:
        labels.extend(str(item) for item in placeholder.get("placeholders", []))
    return _dedupe(labels)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
