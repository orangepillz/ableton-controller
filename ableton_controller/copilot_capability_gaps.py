"""Request-level capability gap hints for copilot planning."""

from __future__ import annotations

import re
from typing import Any


def capability_gap_hints(
    *,
    query: str,
    matches: list[dict[str, Any]],
    command_sources: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
    readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    """Explain weak plan support that should feed future CLI or memory work."""
    gaps: list[dict[str, Any]] = []
    if _has_only_baseline(command_sources) and not matches and not _has_verification_requirement(readiness):
        gaps.append(_missing_intent_gap(query))
    if readiness.get("status") == "under-supported":
        gaps.append(_under_supported_gap(query, command_sources, suppressed_commands))
    if readiness.get("status") in {"verify-assumptions", "verify-execution-context"}:
        gaps.append(_verification_gate_gap(readiness))
    if readiness.get("status") == "inputs-required":
        gaps.append(_macro_input_gap(readiness))
    if readiness.get("status") == "approval-required":
        gaps.append(_approval_gate_gap(readiness))
    if readiness.get("status") == "preview-required":
        gaps.append(_preview_gate_gap(readiness))
    gaps.extend(_suppressed_command_gaps(suppressed_commands))
    if readiness.get("status") == "ready-to-render" and not readiness.get("can_execute_mutations_now"):
        gaps.append(_macro_render_gap(command_sources))
    return _dedupe_gaps(gaps)


def _missing_intent_gap(query: str) -> dict[str, Any]:
    return {
        "id": "missing-personal-intent",
        "type": "personalization-gap",
        "priority": "high",
        "confidence": 0.72,
        "why": "No active personalized intent mapping or reusable workflow supported this request beyond baseline inspection.",
        "expected_impact": "Future runs can learn this phrasing and reduce broad clarification for the same workflow.",
        "next_action": "Capture this query as candidate chat evidence or add a focused intent mapping after the workflow is understood.",
        "evidence": {"query": query, "matched_intent_count": 0, "command_support": ["session-snapshot"]},
    }


def _under_supported_gap(
    query: str,
    command_sources: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": "under-supported-plan",
        "type": "planning-support-gap",
        "priority": "high",
        "confidence": 0.66,
        "why": "The planner found learned hints but not enough executable support for a deterministic Ableton plan.",
        "expected_impact": "Improves reliability by preventing weak plans from becoming broad or risky edits.",
        "next_action": "Ask one focused clarification or collect stronger current-set evidence before adding a macro or command.",
        "evidence": {
            "query": query,
            "command_count": len(command_sources),
            "suppressed_count": len(suppressed_commands),
        },
    }


def _verification_gate_gap(readiness: dict[str, Any]) -> dict[str, Any]:
    required = [
        item
        for item in readiness.get("required_before_execution", [])
        if str(item.get("level", "")) == "verify-before-execution"
    ]
    labels = [str(item.get("label", "")) for item in required if item.get("label")]
    commands = [
        str(item.get("verify_with", ""))
        for item in required
        if str(item.get("verify_with", "")).strip()
    ]
    return {
        "id": "verification-before-execution",
        "type": "current-set-evidence-gap",
        "priority": "medium",
        "confidence": 0.62,
        "why": "The planner has enough context to avoid broad clarification, but it must verify current-set assumptions before execution.",
        "expected_impact": "Keeps iterative and personalized workflows deterministic by turning uncertainty into explicit readback commands.",
        "next_action": "Run the required readback command(s) before asking broad setup questions or executing mutations.",
        "evidence": {
            "required_labels": labels,
            "readback_commands": _dedupe(commands),
            "next_required_summary": readiness.get("next_required_summary"),
        },
    }


def _macro_input_gap(readiness: dict[str, Any]) -> dict[str, Any]:
    required = [
        item
        for item in readiness.get("required_before_execution", [])
        if str(item.get("level", "")) == "inputs-required"
    ]
    return {
        "id": "macro-inputs-before-execution",
        "type": "workflow-input-gap",
        "priority": "high",
        "confidence": 0.68,
        "why": "A reusable macro plan is available, but concrete placeholder inputs must be resolved before mutating Ableton state.",
        "expected_impact": "Turns blocked macro execution into deterministic sample/search work instead of broad clarification.",
        "next_action": "Resolve the required macro inputs with the listed browser-search command(s), then re-render or adapt the macro plan.",
        "evidence": {
            "required_inputs": [str(item.get("label", "")) for item in required if item.get("label")],
            "search_queries": _dedupe([str(item.get("search_query", "")) for item in required if str(item.get("search_query", "")).strip()]),
            "resolution_commands": _dedupe([str(item.get("resolution_command", "")) for item in required if str(item.get("resolution_command", "")).strip()]),
            "next_required_summary": readiness.get("next_required_summary"),
        },
    }


def _approval_gate_gap(readiness: dict[str, Any]) -> dict[str, Any]:
    required = _gate_items(readiness, {"approval-required", "plan-first", "review-before-execute"})
    return {
        "id": "approval-before-execution",
        "type": "execution-safety-gap",
        "priority": "high",
        "confidence": 0.7,
        "why": "The request has executable support, but approval-level Ableton mutations must be explicitly authorized first.",
        "expected_impact": "Prevents risky resampling, destructive, routing, or direct Live Object Model workflows from bypassing review.",
        "next_action": "Present the listed gate(s), get explicit approval for approval-required items, then rerender or execute the reviewed plan.",
        "evidence": _gate_evidence(readiness, required),
    }


def _preview_gate_gap(readiness: dict[str, Any]) -> dict[str, Any]:
    required = _gate_items(readiness, {"plan-first", "review-before-execute", "review-required"})
    return {
        "id": "preview-before-execution",
        "type": "execution-review-gap",
        "priority": "medium",
        "confidence": 0.64,
        "why": "The planner can continue, but it should present a preview for review before mutating Ableton state.",
        "expected_impact": "Turns review-only blockers into concrete preview work, reducing unnecessary broad clarification.",
        "next_action": "Render or present the listed preview gate(s), resolve review feedback, then execute only the approved command sequence.",
        "evidence": _gate_evidence(readiness, required),
    }


def _suppressed_command_gaps(suppressed_commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for command in suppressed_commands:
        reason = str(command.get("reason", ""))
        if reason in {"meta-command", "weak-generic-match"}:
            continue
        gaps.append(
            {
                "id": f"suppressed-command-{_slug(str(command.get('command', '')))}",
                "type": "query-support-gap",
                "priority": "medium",
                "confidence": _confidence(command),
                "why": str(command.get("why", "")),
                "expected_impact": "Keeps learned workflows available without silently planning unsupported edits.",
                "next_action": _suppressed_next_action(reason),
                "evidence": {
                    "command": str(command.get("command", "")),
                    "reason": reason,
                    "source_types": _source_types(command),
                },
            }
        )
    return gaps


def _macro_render_gap(command_sources: list[dict[str, Any]]) -> dict[str, Any]:
    macros = [
        str(entry.get("command", ""))
        for entry in command_sources
        if str(entry.get("command", "")).startswith("workflow-macro render ")
    ]
    return {
        "id": "macro-render-before-execution",
        "type": "workflow-orchestration-gap",
        "priority": "low",
        "confidence": 0.54,
        "why": "The request is supported by reusable macro rendering, but exact mutating commands still need to be materialized before execution.",
        "expected_impact": "Repeated macro-only requests can become faster if future runs promote common rendered plans into richer orchestration.",
        "next_action": "Render the macro plan and compare repeated outcomes before adding a direct command path.",
        "evidence": {"macro_commands": macros[:4]},
    }


def _suppressed_next_action(reason: str) -> str:
    if reason == "query-mismatch":
        return "Ask a focused clarification or require explicit query terms before enabling this learned operation."
    return "Inspect the suppressed command source before turning it into an executable plan."


def _has_only_baseline(command_sources: list[dict[str, Any]]) -> bool:
    return [str(entry.get("command", "")) for entry in command_sources] == ["session-snapshot"]


def _has_verification_requirement(readiness: dict[str, Any]) -> bool:
    return any(
        str(item.get("level", "")) == "verify-before-execution"
        for item in readiness.get("required_before_execution", [])
    )


def _source_types(command: dict[str, Any]) -> list[str]:
    return _dedupe([str(source.get("type", "")) for source in command.get("sources", []) if source.get("type")])


def _gate_items(readiness: dict[str, Any], levels: set[str]) -> list[dict[str, Any]]:
    return [
        item
        for item in readiness.get("required_before_execution", [])
        if str(item.get("level", "")) in levels
    ]


def _gate_evidence(readiness: dict[str, Any], required: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "required_labels": [str(item.get("label", "")) for item in required if item.get("label")],
        "required_levels": _dedupe([str(item.get("level", "")) for item in required if item.get("level")]),
        "macros": _dedupe([str(item.get("macro", "")) for item in required if str(item.get("macro", "")).strip()]),
        "gate_labels": readiness.get("gate_labels", []),
        "next_required_summary": readiness.get("next_required_summary"),
    }


def _confidence(command: dict[str, Any]) -> float:
    try:
        return round(float(command.get("confidence", 0)), 3)
    except (TypeError, ValueError):
        return 0.0


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def _dedupe_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for gap in gaps:
        gap_id = gap.get("id")
        if gap_id and gap_id not in seen:
            seen.add(gap_id)
            result.append(gap)
    return result


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
