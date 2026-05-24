"""Active match selection for copilot orchestration."""

from __future__ import annotations

from typing import Any


def active_matches(matches: list[dict[str, Any]], command_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only matches that still contribute to executable command sources."""
    active_ids = {
        str(source.get("id", ""))
        for entry in command_sources
        for source in entry.get("sources", [])
        if source.get("type") in {"intent_mapping", "built_in_intent"}
    }
    active = [match for match in matches if str(match.get("id", "")) in active_ids]
    return active or matches[:1]


def active_section_labels(
    section_labels: list[dict[str, Any]],
    ordered_commands: list[str],
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Use learned section labels only when an active arrangement plan needs them."""
    active_ids = {str(match.get("id", "")) for match in matches}
    has_arrangement_command = any(
        "arrangement-marker" in command or "arrangement-phase" in command or "set-locator" in command
        for command in ordered_commands
    )
    return section_labels if "arrangement-flow" in active_ids or has_arrangement_command else []
