"""Recommended next actions for rendered workflow macro previews."""

from __future__ import annotations

from typing import Any


def macro_recommended_action(
    macro: str,
    execution_status: dict[str, Any],
    *,
    required_inputs: list[dict[str, str]],
    execution_gates: list[dict[str, str]],
    command_sequence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a structured planner action from a macro execution status."""
    status = str(execution_status.get("status", ""))
    if status == "approval-required":
        return _action("ask-approval", macro, "high", execution_status, gate_labels=execution_gates)
    if status == "inputs-required":
        return _action("collect-inputs", macro, "high", execution_status, input_labels=required_inputs)
    if status == "review-required":
        return _action("review-plan", macro, "medium", execution_status, gate_labels=execution_gates)
    return _action("adapt-plan", macro, "normal", execution_status, command_heads=command_sequence)


def _action(
    action_type: str,
    macro: str,
    priority: str,
    execution_status: dict[str, Any],
    *,
    gate_labels: list[dict[str, str]] | None = None,
    input_labels: list[dict[str, str]] | None = None,
    command_heads: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "type": action_type,
        "macro": macro,
        "priority": priority,
        "status": str(execution_status.get("status", "")),
        "blocking_reasons": list(execution_status.get("blocking_reasons", [])),
        "gate_labels": [str(item.get("label", "")) for item in gate_labels or [] if item.get("label")],
        "gate_details": _gate_details(gate_labels or []),
        "required_inputs": [str(item.get("label", "")) for item in input_labels or [] if item.get("label")],
        "required_input_details": _input_details(input_labels or []),
        "input_resolution_commands": _input_resolution_commands(input_labels or []),
        "command_heads": _sequence_heads(command_heads or []),
        "why": str(execution_status.get("next_action", "")),
    }


def _gate_details(gate_labels: list[dict[str, str]]) -> list[dict[str, str]]:
    details = []
    for item in gate_labels:
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        details.append(
            {
                "label": label,
                "level": str(item.get("level", "")),
                "why": str(item.get("why", "")),
            }
        )
    return details


def _input_details(input_labels: list[dict[str, str]]) -> list[dict[str, str]]:
    details = []
    for item in input_labels:
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        details.append(
            {
                "label": label,
                "source": str(item.get("source", "")),
                "search_query": str(item.get("search_query", "")),
                "resolution_command": str(item.get("resolution_command", "")),
                "why": str(item.get("why", "")),
            }
        )
    return details


def _input_resolution_commands(input_labels: list[dict[str, str]]) -> list[str]:
    commands = []
    for item in input_labels:
        command = str(item.get("resolution_command", "")).strip()
        if command:
            commands.append(command)
    return _dedupe(commands)


def _sequence_heads(sequence: list[dict[str, Any]]) -> list[str]:
    heads = []
    for item in sequence:
        if not item.get("read_only"):
            heads.append(str(item.get("head", "")))
        if len(heads) >= 4:
            break
    return [head for head in heads if head]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
