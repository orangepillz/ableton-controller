"""Snare and backbeat verification gate."""

from __future__ import annotations

from .common import clipping, crack_energy, energy, gate_result, score_from_checks
from ..schemas import GateResult


def score_snare(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    body = energy(features, "band_energy_140_250")
    crack = crack_energy(features)
    noise = energy(features, "band_energy_4000_8000", "band_energy_8000_14000")
    peak = float(features.get("peak_dbfs", -120.0))
    crest = float(features.get("crest_factor_db", 0.0))
    attack = float(features.get("attack_ms", 999.0))
    decay = float(features.get("estimated_decay_ms", 0.0))
    correlation = float(features.get("stereo_correlation", 1.0))
    problems: list[str] = []
    actions: list[str] = []
    if peak < -12.0:
        problems.append("snare_too_quiet_vs_kick")
        actions.append("raise the snare bus after the kick passes")
    if crest < 7.0 or attack > 16.0:
        problems.append("snare_transient_too_soft")
        actions.append("add a short clap, rim, or transient crack layer")
    if body < 0.012:
        problems.append("snare_body_missing")
        actions.append("layer a body sample or tom-like synthesized body")
    if crack < 0.035:
        problems.append("snare_crack_missing")
        actions.append("add or EQ a 1.5 to 4 kHz crack layer")
    if noise > 0.62 and body < 0.03:
        problems.append("snare_noise_tail_overdominant")
        actions.append("band-pass and envelope the noise tail instead of using raw noise")
    if correlation < 0.2 and attack < 30.0:
        problems.append("snare_too_wide_on_transient")
        actions.append("make the transient mostly mono while allowing the tail to widen")
    if decay > 700.0:
        problems.append("snare_tail_too_long")
        actions.append("shorten the noise or room tail so it does not mask the groove")
    if clipping(features):
        problems.append("snare_clipping")
        actions.append("lower the snare bus or remove clipping before judging tone")
    checks = [peak >= -12.0, crest >= 7.0, attack <= 16.0, body >= 0.012, crack >= 0.035, noise <= 0.72, decay <= 700.0]
    metrics = {
        "peak_dbfs": peak,
        "crest_factor_db": crest,
        "attack_ms": attack,
        "estimated_decay_ms": decay,
        "body_140_250hz_ratio": round(body, 6),
        "crack_1k5_8khz_ratio": round(crack, 6),
        "noise_tail_4k_14khz_ratio": round(noise, 6),
        "stereo_correlation": correlation,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=clipping(features))
