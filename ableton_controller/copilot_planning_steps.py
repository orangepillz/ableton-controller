"""Human-readable planning steps for copilot orchestration."""

from __future__ import annotations

from typing import Any

from .copilot_macro_preview_cues import macro_preview_planning_steps
from .target_aliases import target_alias_probe_command


def planning_steps_summary(
    *,
    revisions: list[dict[str, Any]],
    artist_hints: list[dict[str, Any]],
    active_matches: list[dict[str, Any]],
    objectives: list[dict[str, Any]],
    target_aliases: list[dict[str, Any]],
    device_chains: list[dict[str, Any]],
    workflow_habits: list[dict[str, Any]],
    workflow_playbooks: list[dict[str, Any]],
    command_sources: list[dict[str, Any]],
    macro_previews: list[dict[str, Any]],
    active_section_labels: list[dict[str, Any]],
    followups: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
    safety_checks: list[dict[str, str]],
    clarify_policy: dict[str, Any],
    verify_steps: list[dict[str, str]],
    staged_execution: dict[str, Any],
    readiness: dict[str, Any],
    refinement_strategy: dict[str, Any],
    capability_gaps: list[dict[str, Any]],
    recovery: dict[str, Any],
) -> list[str]:
    """Build ordered planning steps from already-computed orchestration state."""
    steps: list[str] = []
    if revisions:
        labels = ", ".join(str(item.get("label", "")) for item in revisions if item.get("label"))
        steps.append(f"Treat the message as a revision to the current plan: {labels}.")
    if refinement_strategy.get("planning_biases"):
        bias = "; ".join(_sentence_fragment(item) for item in refinement_strategy["planning_biases"][:3])
        steps.append(f"Apply learned refinement strategy: {bias}.")
    if refinement_strategy.get("verification_biases"):
        labels = ", ".join(str(item.get("label", "")) for item in refinement_strategy["verification_biases"][:3])
        steps.append(f"Apply refinement verification bias: {labels}.")
    for hint in artist_hints:
        steps.append(f"Translate the reference into original production constraints: {hint.get('translate_to')}")
    if active_matches:
        bias = active_matches[0].get("planning_bias") or f"Use mapped intent {active_matches[0].get('id')}."
        steps.append(str(bias))
    if objectives:
        labels = ", ".join(str(item.get("id", "")) for item in objectives[:3])
        steps.append(f"Aim edits at explicit musical objective(s): {labels}.")
    if target_aliases:
        command = target_alias_probe_command(target_aliases)
        suffix = f" Use {command}." if command else ""
        steps.append(
            f"Resolve matched personal target aliases with current-set inspection: {_target_alias_phrase(target_aliases)}.{suffix}"
        )
    if device_chains:
        labels = ", ".join(str(chain.get("label", "")) for chain in device_chains[:3])
        steps.append(f"Use matched learned device-chain preferences as starting points: {labels}.")
    if workflow_habits:
        labels = ", ".join(str(habit.get("label", "")) for habit in workflow_habits[:3])
        steps.append(f"Use matched historical workflow habits as planning bias: {labels}.")
    if workflow_playbooks:
        steps.extend(_workflow_playbook_steps(workflow_playbooks))
    macro_commands = _commands_from_source_type(command_sources, "workflow_macro")
    if macro_commands:
        steps.append(f"Render and adapt reusable macro plan(s): {', '.join(macro_commands[:3])}.")
    steps.extend(macro_preview_planning_steps(macro_previews))
    if active_section_labels:
        labels = ", ".join(f"beat {hint.get('beat'):g}: {hint.get('label')}" for hint in active_section_labels[:3])
        steps.append(f"Use derived section label proposals before mutating arrangement anchors: {labels}.")
    if followups:
        labels = ", ".join(_followup_phrase(item) for item in followups[:4])
        steps.append(f"Anticipate likely follow-up operations: {labels}.")
    if command_sources:
        labels = ", ".join(str(item.get("command", "")) for item in command_sources[:4])
        steps.append(f"Use auditable command-source ordering: {labels}.")
    if suppressed_commands:
        labels = ", ".join(str(item.get("command", "")) for item in suppressed_commands[:4])
        steps.append(f"Suppress learned commands that need clearer current-query support: {labels}.")
    if safety_checks:
        labels = ", ".join(str(item.get("label", "")) for item in safety_checks)
        steps.append(f"Apply safety checks before execution: {labels}.")
    if clarify_policy.get("verify_before_asking"):
        labels = ", ".join(str(item.get("label", "")) for item in clarify_policy["verify_before_asking"])
        steps.append(f"Verify personalized assumptions before asking broad clarification: {labels}.")
    if clarify_policy.get("ask_before_execution"):
        labels = ", ".join(str(item.get("label", "")) for item in clarify_policy["ask_before_execution"])
        steps.append(f"Ask only for approval-level execution risks: {labels}.")
    if verify_steps:
        labels = ", ".join(str(item.get("command", "")) for item in verify_steps[:4])
        steps.append(f"Verify with readback probes: {labels}.")
    if staged_execution.get("phases"):
        phase_labels = ", ".join(str(phase.get("id", "")) for phase in staged_execution["phases"][:5])
        steps.append(f"Follow staged execution phases: {phase_labels}.")
    _append_next_step_summaries(steps, staged_execution, readiness, recovery)
    if capability_gaps:
        labels = ", ".join(str(item.get("id", "")) for item in capability_gaps[:3])
        steps.append(f"Track request-level capability gaps: {labels}.")
    if recovery.get("checkpoint_commands"):
        labels = ", ".join(str(command) for command in recovery["checkpoint_commands"][:4])
        steps.append(f"Capture recovery checkpoints before mutating edits: {labels}.")
    steps.append("Verify touched tracks, clips, devices, or automation after the planned edits.")
    return steps


def _append_next_step_summaries(
    steps: list[str],
    staged_execution: dict[str, Any],
    readiness: dict[str, Any],
    recovery: dict[str, Any],
) -> None:
    if staged_execution.get("next_phase_summary"):
        steps.append(f"Start with execution phase: {staged_execution['next_phase_summary']}.")
    if staged_execution.get("next_gate_summary"):
        steps.append(f"Respect next execution gate: {staged_execution['next_gate_summary']}.")
    steps.append(f"Check execution readiness: {readiness['status']} ({readiness['score']}).")
    habit_labels = _readiness_workflow_habit_labels(readiness)
    if habit_labels:
        steps.append(f"Treat readiness confidence as personalized by workflow habit evidence: {', '.join(habit_labels[:3])}.")
    if readiness.get("next_required_summary"):
        steps.append(f"Resolve next readiness requirement: {readiness['next_required_summary']}.")
    if recovery.get("next_stop_summary"):
        steps.append(f"Use recovery stop priority: {recovery['next_stop_summary']}.")


def _commands_from_source_type(command_sources: list[dict[str, Any]], source_type: str) -> list[str]:
    return [
        str(entry.get("command", ""))
        for entry in command_sources
        if any(source.get("type") == source_type for source in entry.get("sources", []))
    ]


def _workflow_playbook_steps(workflow_playbooks: list[dict[str, Any]]) -> list[str]:
    steps = []
    for playbook in workflow_playbooks[:2]:
        steps.append(
            "Apply personalized workflow playbook "
            f"{playbook.get('id')}: {playbook.get('first_move')} "
            f"Follow-through: {playbook.get('follow_through')}"
        )
    return steps


def _followup_phrase(followup: dict[str, Any]) -> str:
    return f"{followup.get('label')} ({followup.get('priority')}, {followup.get('confidence')})"


def _target_alias_phrase(target_aliases: list[dict[str, Any]]) -> str:
    parts = []
    for alias in target_aliases[:3]:
        preferred = ", ".join(_as_strings(alias.get("aliases"))[:3])
        matched = ", ".join(_as_strings(alias.get("matched_terms")))
        parts.append(f"{alias.get('role')} from {matched} -> {preferred}")
    return "; ".join(parts)


def _readiness_workflow_habit_labels(readiness: dict[str, Any]) -> list[str]:
    supporting = readiness.get("supporting_signals", {})
    if not isinstance(supporting, dict):
        return []
    return [
        str(habit.get("label", ""))
        for habit in supporting.get("workflow_habits", [])
        if str(habit.get("label", "")).strip()
    ]


def _sentence_fragment(value: Any) -> str:
    return str(value).strip().rstrip(".")


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]
