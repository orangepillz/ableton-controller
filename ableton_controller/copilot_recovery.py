"""Recovery checkpoints for copilot execution plans."""

from __future__ import annotations

from typing import Any

from .copilot_macro_blockers import dedupe_items, input_resolution_commands, macro_blocker_items


def recovery_plan(
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
    safety_checks: list[dict[str, str]],
    execution_plan: dict[str, Any],
    macro_action_plan: dict[str, Any] | None = None,
    clarification_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build rollback/recovery hints from planned commands and gates."""
    macro_plan = macro_action_plan or {}
    clarify_policy = clarification_policy or {}
    checkpoints = _checkpoint_commands(ordered_commands, verification_steps, execution_plan)
    stop_conditions = _stop_conditions(safety_checks, macro_plan, clarify_policy)
    post_failure = _post_failure_readbacks(checkpoints, verification_steps)
    resolution_commands = input_resolution_commands(macro_plan)
    next_stop = _next_stop_condition(stop_conditions)
    return {
        "checkpoint_commands": checkpoints,
        "post_failure_readbacks": post_failure,
        "stop_conditions": stop_conditions,
        "next_stop_condition": next_stop,
        "next_stop_summary": _stop_summary(next_stop),
        "input_resolution_commands": resolution_commands,
        "manual_recovery_steps": _manual_recovery_steps(stop_conditions, post_failure, resolution_commands),
        "resume_rule": "Resume from the next phase only after checkpoint/readback state matches the intended edit.",
    }


def _checkpoint_commands(
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
    execution_plan: dict[str, Any],
) -> list[str]:
    commands = ["session-snapshot"]
    for phase in execution_plan.get("phases", []):
        if phase.get("id") in {"inspect-context", "verify-assumptions", "verify-refinement-context"}:
            commands.extend(_as_strings(phase.get("commands")))
    for command in ordered_commands:
        commands.extend(_command_checkpoints(command))
    for step in verification_steps:
        commands.append(str(step.get("command", "")))
    return _dedupe(commands)


def _command_checkpoints(command: str) -> list[str]:
    normalized = command.lower()
    checkpoints = []
    if "arrangement-marker-naming" in normalized or "set-locator" in normalized:
        checkpoints.append("locators")
    if "drum-pad-load" in normalized or "device-add-stock" in normalized:
        checkpoints.append("device-tree")
    if "drum-punch-bus" in normalized or "personalized-space-chain" in normalized or "mix-bus-control" in normalized:
        checkpoints.append("device-tree")
    if "set-stock-control" in normalized or "stock-controls" in normalized:
        checkpoints.append("stock-controls")
    if "midi-" in normalized or "call-response-bass" in normalized:
        checkpoints.append("midi-get-notes")
    if "clip-stock-automation" in normalized or "bass-movement" in normalized:
        checkpoints.append("clip-stock-automation-get")
    if "set-routing" in normalized or "bass-resampling-pass" in normalized or "arrangement-automation-set" in normalized:
        checkpoints.append("session-snapshot")
    return checkpoints


def _stop_conditions(
    safety_checks: list[dict[str, str]],
    macro_action_plan: dict[str, Any],
    clarification_policy: dict[str, Any],
) -> list[dict[str, str]]:
    conditions = [
        {
            "label": "verification-failed",
            "level": "stop-and-readback",
            "why": "Stop if readback probes do not show the intended track, clip, device, routing, or automation state.",
        }
    ]
    for check in safety_checks:
        level = str(check.get("level", ""))
        if level in {"approval-required", "review-before-execute", "plan-first"}:
            conditions.append(
                {
                    "label": str(check.get("label", "")),
                    "level": level,
                    "why": str(check.get("hint", "")),
                }
            )
    conditions.extend(_refinement_stop_conditions(clarification_policy))
    conditions.extend(macro_blocker_items(macro_action_plan))
    return dedupe_items(conditions)


def _refinement_stop_conditions(clarification_policy: dict[str, Any]) -> list[dict[str, str]]:
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


def _post_failure_readbacks(checkpoints: list[str], verification_steps: list[dict[str, str]]) -> list[str]:
    commands = ["session-snapshot", *checkpoints]
    commands.extend(str(step.get("command", "")) for step in verification_steps)
    return _dedupe([command for command in commands if command])


def _next_stop_condition(stop_conditions: list[dict[str, str]]) -> dict[str, str] | None:
    for condition in stop_conditions:
        if condition.get("level") != "stop-and-readback":
            return condition
    return stop_conditions[0] if stop_conditions else None


def _stop_summary(condition: dict[str, str] | None) -> str | None:
    if not condition:
        return None
    label = str(condition.get("label", ""))
    level = str(condition.get("level", ""))
    command = str(condition.get("resolution_command") or condition.get("verify_with") or "")
    suffix = f" via {command}" if command else ""
    return f"{level}: {label}{suffix}"


def _manual_recovery_steps(
    stop_conditions: list[dict[str, str]],
    post_failure: list[str],
    input_resolution_commands: list[str],
) -> list[dict[str, str]]:
    steps = [
        {
            "label": "stop-sequence",
            "why": "Do not continue later execution phases after a failed command or unexpected readback.",
        },
        {
            "label": "refresh-state",
            "why": f"Run recovery readbacks before the next edit: {', '.join(post_failure[:4])}.",
        },
    ]
    if any(condition.get("level") == "approval-required" for condition in stop_conditions):
        steps.append(
            {
                "label": "approval-recovery",
                "why": "For approval-gated edits, do not record, export, save, or continue until the user approves the revised plan.",
            }
        )
    if any(condition.get("level") == "review-before-execute" for condition in stop_conditions):
        steps.append(
            {
                "label": "review-recovery",
                "why": "For review-gated edits, re-render the plan and compare it with checkpoint readbacks before applying changes.",
            }
        )
    if any(condition.get("level") == "inputs-required" for condition in stop_conditions):
        command_phrase = f": {', '.join(input_resolution_commands[:4])}" if input_resolution_commands else ""
        steps.append(
            {
                "label": "input-recovery",
                "why": f"Resolve required macro inputs from concrete browser-search results{command_phrase} before resuming mutating commands.",
            }
        )
    if any(condition.get("level") == "verify-before-execution" for condition in stop_conditions):
        steps.append(
            {
                "label": "verification-gate-recovery",
                "why": "Run the required verification readback before resuming mutating commands or asking broad setup questions.",
            }
        )
    return steps


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
