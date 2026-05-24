"""Workflow-pattern detection from historical Ableton chat terms."""

from __future__ import annotations

from typing import Any


WORKFLOW_PATTERNS = (
    {
        "label": "glitch-drum-transition",
        "groups": (
            ("glitch", "glitchy", "stutter"),
            ("zap", "perc", "drum rack"),
            ("transition", "cut out", "loop"),
        ),
    },
    {
        "label": "bass-movement-workflow",
        "groups": (
            ("bass", "sub"),
            ("movement", "automation", "resample", "drop"),
        ),
    },
    {
        "label": "kick-sub-sidechain-workflow",
        "groups": (
            ("kick", "bd"),
            ("sidechain", "sub"),
        ),
    },
    {
        "label": "riser-transition-workflow",
        "groups": (
            ("riser", "rise", "swell", "inhale", "uplifter"),
            ("drop", "transition", "build", "buildup"),
        ),
    },
    {
        "label": "mix-master-polish-workflow",
        "groups": (
            ("mix", "master"),
            ("automation", "movement", "loudness", "limiter"),
        ),
    },
)


def chat_workflow_patterns(terms: dict[str, int]) -> list[dict[str, Any]]:
    """Return workflow-level chat patterns supported by co-occurring terms."""
    patterns: list[dict[str, Any]] = []
    normalized = {str(term).lower(): int(count) for term, count in terms.items()}
    for pattern in WORKFLOW_PATTERNS:
        matched_terms: list[str] = []
        group_counts: list[int] = []
        for group in pattern["groups"]:
            hits = [term for term in group if normalized.get(term, 0) > 0]
            if not hits:
                break
            matched_terms.extend(hits)
            group_counts.append(sum(normalized[term] for term in hits))
        else:
            patterns.append(
                {
                    "label": str(pattern["label"]),
                    "matched_terms": sorted(set(matched_terms)),
                    "count": min(group_counts) if group_counts else 1,
                }
            )
    return patterns
