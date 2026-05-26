"""Analyze rendered WAV probes against target-specific gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .features import extract_features
from .gates import GATES, SUPPORTED_TARGETS
from .references import reference_deltas
from .reports import manifest_path_for_audio
from .schemas import AudioQAReport, stable_created_at


def analyze_file(
    file_path: str | Path,
    target: str,
    tempo: float | None = None,
    reference_data: dict[str, Any] | None = None,
    render_manifest: str | None = None,
) -> dict[str, Any]:
    normalized_target = normalize_target(target)
    features = extract_features(file_path)
    gate = GATES[normalized_target](features, tempo)
    metrics = dict(features)
    metrics.update(gate.metrics)
    if reference_data:
        metrics.update(reference_deltas(normalized_target, features, reference_data))
    manifest = render_manifest or _existing_manifest(file_path)
    report = AudioQAReport(
        target=normalized_target,
        file=str(file_path),
        pass_=gate.pass_,
        score=gate.score,
        severity=gate.severity,
        problems=gate.problems,
        metrics=metrics,
        recommended_actions=gate.recommended_actions,
        render_manifest=manifest,
        created_at=stable_created_at(file_path),
    )
    return report.to_dict()


def normalize_target(target: str) -> str:
    normalized = target.strip().lower().replace("_", "-")
    aliases = {
        "bass": "bass-bus",
        "bass_bus": "bass-bus",
        "full": "full-mix",
        "mix": "full-mix",
        "downlift": "downlifter",
        "faller": "downlifter",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in GATES:
        raise ValueError(f"Unsupported target {target!r}. Supported targets: {', '.join(SUPPORTED_TARGETS)}")
    return normalized


def _existing_manifest(file_path: str | Path) -> str | None:
    manifest = manifest_path_for_audio(file_path)
    return str(manifest) if manifest.exists() else None
