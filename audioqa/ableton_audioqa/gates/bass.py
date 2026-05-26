"""Bass bus and reese-style verification gates."""

from __future__ import annotations

from .common import clipping, energy, gate_result, low_energy, score_from_checks
from ..schemas import GateResult


def score_bass_bus(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    mud = energy(features, "band_energy_140_250", "band_energy_250_500")
    mono = float(features.get("mono_low_end_ratio", 1.0))
    crest = float(features.get("crest_factor_db", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if low < 0.10:
        problems.append("bass_sub_missing")
        actions.append("restore mono sub support before judging mid-bass tone")
    if mud > 0.45:
        problems.append("bass_low_mid_muddy")
        actions.append("use EQ to control 150 to 350 Hz buildup")
    if mono < 0.78:
        problems.append("bass_sub_too_wide")
        actions.append("split sub and stereo mid layers; keep sub mono")
    if crest < 3.0:
        problems.append("bass_overcompressed_flat")
        actions.append("restore transient or phrase contrast in the bass bus")
    if clipping(features):
        problems.append("bass_clipping")
        actions.append("leave headroom before comparing bass to drums")
    checks = [low >= 0.10, mud <= 0.45, mono >= 0.78, crest >= 3.0, not clipping(features)]
    metrics = {
        "low_energy_40_95_ratio": round(low, 6),
        "low_mid_140_500_ratio": round(mud, 6),
        "mono_low_end_ratio": mono,
        "crest_factor_db": crest,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics, critical=clipping(features))


def score_reese(features: dict[str, float | int], tempo: float | None = None) -> GateResult:
    low = low_energy(features)
    low_mid = energy(features, "band_energy_95_140", "band_energy_140_250", "band_energy_250_500")
    motion = float(features.get("spectral_centroid_modulation", 0.0))
    mono = float(features.get("mono_low_end_ratio", 1.0))
    problems: list[str] = []
    actions: list[str] = []
    if motion < 0.035:
        problems.append("reese_too_static")
        actions.append("add detuned oscillators or chorus above the sub")
    if mono < 0.78:
        problems.append("reese_sub_too_wide")
        actions.append("keep the sub mono and widen only the mid layer")
    if low_mid > 0.52:
        problems.append("reese_low_mid_muddy")
        actions.append("control 150 to 350 Hz buildup")
    if low < 0.08:
        problems.append("reese_harmonics_too_weak")
        actions.append("restore low support below the moving stereo layer")
    checks = [motion >= 0.035, mono >= 0.78, low_mid <= 0.52, low >= 0.08]
    metrics = {
        "low_energy_40_95_ratio": round(low, 6),
        "low_mid_95_500_ratio": round(low_mid, 6),
        "spectral_centroid_modulation": motion,
        "mono_low_end_ratio": mono,
    }
    return gate_result(score_from_checks(checks), problems, actions, metrics)
