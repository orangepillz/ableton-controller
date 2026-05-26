"""Shared helpers for target-specific audio gates."""

from __future__ import annotations

from ..schemas import GateResult, Severity


def energy(features: dict[str, float | int], *bands: str) -> float:
    return float(sum(float(features.get(name, 0.0)) for name in bands))


def low_energy(features: dict[str, float | int]) -> float:
    return energy(features, "band_energy_40_60", "band_energy_60_95")


def body_energy(features: dict[str, float | int]) -> float:
    return energy(features, "band_energy_95_140", "band_energy_140_250")


def crack_energy(features: dict[str, float | int]) -> float:
    return energy(features, "band_energy_1500_4000", "band_energy_4000_8000")


def score_from_checks(checks: list[bool]) -> float:
    if not checks:
        return 1.0
    return sum(1 for item in checks if item) / float(len(checks))


def severity_for(score: float, critical: bool = False) -> Severity:
    if critical or score < 0.45:
        return "critical"
    if score < 0.65:
        return "major"
    if score < 0.82:
        return "warning"
    return "info"


def gate_result(
    score: float,
    problems: list[str],
    actions: list[str],
    metrics: dict[str, float | int | str | bool],
    critical: bool = False,
    threshold: float = 0.72,
) -> GateResult:
    passed = score >= threshold and not critical and not problems
    severity = severity_for(score, critical=critical)
    if problems and severity == "info":
        severity = "warning"
    return GateResult(
        pass_=passed,
        score=score,
        severity=severity,
        problems=problems,
        metrics=metrics,
        recommended_actions=actions if problems else [],
    )


def clipping(features: dict[str, float | int]) -> bool:
    return float(features.get("peak_dbfs", -120.0)) >= -0.1
