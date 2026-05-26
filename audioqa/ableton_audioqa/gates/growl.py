"""Growl, yoi, and talking-bass verification gate."""

from __future__ import annotations

from .common import energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_growl(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    mids = energy(features, "band_energy_250_500", "band_energy_500_1500", "band_energy_1500_4000")
    bandwidth = float(features.get("spectral_bandwidth_mean", 0.0))
    flux = float(features.get("spectral_flux", 0.0))
    motion = float(features.get("spectral_centroid_modulation", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if motion < 0.07:
        problems.append("no_formant_motion")
        actions.append("automate moving band-pass, notch, or formant-like EQ peaks")
    if bandwidth < 300.0 or mids < 0.08:
        problems.append("too_sine_like")
        actions.append("add harmonic density with FM-like movement or saturation after filtering")
    if low + mids < 0.22:
        problems.append("too_thin")
        actions.append("restore low body before adding harshness")
    if flux < 0.015:
        problems.append("too_static")
        actions.append("vary modulation position between notes")
    checks = [motion >= 0.07, bandwidth >= 300.0, mids >= 0.08, low + mids >= 0.22, flux >= 0.015]
    metrics = {
        "low_energy_40_95_ratio": round(low, 6),
        "midrange_250_4k_ratio": round(mids, 6),
        "spectral_bandwidth_mean": bandwidth,
        "spectral_flux": flux,
        "spectral_centroid_modulation": motion,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics)
