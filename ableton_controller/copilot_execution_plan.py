"""Structured execution phases for copilot orchestration."""

from __future__ import annotations

from typing import Any


READ_ONLY_COMMANDS = {
    "session-snapshot",
    "status",
    "tracks",
    "selected",
    "device-tree",
    "devices",
    "clips",
    "clip-slots",
    "locators",
    "stock-controls",
    "midi-get-notes",
    "clip-stock-automation-get",
    "params",
    "serum-params",
}


def execution_plan(
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
    clarification_policy: dict[str, Any],
    macro_action_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Group ordered command hints into staged execution phases."""
    macro_plan = macro_action_plan or {}
    inspect = [command for command in ordered_commands if _is_read_only(command)]
    render = [command for command in ordered_commands if command.startswith("workflow-macro render ")]
    execute = [command for command in ordered_commands if command not in inspect and command not in render]
    pre_verify_steps = _pre_execution_verification_steps(verification_steps)
    phases = [_phase("inspect-context", "ready", inspect, "Read current Ableton state before planning edits.")]
    if render:
        phases.append(_phase("render-reusable-plans", "ready", render, "Render learned macro plans before adapting edits."))
    phases.extend(_gate_phases(clarification_policy))
    macro_gate = _macro_gate_phase(macro_plan)
    if macro_gate:
        phases.append(macro_gate)
    pre_verify_commands = _verification_commands(pre_verify_steps)
    if pre_verify_commands:
        phases.append(
            _phase(
                "verify-playbook-context",
                "before-execution",
                pre_verify_commands,
                _pre_execution_why(pre_verify_steps),
            )
        )
    if execute:
        phases.append(
            _phase(
                "execute-edits",
                _execute_status(clarification_policy, macro_plan, bool(pre_verify_steps)),
                execute,
                _execute_why(clarification_policy, macro_plan, bool(pre_verify_steps)),
            )
        )
    verify_commands = _verification_commands(_post_execution_verification_steps(verification_steps, pre_verify_steps))
    if verify_commands:
        phases.append(_phase("verify-readback", "after-execution", verify_commands, "Read back touched state after edits."))
    phases = [phase for phase in phases if phase["commands"] or phase["status"] != "ready"]
    next_phase = _next_phase(phases)
    next_gate = _next_gate_phase(phases)
    return {
        "mode": clarification_policy.get("mode", "inspect-first"),
        "requires_approval": bool(clarification_policy.get("ask_before_execution")) or bool(macro_plan.get("needs_approval")),
        "requires_preview": bool(clarification_policy.get("preview_before_execution")) or bool(macro_plan.get("needs_review")),
        "requires_inputs": bool(macro_plan.get("needs_inputs")),
        "next_phase": next_phase,
        "next_phase_summary": _phase_summary(next_phase),
        "next_gate_phase": next_gate,
        "next_gate_summary": _phase_summary(next_gate),
        "phases": phases,
    }


def _gate_phases(clarification_policy: dict[str, Any]) -> list[dict[str, Any]]:
    phases = []
    preview = [str(item.get("label", "")) for item in clarification_policy.get("preview_before_execution", [])]
    approval = [str(item.get("label", "")) for item in clarification_policy.get("ask_before_execution", [])]
    verify = [str(item.get("label", "")) for item in clarification_policy.get("verify_before_asking", [])]
    refinement = clarification_policy.get("refinement_context") or {}
    refinement_biases = _refinement_bias_labels(refinement)
    if verify:
        phases.append(
            _phase(
                "verify-assumptions",
                "before-asking",
                _as_strings(clarification_policy.get("readback_commands")),
                f"Verify personalized assumptions before asking broad questions: {', '.join(verify)}.",
            )
        )
    if refinement_biases:
        phases.append(
            _phase(
                "verify-refinement-context",
                "before-asking",
                _as_strings(clarification_policy.get("readback_commands")),
                f"Verify learned refinement context before asking broad questions: {', '.join(refinement_biases)}.",
            )
        )
    if preview:
        phases.append(_phase("preview-gate", "review-required", [], f"Review before execution: {', '.join(preview)}."))
    if approval:
        phases.append(_phase("approval-gate", "approval-required", [], f"Ask before execution: {', '.join(approval)}."))
    return phases


def _macro_gate_phase(macro_plan: dict[str, Any]) -> dict[str, Any] | None:
    if not macro_plan.get("blocked"):
        return None
    action = str(macro_plan.get("next_action", ""))
    macro = str(macro_plan.get("next_macro", "macro"))
    labels = _macro_blocking_labels(macro_plan)
    detail = f": {', '.join(labels[:4])}" if labels else ""
    phase = {
        "ask-approval": ("macro-approval-gate", "approval-required", "Ask before executing macro"),
        "collect-inputs": ("macro-input-gate", "inputs-required", "Resolve macro input(s) for"),
        "review-plan": ("macro-review-gate", "review-required", "Review macro plan for"),
    }.get(action)
    if not phase:
        return None
    phase_id, status, prefix = phase
    commands = _as_strings(macro_plan.get("input_resolution_commands")) if action == "collect-inputs" else []
    return _phase(phase_id, status, commands, f"{prefix} {macro}{detail}.")


def _phase(phase_id: str, status: str, commands: list[str], why: str) -> dict[str, Any]:
    return {"id": phase_id, "status": status, "commands": _dedupe(commands), "why": why}


def _execute_status(clarification_policy: dict[str, Any], macro_plan: dict[str, Any], needs_pre_verification: bool) -> str:
    if clarification_policy.get("ask_before_execution") or macro_plan.get("needs_approval"):
        return "after-approval"
    if macro_plan.get("needs_inputs"):
        return "after-inputs"
    if clarification_policy.get("preview_before_execution") or macro_plan.get("needs_review"):
        return "after-preview"
    if needs_pre_verification:
        return "after-verification"
    return "ready"


def _execute_why(clarification_policy: dict[str, Any], macro_plan: dict[str, Any], needs_pre_verification: bool) -> str:
    mode = str(clarification_policy.get("mode", "inspect-first"))
    if mode == "ask-before-execution" or macro_plan.get("needs_approval"):
        return "Execute mutating commands only after explicit approval."
    if macro_plan.get("needs_inputs"):
        return "Execute mutating commands only after macro placeholder inputs are resolved."
    if mode == "preview-before-execution":
        return "Execute mutating commands after the preview/review gate."
    if needs_pre_verification:
        return "Execute safe planned edits after learned playbook context is verified."
    return "Execute safe planned edits after read-only inspection."


def _verification_commands(verification_steps: list[dict[str, str]]) -> list[str]:
    return [str(step.get("command", "")) for step in verification_steps if str(step.get("command", "")).strip()]


def _pre_execution_verification_steps(verification_steps: list[dict[str, str]]) -> list[dict[str, str]]:
    return [step for step in verification_steps if _is_pre_execution_playbook_step(step)]


def _post_execution_verification_steps(
    verification_steps: list[dict[str, str]], pre_execution_steps: list[dict[str, str]]
) -> list[dict[str, str]]:
    pre_keys = {_step_key(step) for step in pre_execution_steps}
    return [step for step in verification_steps if _step_key(step) not in pre_keys]


def _is_pre_execution_playbook_step(step: dict[str, str]) -> bool:
    label = str(step.get("label", ""))
    why = str(step.get("why", "")).lower()
    if "after applying" in why or "after writing" in why:
        return False
    return label.startswith("verify-playbook-") or "playbook" in why or "learned" in why


def _step_key(step: dict[str, str]) -> tuple[str, str]:
    return (str(step.get("label", "")), str(step.get("command", "")))


def _pre_execution_why(verification_steps: list[dict[str, str]]) -> str:
    labels = [str(step.get("label", "")) for step in verification_steps if str(step.get("label", "")).strip()]
    label_suffix = f": {', '.join(labels[:4])}" if labels else ""
    return f"Verify learned workflow playbook context before executing edits{label_suffix}."


def _next_phase(phases: list[dict[str, Any]]) -> dict[str, Any] | None:
    statuses = {"ready", "before-asking", "before-execution", "review-required", "approval-required", "inputs-required"}
    for phase in phases:
        if phase.get("status") in statuses:
            return phase
    return phases[0] if phases else None


def _next_gate_phase(phases: list[dict[str, Any]]) -> dict[str, Any] | None:
    gate_statuses = {"before-asking", "before-execution", "review-required", "approval-required", "inputs-required"}
    for phase in phases:
        if phase.get("status") in gate_statuses:
            return phase
    return None


def _phase_summary(phase: dict[str, Any] | None) -> str | None:
    if not phase:
        return None
    commands = _as_strings(phase.get("commands"))
    command_suffix = f" -> {', '.join(commands[:3])}" if commands else ""
    return f"{phase.get('status')}: {phase.get('id')}{command_suffix}"


def _is_read_only(command: str) -> bool:
    head = command.strip().split(maxsplit=1)[0]
    return head in READ_ONLY_COMMANDS


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _macro_blocking_labels(macro_plan: dict[str, Any]) -> list[str]:
    labels = []
    for action in macro_plan.get("actions", []):
        if not isinstance(action, dict) or action.get("type") == "adapt-plan":
            continue
        labels.extend(_as_strings(action.get("required_inputs")))
        labels.extend(_as_strings(action.get("gate_labels")))
        labels.extend(_as_strings(action.get("blocking_reasons")))
    return _dedupe(labels)


def _refinement_bias_labels(refinement_context: dict[str, Any]) -> list[str]:
    return [
        str(item.get("label", ""))
        for item in refinement_context.get("verification_biases", [])
        if str(item.get("label", "")).strip()
    ]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
