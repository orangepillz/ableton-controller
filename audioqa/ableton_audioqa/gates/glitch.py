"""Glitch and microfill verification gate."""

from __future__ import annotations

from .common import gate_result, score_from_checks
from ..schemas import GateResult


def score_glitch(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    duration = max(0.001, float(features.get("duration_seconds", 0.0)))
    density = float(features.get("onset_count", 0)) / duration
    flux = float(features.get("spectral_flux", 0.0))
    width = 1.0 - abs(float(features.get("stereo_correlation", 1.0)))
    peak = float(features.get("peak_dbfs", -120.0))
    problems: list[str] = []
    actions: list[str] = []
    if density < 1.2:
        problems.append("glitch_density_too_low")
        actions.append("add short 1/16 or 1/32 edits before transitions")
    if peak > -3.0:
        problems.append("glitch_events_too_loud")
        actions.append("lower the glitch bus if it masks drums")
    if width < 0.05:
        problems.append("no_stereo_motion")
        actions.append("use small pan or Auto Pan movements for ear-candy motion")
    if flux < 0.02:
        problems.append("glitches_not_rhythmically_intentional")
        actions.append("make edits short and contrasted instead of static noise")
    checks = [density >= 1.2, peak <= -3.0, width >= 0.05, flux >= 0.02]
    metrics = {
        "event_density_per_second": round(density, 6),
        "spectral_flux": flux,
        "stereo_motion_width": round(width, 6),
        "peak_dbfs": peak,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics)
