"""Drop impact verification gate."""

from __future__ import annotations

from .common import clipping, crack_energy, energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_drop(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    snare_body = energy(features, "band_energy_140_250")
    snare_crack = crack_energy(features)
    noise = energy(features, "band_energy_4000_8000", "band_energy_8000_14000")
    onset_count = int(features.get("onset_count", 0))
    onset_max = float(features.get("onset_strength_max", 0.0))
    crest = float(features.get("crest_factor_db", 0.0))
    mono = float(features.get("mono_low_end_ratio", 1.0))
    problems: list[str] = []
    actions: list[str] = []
    if low < 0.08 or onset_max < 0.035:
        problems.append("kick_missing_in_drop")
        actions.append("fix kick impact before adding more layers")
    if snare_body < 0.008 or snare_crack < 0.008:
        problems.append("snare_missing_in_drop")
        actions.append("rebuild snare body and crack before adding ear candy")
    if mono < 0.75:
        problems.append("low_end_not_mono_compatible")
        actions.append("keep sub and kick fundamentals mono")
    if noise > 0.62 and snare_body < 0.02:
        problems.append("too_much_noise")
        actions.append("reduce noise washes if they mask snare")
    if crest < 4.0:
        problems.append("overcompressed_flat_drop")
        actions.append("restore transient contrast in the drum and bass buses")
    if onset_count < 2:
        problems.append("transition_impact_missing")
        actions.append("add clear downbeat and backbeat anchors")
    if clipping(features):
        problems.append("full_mix_clipping")
        actions.append("leave headroom before judging drop impact")
    checks = [low >= 0.08, onset_max >= 0.035, snare_body >= 0.008, snare_crack >= 0.008, mono >= 0.75, noise <= 0.68, crest >= 4.0, onset_count >= 2, not clipping(features)]
    metrics = {
        "low_energy_40_95_ratio": round(low, 6),
        "snare_body_140_250hz_ratio": round(snare_body, 6),
        "snare_crack_1k5_8khz_ratio": round(snare_crack, 6),
        "noise_4k_14khz_ratio": round(noise, 6),
        "onset_count": onset_count,
        "onset_strength_max": onset_max,
        "crest_factor_db": crest,
        "mono_low_end_ratio": mono,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=clipping(features))
