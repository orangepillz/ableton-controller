"""Workflow macro hint ranking for personalized copilot intent results."""

from __future__ import annotations

from typing import Any

from .copilot_term_match import matched_terms


def workflow_macro_hints(memory: dict[str, Any], query: str, limit: int = 4, linked_intent_ids: set[str] | None = None) -> list[dict[str, Any]]:
    macros = [macro for macro in memory.get("workflow_macros", []) if isinstance(macro, dict) and macro.get("status", "active") == "active"]
    scored = [_scored_macro(macro, query, linked_intent_ids or set()) for macro in macros]
    has_intent_matches = bool(linked_intent_ids)
    relevant = [item for item in scored if _is_relevant(item, has_intent_matches)]
    ranked = sorted(relevant, key=lambda item: (-float(item["score"]), str(item["macro"].get("name", ""))))[:limit]
    return [_macro_hint(item["macro"], item["matched_terms"], item["matched_intent_ids"]) for item in ranked]


def _is_relevant(scored: dict[str, Any], has_intent_matches: bool) -> bool:
    if scored["matched_intent_ids"]:
        return True
    if has_intent_matches:
        return len(scored["matched_terms"]) >= 2
    return bool(scored["matched_terms"])


def _scored_macro(macro: dict[str, Any], query: str, linked_intent_ids: set[str]) -> dict[str, Any]:
    terms = [
        str(macro.get("name", "")),
        str(macro.get("description", "")),
        *[str(tag) for tag in macro.get("tags", [])],
        *[str(intent_id) for intent_id in macro.get("linked_intent_ids", [])],
    ]
    matched = _matched_terms(query, terms)
    matched_intents = sorted(linked_intent_ids.intersection(str(item) for item in macro.get("linked_intent_ids", [])))
    confidence = float(macro.get("confidence", 0.25))
    score = confidence + min(0.45, 0.15 * len(matched)) + (0.35 if matched_intents else 0.0)
    return {"macro": macro, "score": score, "matched_terms": matched, "matched_intent_ids": matched_intents}


def _macro_hint(macro: dict[str, Any], matched_terms: list[str], matched_intents: list[str]) -> dict[str, Any]:
    name = str(macro.get("name", ""))
    tags = [str(tag) for tag in macro.get("tags", []) if str(tag).strip()]
    links = [str(link) for link in macro.get("linked_intent_ids", []) if str(link).strip()]
    return {
        "id": str(macro.get("id", f"workflow-macro.{name}")),
        "label": name,
        "confidence": macro.get("confidence", 0),
        "tags": tags,
        "linked_intent_ids": links,
        "matched_terms": matched_terms,
        "matched_intent_ids": matched_intents,
        "recommended_command": f"workflow-macro render {name}",
        "hint": _hint_text(name, tags, links),
    }


def _hint_text(name: str, tags: list[str], links: list[str]) -> str:
    tag_text = ", ".join(tags) or "untagged"
    link_text = ", ".join(links) or "no linked intent yet"
    return f"Reusable workflow macro for {tag_text}; linked intent: {link_text}."


def _matched_terms(query: str, terms: list[str]) -> list[str]:
    return matched_terms(query, terms, allow_keyword_overlap=True)
