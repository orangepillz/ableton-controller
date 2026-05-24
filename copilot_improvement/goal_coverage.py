"""Coverage audit for the long-running copilot self-improvement goal."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .config import ImprovementConfig


AUTOMATION_ID = "ableton-producer-copilot-self-improvement"


def audit_goal_coverage(
    config: ImprovementConfig,
    run: dict[str, Any],
    memory: dict[str, Any],
    codex_home: Path | None = None,
) -> dict[str, Any]:
    repo = run["repository"]
    projects = run["projects"]
    chats = run["chats"]
    validation = run.get("validation", [])
    items = [
        _scheduler_item(config, codex_home),
        _memory_item(memory, run),
        _reporting_item(run, config.state_dir),
        _rollback_item(run),
        _validation_item(validation),
        _project_evidence_item(projects),
        _chat_evidence_item(chats),
        _personalization_item(memory, run),
        _workflow_item(repo),
        _research_item(config.repo_root),
        _maintainability_item(repo),
    ]
    return {"items": items, "summary": _summary(items), "next_targets": _next_targets(items)}


def _scheduler_item(config: ImprovementConfig, codex_home: Path | None) -> dict[str, Any]:
    path = _automation_path(codex_home)
    if not path.exists():
        return _item("scheduler", "Six-hour recurring scheduler", "missing", "Automation TOML was not found.", "Create or restore the six-hour cron automation.")
    text = path.read_text(encoding="utf-8", errors="ignore")
    has_cwd = str(config.repo_root) in text
    has_schedule = 'rrule = "FREQ=HOURLY;INTERVAL=6"' in text
    active = 'status = "ACTIVE"' in text
    has_final_report = "run --validate --note" in text
    has_remote_compile = "remote_scripts" in text
    if active and has_schedule and has_cwd and has_final_report and has_remote_compile:
        return _item("scheduler", "Six-hour recurring scheduler", "proven", f"Active automation at {path}.", "Keep automation prompt aligned with validation commands.")
    details = []
    if not active:
        details.append("not active")
    if not has_schedule:
        details.append("not six-hour")
    if not has_cwd:
        details.append("workspace missing")
    if not has_final_report:
        details.append("final report command missing")
    if not has_remote_compile:
        details.append("remote_scripts compile gate missing")
    return _item("scheduler", "Six-hour recurring scheduler", "partial", f"Automation exists but needs attention: {', '.join(details)}.", "Update the automation prompt and schedule.")


def _memory_item(memory: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    signals = len(memory.get("signals", []))
    runs = len(memory.get("runs", []))
    if signals and runs:
        return _item("memory", "Long-term memory persistence", "proven", f"Memory has {signals} signals and {runs} recorded runs.", "Continue pruning duplicate evidence and preserving confidence history.")
    return _item("memory", "Long-term memory persistence", "missing", "Memory has no recorded signals or runs.", "Run the improvement scanner to seed memory.")


def _reporting_item(run: dict[str, Any], state_dir: Path) -> dict[str, Any]:
    has_paths = bool(run.get("report_path") and run.get("reasoning_log_path"))
    changelog = state_dir / "CHANGELOG.md"
    if has_paths and changelog.exists():
        return _item("reports", "Reports, reasoning logs, and changelog", "proven", "Run records report path, reasoning-log path, and changelog exists.", "Keep each run note explicit about what changed and why.")
    return _item("reports", "Reports, reasoning logs, and changelog", "partial", "One or more report artifacts are not yet visible to the audit.", "Record report and reasoning log paths before rendering coverage.")


def _rollback_item(run: dict[str, Any]) -> dict[str, Any]:
    backup = run.get("memory_backup")
    if backup:
        return _item("rollback", "Rollback and recovery", "proven", f"Memory backup recorded at {backup}.", "Use targeted git rollback for source changes and memory rollback for state.")
    return _item("rollback", "Rollback and recovery", "partial", "No memory backup because this may be an initial run.", "Verify rollback after at least one follow-up run.")


def _validation_item(validation: list[dict[str, Any]]) -> dict[str, Any]:
    if validation and all(item.get("returncode") == 0 for item in validation):
        commands = ", ".join(item["command"] for item in validation)
        return _item("validation", "Regression prevention validation", "proven", f"Validation passed: {commands}.", "Keep validation commands in automation and reports synchronized.")
    if validation:
        return _item("validation", "Regression prevention validation", "partial", "Validation ran but at least one command failed.", "Fix failing gates before accepting the run.")
    return _item("validation", "Regression prevention validation", "partial", "Validation was not requested for this run.", "Run with --validate after source edits.")


def _project_evidence_item(projects: dict[str, Any]) -> dict[str, Any]:
    files = int(projects.get("files_seen", 0))
    if files:
        return _item("historical-projects", "Historical Ableton project analysis", "proven", f"Scanned {files} project file(s).", "Broaden project feature extraction beyond names/devices over time.")
    return _item("historical-projects", "Historical Ableton project analysis", "missing", "No project files were scanned.", "Connect Ableton project roots.")


def _chat_evidence_item(chats: dict[str, Any]) -> dict[str, Any]:
    files = int(chats.get("files_seen", 0))
    if files:
        return _item("historical-chats", "Historical Ableton chat analysis", "proven", f"Scanned {files} chat/session file(s).", "Keep extracting shorthand, corrections, and recurring prompt shapes.")
    return _item("historical-chats", "Historical Ableton chat analysis", "missing", "No chat files were scanned.", "Connect ableton-chats or local Codex sessions.")


def _personalization_item(memory: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    mappings = len(memory.get("intent_mappings", []))
    profile = Path(run.get("profile_path", ""))
    if mappings and profile.exists():
        return _item("personalization", "Personalized intent mappings and profile", "proven", f"{mappings} active mappings and profile at {profile}.", "Keep turning repeated requests into executable workflow abstractions.")
    return _item("personalization", "Personalized intent mappings and profile", "partial", "Profile or mappings are missing.", "Generate the workflow profile after memory updates.")


def _workflow_item(repo: dict[str, Any]) -> dict[str, Any]:
    commands = set(repo.get("cli_commands", []))
    required = {"copilot-intent", "workflow-macro", "session-snapshot", "drum-pad-load"}
    if required.issubset(commands):
        return _item(
            "workflow-abstractions",
            "Reusable workflow abstractions",
            "proven",
            "CLI exposes copilot-intent, workflow-macro, session-snapshot, and drum-pad-load.",
            "Keep adding macros only when evidence shows repeated workflows.",
        )
    return _item("workflow-abstractions", "Reusable workflow abstractions", "partial", "Some workflow command surfaces are missing.", "Add focused command or macro support for repeated workflows.")


def _research_item(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "skills" / "ableton-producer" / "references" / "research-synthesis.md"
    if not path.exists():
        return _item("research", "Production research synthesis", "missing", "Research synthesis reference is absent.", "Create source-backed synthesis for producer inspiration.")
    text = path.read_text(encoding="utf-8", errors="ignore")
    names = all(name in text for name in ("Tipper", "G Jones", "Chris Lake"))
    source_backed = "https://" in text and "Non-Imitation Rule" in text
    if names and source_backed:
        return _item("research", "Production research synthesis", "proven", "Research reference includes named artists, sources, and non-imitation guidance.", "Continue adding focused technique updates from credible sources.")
    return _item("research", "Production research synthesis", "partial", "Research reference exists but lacks required names, sources, or non-imitation guidance.", "Fill the missing research sections.")


def _maintainability_item(repo: dict[str, Any]) -> dict[str, Any]:
    warnings = repo.get("size_warnings", [])
    drift = repo.get("planner_missing_commands") or repo.get("planner_stale_commands")
    if not warnings and not drift:
        return _item("maintainability", "Maintainability and planner drift", "proven", "No size warnings and no planner command drift.", "Keep modules focused as new capabilities land.")
    details = []
    if warnings:
        details.append(f"{len(warnings)} size warning(s)")
    if drift:
        details.append("planner command drift")
    return _item("maintainability", "Maintainability and planner drift", "partial", ", ".join(details), "Resolve drift or split oversized modules.")


def _automation_path(codex_home: Path | None) -> Path:
    root = codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return root / "automations" / AUTOMATION_ID / "automation.toml"


def _item(item_id: str, title: str, status: str, evidence: str, next_action: str) -> dict[str, str]:
    return {"id": item_id, "title": title, "status": status, "evidence": evidence, "next_action": next_action}


def _summary(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "proven": sum(1 for item in items if item["status"] == "proven"),
        "partial": sum(1 for item in items if item["status"] == "partial"),
        "missing": sum(1 for item in items if item["status"] == "missing"),
    }


def _next_targets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item["status"] != "proven"][:4]
