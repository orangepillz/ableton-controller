"""Personalized intent matching for local copilot planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .copilot_intent_rules import INTENT_RULES
from .copilot_orchestration import orchestration_summary
from .copilot_profile_hints import profile_hints
from .copilot_term_match import matched_terms, normalize


STATE_DIR = ".ableton-copilot"
MEMORY_FILE = "memory.json"
FALLBACK_SKIP_TERMS = {"build", "drop", "movement", "transition"}


def default_memory_path(start: Path | None = None) -> Path:
    """Find the nearest persisted copilot memory from the current workspace."""
    root = (start or Path.cwd()).resolve()
    for candidate in (root, *root.parents):
        path = candidate / STATE_DIR / MEMORY_FILE
        if path.exists():
            return path
    return root / STATE_DIR / MEMORY_FILE


def match_copilot_intent(
    query: str,
    *,
    memory_path: Path | None = None,
    limit: int = 5,
    min_score: float = 0.15,
    include_inactive: bool = False,
) -> dict[str, Any]:
    """Rank persisted personalized intent mappings for a natural-language query."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("copilot-intent needs a non-empty query.")

    path = memory_path or default_memory_path()
    try:
        memory = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _missing_memory_result(cleaned_query, path)
    if not isinstance(memory, dict):
        raise ValueError(f"{path} must contain a JSON object.")

    matches = []
    for mapping in memory.get("intent_mappings", []):
        if not isinstance(mapping, dict):
            continue
        if mapping.get("status", "active") != "active" and not include_inactive:
            continue
        scored = _score_mapping(cleaned_query, mapping)
        if scored["score"] >= min_score:
            matches.append(scored)
    matches.extend(_fallback_matches(cleaned_query, matches, min_score))

    matches.sort(key=lambda item: (-item["score"], -float(item.get("confidence", 0)), item["id"]))
    limited_matches = matches[: max(1, limit)]
    hints = profile_hints(memory, cleaned_query, {match["id"] for match in matches})
    return {
        "query": cleaned_query,
        "memory_path": str(path),
        "memory_found": True,
        "count": len(matches),
        "matches": limited_matches,
        "profile_hints": hints,
        "orchestration": orchestration_summary(cleaned_query, limited_matches, hints, memory_path=path),
        "guidance": "Use matches as planning hints, then verify against the current Ableton set before editing.",
    }


def _missing_memory_result(query: str, path: Path) -> dict[str, Any]:
    return {
        "query": query,
        "memory_path": str(path),
        "memory_found": False,
        "count": 0,
        "matches": [],
        "profile_hints": {},
        "guidance": "Run `python3 scripts/copilot_improvement.py run` to build personalized intent memory.",
    }


def _score_mapping(query: str, mapping: dict[str, Any]) -> dict[str, Any]:
    query_terms = _as_strings(mapping.get("query_terms")) or _as_strings(mapping.get("triggers"))
    trigger_terms = _as_strings(mapping.get("triggers"))
    followup_terms = _as_strings(mapping.get("likely_followups"))
    command_terms = _as_strings(mapping.get("recommended_commands"))
    matched_query_terms = matched_terms(query, query_terms)
    matched_triggers = matched_terms(query, trigger_terms)
    matched_followups = matched_terms(query, followup_terms)
    matched_commands = matched_terms(query, command_terms)
    if not matched_query_terms and not matched_triggers and not matched_followups and not matched_commands:
        score = 0.0
    else:
        confidence = float(mapping.get("confidence", 0.2))
        term_bonus = min(0.55, 0.14 * len(matched_query_terms))
        trigger_bonus = min(0.25, 0.08 * len(matched_triggers))
        followup_bonus = min(0.32, 0.16 * len(matched_followups))
        command_bonus = min(0.22, 0.11 * len(matched_commands))
        score = min(1.0, confidence * 0.45 + term_bonus + trigger_bonus + followup_bonus + command_bonus)

    return {
        "id": str(mapping.get("id", "")),
        "title": str(mapping.get("title", "")),
        "score": round(score, 3),
        "confidence": mapping.get("confidence", 0),
        "matched_query_terms": matched_query_terms,
        "matched_triggers": matched_triggers,
        "matched_likely_followups": matched_followups,
        "matched_recommended_commands": matched_commands,
        "planning_bias": mapping.get("planning_bias"),
        "recommended_commands": list(_as_strings(mapping.get("recommended_commands"))),
        "likely_followups": list(_as_strings(mapping.get("likely_followups"))),
        "evidence_signal_ids": list(_as_strings(mapping.get("evidence_signal_ids")))[:6],
        "source": str(mapping.get("source", "memory")),
    }


def _fallback_matches(query: str, existing_matches: list[dict[str, Any]], min_score: float) -> list[dict[str, Any]]:
    existing_ids = {match["id"] for match in existing_matches}
    matches = []
    for rule in INTENT_RULES:
        if rule["id"] in existing_ids or not _has_distinctive_match(query, list(rule["terms"])):
            continue
        scored = _score_mapping(query, _fallback_mapping(rule))
        if scored["score"] >= min_score:
            matches.append(scored)
    return matches


def _fallback_mapping(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": rule["id"],
        "title": rule["title"],
        "confidence": 0.36,
        "status": "active",
        "triggers": list(rule["terms"]),
        "query_terms": list(rule["terms"]),
        "recommended_commands": list(rule["commands"]),
        "planning_bias": rule["planning_bias"],
        "likely_followups": list(rule["likely_followups"]),
        "source": "built-in",
    }


def _has_distinctive_match(query: str, terms: list[str]) -> bool:
    normalized_query = f" {normalize(query)} "
    query_tokens = set(normalized_query.split())
    distinctive = [term for term in terms if term not in FALLBACK_SKIP_TERMS]
    for term in distinctive:
        normalized_term = normalize(term)
        if " " in normalized_term and f" {normalized_term} " in normalized_query:
            return True
        if normalized_term in query_tokens:
            return True
    return False


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]
