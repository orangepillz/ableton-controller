"""Execution readiness summaries for copilot orchestration."""

from __future__ import annotations

from typing import Any

from .copilot_macro_blockers import dedupe_items, input_resolution_commands, macro_blocker_items, macro_blocker_labels
from .copilot_readiness_habits import workflow_habit_signals
from .copilot_readiness_playbooks import playbook_readiness_bonus, playbook_supporting_signals
from .copilot_readiness_phases import staged_execution_gate_items


def readiness_summary(
    *,
    command_sources: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
    clarification_policy: dict[str, Any],
    execution_plan: dict[str, Any],
    musical_objectives: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
    recovery_plan: dict[str, Any],
    macro_action_plan: dict[str, Any] | None = None,
    workflow_playbooks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize whether a plan can proceed, needs a gate, or lacks support."""
    macro_plan = macro_action_plan or {}
    playbooks = workflow_playbooks or []
    phases = execution_plan.get("phases", [])
    render_commands = _phase_commands(phases, "render-reusable-plans")
    execute_commands = _phase_commands(phases, "execute-edits")
    staged_gates = staged_execution_gate_items(execution_plan)
    status = _status(
        suppressed_commands=suppressed_commands,
        clarification_policy=clarification_policy,
        macro_action_plan=macro_plan,
        render_commands=render_commands,
        execute_commands=execute_commands,
        command_sources=command_sources,
        staged_gates=staged_gates,
    )
    required = _required_before_execution(status, clarification_policy, macro_plan, staged_gates)
    gate_labels = _gate_labels(clarification_policy, macro_plan, staged_gates)
    risk_labels = _risk_labels(clarification_policy, suppressed_commands, macro_plan, staged_gates)
    score = _score(
        status=status,
        command_sources=command_sources,
        suppressed_commands=suppressed_commands,
        musical_objectives=musical_objectives,
        verification_steps=verification_steps,
        recovery_plan=recovery_plan,
        workflow_playbooks=playbooks,
    )
    return {
        "status": status,
        "score": score,
        "can_execute_mutations_now": status == "ready-to-execute",
        "next_action": _next_action(status),
        "next_required_before_execution": required[0] if required else None,
        "next_required_summary": _next_required_summary(required),
        "required_before_execution": required,
        "input_resolution_commands": input_resolution_commands(macro_plan),
        "gate_labels": gate_labels,
        "risk_labels": risk_labels,
        "supporting_signals": _supporting_signals(
            command_sources,
            clarification_policy,
            macro_plan,
            musical_objectives,
            verification_steps,
            recovery_plan,
            playbooks,
        ),
    }


def _status(
    *,
    suppressed_commands: list[dict[str, Any]],
    clarification_policy: dict[str, Any],
    macro_action_plan: dict[str, Any],
    render_commands: list[str],
    execute_commands: list[str],
    command_sources: list[dict[str, Any]],
    staged_gates: list[dict[str, Any]],
) -> str:
    if clarification_policy.get("ask_before_execution") or macro_action_plan.get("needs_approval"):
        return "approval-required"
    if macro_action_plan.get("needs_inputs"):
        return "inputs-required"
    if clarification_policy.get("preview_before_execution") or macro_action_plan.get("needs_review"):
        return "preview-required"
    if clarification_policy.get("verify_before_asking") or _refinement_items(clarification_policy):
        return "verify-assumptions"
    if execute_commands and staged_gates:
        return "verify-execution-context"
    if suppressed_commands and not render_commands and not execute_commands and len(command_sources) <= 1:
        return "under-supported"
    if execute_commands:
        return "ready-to-execute"
    if render_commands:
        return "ready-to-render"
    return "inspect-only"


def _required_before_execution(
    status: str,
    clarification_policy: dict[str, Any],
    macro_action_plan: dict[str, Any],
    staged_gates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    required = macro_blocker_items(macro_action_plan)
    if status == "approval-required":
        return dedupe_items(_policy_items(clarification_policy, "ask_before_execution") + required)
    if status == "preview-required":
        return dedupe_items(_policy_items(clarification_policy, "preview_before_execution") + required)
    if status == "verify-assumptions":
        return dedupe_items(_assumption_items(clarification_policy) + _refinement_items(clarification_policy) + required)
    if status == "verify-execution-context":
        return dedupe_items(staged_gates + required)
    return required


def _policy_items(clarification_policy: dict[str, Any], key: str) -> list[dict[str, str]]:
    return [
        {
            "label": str(item.get("label", "")),
            "level": str(item.get("level", "")),
            "why": str(item.get("why", "")),
        }
        for item in clarification_policy.get(key, [])
    ]


def _assumption_items(clarification_policy: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "label": str(item.get("label", "")),
            "level": "verify-before-execution",
            "why": str(item.get("why", "")),
            "verify_with": str(item.get("verify_with", "")),
            "resolution_command": str(item.get("resolution_command") or item.get("verify_with") or ""),
        }
        for item in clarification_policy.get("verify_before_asking", [])
    ]


def _refinement_items(clarification_policy: dict[str, Any]) -> list[dict[str, str]]:
    context = clarification_policy.get("refinement_context") or {}
    return [
        {
            "label": str(item.get("label", "")),
            "level": "verify-before-execution",
            "why": str(item.get("why", "")),
            "verify_with": str(item.get("command", "")),
        }
        for item in context.get("verification_biases", [])
        if str(item.get("label", "")).strip()
    ]


def _gate_labels(
    clarification_policy: dict[str, Any], macro_action_plan: dict[str, Any], staged_gates: list[dict[str, Any]]
) -> list[str]:
    labels = []
    for key in ("ask_before_execution", "preview_before_execution", "verify_before_asking"):
        labels.extend(str(item.get("label", "")) for item in clarification_policy.get(key, []))
    labels.extend(str(item.get("label", "")) for item in _refinement_items(clarification_policy))
    labels.extend(macro_blocker_labels(macro_action_plan))
    labels.extend(str(item.get("label", "")) for item in staged_gates)
    return _dedupe([label for label in labels if label])


def _risk_labels(
    clarification_policy: dict[str, Any],
    suppressed_commands: list[dict[str, Any]],
    macro_action_plan: dict[str, Any],
    staged_gates: list[dict[str, Any]],
) -> list[str]:
    labels = _gate_labels(clarification_policy, macro_action_plan, staged_gates)
    labels.extend(f"suppressed:{item.get('reason')}" for item in suppressed_commands if item.get("reason"))
    return _dedupe(labels)


def _score(
    *,
    status: str,
    command_sources: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
    musical_objectives: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
    recovery_plan: dict[str, Any],
    workflow_playbooks: list[dict[str, Any]],
) -> float:
    source_confidence = max([float(item.get("confidence", 0)) for item in command_sources] or [0.0])
    objective_bonus = 0.12 if musical_objectives else 0.0
    habit_bonus = min(0.06, 0.02 * len(workflow_habit_signals(musical_objectives)))
    playbook_bonus = playbook_readiness_bonus(workflow_playbooks)
    verification_bonus = 0.1 if verification_steps else 0.0
    recovery_bonus = 0.08 if recovery_plan.get("checkpoint_commands") else 0.0
    status_penalty = {
        "approval-required": 0.28,
        "preview-required": 0.16,
        "inputs-required": 0.22,
        "verify-assumptions": 0.08,
        "verify-execution-context": 0.08,
        "under-supported": 0.35,
    }.get(status, 0.0)
    suppression_penalty = min(0.16, 0.04 * len(suppressed_commands))
    score = source_confidence * 0.55 + objective_bonus + habit_bonus + playbook_bonus + verification_bonus + recovery_bonus
    return round(max(0.0, min(1.0, score - status_penalty - suppression_penalty)), 3)


def _supporting_signals(
    command_sources: list[dict[str, Any]],
    clarification_policy: dict[str, Any],
    macro_action_plan: dict[str, Any],
    musical_objectives: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
    recovery_plan: dict[str, Any],
    workflow_playbooks: list[dict[str, Any]],
) -> dict[str, Any]:
    workflow_habits = workflow_habit_signals(musical_objectives)
    playbooks = playbook_supporting_signals(workflow_playbooks)
    refinement_items = _refinement_items(clarification_policy)
    return {
        "command_count": len(command_sources),
        "max_command_confidence": max([float(item.get("confidence", 0)) for item in command_sources] or [0.0]),
        "macro_blocked_count": int(macro_action_plan.get("blocked_count", 0) or 0),
        "macro_ready_count": int(macro_action_plan.get("ready_count", 0) or 0),
        "objective_ids": [str(item.get("id", "")) for item in musical_objectives],
        "workflow_habit_count": len(workflow_habits),
        "workflow_habits": workflow_habits,
        "workflow_playbook_count": len(playbooks),
        "workflow_playbooks": playbooks,
        "refinement_verification_labels": [str(item.get("label", "")) for item in refinement_items],
        "verification_labels": [str(item.get("label", "")) for item in verification_steps],
        "checkpoint_count": len(recovery_plan.get("checkpoint_commands", [])),
    }


def _next_action(status: str) -> str:
    actions = {
        "approval-required": "Ask for explicit approval before mutating Ableton state.",
        "inputs-required": "Resolve macro placeholder inputs before executing mutating commands.",
        "preview-required": "Render or present the preview gate before execution.",
        "verify-assumptions": "Run readback probes to verify assumptions before executing mutations.",
        "verify-execution-context": "Run staged context readbacks before executing learned workflow edits.",
        "under-supported": "Ask a focused clarification or collect stronger current-set evidence.",
        "ready-to-execute": "Execute the staged mutating commands, then run verification readbacks.",
        "ready-to-render": "Render the reusable macro plan before choosing mutating commands.",
        "inspect-only": "Inspect current Ableton state before planning edits.",
    }
    return actions.get(status, actions["inspect-only"])


def _next_required_summary(required: list[dict[str, str]]) -> str | None:
    if not required:
        return None
    item = required[0]
    label = str(item.get("label", ""))
    level = str(item.get("level", ""))
    command = str(item.get("resolution_command") or item.get("verify_with") or "")
    suffix = f" via {command}" if command else ""
    return f"{level}: {label}{suffix}"


def _phase_commands(phases: list[Any], phase_id: str) -> list[str]:
    for phase in phases:
        if isinstance(phase, dict) and phase.get("id") == phase_id:
            return [str(command) for command in phase.get("commands", []) if str(command).strip()]
    return []


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
