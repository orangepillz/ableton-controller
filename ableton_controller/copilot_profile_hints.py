"""Profile hint rendering for personalized copilot intent results."""

from __future__ import annotations

from typing import Any

from .arrangement_labels import marker_label_proposals
from .copilot_artist_hints import artist_inspiration_hints
from .copilot_macro_hints import workflow_macro_hints
from .copilot_revision_hints import revision_hints
from .copilot_term_match import matched_terms
from .target_aliases import target_alias_hint, target_aliases


PROFILE_HINT_CATEGORIES = {
    "arrangement_phases": "project.arrangement-phase",
    "arrangement_roles": "project.arrangement-role",
    "arrangement_shape": "project.arrangement-shape",
    "arrangement_markers": "project.arrangement-marker",
    "device_chains": "project.device-chain",
    "routing": "project.routing",
    "automation": "project.automation",
    "project_workflows": "project.workflow",
    "chat_workflows": "chat.workflow",
    "refinement_patterns": "chat.refinement",
}


def profile_hints(memory: dict[str, Any], query: str, matched_intent_ids: set[str] | None = None, per_category: int = 4) -> dict[str, list[dict[str, Any]]]:
    signals = [signal for signal in memory.get("signals", []) if isinstance(signal, dict)]
    hints: dict[str, list[dict[str, Any]]] = {}
    revisions = revision_hints(query)
    if revisions:
        hints["revision_requests"] = revisions
    inspiration = artist_inspiration_hints(query)
    if inspiration:
        hints["artist_inspiration"] = inspiration
    section_labels = _section_label_hints(memory, query, matched_intent_ids or set(), per_category)
    if section_labels:
        hints["section_label_proposals"] = section_labels
    for name, category in PROFILE_HINT_CATEGORIES.items():
        ranked = sorted(
            [signal for signal in signals if signal.get("category") == category],
            key=lambda signal: (-_hint_score(signal, query), str(signal.get("label", ""))),
        )[:per_category]
        if ranked:
            hints[name] = [_hint_item(signal, query) for signal in ranked]
    aliases = _ranked_target_aliases(memory, query)[:per_category]
    if aliases:
        hints["target_aliases"] = [_target_alias_item(alias, query) for alias in aliases]
    macros = workflow_macro_hints(memory, query, per_category, matched_intent_ids or set())
    if macros:
        hints["workflow_macros"] = macros
    return hints


def _section_label_hints(memory: dict[str, Any], query: str, matched_intent_ids: set[str], limit: int) -> list[dict[str, Any]]:
    if "arrangement-flow" not in matched_intent_ids and not matched_terms(query, ["arrangement marker", "locator", "section label", "scene label"]):
        return []
    return [_section_label_hint(proposal) for proposal in marker_label_proposals(memory)[:limit]]


def _target_alias_item(alias: dict[str, Any], query: str) -> dict[str, Any]:
    terms = [str(alias.get("role", "")), *[str(item) for item in alias.get("aliases", [])]]
    return target_alias_hint(alias, matched_terms(query, terms))


def _section_label_hint(proposal: dict[str, Any]) -> dict[str, Any]:
    beat = float(proposal.get("beat", 0))
    name = str(proposal.get("name", ""))
    return {
        "id": f"section-label-proposal.{beat:g}",
        "label": name,
        "beat": beat,
        "confidence": proposal.get("confidence", 0),
        "evidence_signal_ids": list(proposal.get("evidence_signal_ids", []))[:6],
        "hint": f"Derived section label proposal: beat {beat:g} -> {name}.",
    }


def _ranked_target_aliases(memory: dict[str, Any], query: str) -> list[dict[str, Any]]:
    aliases = target_aliases(memory)
    return sorted(
        aliases,
        key=lambda alias: (
            -_alias_score(alias, query),
            -float(alias.get("confidence", 0)),
            str(alias.get("role", "")),
        ),
    )


def _alias_score(alias: dict[str, Any], query: str) -> float:
    terms = [str(alias.get("role", "")), *[str(item) for item in alias.get("aliases", [])]]
    return float(alias.get("confidence", 0)) + (0.3 if matched_terms(query, terms) else 0.0)


def _hint_score(signal: dict[str, Any], query: str) -> float:
    label = str(signal.get("label", ""))
    confidence = float(signal.get("confidence", 0.2))
    evidence = min(0.08, 0.01 * int(signal.get("evidence_count", 0)))
    return confidence + evidence + (0.18 if matched_terms(query, [label, *label.split("-")]) else 0.0)


def _hint_item(signal: dict[str, Any], query: str) -> dict[str, Any]:
    label = str(signal.get("label", ""))
    return {
        "id": str(signal.get("id", "")),
        "label": label,
        "confidence": signal.get("confidence", 0),
        "evidence_count": signal.get("evidence_count", 0),
        "matched_terms": _hint_matched_terms(label, query),
        "hint": _hint_text(label),
    }


def _hint_matched_terms(label: str, query: str) -> list[str]:
    return matched_terms(query, _hint_terms(label))


def _hint_terms(label: str) -> list[str]:
    workflow_terms = _workflow_hint_terms(label)
    if workflow_terms:
        return workflow_terms
    if ">" in label and ":" in label:
        _prefix, chain = label.split(":", 1)
        return [label, *[part.strip() for part in chain.split(">")]]
    return [label, *label.split("-")]


def _hint_text(label: str) -> str:
    if label.startswith("clip-role-"):
        return f"Historical arrangements include {_readable_role(label.removeprefix('clip-role-'))} clips."
    for prefix in ("early-arrangement-role-", "main-section-role-", "late-arrangement-role-"):
        if label.startswith(prefix):
            bucket = _section_phrase(prefix.removesuffix("-role-"))
            return f"Historical {bucket} include {_readable_role(label.removeprefix(prefix))} material."
    for prefix in ("early-arrangement-phase-", "main-section-phase-", "late-arrangement-phase-"):
        if label.startswith(prefix):
            bucket = _section_phrase(prefix.removesuffix("-phase-"))
            roles = _role_list(label.removeprefix(prefix))
            return f"Historical {bucket} combine {roles}."
    if label.startswith("common-clip-length-"):
        beats = label.removeprefix("common-clip-length-").removesuffix("-beats")
        return f"Historical projects commonly use {beats}-beat clips."
    if label.startswith("arrangement-start-grid-"):
        beats = label.removeprefix("arrangement-start-grid-").removesuffix("-beats")
        return f"Historical arrangement clips often land on a {beats}-beat grid."
    if label.startswith("arrangement-clips-"):
        bucket = label.removeprefix("arrangement-clips-").replace("-plus", "+")
        return f"Historical projects use {bucket} arrangement clips."
    if label.startswith("scene-count-"):
        return f"Historical sets often include {label.removeprefix('scene-count-')} scenes."
    if label.startswith("locator-count-"):
        return f"Historical sets often include {label.removeprefix('locator-count-')} locators."
    if label.startswith("locator-") and "-at-" in label:
        marker, beat = label.removeprefix("locator-").split("-at-", 1)
        return f"Historical arrangements place locator {marker.replace('-', ' ')} at beat {beat.removesuffix('-beats')}."
    if label.startswith("timeline-span-"):
        return f"Historical timeline span pattern: {label.removeprefix('timeline-span-').replace('-', ' ')} beats."
    if ">" in label and ":" in label:
        return f"Historical device-chain preference: {label}."
    workflow_hint = _workflow_hint(label)
    if workflow_hint:
        return workflow_hint
    refinements = {
        "correction-instead-of": "Historical chats include redirection with 'instead of'; adapt the existing plan before asking fresh setup questions.",
        "correction-actually": "Historical chats include precision corrections; treat the next user message as an update to current intent.",
        "negative-revision-not-quite": "Historical chats include mismatch corrections; verify the specific failed assumption before continuing.",
        "increase-intensity-more": "Historical chats include 'more' refinements; expect additive follow-ups for energy, motion, or density.",
        "reduce-intensity-less": "Historical chats include 'less' refinements; expect subtractive follow-ups for space or restraint.",
        "pad-mapping-correction": "Historical chats corrected drum-rack pad mapping; verify samples land on distinct pads.",
    }
    return refinements.get(label, f"Historical project evidence: {label}.")


def _workflow_hint_terms(label: str) -> list[str]:
    terms = {
        "bass-movement": ("bass", "movement", "automation", "sub", "resample"),
        "spatial-send": ("space", "spatial", "send", "reverb", "delay", "echo"),
        "glitch-drum": ("glitch", "drum", "zap", "perc", "transition", "stutter"),
        "kick-sub": ("kick", "sub", "sidechain", "bd", "sc"),
        "mix-bus": ("mix", "master", "bus", "limiter", "loudness"),
        "riser-transition": ("riser", "rise", "swell", "inhale", "build", "buildup", "drop", "transition"),
    }
    for prefix, values in terms.items():
        if label.startswith(prefix):
            return [label, *values]
    return []


def _workflow_hint(label: str) -> str | None:
    hints = {
        "bass-movement": "Historical workflow habit: bass movement combines bass/sub targets, motion devices, and automation.",
        "spatial-send": "Historical workflow habit: spatial moves often use send-style Delay/Reverb routing.",
        "glitch-drum": "Historical workflow habit: glitch drum transitions combine zap/perc material with transition timing.",
        "kick-sub": "Historical workflow habit: low-end work often pairs kick/sub separation with sidechain context.",
        "mix-bus": "Historical workflow habit: mix/master polish stays conservative and inspectable.",
        "riser-transition": "Historical workflow habit: riser transitions build tension with inhale motion, filtered lift, and a clean drop handoff.",
    }
    for prefix, hint in hints.items():
        if label.startswith(prefix):
            return hint
    return None


def _readable_role(role: str) -> str:
    names = {"drums": "drum", "fx": "FX"}
    return names.get(role, role.replace("-", " "))


def _section_phrase(bucket: str) -> str:
    names = {
        "early-arrangement": "early arrangement sections",
        "main-section": "main sections",
        "late-arrangement": "late arrangement sections",
    }
    return names.get(bucket, bucket.replace("-", " "))


def _role_list(raw: str) -> str:
    roles = [_readable_role(role) for role in raw.split("-") if role]
    if len(roles) <= 1:
        return "".join(roles)
    if len(roles) == 2:
        return f"{roles[0]} and {roles[1]}"
    return ", ".join(roles[:-1]) + f", and {roles[-1]}"
