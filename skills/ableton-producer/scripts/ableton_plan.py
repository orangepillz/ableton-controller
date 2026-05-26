#!/usr/bin/env python3
"""Render and optionally execute Ableton CLI operation plans."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


KNOWN_COMMANDS = {
    "ping", "status", "tracks", "selected", "select-track", "devices", "device-tree",
    "session-snapshot", "copilot-intent", "workflow-macro",
    "device-add-stock", "device-move", "device-delete", "drum-pad-load", "params", "stock-devices",
    "serum-add", "serum-params", "serum-names", "serum-set", "serum-set-many",
    "serum-build-preset",
    "stock-controls", "stock-coverage", "set-stock-control", "set-track", "set-send",
    "set-param", "tempo", "play", "stop", "continue", "undo", "redo", "hotkey",
    "key-sequence", "type-text", "menu-search", "save", "lom-get", "lom-set",
    "lom-call", "lom-inspect", "show-view", "hide-view", "focus-view",
    "toggle-browse", "browser-roots", "browser-children", "browser-tree",
    "browser-search", "browser-load", "browser-preview", "browser-stop-preview",
    "create-track", "delete-track", "duplicate-track", "create-scene",
    "delete-scene", "duplicate-scene", "fire-scene", "locators",
    "set-locator", "set-routing", "clips",
    "clip-create-midi", "clip-create-audio", "clip-set", "clip-warp",
    "clip-warp-marker-add", "clip-warp-marker-move", "clip-warp-marker-remove",
    "clip-automation-get", "clip-automation-set", "arrangement-automation-get",
    "arrangement-automation-file-get", "arrangement-automation-file-set",
    "arrangement-automation-set", "arrangement-automation-set-many", "clip-automation-set-many", "clip-automation-clear",
    "clip-stock-automation-get", "clip-stock-automation-set",
    "clip-stock-automation-clear", "clip-envelope-targets", "clip-envelope-get",
    "clip-envelope-set", "clip-envelope-clear", "clip-audio-set",
    "clip-delete", "clip-copy", "clip-move",
    "clip-split", "clip-slots", "fire-clip", "stop-track-clips", "midi-get-notes",
    "midi-add-notes", "midi-replace-notes", "midi-update-notes",
    "midi-remove-notes", "midi-clear-notes", "midi-transform-notes",
    "midi-duplicate-region", "raw",
}

DESTRUCTIVE_COMMANDS = {
    "delete-track", "delete-scene", "device-delete", "clip-delete", "clip-move",
    "arrangement-automation-file-set", "clip-automation-clear", "clip-stock-automation-clear",
    "clip-envelope-clear", "midi-replace-notes",
    "midi-remove-notes", "midi-clear-notes", "save", "set-locator", "lom-set",
    "lom-call",
}


def default_abletonctl() -> str:
    return "abletonctl"


def load_plan(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    plan = json.loads(raw)
    if not isinstance(plan, dict):
        raise ValueError("plan must be a JSON object")
    return plan


def command_args(step: dict[str, Any]) -> list[str]:
    args = step.get("args")
    if args is None and "command" in step:
        flags = step.get("flags", [])
        if not isinstance(flags, list):
            raise ValueError("step flags must be a list when command shorthand is used")
        args = [step["command"], *flags]
    if args is None:
        return []
    if not isinstance(args, list) or not all(isinstance(item, (str, int, float, bool)) for item in args):
        raise ValueError("step args must be a list of scalar values")
    return [str(item) for item in args]


def validate_plan(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    steps = plan.get("commands")
    if not isinstance(steps, list):
        return [], ["plan.commands must be a list"], []

    errors: list[str] = []
    warnings: list[str] = []
    normalized: list[dict[str, Any]] = []

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"step {index}: must be an object")
            continue
        try:
            args = command_args(step)
        except ValueError as exc:
            errors.append(f"step {index}: {exc}")
            continue
        if not args:
            if "comment" in step or "why" in step:
                normalized.append({**step, "args": []})
                continue
            errors.append(f"step {index}: missing args")
            continue
        command = args[0]
        if command not in KNOWN_COMMANDS:
            errors.append(f"step {index}: unknown abletonctl command {command!r}")
        if command in DESTRUCTIVE_COMMANDS or "--replace" in args or "--clear" in args:
            warnings.append(f"step {index}: potentially destructive command {command!r}")
        normalized.append({**step, "args": args})

    return normalized, errors, warnings


def shell_command(args: list[str], abletonctl: str, python_cmd: str | None = None) -> str:
    full = [abletonctl, *args]
    if python_cmd:
        full = [python_cmd, *full]
    return " ".join(shlex.quote(part) for part in full)


def render_plan(plan: dict[str, Any], abletonctl: str = "abletonctl", python_cmd: str | None = None) -> str:
    steps, errors, warnings = validate_plan(plan)
    if errors:
        return "\n".join(["Plan has errors:", *[f"- {error}" for error in errors]])

    lines: list[str] = []
    summary = plan.get("summary")
    if summary:
        lines.append(f"Summary: {summary}")
    assumptions = plan.get("assumptions")
    if assumptions:
        lines.append("Assumptions:")
        for item in assumptions:
            lines.append(f"- {item}")
    if warnings:
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.append("Commands:")
    command_number = 1
    for step in steps:
        args = step["args"]
        why = step.get("why") or step.get("comment")
        if not args:
            lines.append(f"# {why}")
            continue
        if why:
            lines.append(f"# {command_number}. {why}")
        else:
            lines.append(f"# {command_number}. {args[0]}")
        lines.append(shell_command(args, abletonctl, python_cmd))
        command_number += 1
    lines.append("Dry run only. Add --execute to run these commands.")
    return "\n".join(lines)


def has_destructive_warning(warnings: list[str]) -> bool:
    return bool(warnings)


def execute_plan(plan: dict[str, Any], abletonctl: str, python_cmd: str | None, allow_destructive: bool) -> int:
    steps, errors, warnings = validate_plan(plan)
    if errors:
        print(render_plan(plan, abletonctl, python_cmd), file=sys.stderr)
        return 2
    if has_destructive_warning(warnings) and not allow_destructive:
        print("Refusing to execute potentially destructive plan without --allow-destructive.", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
        return 3

    for step in steps:
        args = step["args"]
        if not args:
            continue
        print(shell_command(args, abletonctl, python_cmd), flush=True)
        command = [abletonctl, *args]
        if python_cmd:
            command = [python_cmd, *command]
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="Path to plan JSON, or '-' for stdin.")
    parser.add_argument("--abletonctl", default=default_abletonctl(), help="Ableton CLI command or script path.")
    parser.add_argument("--python", help="Optional Python executable used when --abletonctl points to a .py script.")
    parser.add_argument("--execute", action="store_true", help="Run the plan instead of rendering it.")
    parser.add_argument("--allow-destructive", action="store_true", help="Permit destructive commands during execution.")
    args = parser.parse_args(argv)

    try:
        plan = load_plan(args.plan)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not load plan: {exc}", file=sys.stderr)
        return 2

    if args.execute:
        return execute_plan(plan, args.abletonctl, args.python, args.allow_destructive)

    print(render_plan(plan, args.abletonctl, args.python))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
