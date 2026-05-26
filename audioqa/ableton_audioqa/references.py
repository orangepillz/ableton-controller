"""Reference feature extraction and similarity deltas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .features import extract_features

AUDIO_SUFFIXES = {".wav", ".wave"}
CLASS_FOLDERS = {
    "kicks": "kick",
    "snares": "snare",
    "wubs": "wub",
    "growls": "growl",
    "glitches": "glitch",
    "risers": "riser",
    "drops": "drop",
}
REFERENCE_METRICS = (
    "spectral_centroid_mean",
    "crest_factor_db",
    "attack_ms",
    "estimated_decay_ms",
    "modulation_depth",
    "spectral_centroid_modulation",
    "band_energy_40_60",
    "band_energy_60_95",
    "band_energy_140_250",
    "band_energy_1500_4000",
)


def learn_references(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    classes: dict[str, list[dict[str, Any]]] = {}
    for folder, class_name in CLASS_FOLDERS.items():
        folder_path = base / folder
        if not folder_path.exists():
            classes[class_name] = []
            continue
        entries = []
        for audio_file in sorted(folder_path.rglob("*")):
            if audio_file.suffix.lower() not in AUDIO_SUFFIXES:
                continue
            features = extract_features(audio_file)
            entries.append({"file": str(audio_file), "features": _selected_features(features)})
        classes[class_name] = entries
    return {"version": 1, "classes": classes}


def reference_deltas(target: str, features: dict[str, float | int], reference_data: dict[str, Any]) -> dict[str, float | int]:
    entries = reference_data.get("classes", {}).get(target, [])
    if not entries:
        return {}
    means: dict[str, float] = {}
    for metric in REFERENCE_METRICS:
        values = [float(entry.get("features", {}).get(metric, 0.0)) for entry in entries]
        means[metric] = sum(values) / len(values)
    distance = 0.0
    deltas: dict[str, float | int] = {"reference_count": len(entries)}
    for metric, mean in means.items():
        value = float(features.get(metric, 0.0))
        scale = max(abs(mean), abs(value), 1.0)
        delta = (value - mean) / scale
        deltas[f"reference_delta_{metric}"] = round(delta, 6)
        distance += delta * delta
    similarity = max(0.0, 1.0 - (distance / max(1, len(means))) ** 0.5)
    deltas["reference_similarity"] = round(similarity, 6)
    return deltas


def _selected_features(features: dict[str, float | int]) -> dict[str, float | int]:
    return {key: features[key] for key in REFERENCE_METRICS if key in features}
