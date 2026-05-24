"""Small render helpers for personalized workflow profiles."""

from __future__ import annotations

from typing import Any

from ableton_controller.copilot_workflow_playbooks import workflow_playbooks_from_signals


def section_label_proposal_lines(proposals: list[dict[str, Any]]) -> list[str]:
    if not proposals:
        return ["- No derived section label proposals yet."]
    return [
        f"- Beat {proposal['beat']:g}: {proposal['name']} confidence {proposal['confidence']} from {', '.join(proposal.get('evidence_signal_ids', [])[:3])}."
        for proposal in proposals[:8]
    ]


def refinement_pattern_lines(memory: dict[str, Any]) -> list[str]:
    signals = [signal for signal in memory.get("signals", []) if signal.get("category") == "chat.refinement"]
    lines = ["", "## Iterative Refinement Patterns"]
    if not signals:
        lines.append("- No chat refinement patterns have been learned yet.")
        return lines
    ranked = sorted(signals, key=lambda signal: (-float(signal.get("confidence", 0)), signal.get("label", "")))[:6]
    lines.extend(
        f"- `{signal.get('label')}` confidence {signal.get('confidence')} from {signal.get('evidence_count', 0)} evidence item(s): {_refinement_hint(str(signal.get('label', '')))}"
        for signal in ranked
    )
    return lines


def workflow_playbook_lines(memory: dict[str, Any]) -> list[str]:
    lines = ["", "## Personalized Workflow Playbooks"]
    playbooks = workflow_playbooks_from_signals(memory.get("signals", []))
    if not playbooks:
        lines.append("- No workflow playbooks have enough project or chat evidence yet.")
        return lines
    for item in playbooks[:8]:
        lines.append(f"- `{item['id']}` confidence {item['confidence']}: {item['title']}.")
        lines.append(f"  First move: {item['first_move']}")
        lines.append(f"  Follow-through: {item['follow_through']}")
        lines.append(f"  Evidence: {', '.join(item['evidence_signal_ids'][:5])}")
    return lines


def target_alias_lines(aliases: list[dict[str, Any]]) -> list[str]:
    lines = ["", "## Personal Target Aliases"]
    if not aliases:
        lines.append("- No personal target aliases have been derived yet.")
        return lines
    lines.extend(
        f"- `{alias['role']}` confidence {alias['confidence']}: {', '.join(alias.get('aliases', []))}"
        for alias in aliases[:8]
    )
    return lines


def evidence_gap_lines(signals: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not any(signal.get("category", "").startswith("chat.") for signal in signals):
        lines.append("- No chat evidence has been scanned yet, so communication-style personalization is still weak.")
    if not any(signal.get("category") == "project.name" for signal in signals):
        lines.append("- No project naming evidence has been scanned yet.")
    has_section_labels = any(signal.get("category") == "project.arrangement" for signal in signals)
    has_locator_markers = any(signal.get("category") == "project.arrangement-marker" for signal in signals)
    if not has_section_labels and not has_locator_markers:
        lines.append("- No project arrangement marker or scene evidence has been learned yet.")
    elif not has_section_labels:
        lines.append("- No project musical scene or locator label evidence has been learned yet.")
    if not has_locator_markers:
        lines.append("- No project locator timing marker evidence has been learned yet.")
    if not any(signal.get("category") == "project.arrangement-phase" for signal in signals):
        lines.append("- No project arrangement phase-signature evidence has been learned yet.")
    if not any(signal.get("category") == "project.arrangement-role" for signal in signals):
        lines.append("- No project arrangement clip-role evidence has been learned yet.")
    if not any(signal.get("category") == "project.arrangement-shape" for signal in signals):
        lines.append("- No project arrangement shape evidence has been learned yet.")
    return lines or ["- No major evidence gaps detected by the current profile renderer."]


def workflow_macro_lines(macros: list[dict[str, Any]]) -> list[str]:
    lines = ["", "## Reusable Workflow Macros"]
    if not macros:
        lines.append("- No workflow macros have been confidence-tracked yet.")
        return lines
    ranked = sorted(macros, key=lambda macro: (-float(macro.get("confidence", 0)), macro.get("name", "")))[:10]
    for macro in ranked:
        links = ", ".join(macro.get("linked_intent_ids", [])) or "registry-only"
        tags = ", ".join(macro.get("tags", [])) or "untagged"
        lines.append(f"- `{macro.get('name')}` confidence {macro.get('confidence')}: {tags}. Linked intents: {links}.")
    return lines


def _refinement_hint(label: str) -> str:
    hints = {
        "correction-instead-of": "adapt the existing plan when the user redirects a choice.",
        "correction-actually": "treat the next message as a precision update, not a new unrelated request.",
        "negative-revision-not-quite": "probe the mismatch and revise the same workflow.",
        "increase-intensity-more": "expect additive follow-ups around motion, density, level, or energy.",
        "reduce-intensity-less": "expect subtractive follow-ups around restraint, space, or cleanup.",
        "pad-mapping-correction": "verify one-sample-per-pad routing after drum-rack edits.",
    }
    return hints.get(label, "use this as a communication-style planning hint.")
