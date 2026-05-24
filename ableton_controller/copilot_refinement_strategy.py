"""Revision and correction strategy for iterative copilot planning."""

from __future__ import annotations

from typing import Any


def refinement_strategy(
    *,
    revision_requests: list[dict[str, Any]],
    refinement_patterns: list[dict[str, Any]],
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
) -> dict[str, Any]:
    """Turn current and historical correction habits into planning bias."""
    current = [_signal_item(item) for item in revision_requests]
    historical = _historical_patterns(refinement_patterns, current, ordered_commands, verification_steps)
    if not current and not historical:
        return {}
    labels = [item["label"] for item in [*current, *historical]]
    return {
        "mode": "revise-current-plan" if current else "historical-refinement-bias",
        "current_revisions": current,
        "historical_patterns": historical,
        "planning_biases": _biases(labels),
        "verification_biases": _verification_biases(labels, ordered_commands, verification_steps),
        "can_reduce_clarification": True,
    }


def refinement_labels(strategy: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for key in ("current_revisions", "historical_patterns"):
        for item in strategy.get(key, []):
            label = str(item.get("label", ""))
            if label:
                labels.append(label)
    return _dedupe(labels)


def _historical_patterns(
    patterns: list[dict[str, Any]],
    current: list[dict[str, Any]],
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
) -> list[dict[str, Any]]:
    current_labels = {item["label"] for item in current}
    return [
        _signal_item(pattern)
        for pattern in patterns
        if _pattern_is_relevant(pattern, current_labels, ordered_commands, verification_steps)
    ][:4]


def _pattern_is_relevant(
    pattern: dict[str, Any],
    current_labels: set[str],
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
) -> bool:
    label = str(pattern.get("label", ""))
    if label in current_labels:
        return True
    if pattern.get("matched_terms"):
        return True
    if current_labels and label in _GENERAL_ITERATIVE_LABELS:
        return True
    if label == "pad-mapping-correction":
        return _has_drum_pad_context(ordered_commands, verification_steps)
    return False


def _has_drum_pad_context(
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
) -> bool:
    command_text = " ".join(ordered_commands).lower()
    labels = " ".join(str(step.get("label", "")) for step in verification_steps).lower()
    return any(term in command_text for term in ("drum-pad-load", "glitch-drum-transition")) or "drum-rack-pad" in labels


def _signal_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": str(item.get("label", "")),
        "confidence": item.get("confidence", 0),
        "matched_terms": [str(term) for term in item.get("matched_terms", []) if str(term).strip()],
        "hint": str(item.get("hint", "")),
    }


def _biases(labels: list[str]) -> list[str]:
    messages = []
    if any(label in labels for label in ("correction-actually", "correction-instead-of")):
        messages.append("Adapt the current plan choice before starting a fresh workflow.")
    if "negative-revision-not-quite" in labels:
        messages.append("Identify the failed assumption and continue with a corrected move.")
    if "increase-intensity-more" in labels:
        messages.append("Treat 'more' as additive energy, motion, density, width, or contrast.")
    if "reduce-intensity-less" in labels:
        messages.append("Treat 'less' as subtractive space, restraint, cleanup, or reduced processing.")
    if "pad-mapping-correction" in labels:
        messages.append("Keep Drum Rack sample placement explicit and one-sample-per-pad unless asked otherwise.")
    return _dedupe(messages)


def _verification_biases(
    labels: list[str],
    ordered_commands: list[str],
    verification_steps: list[dict[str, str]],
) -> list[dict[str, str]]:
    biases = []
    if "pad-mapping-correction" in labels and _has_drum_pad_context(ordered_commands, verification_steps):
        biases.append(
            {
                "label": "verify-drum-pad-mapping",
                "command": "device-tree",
                "why": "Historical correction memory says to verify Drum Rack pads before writing or revising MIDI.",
            }
        )
    if any(label in labels for label in ("correction-actually", "correction-instead-of", "negative-revision-not-quite")):
        biases.append(
            {
                "label": "preserve-current-plan-context",
                "command": "session-snapshot",
                "why": "Revision language should reuse current-set context before asking broad setup questions.",
            }
        )
    return biases


def _dedupe(values: list[Any]) -> list[Any]:
    seen = set()
    result = []
    for value in values:
        key = repr(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


_GENERAL_ITERATIVE_LABELS = {
    "correction-actually",
    "correction-instead-of",
    "negative-revision-not-quite",
    "increase-intensity-more",
    "reduce-intensity-less",
}
