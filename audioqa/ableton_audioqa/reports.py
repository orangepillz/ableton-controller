"""Report file IO and section-level summaries."""

from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path | None, payload: dict[str, Any]) -> None:
    text = dumps(payload)
    if path is None:
        print(text)
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def expand_report_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(Path(match) for match in (matches or [pattern]))
    return paths


def summarize_section(section: str, report_paths: list[str], bars: str | None = None) -> dict[str, Any]:
    reports = [read_json(path) for path in expand_report_paths(report_paths)]
    failed = [report for report in reports if not report.get("pass", False)]
    score_values = [float(report.get("score", 0.0)) for report in reports]
    priority_failures = [_failure_summary(report) for report in sorted(failed, key=_failure_sort_key)]
    return {
        "section": section,
        "bars": bars or "",
        "overall_pass": not failed and bool(reports),
        "score": round(sum(score_values) / len(score_values), 4) if score_values else 0.0,
        "priority_failures": priority_failures,
        "allowed_next_actions": _allowed_actions(priority_failures),
        "blocked_next_actions": [
            "add more glitches",
            "add more atmospheric pads",
            "add new bass phrases before drum impact passes",
        ]
        if priority_failures
        else [],
        "reports": [str(path) for path in expand_report_paths(report_paths)],
    }


def manifest_path_for_audio(path: str | Path) -> Path:
    audio = Path(path)
    return audio.with_suffix(".manifest.json")


def _failure_sort_key(report: dict[str, Any]) -> tuple[int, float]:
    severity_order = {"critical": 0, "major": 1, "warning": 2, "info": 3}
    return (severity_order.get(str(report.get("severity")), 9), float(report.get("score", 1.0)))


def _failure_summary(report: dict[str, Any]) -> dict[str, Any]:
    problems = report.get("problems") or ["gate failed"]
    actions = report.get("recommended_actions") or ["repair the highest-priority failed gate"]
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    evidence = {key: metrics[key] for key in list(metrics)[:8]}
    return {
        "target": report.get("target", "unknown"),
        "severity": report.get("severity", "critical"),
        "summary": str(problems[0]),
        "evidence": evidence,
        "required_fix": str(actions[0]),
    }


def _allowed_actions(priority_failures: list[dict[str, Any]]) -> list[str]:
    if not priority_failures:
        return ["continue with creative polish after preserving render evidence"]
    targets = {str(item.get("target", "")) for item in priority_failures}
    actions = []
    if any("kick" in target for target in targets):
        actions.append("rebuild kick rack")
    if any("snare" in target for target in targets):
        actions.append("rebuild snare rack")
    if any("bass" in target or "low" in target for target in targets):
        actions.append("add kick and bass ducking")
    actions.append("rebalance drop drums before adding ear candy")
    return actions
