"""Workflow-pattern detection from scanned Ableton project features."""

from __future__ import annotations

from typing import Any


PROJECT_WORKFLOW_PATTERNS = (
    {
        "label": "bass-movement-project-workflow",
        "groups": (
            (("common_names", "arrangement_roles", "arrangement_phases"), ("bass", "sub")),
            (("devices", "device_chains"), ("Operator", "AutoFilter", "Saturator", "Roar")),
            (("automation_features",), ("AutomationEnvelope", "ClipEnvelope")),
        ),
    },
    {
        "label": "spatial-send-project-workflow",
        "groups": (
            (("routing_targets", "common_names"), ("A-Reverb", "B-Delay", "Reverb", "Delay")),
            (("devices", "device_chains"), ("Reverb", "Delay", "Echo")),
        ),
    },
    {
        "label": "arrangement-transition-project-workflow",
        "groups": (
            (("arrangement_markers", "arrangement_sections"), ("drop", "fakeout", "break", "transition")),
            (("arrangement_roles", "arrangement_phases"), ("drums", "fx", "kick", "bass")),
        ),
    },
    {
        "label": "mix-bus-project-workflow",
        "groups": (
            (("common_names",), ("master", "mix", "bus")),
            (("devices", "device_chains"), ("Limiter", "GlueCompressor", "Compressor", "Utility", "Eq8")),
        ),
    },
)


def project_workflow_patterns(project: dict[str, Any]) -> list[dict[str, Any]]:
    """Return project workflow patterns supported by co-occurring feature groups."""
    patterns: list[dict[str, Any]] = []
    for pattern in PROJECT_WORKFLOW_PATTERNS:
        matched: list[str] = []
        group_counts: list[int] = []
        for fields, terms in pattern["groups"]:
            hits, count = _group_hits(project, fields, terms)
            if not hits:
                break
            matched.extend(hits)
            group_counts.append(count)
        else:
            patterns.append(
                {
                    "label": str(pattern["label"]),
                    "matched_features": sorted(set(matched)),
                    "count": min(group_counts) if group_counts else 1,
                }
            )
    return patterns


def _group_hits(project: dict[str, Any], fields: tuple[str, ...], terms: tuple[str, ...]) -> tuple[list[str], int]:
    hits: list[str] = []
    count = 0
    for field in fields:
        features = project.get(field, {})
        if not isinstance(features, dict):
            continue
        for label, value in features.items():
            if _matches_any(str(label), terms):
                hits.append(f"{field}:{label}")
                count += int(value or 1)
    return hits, count


def _matches_any(label: str, terms: tuple[str, ...]) -> bool:
    lowered = label.lower()
    return any(term.lower() in lowered for term in terms)
