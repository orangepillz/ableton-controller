"""Recurring improvement run orchestration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ableton_controller.arrangement_labels import marker_label_proposals
from ableton_controller.target_aliases import target_aliases

from .chat_memory import chat_signal_updates
from .config import ImprovementConfig
from .evidence_backlog import add_evidence_backlog
from .goal_coverage import audit_goal_coverage
from .memory import backup_memory, load_memory, record_run, save_memory, set_backlog_status, upsert_backlog, upsert_signal, utc_now
from .personalization import render_profile, sync_intent_mappings, write_profile
from .project_memory import project_signal_updates
from .repo_scan import EXPECTED_CAPABILITIES, scan_repository
from .reports import VALIDATION_COMMANDS, append_changelog, render_report, write_report
from .source_scan import scan_chats, scan_projects
from .workflow_memory import sync_workflow_macros


RESEARCH_BACKLOG = (
    {
        "id": "research-bass-movement",
        "title": "Research modern bass movement and resampling workflows",
        "why": "The copilot should keep improving original bass music sound-design decisions.",
        "expected_impact": "Better movement plans, automation shapes, and resampling sequences.",
        "priority": 4,
    },
    {
        "id": "research-tipper-gjones-chrislake-synthesis",
        "title": "Synthesize non-imitative references from Tipper, G Jones, and Chris Lake",
        "why": "The user explicitly wants inspiration across sound design, groove, arrangement, and mix feel.",
        "expected_impact": "More musically specific heuristics while avoiding direct imitation.",
        "priority": 5,
    },
)


def _add_repo_findings(memory: dict[str, Any], repo: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    updates = {"signals": [], "backlog": []}
    for command in repo["cli_commands"]:
        updates["signals"].append(
            upsert_signal(
                memory,
                category="cli.command",
                label=command,
                evidence="Command is exposed by ableton_controller.parser.build_parser().",
                source="repo-scan",
                confidence_delta=0.01,
            )
        )
    if repo["planner_missing_commands"] or repo["planner_stale_commands"]:
        updates["backlog"].append(
            upsert_backlog(
                memory,
                item_id="planner-command-drift",
                title="Keep producer plan validation command list in sync with the CLI parser",
                why="Dry-run plans should reject impossible commands without rejecting valid new commands.",
                expected_impact="Improves deterministic multi-step planning and regression prevention.",
                priority=1,
                evidence=json.dumps(
                    {
                        "missing": repo["planner_missing_commands"],
                        "stale": repo["planner_stale_commands"],
                    },
                    sort_keys=True,
                ),
            )
        )
    for gap in repo["capability_gaps"]:
        updates["backlog"].append(
            upsert_backlog(
                memory,
                item_id=gap["id"],
                title=gap["title"],
                why=gap["why"],
                expected_impact=gap["impact"],
                priority=3,
                evidence=f"Supporting commands already present: {', '.join(gap['supporting_commands'])}",
            )
        )
    open_gap_ids = {gap["id"] for gap in repo["capability_gaps"]}
    for capability in EXPECTED_CAPABILITIES:
        if capability["id"] in open_gap_ids:
            continue
        resolved = set_backlog_status(
            memory,
            capability["id"],
            "resolved",
            f"Capability marker `{capability['missing_marker']}` is now exposed by the CLI parser.",
        )
        if resolved is not None:
            updates["backlog"].append(resolved)
    return updates


def _add_target_alias_findings(memory: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for alias in target_aliases(memory):
        updates.append(
            upsert_signal(
                memory,
                category="project.target-alias",
                label=alias["label"],
                evidence=f"Derived from project name signals: {', '.join(alias['evidence_signal_ids'])}.",
                source="derived-target-aliases",
                confidence_delta=0.02,
            )
        )
    return updates


def _add_arrangement_label_proposals(memory: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for proposal in marker_label_proposals(memory):
        evidence = ", ".join(proposal.get("evidence_signal_ids", [])[:5])
        updates.append(
            upsert_signal(
                memory,
                category="project.arrangement-label-proposal",
                label=f"beat {proposal['beat']:g}: {proposal['name']}",
                evidence=f"Derived from marker timing and role/phase evidence: {evidence}.",
                source="derived-arrangement-label-proposals",
                confidence_delta=0.02,
            )
        )
    return updates


def _add_research_backlog(memory: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for item in RESEARCH_BACKLOG:
        updates.append(
            upsert_backlog(
                memory,
                item_id=item["id"],
                title=item["title"],
                why=item["why"],
                expected_impact=item["expected_impact"],
                priority=item["priority"],
                evidence="Seeded from active long-term goal.",
            )
        )
    synthesis = Path(__file__).resolve().parents[1] / "skills" / "ableton-producer" / "references" / "research-synthesis.md"
    if synthesis.exists():
        text = synthesis.read_text(encoding="utf-8")
        has_artist_synthesis = all(name in text for name in ("Tipper", "G Jones", "Chris Lake"))
        has_sources = "https://" in text and "Non-Imitation Rule" in text
        if has_artist_synthesis and has_sources:
            resolved = set_backlog_status(
                memory,
                "research-tipper-gjones-chrislake-synthesis",
                "resolved",
                "Research synthesis reference exists with named artists, source links, and non-imitation guidance.",
            )
            if resolved is not None:
                updates.append(resolved)
        has_bass_resampling = all(
            phrase in text
            for phrase in ("Bass Movement And Resampling Workflow", "bass-resampling-pass", "Resampling")
        )
        if has_bass_resampling:
            resolved = set_backlog_status(
                memory,
                "research-bass-movement",
                "resolved",
                "Research synthesis reference includes bass movement, resampling guidance, and a reusable macro hook.",
            )
            if resolved is not None:
                updates.append(resolved)
    return updates


def _run_validation(repo_root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in VALIDATION_COMMANDS:
        result = subprocess.run(command.split(), cwd=repo_root, text=True, capture_output=True, check=False)
        results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
            }
        )
    return results


def run_improvement(
    config: ImprovementConfig,
    validate: bool = False,
    note: str | None = None,
    why: str | None = None,
    expected_impact: str | None = None,
) -> dict[str, Any]:
    run_id = utc_now().replace(":", "").replace("-", "")
    run_dir = config.state_dir / "runs" / run_id
    memory_path = config.state_dir / "memory.json"
    memory_backup = backup_memory(memory_path, config.state_dir / "backups", run_id)
    memory = load_memory(memory_path)

    repository = scan_repository(config.repo_root)
    projects = scan_projects(config.project_roots)
    chats = scan_chats(config.chat_roots)

    repo_updates = _add_repo_findings(memory, repository)
    memory_updates = {
        "signals": repo_updates["signals"],
        "backlog": repo_updates["backlog"],
    }
    memory_updates["signals"].extend(project_signal_updates(memory, projects))
    memory_updates["signals"].extend(_add_arrangement_label_proposals(memory))
    memory_updates["signals"].extend(_add_target_alias_findings(memory))
    memory_updates["signals"].extend(chat_signal_updates(memory, chats))
    memory_updates["backlog"].extend(add_evidence_backlog(memory, projects, chats))
    memory_updates["backlog"].extend(_add_research_backlog(memory))
    memory_updates["intent_mappings"] = sync_intent_mappings(memory)
    memory_updates["workflow_macros"] = sync_workflow_macros(memory)

    validation = _run_validation(config.repo_root) if validate else []
    run = {
        "run_id": run_id,
        "started_at": utc_now(),
        "repository": repository,
        "projects": projects,
        "chats": chats,
        "memory_updates": memory_updates,
        "memory_backup": str(memory_backup) if memory_backup else None,
        "validation": validation,
        "operator_note": {
            "changed": note or "",
            "why": why or "",
            "expected_impact": expected_impact or "",
        },
    }
    run["report_path"] = str(run_dir / "improvement-report.md")
    run["reasoning_log_path"] = str(run_dir / "reasoning-log.json")
    record_run(memory, {"run_id": run_id, "started_at": run["started_at"], "report": str(run_dir / "improvement-report.md")})

    run_dir.mkdir(parents=True, exist_ok=True)
    memory["updated_at"] = utc_now()
    profile_paths = write_profile(render_profile(memory, run), run_dir, config.state_dir)
    run["profile_path"] = str(profile_paths["latest"])
    run["run_profile_path"] = str(profile_paths["run"])
    save_memory(memory, memory_path)
    run["goal_coverage"] = audit_goal_coverage(config, run, memory)
    (run_dir / "reasoning-log.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = write_report(render_report(run, memory), run_dir, config.state_dir)
    append_changelog(config.state_dir, run)
    run["report_path"] = str(report_path)
    run["memory_path"] = str(memory_path)
    return run
