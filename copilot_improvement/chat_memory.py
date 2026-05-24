"""Persist chat-derived personalization signals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .memory import upsert_signal


def chat_signal_updates(memory: dict[str, Any], chats: dict[str, Any]) -> list[dict[str, Any]]:
    """Upsert long-term memory signals from scanned chat evidence."""
    updates: list[dict[str, Any]] = []
    for chat in chats["chats"]:
        source = chat["path"]
        updates.extend(_term_updates(memory, source, chat.get("terms", {})))
        updates.extend(_command_updates(memory, source, chat.get("commands", {})))
        updates.extend(_refinement_updates(memory, source, chat.get("refinements", {})))
        updates.extend(_workflow_updates(memory, source, chat.get("workflows", [])))
    return updates


def _term_updates(memory: dict[str, Any], source: str, terms: dict[str, int]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="chat.intent",
            label=term,
            evidence=f"Appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.04,
        )
        for term, count in terms.items()
    ]


def _command_updates(memory: dict[str, Any], source: str, commands: dict[str, int]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="chat.command",
            label=command,
            evidence=f"Mentioned {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.04,
        )
        for command, count in commands.items()
    ]


def _refinement_updates(memory: dict[str, Any], source: str, refinements: dict[str, int]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="chat.refinement",
            label=refinement,
            evidence=f"Observed {count} refinement marker(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for refinement, count in refinements.items()
    ]


def _workflow_updates(memory: dict[str, Any], source: str, workflows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for workflow in workflows:
        matched = ", ".join(str(term) for term in workflow.get("matched_terms", []))
        updates.append(
            upsert_signal(
                memory,
                category="chat.workflow",
                label=str(workflow.get("label", "")),
                evidence=f"Detected workflow pattern from {matched} in {Path(source).name}.",
                source=source,
                confidence_delta=0.05,
            )
        )
    return updates
