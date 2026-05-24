"""Current-query revision hints for iterative copilot planning."""

from __future__ import annotations

from typing import Any

from .copilot_term_match import matched_terms


REVISION_PATTERNS: tuple[dict[str, Any], ...] = (
    {
        "label": "correction-actually",
        "terms": ["actually"],
        "confidence": 0.64,
        "hint": "Treat this as a precision update to the current plan, preserving relevant session context.",
    },
    {
        "label": "correction-instead-of",
        "terms": ["instead of", "instead"],
        "confidence": 0.66,
        "hint": "Swap or redirect the existing plan choice before asking fresh setup questions.",
    },
    {
        "label": "negative-revision-not-quite",
        "terms": ["not quite", "not right", "wrong"],
        "confidence": 0.62,
        "hint": "Verify the failed assumption and continue the same workflow with a corrected move.",
    },
    {
        "label": "increase-intensity-more",
        "terms": ["more", "bigger", "harder", "intense"],
        "confidence": 0.58,
        "hint": "Expect an additive refinement around energy, motion, density, width, or contrast.",
    },
    {
        "label": "reduce-intensity-less",
        "terms": ["less", "simpler", "back off", "too much"],
        "confidence": 0.58,
        "hint": "Expect a subtractive refinement around restraint, space, cleanup, or reduced processing.",
    },
    {
        "label": "pad-mapping-correction",
        "terms": ["other pad", "different pad", "pad instead", "pad mapping"],
        "confidence": 0.6,
        "hint": "For drum-rack edits, verify the target pad before placing or replacing samples.",
    },
)


def revision_hints(query: str) -> list[dict[str, Any]]:
    """Return deterministic hints when the current message looks like a revision."""
    hints = []
    for pattern in REVISION_PATTERNS:
        terms = [str(term) for term in pattern["terms"]]
        matches = matched_terms(query, terms)
        if matches:
            hints.append(
                {
                    "label": str(pattern["label"]),
                    "confidence": pattern["confidence"],
                    "matched_terms": matches,
                    "hint": str(pattern["hint"]),
                }
            )
    return hints
