"""Stable JSON-compatible report schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Severity = Literal["info", "warning", "major", "critical"]
MetricValue = float | int | str | bool

SEVERITIES = {"info", "warning", "major", "critical"}


@dataclass
class AudioQAReport:
    target: str
    file: str
    pass_: bool
    score: float
    severity: Severity
    problems: list[str]
    metrics: dict[str, MetricValue]
    recommended_actions: list[str]
    version: int = 1
    render_manifest: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _clean(
            {
                "version": self.version,
                "target": self.target,
                "file": self.file,
                "pass": self.pass_,
                "score": _clamp_score(self.score),
                "severity": _severity(self.severity),
                "problems": list(self.problems),
                "metrics": dict(self.metrics),
                "recommended_actions": list(self.recommended_actions),
                "render_manifest": self.render_manifest,
                "created_at": self.created_at,
            }
        )


@dataclass
class AudioQACompareReport:
    target: str
    primary_file: str
    context_file: str
    pass_: bool
    score: float
    severity: Severity
    problems: list[str]
    metrics: dict[str, MetricValue]
    recommended_actions: list[str]
    version: int = 1
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "target": self.target,
            "primary_file": self.primary_file,
            "context_file": self.context_file,
            "pass": self.pass_,
            "score": _clamp_score(self.score),
            "severity": _severity(self.severity),
            "problems": list(self.problems),
            "metrics": dict(self.metrics),
            "recommended_actions": list(self.recommended_actions),
            "created_at": self.created_at,
        }


@dataclass
class GateResult:
    pass_: bool
    score: float
    severity: Severity
    problems: list[str] = field(default_factory=list)
    metrics: dict[str, MetricValue] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)


def stable_created_at(*paths: str | Path) -> str:
    """Return a deterministic timestamp derived from analyzed input files."""

    mtimes = []
    for path in paths:
        file_path = Path(path)
        if file_path.exists():
            mtimes.append(file_path.stat().st_mtime)
    timestamp = max(mtimes) if mtimes else datetime.now(timezone.utc).timestamp()
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _severity(value: str) -> Severity:
    if value in SEVERITIES:
        return value  # type: ignore[return-value]
    return "critical"


def _clamp_score(score: float) -> float:
    return round(max(0.0, min(1.0, float(score))), 4)


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}
