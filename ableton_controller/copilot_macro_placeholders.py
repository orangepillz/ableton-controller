"""Placeholder resolution summaries for workflow macro previews."""

from __future__ import annotations

import re
from typing import Any


PLACEHOLDER_RE = re.compile(r"<[^<>]+>")


def unresolved_placeholders(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe placeholder command args that must be replaced before execution."""
    search_steps = _search_steps(commands)
    unresolved = []
    for order, command in enumerate(commands, start=1):
        args = command.get("args")
        if not isinstance(args, list):
            continue
        placeholders = _placeholders(args)
        if not placeholders:
            continue
        unresolved.append(
            {
                "order": order,
                "head": str(args[0]) if args else "",
                "placeholders": placeholders,
                "why": str(command.get("why", "")),
                "resolve_with": search_steps[:4],
            }
        )
    return unresolved


def required_inputs(placeholders: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Turn unresolved placeholders into concise planning requirements."""
    inputs = []
    for placeholder in placeholders:
        for token in placeholder.get("placeholders", []):
            query = _resolution_query(str(token), placeholder.get("resolve_with"))
            inputs.append(
                {
                    "label": str(token),
                    "source": "browser-search-result",
                    "search_query": query,
                    "resolution_command": f"browser-search {query}" if query else "browser-search",
                    "why": f"Replace {token} before executing {placeholder.get('head', 'the macro command')}.",
                }
            )
    return _dedupe_inputs(inputs)


def _placeholders(args: list[Any]) -> list[str]:
    values = []
    for arg in args:
        text = str(arg)
        if PLACEHOLDER_RE.search(text):
            values.append(text)
    return values


def _search_steps(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps = []
    for order, command in enumerate(commands, start=1):
        args = command.get("args")
        if isinstance(args, list) and args and args[0] == "browser-search":
            steps.append({"order": order, "query": str(args[1]) if len(args) > 1 else "", "head": "browser-search"})
    return steps


def _resolution_query(token: str, steps: Any) -> str:
    if not isinstance(steps, list):
        return ""
    normalized_token = token.lower()
    fallback = ""
    for step in steps:
        if not isinstance(step, dict):
            continue
        query = str(step.get("query", "")).strip()
        if not query:
            continue
        if not fallback:
            fallback = query
        if query.lower() in normalized_token:
            return query
    return fallback


def _dedupe_inputs(inputs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for item in inputs:
        label = item["label"]
        if label not in seen:
            seen.add(label)
            result.append(item)
    return result
