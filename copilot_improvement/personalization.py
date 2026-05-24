"""Personalized workflow profile generation for recurring improvement runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ableton_controller.arrangement_labels import marker_label_proposals
from ableton_controller.copilot_intent_rules import INTENT_RULES
from ableton_controller.target_aliases import target_aliases

from .memory import slugify, utc_now
from .profile_sections import (
    evidence_gap_lines,
    refinement_pattern_lines,
    section_label_proposal_lines,
    target_alias_lines,
    workflow_macro_lines,
    workflow_playbook_lines,
)


PROFILE_NAME = "personal-workflow-profile.md"
EVIDENCE_CATEGORIES = {
    "chat.command", "chat.intent", "chat.refinement", "chat.workflow", "project.arrangement", "project.arrangement-label-proposal", "project.arrangement-marker",
    "project.arrangement-phase", "project.arrangement-role", "project.arrangement-shape", "project.device-chain",
    "project.automation", "project.device", "project.name", "project.routing", "project.target-alias", "project.workflow",
}

def derive_intent_mappings(memory: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_signals = [signal for signal in memory.get("signals", []) if signal.get("category") in EVIDENCE_CATEGORIES]
    mappings: list[dict[str, Any]] = []
    for rule in INTENT_RULES:
        matches = _matching_signals(evidence_signals, rule["terms"])
        if len(matches) < 2:
            continue
        confidence = _mapping_confidence(matches)
        mappings.append(
            {
                "id": rule["id"],
                "title": rule["title"],
                "confidence": confidence,
                "triggers": sorted(set(_matched_terms(matches, rule["terms"]))),
                "query_terms": list(rule["terms"]),
                "recommended_commands": list(rule["commands"]),
                "planning_bias": rule["planning_bias"],
                "likely_followups": list(rule["likely_followups"]),
                "evidence_signal_ids": [signal["id"] for signal in matches[:8]],
                "source": "derived",
                "status": "active",
                "updated_at": utc_now(),
            }
        )
    return sorted(mappings, key=lambda item: (-float(item["confidence"]), item["id"]))


def sync_intent_mappings(memory: dict[str, Any]) -> list[dict[str, Any]]:
    derived = derive_intent_mappings(memory)
    existing = {item.get("id"): item for item in memory.setdefault("intent_mappings", [])}
    updates: list[dict[str, Any]] = []
    next_items = [item for item in memory.get("intent_mappings", []) if item.get("source") != "derived"]

    for mapping in derived:
        previous = existing.get(mapping["id"])
        changed = previous is None or _mapping_core(previous) != _mapping_core(mapping)
        if not changed and previous is not None:
            mapping["updated_at"] = previous.get("updated_at", mapping["updated_at"])
        next_items.append(mapping)
        updates.append({**mapping, "changed": changed})

    memory["intent_mappings"] = next_items
    return updates


def render_profile(memory: dict[str, Any], run: dict[str, Any]) -> str:
    signals = memory.get("signals", [])
    lines = [
        "# Ableton Copilot Personalized Workflow Profile",
        "",
        f"- Updated: {memory.get('updated_at') or utc_now()}",
        f"- Run: {run.get('run_id', 'unknown')}",
        "- Use these as confidence-scored planning hints, not hard rules.",
        "",
        "## Derived Intent Mappings",
    ]
    mappings = sorted(memory.get("intent_mappings", []), key=lambda item: (-float(item.get("confidence", 0)), item.get("id", "")))
    if mappings:
        for mapping in mappings[:8]:
            lines.extend(_mapping_lines(mapping))
    else:
        lines.append("- No derived intent mappings yet. More project or chat evidence is needed.")

    lines.extend(workflow_macro_lines(memory.get("workflow_macros", [])))
    lines.extend(workflow_playbook_lines(memory))

    lines.extend(["", "## Strongest Evidence Signals"])
    for category in ("project.device", "project.name", "chat.intent", "chat.workflow", "chat.command", "chat.refinement"):
        lines.extend(_signal_lines(memory, category))

    lines.extend(target_alias_lines(target_aliases(memory)))
    lines.extend(refinement_pattern_lines(memory))

    lines.extend(["", "## Project Workflow Evidence"])
    for category in (
        "project.arrangement",
        "project.arrangement-label-proposal",
        "project.arrangement-marker",
        "project.arrangement-phase",
        "project.arrangement-role",
        "project.arrangement-shape",
        "project.device-chain",
        "project.workflow",
        "project.routing",
        "project.automation",
        "project.track-type",
    ):
        lines.extend(_signal_lines(memory, category))

    lines.extend(["", "## Derived Section Label Proposals"])
    lines.extend(section_label_proposal_lines(marker_label_proposals(memory)))

    lines.extend(["", "## Evidence Gaps"])
    lines.extend(evidence_gap_lines(signals))
    return "\n".join(lines) + "\n"


def write_profile(profile: str, run_dir: Path, state_dir: Path) -> dict[str, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    run_path = run_dir / PROFILE_NAME
    latest_path = state_dir / PROFILE_NAME
    run_path.write_text(profile, encoding="utf-8")
    latest_path.write_text(profile, encoding="utf-8")
    return {"run": run_path, "latest": latest_path}


def _mapping_lines(mapping: dict[str, Any]) -> list[str]:
    lines = [
        f"- `{mapping['id']}` confidence {mapping.get('confidence')}: {mapping.get('title')}",
        f"  Planning bias: {mapping.get('planning_bias')}",
        f"  Triggers: {', '.join(mapping.get('triggers', []))}",
        f"  Recognition terms: {', '.join(mapping.get('query_terms', []))}",
        f"  Commands: {', '.join(mapping.get('recommended_commands', []))}",
        f"  Likely follow-ups: {', '.join(mapping.get('likely_followups', []))}",
    ]
    evidence = mapping.get("evidence_signal_ids", [])
    if evidence:
        lines.append(f"  Evidence: {', '.join(evidence[:6])}")
    return lines


def _signal_lines(memory: dict[str, Any], category: str) -> list[str]:
    signals = [signal for signal in memory.get("signals", []) if signal.get("category") == category]
    if not signals:
        return [f"- No `{category}` signals yet."]
    ranked = sorted(signals, key=lambda item: (-float(item.get("confidence", 0)), item.get("label", "")))[:8]
    return [
        f"- `{category}` {signal.get('label')} confidence {signal.get('confidence')} from {signal.get('evidence_count', 0)} evidence item(s)."
        for signal in ranked
    ]


def _mapping_core(mapping: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "title",
        "confidence",
        "triggers",
        "query_terms",
        "recommended_commands",
        "planning_bias",
        "likely_followups",
        "evidence_signal_ids",
        "status",
    )
    return {key: mapping.get(key) for key in keys}


def _matching_signals(signals: list[dict[str, Any]], terms: tuple[str, ...]) -> list[dict[str, Any]]:
    matches = [signal for signal in signals if any(_label_matches(str(signal.get("label", "")), term) for term in terms)]
    return sorted(matches, key=lambda item: (-float(item.get("confidence", 0)), item.get("id", "")))


def _matched_terms(signals: list[dict[str, Any]], terms: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for signal in signals:
        label = str(signal.get("label", ""))
        found.extend(term for term in terms if _label_matches(label, term))
    return found


def _label_matches(label: str, term: str) -> bool:
    normalized_label = slugify(label).replace("-", "")
    normalized_term = slugify(term).replace("-", "")
    if len(normalized_term) <= 2:
        return normalized_label == normalized_term
    return normalized_term in normalized_label


def _mapping_confidence(signals: list[dict[str, Any]]) -> float:
    selected = signals[:6]
    average = sum(float(signal.get("confidence", 0.2)) for signal in selected) / len(selected)
    evidence_bonus = min(0.18, 0.03 * (len(signals) - 1))
    return round(max(0.2, min(0.95, average + evidence_bonus)), 3)
