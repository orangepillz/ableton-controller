"""Clarification policy summaries for copilot orchestration."""

from __future__ import annotations

from typing import Any

from .target_aliases import target_alias_probe_command


def clarification_policy(
    *,
    safety_checks: list[dict[str, str]],
    target_aliases: list[dict[str, Any]],
    device_chains: list[dict[str, Any]],
    section_labels: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
    refinement_strategy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explain when to ask the user versus verify assumptions from Live."""
    refinement = refinement_strategy or {}
    ask_before = [check for check in safety_checks if check.get("level") == "approval-required"]
    preview_first = [check for check in safety_checks if check.get("level") in {"plan-first", "review-before-execute"}]
    assumptions = _assumptions_to_verify(target_aliases, device_chains, section_labels)
    mode = _mode(ask_before, preview_first, assumptions, verification_steps)
    policy = {
        "mode": mode,
        "can_reduce_clarification": bool(assumptions or verification_steps or refinement.get("can_reduce_clarification")) and not ask_before,
        "ask_before_execution": [_safety_item(check) for check in ask_before],
        "preview_before_execution": [_safety_item(check) for check in preview_first],
        "verify_before_asking": assumptions,
        "refinement_context": _refinement_context(refinement),
        "readback_commands": _readback_commands(assumptions, verification_steps, refinement),
        "why": _why(mode, ask_before, assumptions, refinement),
    }
    return policy


def _mode(
    ask_before: list[dict[str, str]],
    preview_first: list[dict[str, str]],
    assumptions: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
) -> str:
    if ask_before:
        return "ask-before-execution"
    if preview_first:
        return "preview-before-execution"
    if assumptions or verification_steps:
        return "verify-then-act"
    return "inspect-first"


def _assumptions_to_verify(
    target_aliases: list[dict[str, Any]],
    device_chains: list[dict[str, Any]],
    section_labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assumptions: list[dict[str, Any]] = []
    if target_aliases:
        labels = [str(alias.get("role", "")) for alias in target_aliases[:3]]
        resolution_command = target_alias_probe_command(target_aliases)
        assumptions.append(
            {
                "label": "matched-target-aliases",
                "confidence": _max_confidence(target_aliases),
                "verify_with": "session-snapshot",
                "resolution_command": resolution_command or "session-snapshot",
                "why": f"Resolve learned target aliases in the current set before asking: {', '.join(labels)}.",
            }
        )
    if device_chains:
        labels = [str(chain.get("label", "")) for chain in device_chains[:3]]
        assumptions.append(
            {
                "label": "matched-device-chain-preferences",
                "confidence": _max_confidence(device_chains),
                "verify_with": "device-tree",
                "why": f"Use matched chain preferences as starts after checking devices: {', '.join(labels)}.",
            }
        )
    if section_labels:
        labels = [str(label.get("label", "")) for label in section_labels[:3]]
        assumptions.append(
            {
                "label": "derived-section-labels",
                "confidence": _max_confidence(section_labels),
                "verify_with": "locators",
                "why": f"Review derived labels against current locator state before asking naming questions: {', '.join(labels)}.",
            }
        )
    return assumptions


def _safety_item(check: dict[str, str]) -> dict[str, str]:
    return {
        "label": str(check.get("label", "")),
        "level": str(check.get("level", "")),
        "why": str(check.get("hint", "")),
    }


def _readback_commands(
    assumptions: list[dict[str, Any]],
    verification_steps: list[dict[str, str]],
    refinement: dict[str, Any],
) -> list[str]:
    seen = set()
    commands = []
    for assumption in assumptions:
        command = str(assumption.get("resolution_command") or assumption.get("verify_with") or "").strip()
        if command and command not in seen:
            seen.add(command)
            commands.append(command)
    for step in verification_steps:
        command = str(step.get("command", "")).strip()
        if command and command not in seen:
            seen.add(command)
            commands.append(command)
    for bias in refinement.get("verification_biases", []):
        command = str(bias.get("command", "")).strip()
        if command and command not in seen:
            seen.add(command)
            commands.append(command)
    return commands


def _refinement_context(refinement: dict[str, Any]) -> dict[str, Any] | None:
    if not refinement:
        return None
    return {
        "mode": str(refinement.get("mode", "")),
        "labels": _refinement_labels(refinement),
        "verification_biases": refinement.get("verification_biases", []),
    }


def _why(
    mode: str,
    ask_before: list[dict[str, str]],
    assumptions: list[dict[str, Any]],
    refinement: dict[str, Any],
) -> str:
    if ask_before:
        labels = ", ".join(str(check.get("label", "")) for check in ask_before)
        return f"Ask only for approval-level risk before execution: {labels}."
    if assumptions:
        labels = ", ".join(str(item.get("label", "")) for item in assumptions)
        return f"Prefer current-set verification over broad clarification: {labels}."
    refinement_labels = _refinement_labels(refinement)
    if refinement_labels:
        return f"Use learned revision context before asking broad setup questions: {', '.join(refinement_labels)}."
    if mode == "verify-then-act":
        return "Use readback probes to confirm touched state before asking broad follow-up questions."
    return "Inspect the current set before deciding whether clarification is necessary."


def _refinement_labels(refinement: dict[str, Any]) -> list[str]:
    labels = []
    for key in ("current_revisions", "historical_patterns"):
        labels.extend(str(item.get("label", "")) for item in refinement.get(key, []) if item.get("label"))
    return _dedupe(labels)


def _max_confidence(items: list[dict[str, Any]]) -> float:
    values = []
    for item in items:
        try:
            values.append(float(item.get("confidence", 0)))
        except (TypeError, ValueError):
            values.append(0.0)
    return round(max(values or [0.0]), 3)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
