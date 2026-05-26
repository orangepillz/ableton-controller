"""Full-mix balance verification gate."""

from __future__ import annotations

from .common import clipping, energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_full_mix(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    low_mid = energy(features, "band_energy_140_250", "band_energy_250_500")
    highs = energy(features, "band_energy_4000_8000", "band_energy_8000_14000")
    lufs = float(features.get("integrated_lufs", -120.0))
    peak = float(features.get("peak_dbfs", -120.0))
    crest = float(features.get("crest_factor_db", 0.0))
    correlation = float(features.get("stereo_correlation", 1.0))
    problems: list[str] = []
    actions: list[str] = []
    if clipping(features):
        problems.append("full_mix_clipping")
        actions.append("leave headroom before mix decisions")
    if low < 0.05 or low_mid > 0.55:
        problems.append("low_end_uncontrolled")
        actions.append("fix the loudest masking problem first")
    if highs > 0.65:
        problems.append("highs_too_harsh")
        actions.append("reduce unnecessary bright noise or harsh layers")
    if crest < 3.5:
        problems.append("mix_too_flat")
        actions.append("restore drum-to-bass transient contrast")
    if correlation < -0.1:
        problems.append("stereo_phase_risk")
        actions.append("narrow phasey layers and keep low end mono")
    checks = [not clipping(features), 0.05 <= low <= 0.45, low_mid <= 0.55, highs <= 0.65, crest >= 3.5, correlation >= -0.1, -34.0 <= lufs <= -6.0, peak <= -0.1]
    metrics = {
        "integrated_lufs": lufs,
        "peak_dbfs": peak,
        "crest_factor_db": crest,
        "low_energy_40_95_ratio": round(low, 6),
        "low_mid_140_500_ratio": round(low_mid, 6),
        "high_energy_4k_14k_ratio": round(highs, 6),
        "stereo_correlation": correlation,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=clipping(features))
