"""Shared macro blocker details for readiness and recovery summaries."""

from __future__ import annotations

from typing import Any


LEVEL_RANKS = {
    "approval-required": 0,
    "inputs-required": 1,
    "review-before-execute": 2,
    "review-required": 2,
    "plan-first": 3,
}


def macro_blocker_items(macro_action_plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return deduped non-adapt macro blockers with the most specific detail available."""
    items = []
    for action in macro_action_plan.get("actions", []):
        if not isinstance(action, dict) or action.get("type") == "adapt-plan":
            continue
        items.extend(_action_blockers(action))
    return dedupe_items(items)


def macro_blocker_labels(macro_action_plan: dict[str, Any]) -> list[str]:
    return _dedupe([item["label"] for item in macro_blocker_items(macro_action_plan)])


def input_resolution_commands(macro_action_plan: dict[str, Any]) -> list[str]:
    commands = []
    for action in macro_action_plan.get("actions", []):
        if isinstance(action, dict):
            commands.extend(_as_strings(action.get("input_resolution_commands")))
    return _dedupe(commands)


def dedupe_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for _index, item in sorted(enumerate(items), key=lambda item: _item_rank(item[1], item[0])):
        key = (str(item.get("label", "")), str(item.get("level", "")))
        if key[0] and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _item_rank(item: dict[str, str], index: int) -> tuple[int, int]:
    level = str(item.get("level", ""))
    return LEVEL_RANKS.get(level, 99), index


def _action_blockers(action: dict[str, Any]) -> list[dict[str, str]]:
    details = action.get("required_input_details")
    if isinstance(details, list) and details:
        return [_input_item(action, detail) for detail in details if isinstance(detail, dict) and detail.get("label")]
    gates = action.get("gate_details")
    if isinstance(gates, list) and gates:
        return [_gate_item(action, gate) for gate in gates if isinstance(gate, dict) and gate.get("label")]
    return [_label_item(action, label) for label in _fallback_labels(action)]


def _input_item(action: dict[str, Any], detail: dict[str, Any]) -> dict[str, str]:
    return {
        "label": str(detail.get("label", "")),
        "level": "inputs-required",
        "why": str(detail.get("why") or action.get("why", "")),
        "macro": str(action.get("macro", "")),
        "source": str(detail.get("source", "")),
        "search_query": str(detail.get("search_query", "")),
        "resolution_command": str(detail.get("resolution_command", "")),
    }


def _gate_item(action: dict[str, Any], gate: dict[str, Any]) -> dict[str, str]:
    return {
        "label": str(gate.get("label", "")),
        "level": str(gate.get("level", _fallback_level(str(action.get("type", ""))))),
        "why": str(gate.get("why") or action.get("why", "")),
        "macro": str(action.get("macro", "")),
    }


def _label_item(action: dict[str, Any], label: str) -> dict[str, str]:
    return {
        "label": label,
        "level": _fallback_level(str(action.get("type", ""))),
        "why": str(action.get("why", "")),
        "macro": str(action.get("macro", "")),
    }


def _fallback_labels(action: dict[str, Any]) -> list[str]:
    labels = []
    for key in ("required_inputs", "gate_labels", "blocking_reasons"):
        labels.extend(str(item) for item in action.get(key, []) if str(item).strip())
    return _dedupe(labels)


def _fallback_level(action_type: str) -> str:
    return {
        "ask-approval": "approval-required",
        "collect-inputs": "inputs-required",
        "review-plan": "review-before-execute",
    }.get(action_type, "review-before-execute")


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
