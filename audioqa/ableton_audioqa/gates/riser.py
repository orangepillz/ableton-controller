"""Riser, downlifter, and transition sweep gates."""

from __future__ import annotations

from .common import clipping, gate_result, score_from_checks
from ..schemas import GateResult


def score_riser(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    slope = float(features.get("spectral_centroid_slope", 0.0))
    peak = float(features.get("peak_dbfs", -120.0))
    lufs = float(features.get("integrated_lufs", -120.0))
    motion = float(features.get("spectral_centroid_modulation", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if slope < 40.0:
        problems.append("riser_does_not_rise")
        actions.append("automate pitch upward or open the filter cutoff")
    if peak < -24.0 or lufs < -38.0:
        problems.append("riser_too_quiet")
        actions.append("increase brightness and level gradually into the transition")
    if motion < 0.01:
        problems.append("riser_noisy_without_shape")
        actions.append("shape the noise with pitch, filter, reverb, or density automation")
    if clipping(features):
        problems.append("riser_clips_before_drop")
        actions.append("lower the riser peak so it does not clip before the drop")
    checks = [slope >= 40.0, peak >= -24.0, lufs >= -38.0, motion >= 0.01, not clipping(features)]
    metrics = {
        "spectral_centroid_slope": slope,
        "spectral_centroid_modulation": motion,
        "peak_dbfs": peak,
        "integrated_lufs": lufs,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=clipping(features))


def score_downlifter(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    slope = float(features.get("spectral_centroid_slope", 0.0))
    decay = float(features.get("estimated_decay_ms", 0.0))
    peak = float(features.get("peak_dbfs", -120.0))
    problems: list[str] = []
    actions: list[str] = []
    if slope > -25.0:
        problems.append("downlifter_does_not_fall")
        actions.append("automate pitch downward or close the filter cutoff")
    if decay < 250.0:
        problems.append("tail_too_short")
        actions.append("extend the volume fade or reverb tail")
    if peak > -3.0:
        problems.append("tail_too_loud")
        actions.append("lower the faller so it does not cover the next kick transient")
    checks = [slope <= -25.0, decay >= 250.0, peak <= -3.0]
    metrics = {
        "spectral_centroid_slope": slope,
        "estimated_decay_ms": decay,
        "peak_dbfs": peak,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics)


def score_transition(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    riser = score_riser(features, tempo)
    down = score_downlifter(features, tempo)
    best = riser if riser.score >= down.score else down
    if best.pass_:
        return best
    problems = riser.problems + [item for item in down.problems if item not in riser.problems]
    actions = riser.recommended_actions + [
        item for item in down.recommended_actions if item not in riser.recommended_actions
    ]
    return gate_result(max(riser.score, down.score), problems, actions, {**riser.metrics, **down.metrics})
