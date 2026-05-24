"""Planning-step cues derived from macro plan previews."""

from __future__ import annotations

from typing import Any

from .copilot_macro_blockers import input_resolution_commands, macro_blocker_items


ACTION_RANKS = {
    "ask-approval": 0,
    "collect-inputs": 1,
    "review-plan": 2,
    "adapt-plan": 3,
}


def macro_preview_planning_steps(previews: list[dict[str, Any]]) -> list[str]:
    """Turn rich macro previews into concise orchestration guidance."""
    if not previews:
        return []
    steps = [_shape_step(previews)]
    override_step = _override_step(previews)
    if override_step:
        steps.append(override_step)
    gate_step = _gate_step(previews)
    if gate_step:
        steps.append(gate_step)
    readiness_step = _readiness_step(previews)
    if readiness_step:
        steps.append(readiness_step)
    action_step = _action_step(previews)
    if action_step:
        steps.append(action_step)
    input_step = _input_step(previews)
    if input_step:
        steps.append(input_step)
    sequence_step = _sequence_step(previews)
    if sequence_step:
        steps.append(sequence_step)
    return steps


def macro_action_plan(previews: list[dict[str, Any]]) -> dict[str, Any]:
    """Return structured blocker-first macro action guidance."""
    actions = [_ranked_action(preview, index) for index, preview in enumerate(previews)]
    actions = [action for action in actions if action]
    actions.sort(key=lambda action: (action["rank"], action["source_index"]))
    blocked_actions = [action for action in actions if action["type"] != "adapt-plan"]
    ready_actions = [action for action in actions if action["type"] == "adapt-plan"]
    blocker_details = macro_blocker_items({"actions": blocked_actions})
    return {
        "actions": actions,
        "next_action": actions[0]["type"] if actions else None,
        "next_macro": actions[0]["macro"] if actions else None,
        "blocked": bool(blocked_actions),
        "needs_approval": any(action["type"] == "ask-approval" for action in actions),
        "needs_inputs": any(action["type"] == "collect-inputs" for action in actions),
        "needs_review": any(action["type"] == "review-plan" for action in actions),
        "blocked_count": len(blocked_actions),
        "ready_count": len(ready_actions),
        "first_blocking_reason": _first_blocking_reason(blocked_actions),
        "blocker_details": blocker_details,
        "next_blocker_detail": blocker_details[0] if blocker_details else None,
        "blocker_levels": _dedupe([item["level"] for item in blocker_details]),
        "input_resolution_commands": input_resolution_commands({"actions": blocked_actions}),
        "blocking_macros": [action["macro"] for action in blocked_actions],
        "ready_macros": [action["macro"] for action in ready_actions],
    }


def _ranked_action(preview: dict[str, Any], index: int) -> dict[str, Any] | None:
    action = preview.get("recommended_action")
    if not isinstance(action, dict) or not action.get("type"):
        return None
    result = dict(action)
    result["rank"] = _action_rank(preview)
    result["source_index"] = index
    return result


def _first_blocking_reason(actions: list[dict[str, Any]]) -> str | None:
    for action in actions:
        reasons = action.get("blocking_reasons")
        if isinstance(reasons, list) and reasons:
            return str(reasons[0])
    return None


def _shape_step(previews: list[dict[str, Any]]) -> str:
    labels = ", ".join(f"{preview.get('macro')} ({preview.get('command_count')} commands)" for preview in previews[:3])
    return f"Preview macro plan shape before execution: {labels}."


def _override_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in previews:
        overrides = preview.get("query_overrides")
        if isinstance(overrides, dict) and overrides:
            pairs = ", ".join(f"{key}={value}" for key, value in overrides.items())
            phrases.append(f"{preview.get('macro')} {pairs}")
    return f"Apply explicit macro preview override(s): {'; '.join(phrases[:3])}." if phrases else None


def _gate_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in previews:
        gates = _as_labels(preview.get("execution_gates"))
        if gates:
            label = "approval" if preview.get("approval_required") else "review"
            phrases.append(f"{preview.get('macro')} {label}: {', '.join(gates[:4])}")
    return f"Resolve macro execution gate(s): {'; '.join(phrases[:3])}." if phrases else None


def _readiness_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in previews:
        status = preview.get("execution_status")
        if isinstance(status, dict) and status.get("status"):
            reasons = status.get("blocking_reasons")
            suffix = f" ({', '.join(str(item) for item in reasons[:3])})" if isinstance(reasons, list) and reasons else ""
            phrases.append(f"{preview.get('macro')} {status.get('status')}{suffix}")
    return f"Classify macro execution readiness: {'; '.join(phrases[:3])}." if phrases else None


def _action_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in _action_sorted_previews(previews):
        action = preview.get("recommended_action")
        if not isinstance(action, dict) or not action.get("type"):
            continue
        detail = _action_detail(action)
        suffix = f" ({detail})" if detail else ""
        phrases.append(f"{preview.get('macro')} {action.get('type')}{suffix}")
    return f"Prioritize macro recommended action(s): {'; '.join(phrases[:3])}." if phrases else None


def _action_detail(action: dict[str, Any]) -> str:
    for key in ("required_inputs", "gate_labels", "command_heads", "blocking_reasons"):
        values = action.get(key)
        if isinstance(values, list) and values:
            return ", ".join(str(item) for item in values[:3])
    return str(action.get("priority", ""))


def _action_sorted_previews(previews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [preview for _index, preview in sorted(enumerate(previews), key=lambda item: (_action_rank(item[1]), item[0]))[:3]]


def _action_rank(preview: dict[str, Any]) -> int:
    action = preview.get("recommended_action")
    if not isinstance(action, dict):
        return 99
    return ACTION_RANKS.get(str(action.get("type", "")), 99)


def _input_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in previews:
        required = preview.get("required_inputs")
        labels = [str(item.get("label", "")) for item in required if isinstance(item, dict)] if isinstance(required, list) else []
        if labels:
            heads, queries = _placeholder_context(preview)
            suffix = ""
            if heads:
                suffix += f" for {', '.join(heads[:3])}"
            if queries:
                suffix += f" via browser-search {', '.join(queries[:3])}"
            phrases.append(f"{preview.get('macro')} -> {', '.join(labels[:4])}{suffix}")
    return f"Resolve macro required input(s) before execution: {'; '.join(phrases[:3])}." if phrases else None


def _placeholder_context(preview: dict[str, Any]) -> tuple[list[str], list[str]]:
    placeholders = preview.get("unresolved_placeholders")
    if not isinstance(placeholders, list):
        return [], []
    heads = []
    queries = []
    for placeholder in placeholders:
        if not isinstance(placeholder, dict):
            continue
        heads.append(str(placeholder.get("head", "")))
        for step in placeholder.get("resolve_with", []):
            if isinstance(step, dict):
                queries.append(str(step.get("query", "")))
    return _dedupe(heads), _dedupe(queries)


def _sequence_step(previews: list[dict[str, Any]]) -> str | None:
    phrases = []
    for preview in previews:
        sequence = preview.get("command_sequence_preview")
        heads = [str(step.get("head", "")) for step in sequence[:4] if isinstance(step, dict)] if isinstance(sequence, list) else []
        if heads:
            phrases.append(f"{preview.get('macro')} starts {' -> '.join(heads)}")
    return f"Use macro sequence preview to adapt ordered edits: {'; '.join(phrases[:3])}." if phrases else None


def _as_labels(gates: Any) -> list[str]:
    if not isinstance(gates, list):
        return []
    return [str(gate.get("label", "")) for gate in gates if isinstance(gate, dict) and gate.get("label")]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
