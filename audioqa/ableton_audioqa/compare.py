"""Context comparison gates for solo-vs-mix audibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .features import extract_features
from .schemas import AudioQACompareReport, stable_created_at

SUPPORTED_COMPARE_TARGETS = (
    "kick-audibility",
    "snare-audibility",
    "bass-masking",
    "low-end-masking",
    "drop-vs-build-energy",
    "transition-impact",
)


def compare_files(primary: str | Path, context: str | Path, target: str, tempo: float | None = None) -> dict[str, Any]:
    normalized = normalize_compare_target(target)
    primary_features = extract_features(primary)
    context_features = extract_features(context)
    result = _COMPARE[normalized](primary_features, context_features)
    report = AudioQACompareReport(
        target=normalized,
        primary_file=str(primary),
        context_file=str(context),
        pass_=result["pass"],
        score=result["score"],
        severity=result["severity"],
        problems=result["problems"],
        metrics=result["metrics"],
        recommended_actions=result["recommended_actions"],
        created_at=stable_created_at(primary, context),
    )
    return report.to_dict()


def normalize_compare_target(target: str) -> str:
    normalized = target.strip().lower().replace("_", "-")
    if normalized not in SUPPORTED_COMPARE_TARGETS:
        raise ValueError(
            f"Unsupported comparison target {target!r}. Supported targets: {', '.join(SUPPORTED_COMPARE_TARGETS)}"
        )
    return normalized


def _kick_audibility(primary: dict[str, float | int], context: dict[str, float | int]) -> dict[str, Any]:
    crest_delta = float(context.get("crest_factor_db", 0.0)) - float(primary.get("crest_factor_db", 0.0))
    onset_ratio = _ratio(context.get("onset_strength_max", 0.0), primary.get("onset_strength_max", 0.0))
    low_context = _low(context)
    low_primary = _low(primary)
    problems: list[str] = []
    actions: list[str] = []
    if onset_ratio < 0.55 or crest_delta < -3.0:
        problems.append("kick_masked_by_bass")
        actions.append("duck the bass group 2 to 4 dB for 80 to 140 ms on kick hits")
    if low_context > low_primary * 2.5 and onset_ratio < 0.75:
        problems.append("low_end_masking_50_90hz")
        actions.append("carve competing bass energy around the kick fundamental")
    return _comparison_result(problems, actions, {"context_to_primary_onset_ratio": round(onset_ratio, 6), "crest_delta_db": round(crest_delta, 6), "primary_low_energy": round(low_primary, 6), "context_low_energy": round(low_context, 6)})


def _snare_audibility(primary: dict[str, float | int], context: dict[str, float | int]) -> dict[str, Any]:
    primary_crack = _crack(primary)
    context_crack = _crack(context)
    crack_ratio = _ratio(context_crack, primary_crack)
    rms_delta = float(context.get("rms_dbfs", -120.0)) - float(primary.get("rms_dbfs", -120.0))
    noise = _noise(context)
    problems: list[str] = []
    actions: list[str] = []
    if crack_ratio < 0.5:
        problems.append("snare_crack_masked")
        actions.append("make the snare crack louder or carve competing midrange layers")
    if (noise > 0.40 and rms_delta > 2.0) or (noise > 0.65 and crack_ratio < 0.8):
        problems.append("snare_masked_by_noise_or_glitches")
        actions.append("lower noise and glitch layers around the backbeat")
    return _comparison_result(problems, actions, {"context_to_primary_crack_ratio": round(crack_ratio, 6), "context_minus_primary_rms_db": round(rms_delta, 6), "context_noise_ratio": round(noise, 6), "primary_crack_ratio": round(primary_crack, 6), "context_crack_ratio": round(context_crack, 6)})


def _bass_masking(primary: dict[str, float | int], context: dict[str, float | int]) -> dict[str, Any]:
    crest_loss = float(primary.get("crest_factor_db", 0.0)) - float(context.get("crest_factor_db", 0.0))
    low_context = _low(context)
    mono = float(context.get("mono_low_end_ratio", 1.0))
    problems: list[str] = []
    actions: list[str] = []
    if crest_loss > 4.0 and low_context > 0.22:
        problems.append("bass_masks_drums")
        actions.append("add sidechain or volume ducking around drum hits")
    if mono < 0.75:
        problems.append("low_end_not_mono_compatible")
        actions.append("keep sub layers mono and widen only upper harmonics")
    return _comparison_result(problems, actions, {"crest_loss_db": round(crest_loss, 6), "context_low_energy": round(low_context, 6), "mono_low_end_ratio": mono})


def _drop_vs_build(primary: dict[str, float | int], context: dict[str, float | int]) -> dict[str, Any]:
    loudness_delta = float(primary.get("integrated_lufs", -120.0)) - float(context.get("integrated_lufs", -120.0))
    problems: list[str] = []
    actions: list[str] = []
    if loudness_delta < 1.0:
        problems.append("drop_not_louder_than_build")
        actions.append("increase drop contrast or reduce build energy before the drop")
    return _comparison_result(problems, actions, {"drop_minus_build_lufs": round(loudness_delta, 6)})


def _transition_impact(primary: dict[str, float | int], context: dict[str, float | int]) -> dict[str, Any]:
    onset_ratio = _ratio(primary.get("onset_strength_max", 0.0), context.get("onset_strength_max", 0.0))
    problems: list[str] = []
    actions: list[str] = []
    if onset_ratio < 1.15:
        problems.append("transition_impact_missing")
        actions.append("place a clear impact or faller at the section boundary")
    return _comparison_result(problems, actions, {"transition_to_context_onset_ratio": round(onset_ratio, 6)})


def _comparison_result(problems: list[str], actions: list[str], metrics: dict[str, float | int]) -> dict[str, Any]:
    score = 1.0 if not problems else max(0.2, 1.0 - 0.28 * len(problems))
    severity = "info" if not problems else ("major" if score >= 0.5 else "critical")
    return {"pass": not problems, "score": round(score, 4), "severity": severity, "problems": problems, "metrics": metrics, "recommended_actions": actions}


def _low(features: dict[str, float | int]) -> float:
    return float(features.get("band_energy_40_60", 0.0)) + float(features.get("band_energy_60_95", 0.0))


def _crack(features: dict[str, float | int]) -> float:
    return float(features.get("band_energy_1500_4000", 0.0)) + float(features.get("band_energy_4000_8000", 0.0))


def _noise(features: dict[str, float | int]) -> float:
    return float(features.get("band_energy_4000_8000", 0.0)) + float(features.get("band_energy_8000_14000", 0.0))


def _ratio(numerator: float | int, denominator: float | int) -> float:
    return float(numerator) / max(float(denominator), 1e-9)


_COMPARE = {
    "kick-audibility": _kick_audibility,
    "snare-audibility": _snare_audibility,
    "bass-masking": _bass_masking,
    "low-end-masking": _bass_masking,
    "drop-vs-build-energy": _drop_vs_build,
    "transition-impact": _transition_impact,
}
