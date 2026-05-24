"""Markdown reports for recurring improvement runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


VALIDATION_COMMANDS = (
    "python3 -m compileall -q ableton_controller copilot_improvement remote_scripts scripts tests",
    "python3 -m unittest discover -s tests",
    "python3 scripts/copilot_size_gate.py",
)


def _lines_for_backlog(backlog: list[dict[str, Any]], limit: int = 8) -> list[str]:
    open_items = [item for item in backlog if item.get("status") == "open"]
    if not open_items:
        return ["- No open backlog items."]
    ranked = sorted(open_items, key=lambda item: int(item.get("priority", 99)))[:limit]
    return [
        f"- P{item['priority']} `{item['id']}`: {item['title']} Expected impact: {item['expected_impact']}"
        for item in ranked
    ]


def _unique_by_id(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item.get("id"))
        if item_id in seen:
            continue
        seen.add(item_id)
        unique.append(item)
    return unique


def _runtime_gap_lines(gaps: list[dict[str, Any]], limit: int = 10) -> list[str]:
    if not gaps:
        return ["- No runtime planner gap detectors were cataloged."]
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    ranked = sorted(gaps, key=lambda item: (priority_rank.get(str(item.get("priority", "")), 9), item.get("id", "")))
    return [
        f"- `{item['id']}` {item['priority']} / {item['type']}: {item['scenario']}. Next: {item['next_action']}"
        for item in ranked[:limit]
    ]


def render_report(run: dict[str, Any], memory: dict[str, Any]) -> str:
    repo = run["repository"]
    projects = run["projects"]
    chats = run["chats"]
    updates = run["memory_updates"]
    changed_signals = [signal for signal in updates["signals"] if signal.get("changed", True)]
    changed_backlog = [item for item in updates["backlog"] if item.get("changed", True)]
    changed_mappings = [item for item in updates.get("intent_mappings", []) if item.get("changed", True)]
    changed_macros = [item for item in updates.get("workflow_macros", []) if item.get("changed", True)]
    final_backlog_status = {item.get("id"): item.get("status", "open") for item in memory.get("backlog", [])}
    git = repo["git"]
    validation = run.get("validation", [])
    operator_note = run.get("operator_note") or {}
    open_changed_backlog = [item for item in changed_backlog if final_backlog_status.get(item.get("id"), item.get("status", "open")) == "open"]
    resolved_backlog = _unique_by_id(
        [item for item in changed_backlog if final_backlog_status.get(item.get("id"), item.get("status")) == "resolved"]
    )
    lines = [
        f"# Ableton Copilot Improvement Run {run['run_id']}",
        "",
        "## Summary",
        f"- Started: {run['started_at']}",
        f"- Git: `{git.get('branch', '')}` at `{git.get('head', '')}`",
        f"- CLI commands indexed: {len(repo['cli_commands'])}",
        f"- Project files scanned: {projects['files_seen']}",
        f"- Chat files scanned: {chats['files_seen']}",
        f"- Memory signals observed: {len(updates['signals'])}",
        f"- Memory signals with new evidence: {len(changed_signals)}",
        f"- Intent mappings active: {len(memory.get('intent_mappings', []))}",
        f"- Intent mappings changed: {len(changed_mappings)}",
        f"- Workflow macros tracked: {len(memory.get('workflow_macros', []))}",
        f"- Workflow macros changed: {len(changed_macros)}",
        f"- Runtime planner gap detectors: {len(repo.get('runtime_capability_gaps', []))}",
        f"- Backlog items observed: {len(updates['backlog'])}",
        f"- Backlog items changed: {len(changed_backlog)}",
        "",
        "## What Changed",
    ]
    if operator_note.get("changed"):
        lines.extend(
            [
                f"- Source/workflow change: {operator_note['changed']}",
                f"- Why: {operator_note.get('why') or 'Not specified.'}",
                f"- Expected impact: {operator_note.get('expected_impact') or 'Not specified.'}",
            ]
        )
    if changed_signals:
        for signal in changed_signals[:12]:
            lines.append(
                f"- `{signal['id']}` confidence {signal['confidence']}: {signal['label']}"
            )
    elif not operator_note.get("changed"):
        lines.append("- No new confidence-scored signals this run.")
    if changed_mappings:
        lines.append("")
        lines.append("## Intent Mappings")
        for mapping in changed_mappings[:8]:
            lines.append(
                f"- `{mapping['id']}` confidence {mapping['confidence']}: {mapping['title']}"
            )
    if changed_macros:
        lines.append("")
        lines.append("## Workflow Macros")
        for macro in changed_macros[:8]:
            links = ", ".join(macro.get("linked_intent_ids", [])) or "registry only"
            lines.append(f"- `{macro['name']}` confidence {macro['confidence']}: {macro['description']} Linked intents: {links}.")
    if run.get("profile_path"):
        lines.append("")
        lines.append("## Personalized Profile")
        lines.append(f"- Latest profile: `{run['profile_path']}`")
        lines.append(f"- Run profile: `{run.get('run_profile_path', '')}`")
    lines.append("")
    lines.append("## Planner Gap Coverage")
    lines.extend(_runtime_gap_lines(repo.get("runtime_capability_gaps", [])))
    coverage = run.get("goal_coverage")
    if coverage:
        summary = coverage.get("summary", {})
        lines.append("")
        lines.append("## Goal Coverage")
        lines.append(
            f"- Proven: {summary.get('proven', 0)}; Partial: {summary.get('partial', 0)}; Missing: {summary.get('missing', 0)}"
        )
        for item in coverage.get("items", [])[:12]:
            lines.append(f"- `{item['id']}` {item['status']}: {item['title']}")
            lines.append(f"  Evidence: {item['evidence']}")
            if item["status"] != "proven":
                lines.append(f"  Next: {item['next_action']}")
    if open_changed_backlog:
        lines.append("")
        lines.append("## Improvement Opportunities")
        for item in open_changed_backlog[:12]:
            lines.append(f"- P{item['priority']} `{item['id']}`: {item['title']}")
            lines.append(f"  Why: {item['why']}")
            lines.append(f"  Expected impact: {item['expected_impact']}")
    if resolved_backlog:
        lines.append("")
        lines.append("## Resolved Backlog")
        for item in resolved_backlog[:12]:
            lines.append(f"- `{item['id']}`: {item['title']}")
    lines.extend(
        [
            "",
            "## Current Open Backlog",
            *_lines_for_backlog(memory.get("backlog", [])),
            "",
            "## Validation",
        ]
    )
    if validation:
        for item in validation:
            status = "passed" if item["returncode"] == 0 else f"failed ({item['returncode']})"
            lines.append(f"- `{item['command']}`: {status}")
    else:
        for command in VALIDATION_COMMANDS:
            lines.append(f"- Recommended after source edits: `{command}`")
    lines.extend(
        [
            "",
            "## Rollback And Recovery",
            f"- Memory backup: `{run.get('memory_backup') or 'none; first run created memory'}`",
            "- Source rollback: use git to inspect or revert only the files changed by the scheduled run.",
            "- State rollback: `python3 scripts/copilot_improvement.py rollback --run-id "
            f"{run['run_id']}`",
            "",
            "## Next Run Guidance",
            "- Prefer one measurable improvement over broad cleanup.",
            "- Update tests or skill references whenever behavior changes.",
            "- Synthesize artist inspiration into original heuristics; do not imitate.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(report: str, run_dir: Path, state_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "improvement-report.md"
    report_path.write_text(report, encoding="utf-8")
    latest = state_dir / "latest-report.md"
    latest.write_text(report, encoding="utf-8")
    return report_path


def append_changelog(state_dir: Path, run: dict[str, Any]) -> Path:
    path = state_dir / "CHANGELOG.md"
    created = not path.exists()
    with path.open("a", encoding="utf-8") as handle:
        if created:
            handle.write("# Ableton Copilot Improvement Changelog\n\n")
        changed_signals = [item for item in run["memory_updates"]["signals"] if item.get("changed", True)]
        changed_backlog = [item for item in run["memory_updates"]["backlog"] if item.get("changed", True)]
        changed_mappings = [item for item in run["memory_updates"].get("intent_mappings", []) if item.get("changed", True)]
        changed_macros = [item for item in run["memory_updates"].get("workflow_macros", []) if item.get("changed", True)]
        coverage = run.get("goal_coverage", {}).get("summary", {})
        handle.write(f"## {run['run_id']}\n")
        handle.write(f"- Report: `runs/{run['run_id']}/improvement-report.md`\n")
        handle.write(f"- Signals with new evidence: {len(changed_signals)}\n")
        handle.write(f"- Intent mappings changed: {len(changed_mappings)}\n")
        handle.write(f"- Workflow macros changed: {len(changed_macros)}\n")
        if coverage:
            handle.write(
                f"- Goal coverage: {coverage.get('proven', 0)} proven, {coverage.get('partial', 0)} partial, {coverage.get('missing', 0)} missing\n"
            )
        handle.write(f"- Backlog changed: {len(changed_backlog)}\n\n")
    return path
