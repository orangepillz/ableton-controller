"""Ordered planning summaries for personalized copilot intent results."""

from __future__ import annotations

from typing import Any

from .copilot_active_context import active_matches as select_active_matches
from .copilot_active_context import active_section_labels as select_active_section_labels
from .copilot_capability_gaps import capability_gap_hints
from .copilot_clarification import clarification_policy
from .copilot_command_sources import command_source_summary
from .copilot_execution_plan import execution_plan
from .copilot_followups import likely_followups
from .copilot_macro_preview import macro_plan_previews
from .copilot_macro_preview_cues import macro_action_plan
from .copilot_musical_objectives import musical_objectives
from .copilot_planning_steps import planning_steps_summary
from .copilot_readiness import readiness_summary
from .copilot_recovery import recovery_plan
from .copilot_refinement_strategy import refinement_strategy
from .copilot_term_match import matched_terms
from .copilot_verification import verification_steps
from .copilot_workflow_playbooks import workflow_playbooks_from_habits

def orchestration_summary(query: str, matches: list[dict[str, Any]], profile_hints: dict[str, list[dict[str, Any]]], memory_path=None) -> dict[str, Any]:
    """Combine intent matches and hints into a compact execution-planning cue."""
    revisions = profile_hints.get("revision_requests", [])
    refinement_patterns = profile_hints.get("refinement_patterns", [])
    artist_hints = profile_hints.get("artist_inspiration", [])
    macro_hints = profile_hints.get("workflow_macros", [])
    section_labels = profile_hints.get("section_label_proposals", [])
    target_aliases = _matched_target_aliases(profile_hints.get("target_aliases", []))
    device_chains = _matched_device_chains(profile_hints.get("device_chains", []))
    workflow_habits = _matched_workflow_habits(profile_hints.get("project_workflows", []) + profile_hints.get("chat_workflows", []))
    workflow_playbooks = workflow_playbooks_from_habits(workflow_habits)
    command_sources, suppressed_commands = command_source_summary(query, matches, artist_hints, macro_hints)
    ordered_commands = [entry["command"] for entry in command_sources]
    macro_previews = macro_plan_previews(ordered_commands, memory_path=memory_path, query=query)
    macro_actions = macro_action_plan(macro_previews)
    active_matches = select_active_matches(matches, command_sources)
    followups = likely_followups(active_matches, workflow_habits)
    active_section_labels = select_active_section_labels(section_labels, ordered_commands, active_matches)
    safety_checks = _safety_checks(ordered_commands, query)
    verify_steps = verification_steps(ordered_commands, workflow_playbooks)
    focus_axes = _focus_axes(artist_hints)
    refinement = refinement_strategy(
        revision_requests=revisions,
        refinement_patterns=refinement_patterns,
        ordered_commands=ordered_commands,
        verification_steps=verify_steps,
    )
    clarify_policy = clarification_policy(
        safety_checks=safety_checks,
        target_aliases=target_aliases,
        device_chains=device_chains,
        section_labels=active_section_labels,
        verification_steps=verify_steps,
        refinement_strategy=refinement,
    )
    staged_execution = execution_plan(ordered_commands, verify_steps, clarify_policy, macro_actions)
    recovery = recovery_plan(ordered_commands, verify_steps, safety_checks, staged_execution, macro_actions, clarify_policy)
    objectives = musical_objectives(
        query,
        active_matches,
        focus_axes,
        ordered_commands,
        target_aliases,
        device_chains,
        active_section_labels,
        safety_checks,
        verify_steps,
        workflow_habits,
    )
    readiness = readiness_summary(
        command_sources=command_sources,
        suppressed_commands=suppressed_commands,
        clarification_policy=clarify_policy,
        execution_plan=staged_execution,
        musical_objectives=objectives,
        verification_steps=verify_steps,
        recovery_plan=recovery,
        macro_action_plan=macro_actions,
        workflow_playbooks=workflow_playbooks,
    )
    capability_gaps = capability_gap_hints(
        query=query,
        matches=matches,
        command_sources=command_sources,
        suppressed_commands=suppressed_commands,
        readiness=readiness,
    )
    steps = planning_steps_summary(
        revisions=revisions,
        artist_hints=artist_hints,
        active_matches=active_matches,
        objectives=objectives,
        target_aliases=target_aliases,
        device_chains=device_chains,
        workflow_habits=workflow_habits,
        workflow_playbooks=workflow_playbooks,
        command_sources=command_sources,
        macro_previews=macro_previews,
        active_section_labels=active_section_labels,
        followups=followups,
        suppressed_commands=suppressed_commands,
        safety_checks=safety_checks,
        clarify_policy=clarify_policy,
        verify_steps=verify_steps,
        staged_execution=staged_execution,
        readiness=readiness,
        refinement_strategy=refinement,
        capability_gaps=capability_gaps,
        recovery=recovery,
    )

    return {
        "mode": "revise-current-plan" if revisions else "new-or-continued-plan",
        "focus_axes": focus_axes,
        "musical_objectives": objectives,
        "target_aliases": target_aliases,
        "likely_followups": followups,
        "device_chain_preferences": device_chains,
        "workflow_habits": workflow_habits,
        "workflow_playbooks": workflow_playbooks,
        "safety_checks": safety_checks,
        "verification_steps": verify_steps,
        "macro_plan_previews": macro_previews,
        "macro_action_plan": macro_actions,
        "ordered_commands": ordered_commands,
        "command_sources": command_sources,
        "suppressed_commands": suppressed_commands,
        "clarification_policy": clarify_policy,
        "execution_plan": staged_execution,
        "readiness": readiness,
        "refinement_strategy": refinement,
        "capability_gaps": capability_gaps,
        "recovery_plan": recovery,
        "planning_steps": steps,
        "non_imitation": _non_imitation(artist_hints),
    }


def _focus_axes(artist_hints: list[dict[str, Any]]) -> list[str]:
    axes: list[str] = []
    for hint in artist_hints:
        axes.extend(_as_strings(hint.get("focus_axes")))
    return _dedupe(axes)


def _non_imitation(artist_hints: list[dict[str, Any]]) -> str | None:
    for hint in artist_hints:
        value = hint.get("non_imitation")
        if value:
            return str(value)
    return None


def _matched_target_aliases(target_aliases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched = []
    for alias in target_aliases:
        terms = _as_strings(alias.get("matched_terms"))
        if not terms:
            continue
        matched.append(
            {
                "role": str(alias.get("role", "")),
                "matched_terms": terms,
                "aliases": _as_strings(alias.get("aliases"))[:5],
                "confidence": alias.get("confidence", 0),
            }
        )
    return matched


def _matched_device_chains(device_chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched = []
    for chain in device_chains:
        terms = _as_strings(chain.get("matched_terms"))
        if not terms:
            continue
        matched.append(
            {
                "id": str(chain.get("id", "")),
                "label": str(chain.get("label", "")),
                "confidence": chain.get("confidence", 0),
                "matched_terms": terms,
            }
        )
    return matched


def _matched_workflow_habits(workflow_hints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched = []
    for hint in workflow_hints:
        terms = _as_strings(hint.get("matched_terms"))
        if not terms:
            continue
        matched.append(
            {
                "id": str(hint.get("id", "")),
                "label": str(hint.get("label", "")),
                "confidence": hint.get("confidence", 0),
                "matched_terms": terms,
                "hint": str(hint.get("hint", "")),
            }
        )
    return matched


def _safety_checks(commands: list[str], query: str) -> list[dict[str, str]]:
    rules = (
        (
            "resampling-approval",
            "approval-required",
            ("bass-resampling-pass", "resampling"),
            ("resampling", "resample", "print pass", "print", "record"),
            "Render a dry-run plan first; do not record, export, or save without explicit approval.",
        ),
        (
            "locator-renaming-review",
            "review-before-execute",
            ("arrangement-marker-naming", "set-locator"),
            ("marker", "locator", "name", "rename"),
            "Review proposed section names before mutating Arrangement locator state.",
        ),
        (
            "arrangement-automation-range",
            "plan-first",
            ("arrangement-automation-set",),
            ("automation", "automate", "build", "sweep", "ramp", "movement", "resampling", "resample"),
            "Confirm target track, beat range, and clear behavior before writing Arrangement automation.",
        ),
        (
            "routing-change-review",
            "plan-first",
            ("set-routing",),
            ("route", "routing", "resampling", "resample", "print"),
            "Preview routing changes and verify source/destination tracks before execution.",
        ),
        (
            "destructive-edit-approval",
            "approval-required",
            ("delete-", "midi-clear-notes", "midi-replace-notes", "clip-automation-clear", "clip-stock-automation-clear", "--replace"),
            (),
            "Ask for explicit approval before destructive edits or replacement operations.",
        ),
        (
            "direct-lom-approval",
            "approval-required",
            ("lom-set", "lom-call"),
            (),
            "Use direct LOM mutation only after confirming the path and risk.",
        ),
    )
    normalized = [command.lower() for command in commands]
    checks = []
    for label, level, needles, query_terms, hint in rules:
        if any(needle in command for command in normalized for needle in needles) and _query_supports_check(query, query_terms):
            checks.append({"label": label, "level": level, "hint": hint})
    return checks


def _query_supports_check(query: str, terms: tuple[str, ...]) -> bool:
    return not terms or bool(matched_terms(query, list(terms), allow_keyword_overlap=True))


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _dedupe(values) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
