"""Kick drum verification gate."""

from __future__ import annotations

from .common import body_energy, clipping, crack_energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_kick(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    body = body_energy(features)
    click = crack_energy(features)
    peak = float(features.get("peak_dbfs", -120.0))
    crest = float(features.get("crest_factor_db", 0.0))
    attack = float(features.get("attack_ms", 999.0))
    decay = float(features.get("estimated_decay_ms", 0.0))
    onset = float(features.get("onset_strength_max", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if peak < -12.0:
        problems.append("kick_peak_too_low")
        actions.append("raise or layer the kick transient before balancing other elements")
    if low < 0.12:
        problems.append("kick_sub_energy_too_low")
        actions.append("add an Operator sine body layer tuned to the track root")
    if crest < 7.0 or attack > 18.0:
        problems.append("kick_transient_too_soft")
        actions.append("add a short click layer and controlled bus saturation")
    if body < 0.001:
        problems.append("kick_body_missing")
        actions.append("blend 100 to 220 Hz body so the kick reads on small speakers")
    if click < 0.00002:
        problems.append("kick_click_missing")
        actions.append("add a short click layer between 2 and 6 kHz")
    if decay < 60.0:
        problems.append("kick_decay_too_short")
        actions.append("lengthen the low body decay for drop impact")
    if decay > 520.0:
        problems.append("kick_decay_too_long")
        actions.append("shorten decay or gate the tail so it leaves bass room")
    if clipping(features):
        problems.append("kick_clipping")
        actions.append("lower the kick bus or remove clipping before judging tone")
    checks = [peak >= -12.0, low >= 0.12, crest >= 7.0, attack <= 18.0, 60.0 <= decay <= 520.0]
    metrics = {
        "peak_dbfs": peak,
        "crest_factor_db": crest,
        "attack_ms": attack,
        "estimated_decay_ms": decay,
        "low_energy_40_95_ratio": round(low, 6),
        "body_energy_95_250_ratio": round(body, 6),
        "click_energy_1k5_8k_ratio": round(click, 6),
        "onset_strength_max": onset,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=peak < -30.0 or clipping(features))
