"""Auditable command-source summaries for copilot orchestration."""

from __future__ import annotations

from typing import Any

from .copilot_term_match import matched_terms


GENERIC_MATCH_TERMS = {"bd", "before the drop", "build", "buildup", "drop", "hats", "kick", "movement", "sd", "section", "snare", "transition"}
VERIFICATION_QUERY_TERMS = (
    "verify",
    "check",
    "read",
    "read back",
    "inspect",
    "confirm",
    "audit",
)
VERIFICATION_FOLLOWUP_PREFIXES = ("verify ", "check ", "read ", "read back ", "inspect ", "confirm ", "audit ")


def command_source_summary(
    query: str,
    matches: list[dict[str, Any]],
    artist_hints: list[dict[str, Any]],
    macro_hints: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return deduped command entries plus commands suppressed by query policy."""
    entries: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    candidates = [
        {
            "command": "session-snapshot",
            "source": _source("baseline_probe", "session-snapshot", "Current set inspection", 1.0, []),
        }
    ]
    for hint in artist_hints:
        source = _source(
            "artist_inspiration",
            str(hint.get("label", "")),
            str(hint.get("translate_to", "")),
            hint.get("confidence", 0),
            _as_strings(hint.get("matched_terms")),
        )
        candidates.extend(
            {"command": command, "source": source}
            for command in _as_strings(hint.get("recommended_commands"))
        )
    weak_generic_ids = _weak_generic_match_ids(matches)
    verification_only_ids = _verification_only_match_ids(query, matches)
    for match in matches[:3]:
        source = _source(
            _source_type(match),
            str(match.get("id", "")),
            str(match.get("title", "")),
            match.get("confidence", 0),
            _match_terms(match),
        )
        for command in _as_strings(match.get("recommended_commands")):
            match_id = str(match.get("id", ""))
            if match_id in verification_only_ids and command != "session-snapshot":
                _add_suppressed(suppressed, command, _verification_only_reason(match_id), source)
            elif match_id in weak_generic_ids and command != "session-snapshot":
                _add_suppressed(suppressed, command, _weak_generic_reason(str(match.get("id", ""))), source)
            elif match_id in weak_generic_ids or match_id in verification_only_ids:
                continue
            else:
                candidates.append({"command": command, "source": source})
    for hint in macro_hints:
        source = _source(
            "workflow_macro",
            str(hint.get("id", "")),
            str(hint.get("label", "")),
            hint.get("confidence", 0),
            _as_strings(hint.get("matched_terms")),
            _as_strings(hint.get("matched_intent_ids")),
        )
        command = str(hint.get("recommended_command", "")).strip()
        if command:
            linked_ids = _as_strings(hint.get("matched_intent_ids"))
            if linked_ids and all(linked_id in verification_only_ids for linked_id in linked_ids):
                _add_suppressed(suppressed, command, _verification_only_reason(str(hint.get("id", ""))), source)
            elif linked_ids and all(linked_id in weak_generic_ids for linked_id in linked_ids):
                _add_suppressed(suppressed, command, _weak_generic_reason(str(hint.get("id", ""))), source)
            else:
                candidates.append({"command": command, "source": source})

    for candidate in candidates:
        command = str(candidate.get("command", "")).strip()
        if not command:
            continue
        reason = _suppression_reason(command, query)
        if reason:
            _add_suppressed(suppressed, command, reason, candidate["source"])
            continue
        _add_entry(entries, command, candidate["source"])
    return entries, suppressed


def _source_type(match: dict[str, Any]) -> str:
    return "built_in_intent" if match.get("source") == "built-in" else "intent_mapping"


def _add_entry(entries: list[dict[str, Any]], command: str, source: dict[str, Any]) -> None:
    for entry in entries:
        if entry["command"] == command:
            _add_source(entry["sources"], source)
            entry["confidence"] = _confidence(entry["sources"])
            return
    entries.append({"command": command, "confidence": _confidence([source]), "sources": [source]})


def _add_suppressed(
    suppressed: list[dict[str, Any]],
    command: str,
    reason: dict[str, str],
    source: dict[str, Any],
) -> None:
    for entry in suppressed:
        if entry["command"] == command and entry["reason"] == reason["label"]:
            _add_source(entry["sources"], source)
            entry["confidence"] = _confidence(entry["sources"])
            return
    suppressed.append(
        {
            "command": command,
            "reason": reason["label"],
            "why": reason["why"],
            "confidence": _confidence([source]),
            "sources": [source],
        }
    )


def _add_source(sources: list[dict[str, Any]], source: dict[str, Any]) -> None:
    key = (source.get("type"), source.get("id"))
    if not any((item.get("type"), item.get("id")) == key for item in sources):
        sources.append(source)


def _source(
    source_type: str,
    source_id: str,
    label: str,
    confidence: Any,
    terms: list[str],
    matched_intent_ids: list[str] | None = None,
) -> dict[str, Any]:
    source = {
        "type": source_type,
        "id": source_id,
        "label": label,
        "confidence": _float_confidence(confidence),
    }
    if terms:
        source["matched_terms"] = _dedupe(terms)
    if matched_intent_ids:
        source["matched_intent_ids"] = _dedupe(matched_intent_ids)
    return source


def _match_terms(match: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in (
        "matched_query_terms",
        "matched_triggers",
        "matched_likely_followups",
        "matched_recommended_commands",
    ):
        terms.extend(_as_strings(match.get(key)))
    return _dedupe(terms)


def _weak_generic_match_ids(matches: list[dict[str, Any]]) -> set[str]:
    if not matches:
        return set()
    top = matches[0]
    top_terms = _match_terms(top)
    if not _has_distinctive_terms(top_terms):
        return set()
    try:
        top_score = float(top.get("score", 0))
    except (TypeError, ValueError):
        top_score = 0.0
    weak_ids = set()
    for match in matches[1:3]:
        terms = _match_terms(match)
        try:
            score = float(match.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0
        if terms and not _has_distinctive_terms(terms) and score <= top_score - 0.05:
            weak_ids.add(str(match.get("id", "")))
    return weak_ids


def _verification_only_match_ids(query: str, matches: list[dict[str, Any]]) -> set[str]:
    if not matched_terms(query, list(VERIFICATION_QUERY_TERMS), allow_keyword_overlap=True):
        return set()
    verification_only = set()
    for match in matches[:3]:
        if _is_verification_only_match(match):
            verification_only.add(str(match.get("id", "")))
    return verification_only


def _is_verification_only_match(match: dict[str, Any]) -> bool:
    if _as_strings(match.get("matched_query_terms")) or _as_strings(match.get("matched_triggers")):
        return False
    followups = _as_strings(match.get("matched_likely_followups"))
    if not followups:
        return False
    return all(followup.lower().startswith(VERIFICATION_FOLLOWUP_PREFIXES) for followup in followups)


def _has_distinctive_terms(terms: list[str]) -> bool:
    return any(term.lower() not in GENERIC_MATCH_TERMS for term in terms)


def _weak_generic_reason(source_id: str) -> dict[str, str]:
    return {
        "label": "weak-generic-match",
        "why": f"Suppressed commands from {source_id} because it only matched generic or target-only terms behind a more specific intent.",
    }


def _verification_only_reason(source_id: str) -> dict[str, str]:
    return {
        "label": "verification-followup",
        "why": f"Suppressed editing commands from {source_id} because the current query only asks for verification-oriented follow-up readback.",
    }


def _suppression_reason(command: str, query: str) -> dict[str, str] | None:
    if _is_meta_command(command):
        return {
            "label": "meta-command",
            "why": "The planner is already running this meta command, so it should not appear in the execution sequence.",
        }
    if not _command_supported_by_query(command, query):
        return {
            "label": "query-mismatch",
            "why": "The learned recommendation needs explicit support in the current query before planning that operation.",
        }
    return None


def _command_supported_by_query(command: str, query: str) -> bool:
    rules = (
        (("bass-resampling-pass", "resampling"), ("resampling", "resample", "print pass", "print", "record")),
        (("arrangement-marker-naming", "set-locator"), ("marker", "locator", "name", "rename")),
        (
            ("arrangement-automation-set",),
            ("automation", "automate", "build", "sweep", "ramp", "movement", "resampling", "resample"),
        ),
        (("set-routing",), ("route", "routing", "resampling", "resample", "print")),
        (("drum-pad-load",), ("pad", "sample", "load", "kit", "rack")),
        (("clip-create-midi", "midi-add-notes", "midi-transform-notes"), ("midi", "note", "notes", "pattern", "program", "sequence", "clip", "phrase", "human", "humanize", "groove", "velocity", "probability", "hats")),
    )
    normalized = command.lower()
    for needles, query_terms in rules:
        if any(needle in normalized for needle in needles):
            return bool(matched_terms(query, list(query_terms), allow_keyword_overlap=True))
    return True


def _is_meta_command(command: str) -> bool:
    return command.strip().split(maxsplit=1)[0] == "copilot-intent"


def _confidence(sources: list[dict[str, Any]]) -> float:
    if not sources:
        return 0.0
    return round(max(_float_confidence(source.get("confidence", 0)) for source in sources), 3)


def _float_confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
