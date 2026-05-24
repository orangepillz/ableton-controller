"""Non-imitative artist inspiration hints for copilot planning."""

from __future__ import annotations

from typing import Any

from .copilot_term_match import matched_terms


ARTIST_INSPIRATION_HINTS: tuple[dict[str, Any], ...] = (
    {
        "label": "tipper-inspired-principles",
        "terms": ["tipper", "tipper-ish", "tipper like", "tipper-like"],
        "confidence": 0.64,
        "translate_to": "Sculptural rhythm, clean low end, spatial detail, and restrained sound-system movement.",
        "focus_axes": ["low-end clarity", "rhythmic contour", "spatial detail", "restraint"],
        "recommended_commands": [
            "session-snapshot",
            "workflow-macro render kick-sub-separation",
            "workflow-macro render bass-movement",
        ],
    },
    {
        "label": "g-jones-inspired-principles",
        "terms": ["g jones", "g-jones", "g jones energy", "g-jones energy"],
        "confidence": 0.62,
        "translate_to": "Exploratory sound generation, decisive editing, stark contrast, and narrative transitions.",
        "focus_axes": ["contrast", "glitch edits", "resampling", "arrangement story"],
        "recommended_commands": [
            "session-snapshot",
            "workflow-macro render glitch-drum-transition",
            "workflow-macro render bass-resampling-pass",
        ],
    },
    {
        "label": "chris-lake-inspired-principles",
        "terms": ["chris lake", "chris-lake", "chris lake groove", "chris-lake groove"],
        "confidence": 0.62,
        "translate_to": "Functional groove, kick/bass economy, fast sketch capture, and taste-led restraint.",
        "focus_axes": ["groove", "kick-bass fit", "drum punch", "mix translation"],
        "recommended_commands": [
            "session-snapshot",
            "workflow-macro render drum-punch-bus",
            "workflow-macro render kick-sub-separation",
        ],
    },
)

NON_IMITATION_HINT = "Use this as abstract production guidance only; do not recreate identifiable melodies, patches, drops, or transitions."


def artist_inspiration_hints(query: str) -> list[dict[str, Any]]:
    """Return structured research hints for named artist-inspired prompts."""
    hints = []
    for pattern in ARTIST_INSPIRATION_HINTS:
        terms = [str(term) for term in pattern["terms"]]
        matches = matched_terms(query, terms)
        if matches:
            hints.append(
                {
                    "label": str(pattern["label"]),
                    "confidence": pattern["confidence"],
                    "matched_terms": matches,
                    "translate_to": str(pattern["translate_to"]),
                    "focus_axes": list(pattern["focus_axes"]),
                    "recommended_commands": list(pattern["recommended_commands"]),
                    "non_imitation": NON_IMITATION_HINT,
                }
            )
    return hints
