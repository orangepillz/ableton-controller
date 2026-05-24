"""Confidence-tracked workflow macro memory."""

from __future__ import annotations

import re
from typing import Any

from ableton_controller.workflow_macros import list_workflow_macros

from .memory import utc_now


def sync_workflow_macros(memory: dict[str, Any]) -> list[dict[str, Any]]:
    derived = derive_workflow_macros(memory)
    existing = {item.get("id"): item for item in memory.setdefault("workflow_macros", [])}
    updates: list[dict[str, Any]] = []
    next_items = [item for item in memory.get("workflow_macros", []) if item.get("source") != "derived"]

    for macro in derived:
        previous = existing.get(macro["id"])
        changed = previous is None or _macro_core(previous) != _macro_core(macro)
        if not changed and previous is not None:
            macro["updated_at"] = previous.get("updated_at", macro["updated_at"])
        next_items.append(macro)
        updates.append({**macro, "changed": changed})

    memory["workflow_macros"] = sorted(next_items, key=lambda item: item.get("name", ""))
    return updates


def derive_workflow_macros(memory: dict[str, Any]) -> list[dict[str, Any]]:
    intent_links = _intent_links(memory)
    derived = []
    for macro in list_workflow_macros()["macros"]:
        name = str(macro["name"])
        links = intent_links.get(name, [])
        derived.append(
            {
                "id": f"workflow-macro.{name}",
                "name": name,
                "description": macro.get("description", ""),
                "tags": list(macro.get("tags", [])),
                "confidence": _macro_confidence(links),
                "linked_intent_ids": [link["id"] for link in links],
                "evidence_signal_ids": _linked_evidence(links),
                "source": "derived",
                "status": "active",
                "updated_at": utc_now(),
            }
        )
    return sorted(derived, key=lambda item: (-float(item["confidence"]), item["name"]))


def _intent_links(memory: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    links: dict[str, list[dict[str, Any]]] = {}
    for mapping in memory.get("intent_mappings", []):
        if not isinstance(mapping, dict) or mapping.get("status", "active") != "active":
            continue
        for command in mapping.get("recommended_commands", []):
            name = _macro_name_from_command(str(command))
            if name:
                links.setdefault(name, []).append(mapping)
    return links


def _macro_name_from_command(command: str) -> str | None:
    match = re.search(r"\bworkflow-macro\s+render\s+([a-z0-9-]+)\b", command)
    return match.group(1) if match else None


def _macro_confidence(links: list[dict[str, Any]]) -> float:
    if not links:
        return 0.25
    best = max(float(link.get("confidence", 0.2)) for link in links)
    evidence_bonus = min(0.12, 0.03 * len(_linked_evidence(links)))
    return round(min(0.95, best + 0.05 + evidence_bonus), 3)


def _linked_evidence(links: list[dict[str, Any]]) -> list[str]:
    evidence: list[str] = []
    for link in links:
        for signal_id in link.get("evidence_signal_ids", []):
            if signal_id not in evidence:
                evidence.append(str(signal_id))
    return evidence[:8]


def _macro_core(macro: dict[str, Any]) -> dict[str, Any]:
    keys = ("name", "description", "tags", "confidence", "linked_intent_ids", "evidence_signal_ids", "status")
    return {key: macro.get(key) for key in keys}
