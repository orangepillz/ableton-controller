"""Optional JSON-only musical critic placeholder.

The deterministic gates remain authoritative. This module intentionally works
without network access or an API key so local verification never depends on an
external model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .features import extract_features
from .schemas import stable_created_at


def critic_report(file_path: str | Path, prompt_file: str | Path) -> dict[str, Any]:
    features = extract_features(file_path)
    prompt_text = Path(prompt_file).read_text(encoding="utf-8") if Path(prompt_file).exists() else ""
    score = _musical_score(features)
    notes = _notes(features, prompt_text)
    return {
        "musical_pass": score >= 0.7,
        "score": round(score, 4),
        "notes": notes,
        "recommended_actions": _actions(features, score),
        "deterministic_authority": "audioqa gates remain authoritative for hard failures",
        "created_at": stable_created_at(file_path, prompt_file),
    }


def _musical_score(features: dict[str, float | int]) -> float:
    peak = float(features.get("peak_dbfs", -120.0))
    crest = float(features.get("crest_factor_db", 0.0))
    low = float(features.get("band_energy_40_60", 0.0)) + float(features.get("band_energy_60_95", 0.0))
    motion = float(features.get("modulation_depth", 0.0)) + float(features.get("spectral_centroid_modulation", 0.0))
    score = 0.25
    score += 0.2 if -24.0 <= peak <= -0.5 else 0.05
    score += 0.2 if crest >= 5.0 else 0.05
    score += 0.2 if low >= 0.06 else 0.05
    score += min(0.15, motion)
    return max(0.0, min(1.0, score))


def _notes(features: dict[str, float | int], prompt_text: str) -> list[str]:
    notes: list[str] = []
    if float(features.get("crest_factor_db", 0.0)) < 5.0:
        notes.append("The render has limited transient contrast, so drums may not anchor the section.")
    if float(features.get("band_energy_40_60", 0.0)) + float(features.get("band_energy_60_95", 0.0)) < 0.06:
        notes.append("Low-frequency support is light for an impact-focused bass music section.")
    if float(features.get("modulation_depth", 0.0)) < 0.1 and "bass" in prompt_text.lower():
        notes.append("The bass prompt suggests movement, but the rendered modulation depth is low.")
    return notes or ["The render has no obvious deterministic critic warnings beyond the gate reports."]


def _actions(features: dict[str, float | int], score: float) -> list[str]:
    if score >= 0.7:
        return []
    actions = ["fix failed deterministic audioqa gates before musical polish"]
    if float(features.get("crest_factor_db", 0.0)) < 5.0:
        actions.append("restore kick and snare transient contrast")
    if float(features.get("modulation_depth", 0.0)) < 0.1:
        actions.append("create more silence and movement between bass phrases")
    return actions
