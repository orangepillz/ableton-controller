"""Shared helpers for musical objective planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .copilot_term_match import matched_terms


@dataclass(frozen=True)
class PlanningContext:
    query: str
    matches: list[dict[str, Any]]
    focus_axes: list[str]
    ordered_commands: list[str]
    target_aliases: list[dict[str, Any]]
    device_chains: list[dict[str, Any]]
    section_labels: list[dict[str, Any]]
    safety_checks: list[dict[str, str]]
    verification_steps: list[dict[str, str]]
    workflow_habits: list[dict[str, Any]]

    @property
    def command_text(self) -> str:
        return " ".join(self.ordered_commands).lower()

    @property
    def match_ids(self) -> list[str]:
        return [str(match.get("id", "")) for match in self.matches if match.get("id")]

    @property
    def safety_labels(self) -> set[str]:
        return {str(check.get("label", "")) for check in self.safety_checks}

    @property
    def verification_labels(self) -> set[str]:
        return {str(step.get("label", "")) for step in self.verification_steps}


def add_if_supported(
    objectives: list[dict[str, Any]],
    candidate: dict[str, Any] | None,
    context: PlanningContext,
) -> None:
    if candidate is None or any(item["id"] == candidate["id"] for item in objectives):
        return
    candidate["rank"] = len(objectives) + 1
    candidate["confidence"] = confidence(context, tuple(candidate.pop("_intent_ids")), candidate["id"])
    objectives.append(candidate)


def objective(
    context: PlanningContext,
    objective_id: str,
    goal: str,
    success_criteria: list[str],
    constraints: list[str],
    axes: list[str],
    intent_ids: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "id": objective_id,
        "goal": goal,
        "focus_axes": focus_axes(context.focus_axes, axes),
        "success_criteria": dedupe([*success_criteria, *habit_success_criteria(context, objective_id)]),
        "constraints": dedupe([*constraints, *habit_constraints(context, objective_id)]),
        "evidence": evidence(context, intent_ids, objective_id),
        "_intent_ids": intent_ids,
    }


def has_any(context: PlanningContext, terms: tuple[str, ...]) -> bool:
    if any(term in context.command_text for term in terms):
        return True
    if any(term in context.match_ids for term in terms):
        return True
    return bool(matched_terms(context.query, list(terms), allow_keyword_overlap=True))


def confidence(context: PlanningContext, intent_ids: tuple[str, ...], objective_id: str) -> float:
    values = [
        float(match.get("confidence", 0))
        for match in context.matches
        if str(match.get("id", "")) in intent_ids
    ]
    base = max(values) if values else 0.52
    if context.verification_steps:
        base += 0.05
    if context.safety_checks:
        base += 0.03
    if context.focus_axes:
        base += 0.03
    if matching_workflow_habits(context, objective_id):
        base += 0.04
    return round(min(base, 0.95), 3)


def evidence(context: PlanningContext, intent_ids: tuple[str, ...], objective_id: str) -> dict[str, Any]:
    commands = [
        command
        for command in context.ordered_commands
        if command_matches(command, intent_ids, objective_id) or command == "session-snapshot"
    ][:5]
    payload: dict[str, Any] = {
        "matched_intents": [intent_id for intent_id in context.match_ids if intent_id in intent_ids],
        "commands": commands,
        "verification_labels": sorted(context.verification_labels),
    }
    if context.safety_labels:
        payload["safety_labels"] = sorted(context.safety_labels)
    if context.device_chains:
        payload["device_chain_ids"] = [str(chain.get("id", "")) for chain in context.device_chains[:3]]
    habits = matching_workflow_habits(context, objective_id)
    if habits:
        payload["workflow_habits"] = [
            {
                "id": str(habit.get("id", "")),
                "label": str(habit.get("label", "")),
                "confidence": habit.get("confidence", 0),
            }
            for habit in habits[:3]
        ]
    return payload


def matching_workflow_habits(context: PlanningContext, objective_id: str) -> list[dict[str, Any]]:
    terms = _HABIT_TERMS_BY_OBJECTIVE.get(objective_id, ())
    if not terms:
        return []
    return [
        habit
        for habit in context.workflow_habits
        if _habit_matches(habit, terms)
    ]


def habit_success_criteria(context: PlanningContext, objective_id: str) -> list[str]:
    if not matching_workflow_habits(context, objective_id):
        return []
    criteria = _HABIT_CRITERIA.get(objective_id)
    return [criteria] if criteria else []


def habit_constraints(context: PlanningContext, objective_id: str) -> list[str]:
    if not matching_workflow_habits(context, objective_id):
        return []
    constraint = _HABIT_CONSTRAINTS.get(objective_id)
    return [constraint] if constraint else []


def command_matches(command: str, intent_ids: tuple[str, ...], objective_id: str) -> bool:
    normalized = command.lower()
    objective_terms = [term for term in objective_id.split("-") if len(term) > 4]
    return any(
        intent_id in normalized or intent_id.replace("-", "_") in normalized
        for intent_id in intent_ids
    ) or any(term in normalized for term in objective_terms)


def focus_axes(profile_axes: list[str], default_axes: list[str]) -> list[str]:
    matched_profile_axes = [
        axis
        for axis in profile_axes
        if matched_terms(axis, default_axes, allow_keyword_overlap=True)
        or matched_terms(" ".join(default_axes), [axis], allow_keyword_overlap=True)
    ]
    return dedupe([*matched_profile_axes, *default_axes])


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _habit_matches(habit: dict[str, Any], terms: tuple[str, ...]) -> bool:
    values = [
        str(habit.get("id", "")),
        str(habit.get("label", "")),
        str(habit.get("hint", "")),
        *[str(term) for term in habit.get("matched_terms", []) if term is not None],
    ]
    haystack = " ".join(values).lower()
    return any(term.lower() in haystack for term in terms)


_HABIT_TERMS_BY_OBJECTIVE = {
    "drop-impact": ("kick-sub", "kick sub", "drum", "bass-movement", "mix-bus", "drop", "impact"),
    "low-end-translation": ("kick-sub", "kick sub", "sidechain"),
    "bass-motion": ("bass-movement", "bass movement"),
    "resampling-readiness": ("bass-movement", "bass movement"),
    "arrangement-flow": ("arrangement-transition", "arrangement transition", "arrangement-flow"),
    "transition-contrast": ("glitch-drum", "riser-transition", "transition"),
    "spatial-motion": ("spatial-send", "spatial send", "space"),
    "groove-humanization": ("hat-humanize", "hat humanize", "groove"),
    "mix-translation": ("mix-bus", "mix-master", "mix bus", "master polish"),
}

_HABIT_CRITERIA = {
    "drop-impact": "Use matched workflow habits to coordinate impact through low-end timing, drum transient control, bass motion, and conservative mix checks.",
    "low-end-translation": "Use the matched kick/sub habit as planning bias: resolve kick, sub, sidechain, and timing evidence before proposing broad low-end changes.",
    "bass-motion": "Use the matched bass movement habit as planning bias: separate stable sub from moving mids and verify automation before proposing a print pass.",
    "resampling-readiness": "Use the matched bass movement habit to keep resampling as a reviewable follow-up after motion and routing are inspected.",
    "arrangement-flow": "Use the matched arrangement habit to preserve learned transition placement and section flow while naming or editing anchors.",
    "transition-contrast": "Use the matched transition habit to combine glitch, riser, or percussion detail with a clean handoff into the next section.",
    "spatial-motion": "Use the matched spatial-send habit to prefer controlled throws, automated tails, and return-level verification over permanent wash.",
    "groove-humanization": "Use the matched groove habit to keep humanization subtle, inspectable, and anchored to the current drum phrase.",
    "mix-translation": "Use the matched mix-bus habit to keep polish conservative, inspectable, and headroom-aware before loudness moves.",
}

_HABIT_CONSTRAINTS = {
    "drop-impact": "Do not treat drop impact as permission to add every related macro; keep the chain focused on the current request and readback evidence.",
    "bass-motion": "Treat learned bass movement as a bias, not a requirement to add every historical processing step.",
    "spatial-motion": "Do not assume every space request needs a new return if the current set already has usable routing.",
    "groove-humanization": "Do not turn subtle hat variation into destructive timing randomization without note evidence.",
    "mix-translation": "Do not convert mix-bus habits into mastering commitments without current-chain evidence.",
}
