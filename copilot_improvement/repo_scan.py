"""Repository and CLI analysis for improvement planning."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

from ableton_controller.copilot_capability_gaps import capability_gap_hints
from ableton_controller.parser import build_parser


EXPECTED_CAPABILITIES = (
    {
        "id": "session-snapshot-command",
        "title": "Add an aggregate session snapshot command",
        "commands": {"status", "tracks", "selected", "devices", "clips"},
        "missing_marker": "session-snapshot",
        "why": "Most production requests start with the same state probes.",
        "impact": "Reduces repeated probing and improves natural-language planning context.",
    },
    {
        "id": "drum-rack-pad-loading",
        "title": "Expose deterministic sample-to-drum-rack pad loading",
        "commands": {"browser-search", "browser-load", "device-tree"},
        "missing_marker": "drum-pad-load",
        "why": "Drum rack setup is a recurring workflow, but exact sample placement is still a gap.",
        "impact": "Makes custom kit construction faster and more reliable.",
    },
    {
        "id": "arrangement-automation-workflow",
        "title": "Add arrangement-level automation helpers",
        "commands": {"clip-automation-set", "clip-stock-automation-set"},
        "missing_marker": "arrangement-automation-set",
        "why": "Clip automation exists, while many transitions need arrangement-timed gestures.",
        "impact": "Improves builds, drops, fakeouts, and long-form movement workflows.",
    },
    {
        "id": "workflow-macro-registry",
        "title": "Create reusable workflow macro registry",
        "commands": {"clip-create-midi", "midi-add-notes", "device-add-stock", "set-stock-control"},
        "missing_marker": "workflow-macro",
        "why": "Repeated production operations should become named, auditable macros.",
        "impact": "Speeds up common creative flows without hiding command-level determinism.",
    },
    {
        "id": "personalized-intent-query",
        "title": "Expose personalized intent mapping lookup",
        "commands": {"workflow-macro", "session-snapshot"},
        "missing_marker": "copilot-intent",
        "why": "Learned workflow preferences should be queryable during natural-language planning.",
        "impact": "Reduces clarification and steers plans toward evidence-backed personalized workflows.",
    },
)


def cli_commands() -> list[str]:
    parser = build_parser()
    subparsers = next(action for action in parser._actions if getattr(action, "choices", None))
    return sorted(subparsers.choices)


def planner_commands(repo_root: Path) -> set[str]:
    script = repo_root / "skills" / "ableton-producer" / "scripts" / "ableton_plan.py"
    spec = importlib.util.spec_from_file_location("ableton_plan", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.KNOWN_COMMANDS)


def git_snapshot(repo_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(args, cwd=repo_root, text=True, capture_output=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    return {
        "head": run("git", "rev-parse", "--short", "HEAD"),
        "branch": run("git", "branch", "--show-current"),
        "status_short": run("git", "status", "--short").splitlines(),
    }


def python_size_warnings(repo_root: Path, warn_at: int = 300, hard_at: int = 500) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    skip_parts = {".git", ".mypy_cache", ".ruff_cache", "__pycache__", ".ableton-copilot"}
    for path in sorted(repo_root.rglob("*.py")):
        if skip_parts.intersection(path.parts):
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count >= warn_at:
            warnings.append(
                {
                    "path": str(path.relative_to(repo_root)),
                    "lines": line_count,
                    "severity": "hard" if line_count >= hard_at else "warn",
                }
            )
    return warnings


def capability_gaps(commands: set[str]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for capability in EXPECTED_CAPABILITIES:
        if capability["missing_marker"] in commands:
            continue
        supporting = sorted(capability["commands"].intersection(commands))
        gaps.append(
            {
                "id": capability["id"],
                "title": capability["title"],
                "missing_marker": capability["missing_marker"],
                "why": capability["why"],
                "impact": capability["impact"],
                "supporting_commands": supporting,
            }
        )
    return gaps


def runtime_capability_gap_catalog() -> list[dict[str, Any]]:
    """Probe runtime planner gap emitters so recurring reports expose coverage."""
    found: list[dict[str, Any]] = []
    for probe in _runtime_gap_probes():
        for gap in capability_gap_hints(**probe["request"]):
            found.append(
                {
                    "id": str(gap.get("id", "")),
                    "type": str(gap.get("type", "")),
                    "priority": str(gap.get("priority", "")),
                    "confidence": gap.get("confidence", 0),
                    "scenario": probe["scenario"],
                    "next_action": str(gap.get("next_action", "")),
                }
            )
    return _unique_gaps(found)


def scan_repository(repo_root: Path) -> dict[str, Any]:
    commands = set(cli_commands())
    known = planner_commands(repo_root)
    return {
        "git": git_snapshot(repo_root),
        "cli_commands": sorted(commands),
        "planner_missing_commands": sorted(commands - known),
        "planner_stale_commands": sorted(known - commands),
        "size_warnings": python_size_warnings(repo_root),
        "capability_gaps": capability_gaps(commands),
        "runtime_capability_gaps": runtime_capability_gap_catalog(),
    }


def _runtime_gap_probes() -> list[dict[str, Any]]:
    return [
        _probe(
            "unmapped request",
            "make a velvet crystalline texture",
            [],
            [{"command": "session-snapshot"}],
            [],
            {"status": "inspect-only", "required_before_execution": []},
        ),
        _probe(
            "learned hint without executable support",
            "make this more alive",
            [{"id": "learned-texture"}],
            [{"command": "session-snapshot"}],
            [],
            {"status": "under-supported", "required_before_execution": []},
        ),
        _probe(
            "current-set verification gate",
            "not quite, make it less busy",
            [],
            [{"command": "session-snapshot"}],
            [],
            {
                "status": "verify-assumptions",
                "required_before_execution": [
                    {
                        "label": "preserve-current-plan-context",
                        "level": "verify-before-execution",
                        "verify_with": "session-snapshot",
                    }
                ],
                "next_required_summary": "verify-before-execution: preserve-current-plan-context via session-snapshot",
            },
        ),
        _probe(
            "macro placeholder inputs",
            "make a glitch drum transition",
            [{"id": "glitch-drum-transition"}],
            [{"command": "workflow-macro render glitch-drum-transition"}],
            [],
            {
                "status": "inputs-required",
                "required_before_execution": [
                    {
                        "label": "samples/<zap-1>",
                        "level": "inputs-required",
                        "search_query": "zap",
                        "resolution_command": "browser-search zap",
                    }
                ],
                "next_required_summary": "inputs-required: samples/<zap-1> via browser-search zap",
            },
        ),
        _probe(
            "approval gate",
            "make a bass resampling pass",
            [{"id": "bass-movement"}],
            [{"command": "workflow-macro render bass-resampling-pass"}],
            [],
            {
                "status": "approval-required",
                "required_before_execution": [
                    {"label": "resampling-approval", "level": "approval-required", "macro": "bass-resampling-pass"}
                ],
                "gate_labels": ["resampling-approval"],
                "next_required_summary": "approval-required: resampling-approval",
            },
        ),
        _probe(
            "preview gate",
            "name the arrangement markers",
            [{"id": "arrangement-flow"}],
            [{"command": "workflow-macro render arrangement-marker-naming"}],
            [],
            {
                "status": "preview-required",
                "required_before_execution": [{"label": "locator-renaming-review", "level": "review-before-execute"}],
                "gate_labels": ["locator-renaming-review"],
                "next_required_summary": "review-before-execute: locator-renaming-review",
            },
        ),
        _probe(
            "suppressed learned command",
            "make it G Jones energy",
            [{"id": "artist-inspired-energy"}],
            [{"command": "session-snapshot"}],
            [
                {
                    "command": "workflow-macro render bass-resampling-pass",
                    "reason": "query-mismatch",
                    "why": "Artist hint did not explicitly request a resampling pass.",
                    "confidence": 0.5,
                    "sources": [{"type": "artist_inspiration"}],
                }
            ],
            {"status": "inspect-only", "required_before_execution": []},
        ),
        _probe(
            "macro render materialization",
            "make the drums punchier",
            [{"id": "drum-kit-building"}],
            [{"command": "workflow-macro render drum-punch-bus"}],
            [],
            {"status": "ready-to-render", "can_execute_mutations_now": False, "required_before_execution": []},
        ),
    ]


def _probe(
    scenario: str,
    query: str,
    matches: list[dict[str, Any]],
    command_sources: list[dict[str, Any]],
    suppressed_commands: list[dict[str, Any]],
    readiness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "request": {
            "query": query,
            "matches": matches,
            "command_sources": command_sources,
            "suppressed_commands": suppressed_commands,
            "readiness": readiness,
        },
    }


def _unique_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for gap in gaps:
        gap_id = gap.get("id")
        if gap_id and gap_id not in seen:
            seen.add(gap_id)
            unique.append(gap)
    return unique
