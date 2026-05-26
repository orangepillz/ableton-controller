"""Wub bass verification gate."""

from __future__ import annotations

from .common import energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_wub(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    low_mid = energy(features, "band_energy_95_140", "band_energy_140_250", "band_energy_250_500")
    bright = energy(features, "band_energy_4000_8000", "band_energy_8000_14000")
    depth = float(features.get("modulation_depth", 0.0))
    rate = float(features.get("modulation_rate_hz", 0.0))
    centroid_motion = float(features.get("spectral_centroid_modulation", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if depth < 0.18:
        problems.append("wub_has_no_modulation")
        actions.append("increase rhythmic volume or filter cutoff automation depth")
    if centroid_motion < 0.06:
        problems.append("wub_filter_motion_too_subtle")
        actions.append("add formant-like EQ or Auto Filter movement")
    if rate <= 0.0 or rate > 16.0:
        problems.append("wub_not_rhythmically_locked")
        actions.append("lock modulation rate to a musical subdivision")
    if low + low_mid < 0.24:
        problems.append("wub_sub_missing")
        actions.append("separate sub support from the moving mid-bass layer")
    if bright > 0.45:
        problems.append("wub_too_bright")
        actions.append("reduce high fizz and focus movement in bass and low mids")
    checks = [depth >= 0.18, centroid_motion >= 0.06, 0.25 <= rate <= 16.0, low + low_mid >= 0.24, bright <= 0.45]
    metrics = {
        "modulation_depth": depth,
        "modulation_rate_hz": rate,
        "spectral_centroid_modulation": centroid_motion,
        "low_energy_40_95_ratio": round(low, 6),
        "low_mid_95_500_ratio": round(low_mid, 6),
        "bright_energy_4k_14k_ratio": round(bright, 6),
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics)
