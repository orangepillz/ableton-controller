"""Backlog items for missing personalization evidence sources."""

from __future__ import annotations

import json
from typing import Any

from .memory import set_backlog_status, upsert_backlog


def add_evidence_backlog(memory: dict[str, Any], projects: dict[str, Any], chats: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    updates.extend(_source_backlog(memory, projects, _project_item(), "Project scan found"))
    updates.extend(_source_backlog(memory, chats, _chat_item(), "Chat scan found"))
    updates.extend(_project_feature_backlog(memory, projects))
    return updates


def _source_backlog(
    memory: dict[str, Any],
    scan: dict[str, Any],
    item: dict[str, Any],
    resolved_prefix: str,
) -> list[dict[str, Any]]:
    files_seen = int(scan.get("files_seen", 0))
    if files_seen == 0:
        return [
            upsert_backlog(
                memory,
                item_id=item["id"],
                title=item["title"],
                why=item["why"],
                expected_impact=item["expected_impact"],
                priority=item["priority"],
                evidence=json.dumps({"roots": scan.get("roots", []), "existing_roots": scan.get("existing_roots", [])}, sort_keys=True),
            )
        ]
    resolved = set_backlog_status(memory, item["id"], "resolved", f"{resolved_prefix} {files_seen} file(s).")
    return [resolved] if resolved is not None else []


def _project_item() -> dict[str, Any]:
    return {
        "id": "project-evidence-missing",
        "title": "Connect historical Ableton project evidence",
        "why": "Personalization needs real project files to learn arrangement, routing, device, and naming tendencies.",
        "expected_impact": "Improves style-aware planning and reduces generic production defaults.",
        "priority": 2,
    }


def _project_feature_backlog(memory: dict[str, Any], projects: dict[str, Any]) -> list[dict[str, Any]]:
    if int(projects.get("files_seen", 0)) == 0:
        return []
    has_arrangement = any(project.get("arrangement_sections") for project in projects.get("projects", []))
    has_markers = any(project.get("arrangement_markers") for project in projects.get("projects", []))
    has_roles = any(project.get("arrangement_roles") for project in projects.get("projects", []))
    has_shape = any(project.get("arrangement_shape") for project in projects.get("projects", []))
    has_label_proposals = any(signal.get("category") == "project.arrangement-label-proposal" for signal in memory.get("signals", []))
    if has_arrangement:
        resolved = set_backlog_status(
            memory,
            "project-arrangement-evidence-thin",
            "resolved",
            "Project scan found arrangement marker or scene evidence.",
        )
        return [resolved] if resolved is not None else []
    if has_markers and has_label_proposals:
        resolved = set_backlog_status(
            memory,
            "project-arrangement-evidence-thin",
            "resolved",
            "Derived arrangement label proposals now exist for learned locator markers.",
        )
        return [resolved] if resolved is not None else []
    if has_markers and has_shape and has_roles:
        title = "Add musical names to numbered arrangement markers"
        why = "Project locator markers, arrangement shape, and clip roles are learned, but no musical scene or locator labels were found."
        expected = "Turns existing locator anchors into clearer build, drop, transition, and fakeout labels for future scaffolded sets."
    elif has_markers:
        title = "Connect numbered arrangement markers to musical section names"
        why = "Project locator markers are learned, but no musical scene or locator labels were found."
        expected = "Improves personalized section naming by combining locator timing anchors with clip role and phase evidence."
    elif has_shape and has_roles:
        title = "Improve explicit scene and locator labels"
        why = "Project arrangement shape and clip roles are learned, but no explicit musical scene or locator labels were found."
        expected = "Adds human section names to existing shape and role evidence for clearer transition, fakeout, and build/drop planning."
    elif has_shape:
        title = "Improve named arrangement section evidence"
        why = "Project arrangement shape is learned from clip timing, but no musical scene or locator labels were found."
        expected = "Adds semantic section labels to existing shape evidence for better transition, fakeout, and build/drop planning."
    else:
        title = "Improve historical arrangement structure evidence"
        why = "Project files are connected, but the current scan found no arrangement shape or musical scene/locator labels."
        expected = "Better prediction of preferred section flow, transitions, fakeouts, and build/drop placement."
    return [
        upsert_backlog(
            memory,
            item_id="project-arrangement-evidence-thin",
            title=title,
            why=why,
            expected_impact=expected,
            priority=3,
            evidence=json.dumps({"files_seen": projects.get("files_seen", 0)}, sort_keys=True),
        )
    ]


def _chat_item() -> dict[str, Any]:
    return {
        "id": "chat-history-evidence-missing",
        "title": "Connect ableton-chats history to personalization scan",
        "why": "Communication-style personalization needs historical chats to learn shorthand, corrections, and recurring requests.",
        "expected_impact": "Reduces unnecessary clarification and improves natural-language intent mapping.",
        "priority": 2,
    }
