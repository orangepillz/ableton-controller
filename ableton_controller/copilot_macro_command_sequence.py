"""Bounded command-sequence summaries for workflow macro previews."""

from __future__ import annotations

from typing import Any


READ_ONLY_HEADS = {
    "browser-search",
    "clip-stock-automation-get",
    "device-tree",
    "locators",
    "midi-get-notes",
    "params",
    "serum-params",
    "session-snapshot",
    "stock-controls",
}


def command_sequence_preview(commands: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    """Return ordered, bounded command details without expanding huge payloads."""
    preview = []
    for index, command in enumerate(commands[:limit], start=1):
        args = command.get("args")
        if not isinstance(args, list) or not args:
            continue
        head = str(args[0])
        preview.append(
            {
                "order": index,
                "head": head,
                "args": [_summarize_arg(arg) for arg in args],
                "why": str(command.get("why", "")),
                "read_only": is_read_only_head(head),
            }
        )
    return preview


def is_read_only_head(head: str) -> bool:
    return head in READ_ONLY_HEADS or head.endswith("-get")


def _summarize_arg(value: Any) -> str | int | float | bool:
    if isinstance(value, bool | int | float):
        return value
    text = str(value)
    if len(text) <= 96:
        return text
    if text.startswith("[") or text.startswith("{"):
        return f"<json:{len(text)} chars>"
    return f"{text[:93]}..."
