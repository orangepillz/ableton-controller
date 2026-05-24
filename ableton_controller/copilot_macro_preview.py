"""Compact non-executing previews for workflow macro plans."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Any

from .copilot_macro_actions import macro_recommended_action
from .copilot_macro_command_sequence import command_sequence_preview, is_read_only_head
from .copilot_macro_execution_status import macro_execution_status
from .copilot_macro_placeholders import required_inputs, unresolved_placeholders
from .copilot_macro_query_overrides import query_macro_overrides
from .workflow_macros import render_workflow_macro

RISK_RULES = (
    (
        "resampling-approval",
        "approval-required",
        "Ask for explicit approval before arming, recording, or routing a resampling pass.",
    ),
    (
        "locator-renaming-review",
        "review-before-execute",
        "Review proposed locator names before renaming Arrangement anchors.",
    ),
    (
        "arrangement-automation-range",
        "plan-first",
        "Confirm target track and beat range before writing Arrangement automation.",
    ),
    (
        "routing-change-review",
        "plan-first",
        "Verify routing source and destination before changing track routing.",
    ),
    (
        "placeholder-sample-selection",
        "review-before-execute",
        "Choose real browser-search results before executing placeholder sample loads.",
    ),
    (
        "destructive-edit-approval",
        "approval-required",
        "Ask for explicit approval before delete, replace, or clear-style edits.",
    ),
    (
        "direct-lom-approval",
        "approval-required",
        "Confirm direct Live Object Model mutation paths before execution.",
    ),
)


def macro_plan_previews(
    commands: list[str],
    *,
    memory_path: str | Path | None = None,
    query: str = "",
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Render compact workflow macro summaries without executing Ableton edits."""
    previews = []
    for command in commands:
        args = _preview_args(command, memory_path, query)
        if args is None:
            continue
        try:
            plan = render_workflow_macro(args)
        except SystemExit:
            continue
        previews.append(_compact_preview(plan, args))
        if len(previews) >= limit:
            break
    return previews


def _preview_args(command: str, memory_path: str | Path | None, query: str) -> argparse.Namespace | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if len(parts) < 3 or parts[:2] != ["workflow-macro", "render"] or parts[2].startswith("-"):
        return None

    parser = argparse.ArgumentParser(add_help=False)
    _add_preview_flags(parser)
    defaults = _default_args(parts[2], memory_path)
    overrides = query_macro_overrides(query)
    for key, value in overrides.items():
        setattr(defaults, key, value)
    defaults._query_overrides = overrides
    try:
        return parser.parse_known_args(parts[3:], namespace=defaults)[0]
    except SystemExit:
        return None


def _add_preview_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--track", type=_track_arg)
    parser.add_argument("--slot", type=int)
    parser.add_argument("--start", type=float)
    parser.add_argument("--end", type=float)
    parser.add_argument("--length", type=float)
    parser.add_argument("--name")
    parser.add_argument("--print-track", dest="print_track", type=_track_arg)
    parser.add_argument("--secondary-track", dest="secondary_track", type=_track_arg)
    parser.add_argument("--synth-track", dest="synth_track", type=_track_arg)
    parser.add_argument("--zap-query", dest="zap_query")
    parser.add_argument("--perc-query", dest="perc_query")
    parser.add_argument("--kick-track", dest="kick_track", type=_track_arg)
    parser.add_argument("--sub-track", dest="sub_track", type=_track_arg)
    parser.add_argument("--scene-index", dest="scene_index", type=int)


def _default_args(macro: str, memory_path: str | Path | None) -> argparse.Namespace:
    return argparse.Namespace(
        action="render",
        macro=macro,
        memory=Path(memory_path) if memory_path else None,
        track=None,
        slot=0,
        start=0.0,
        end=None,
        length=8.0,
        name=None,
        print_track="Bass Resample Print",
        secondary_track="Perc Glitch Rack",
        synth_track="Synth",
        zap_query="zap",
        perc_query="perc",
        kick_track="Kick",
        sub_track="Sub",
        scene_index=None,
    )


def _compact_preview(plan: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    commands = [command for command in plan.get("commands", []) if isinstance(command, dict)]
    gates = _execution_gates(commands)
    placeholders = unresolved_placeholders(commands)
    execution_status = macro_execution_status(gates, placeholders)
    inputs = required_inputs(placeholders)
    sequence = command_sequence_preview(commands)
    macro = str(plan.get("macro", ""))
    return {
        "macro": macro,
        "summary": str(plan.get("summary", "")),
        "assumptions": _as_strings(plan.get("assumptions"))[:4],
        "command_count": len(commands),
        "command_heads": _dedupe(_command_head(command) for command in commands)[:10],
        "mutating_command_heads": _dedupe(_command_head(command) for command in commands if not _is_read_only(command))[:10],
        "verification_heads": _dedupe(_command_head(command) for command in commands if _is_verification(command))[:8],
        "command_sequence_preview": sequence,
        "risk_labels": [gate["label"] for gate in gates],
        "execution_gates": gates,
        "approval_required": any(gate["level"] == "approval-required" for gate in gates),
        "review_required": any(gate["level"] in {"approval-required", "review-before-execute", "plan-first"} for gate in gates),
        "unresolved_placeholders": placeholders,
        "required_inputs": inputs,
        "execution_status": execution_status,
        "recommended_action": macro_recommended_action(macro, execution_status, required_inputs=inputs, execution_gates=gates, command_sequence=sequence),
        "next_action": execution_status["next_action"],
        "query_overrides": _applied_query_overrides(args),
        "preview_only": True,
    }


def _is_verification(command: dict[str, Any]) -> bool:
    why = str(command.get("why", "")).lower()
    return any(term in why for term in ("verify", "read back", "readback", "inspect")) or _is_read_only(command)


def _is_read_only(command: dict[str, Any]) -> bool:
    head = _command_head(command)
    return is_read_only_head(head)


def _command_head(command: dict[str, Any]) -> str:
    args = command.get("args")
    if not isinstance(args, list) or not args:
        return ""
    return str(args[0])


def _execution_gates(commands: list[dict[str, Any]]) -> list[dict[str, str]]:
    labels = []
    for command in commands:
        labels.extend(_risk_labels(command))
    return [_gate(label) for label in _dedupe(labels)]


def _risk_labels(command: dict[str, Any]) -> list[str]:
    args = command.get("args")
    if not isinstance(args, list):
        return []
    head = _command_head(command)
    args_text = " ".join(str(arg) for arg in args).lower()
    labels = []
    if head == "set-routing" and "resampling" in args_text:
        labels.append("resampling-approval")
    if head == "set-track" and "--arm" in args_text and "true" in args_text:
        labels.append("resampling-approval")
    if head == "set-locator":
        labels.append("locator-renaming-review")
    if head == "arrangement-automation-set":
        labels.append("arrangement-automation-range")
    if head == "set-routing":
        labels.append("routing-change-review")
    if head == "drum-pad-load" and "<" in args_text and ">" in args_text:
        labels.append("placeholder-sample-selection")
    if _is_destructive(head, args_text):
        labels.append("destructive-edit-approval")
    if head in {"lom-call", "lom-set"}:
        labels.append("direct-lom-approval")
    return labels


def _is_destructive(head: str, args_text: str) -> bool:
    return head.startswith("delete-") or head in {"midi-clear-notes", "midi-replace-notes"} or "--replace" in args_text


def _gate(label: str) -> dict[str, str]:
    for rule_label, level, why in RISK_RULES:
        if rule_label == label:
            return {"label": label, "level": level, "why": why}
    return {"label": label, "level": "review-before-execute", "why": "Review this macro risk before execution."}


def _applied_query_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides = getattr(args, "_query_overrides", {})
    if not isinstance(overrides, dict):
        return {}
    return {key: value for key, value in overrides.items() if getattr(args, key, None) == value}


def _track_arg(value: str) -> str | int:
    try:
        return int(value)
    except ValueError:
        return value


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _dedupe(values) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
