"""Memory updates derived from scanned Ableton project features."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .memory import upsert_signal
from .project_workflow_patterns import project_workflow_patterns


def project_signal_updates(memory: dict[str, Any], projects: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for project in projects["projects"]:
        source = project["path"]
        updates.extend(_name_updates(memory, source, project))
        updates.extend(_device_updates(memory, source, project))
        updates.extend(_track_type_updates(memory, source, project))
        updates.extend(_arrangement_updates(memory, source, project))
        updates.extend(_arrangement_marker_updates(memory, source, project))
        updates.extend(_arrangement_shape_updates(memory, source, project))
        updates.extend(_arrangement_role_updates(memory, source, project))
        updates.extend(_arrangement_phase_updates(memory, source, project))
        updates.extend(_device_chain_updates(memory, source, project))
        updates.extend(_routing_updates(memory, source, project))
        updates.extend(_automation_updates(memory, source, project))
        updates.extend(_workflow_updates(memory, source, project))
    return updates


def _name_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    updates = []
    for name, count in project.get("common_names", {}).items():
        if len(name.strip()) < 2:
            continue
        updates.append(
            upsert_signal(
                memory,
                category="project.name",
                label=name,
                evidence=f"Appeared {count} time(s) in {Path(source).name}.",
                source=source,
                confidence_delta=0.03,
            )
        )
    return updates


def _device_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.device",
            label=device,
            evidence=f"Appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.05,
        )
        for device, count in project.get("devices", {}).items()
    ]


def _track_type_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.track-type",
            label=track_type,
            evidence=f"Appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.02,
        )
        for track_type, count in project.get("track_types", {}).items()
    ]


def _arrangement_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    updates = []
    for section, count in project.get("arrangement_sections", {}).items():
        if len(section.strip()) < 2:
            continue
        updates.append(
            upsert_signal(
                memory,
                category="project.arrangement",
                label=section,
                evidence=f"Arrangement marker or scene appeared {count} time(s) in {Path(source).name}.",
                source=source,
                confidence_delta=0.03,
            )
        )
    return updates


def _arrangement_shape_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.arrangement-shape",
            label=shape,
            evidence=f"Arrangement shape signal appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for shape, count in project.get("arrangement_shape", {}).items()
    ]


def _arrangement_marker_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.arrangement-marker",
            label=marker,
            evidence=f"Arrangement locator marker appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for marker, count in project.get("arrangement_markers", {}).items()
    ]


def _arrangement_role_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.arrangement-role",
            label=role,
            evidence=f"Arrangement clip role signal appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for role, count in project.get("arrangement_roles", {}).items()
    ]


def _arrangement_phase_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.arrangement-phase",
            label=phase,
            evidence=f"Arrangement phase signature appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for phase, count in project.get("arrangement_phases", {}).items()
    ]


def _routing_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    updates = []
    for route, count in project.get("routing_targets", {}).items():
        if len(route.strip()) < 2:
            continue
        updates.append(
            upsert_signal(
                memory,
                category="project.routing",
                label=route,
                evidence=f"Routing target appeared {count} time(s) in {Path(source).name}.",
                source=source,
                confidence_delta=0.03,
            )
        )
    return updates


def _device_chain_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.device-chain",
            label=chain,
            evidence=f"Device chain appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.04,
        )
        for chain, count in project.get("device_chains", {}).items()
    ]


def _automation_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        upsert_signal(
            memory,
            category="project.automation",
            label=automation,
            evidence=f"Automation feature appeared {count} time(s) in {Path(source).name}.",
            source=source,
            confidence_delta=0.03,
        )
        for automation, count in project.get("automation_features", {}).items()
    ]


def _workflow_updates(memory: dict[str, Any], source: str, project: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    workflows = project.get("workflows") or project_workflow_patterns(project)
    for workflow in workflows:
        features = ", ".join(str(feature) for feature in workflow.get("matched_features", []))
        updates.append(
            upsert_signal(
                memory,
                category="project.workflow",
                label=str(workflow.get("label", "")),
                evidence=f"Detected project workflow pattern from {features} in {Path(source).name}.",
                source=source,
                confidence_delta=0.04,
            )
        )
    return updates
