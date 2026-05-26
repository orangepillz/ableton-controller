"""Objective audio feature extraction for rendered WAV probes."""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

import numpy as np

BANDS: tuple[tuple[str, float, float], ...] = (
    ("band_energy_20_40", 20.0, 40.0),
    ("band_energy_40_60", 40.0, 60.0),
    ("band_energy_60_95", 60.0, 95.0),
    ("band_energy_95_140", 95.0, 140.0),
    ("band_energy_140_250", 140.0, 250.0),
    ("band_energy_250_500", 250.0, 500.0),
    ("band_energy_500_1500", 500.0, 1500.0),
    ("band_energy_1500_4000", 1500.0, 4000.0),
    ("band_energy_4000_8000", 4000.0, 8000.0),
    ("band_energy_8000_14000", 8000.0, 14000.0),
)

class AudioFeatureError(ValueError):
    """Raised when an audio file cannot be analyzed deterministically."""


def extract_features(path: str | Path) -> dict[str, float | int]:
    """Read a PCM WAV file and return deterministic scalar audio features."""
    samples, sample_rate = read_wav(path)
    if samples.size == 0:
        raise AudioFeatureError(f"{path} contains no audio frames")
    mono = samples.mean(axis=1)
    duration = float(len(mono)) / float(sample_rate)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(np.square(mono))))
    frames, hop = _frames(mono, sample_rate)
    rms_frames = _frame_rms(frames)
    spectrum = _spectrum(frames)
    freqs = np.fft.rfftfreq(frames.shape[1], 1.0 / sample_rate)
    spectral = _spectral_features(spectrum, freqs, hop, sample_rate)
    envelope = _smooth_envelope(mono, sample_rate)
    onset_strength = _onset_strength(rms_frames)
    band_features = _band_energy_features(spectrum, freqs)
    features: dict[str, float | int] = {
        "duration_seconds": round(duration, 6),
        "sample_rate": int(sample_rate),
        "channels": int(samples.shape[1]),
        "peak_dbfs": _dbfs(peak),
        "rms_dbfs": _dbfs(rms),
        "integrated_lufs": round(_dbfs(rms) - 0.691, 3),
        "short_term_lufs": round(_short_term_lufs(mono, sample_rate) - 0.691, 3),
        "crest_factor_db": round(_dbfs(peak) - _dbfs(rms), 3) if rms > 0 else 0.0,
        "zero_crossing_rate": round(_zero_crossing_rate(mono), 6),
        "onset_count": int(_count_onsets(onset_strength)),
        "onset_strength_mean": round(float(np.mean(onset_strength)), 6),
        "onset_strength_max": round(float(np.max(onset_strength)) if onset_strength.size else 0.0, 6),
        "attack_ms": round(_attack_ms(mono, sample_rate), 3),
        "estimated_decay_ms": round(_decay_ms(envelope, sample_rate), 3),
        "stereo_correlation": round(_stereo_correlation(samples), 6),
        "mono_low_end_ratio": round(_mono_low_end_ratio(samples, sample_rate), 6),
        "modulation_depth": round(_modulation_depth(rms_frames), 6),
        "modulation_rate_hz": round(_dominant_modulation_rate(rms_frames, hop, sample_rate), 6),
        "spectral_flux": round(_spectral_flux(spectrum), 6),
        "spectral_centroid_modulation": round(
            _relative_modulation(np.asarray(spectral["spectral_centroids"])), 6
        ),
    }
    for key, value in spectral.items():
        if key != "spectral_centroids":
            features[key] = value
    features.update(band_features)
    return features


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    file_path = Path(path)
    if not file_path.exists():
        raise AudioFeatureError(f"Audio file does not exist: {file_path}")
    try:
        with wave.open(str(file_path), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frame_count = wav.getnframes()
            raw = wav.readframes(frame_count)
    except wave.Error as exc:
        raise AudioFeatureError(f"Unsupported WAV file {file_path}: {exc}") from exc
    samples = _decode_pcm(raw, channels, sample_width)
    return samples, sample_rate


def _decode_pcm(raw: bytes, channels: int, sample_width: int) -> np.ndarray:
    if channels < 1:
        raise AudioFeatureError("WAV file reports zero channels")
    if sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sample_width == 3:
        bytes_ = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        ints = bytes_[:, 0] | (bytes_[:, 1] << 8) | (bytes_[:, 2] << 16)
        ints = np.where(ints & 0x800000, ints - 0x1000000, ints)
        data = ints.astype(np.float64) / 8388608.0
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise AudioFeatureError(f"Unsupported PCM sample width: {sample_width}")
    if data.size % channels:
        raise AudioFeatureError("WAV byte count is not divisible by channel count")
    return data.reshape(-1, channels)


def _frames(mono: np.ndarray, sample_rate: int) -> tuple[np.ndarray, int]:
    frame_size = 2048 if sample_rate >= 22050 else 1024
    hop = frame_size // 4
    if len(mono) < frame_size:
        mono = np.pad(mono, (0, frame_size - len(mono)))
    frame_count = 1 + max(0, (len(mono) - frame_size) // hop)
    indexes = np.arange(frame_size)[None, :] + hop * np.arange(frame_count)[:, None]
    window = np.hanning(frame_size)
    return mono[indexes] * window, hop


def _frame_rms(frames: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(np.square(frames), axis=1))


def _spectrum(frames: np.ndarray) -> np.ndarray:
    return np.abs(np.fft.rfft(frames, axis=1))


def _spectral_features(spectrum: np.ndarray, freqs: np.ndarray, hop: int, sample_rate: int) -> dict[str, Any]:
    power = np.maximum(spectrum, 1e-12)
    totals = power.sum(axis=1)
    centroids = (power * freqs).sum(axis=1) / totals
    bandwidth = np.sqrt((power * np.square(freqs - centroids[:, None])).sum(axis=1) / totals)
    cumulative = np.cumsum(power, axis=1)
    rolloff_indexes = (cumulative >= (totals * 0.85)[:, None]).argmax(axis=1)
    rolloffs = freqs[rolloff_indexes]
    times = np.arange(len(centroids)) * (float(hop) / float(sample_rate))
    slope = float(np.polyfit(times, centroids, 1)[0]) if len(centroids) > 1 else 0.0
    return {
        "spectral_centroid_mean": round(float(np.mean(centroids)), 3),
        "spectral_centroid_slope": round(slope, 6),
        "spectral_rolloff_mean": round(float(np.mean(rolloffs)), 3),
        "spectral_bandwidth_mean": round(float(np.mean(bandwidth)), 3),
        "spectral_centroids": centroids,
    }


def _band_energy_features(spectrum: np.ndarray, freqs: np.ndarray) -> dict[str, float]:
    power = np.square(spectrum)
    total = float(np.sum(power)) or 1.0
    result: dict[str, float] = {}
    for name, low, high in BANDS:
        mask = (freqs >= low) & (freqs < high)
        result[name] = round(float(np.sum(power[:, mask]) / total), 8)
    return result


def _dbfs(value: float) -> float:
    if value <= 1e-12:
        return -120.0
    return round(20.0 * math.log10(min(value, 1.0)), 3)


def _short_term_lufs(mono: np.ndarray, sample_rate: int) -> float:
    window = max(1, min(len(mono), int(sample_rate * 3.0)))
    if len(mono) <= window:
        return _dbfs(float(np.sqrt(np.mean(np.square(mono)))))
    stride = max(1, window // 4)
    values = [
        float(np.sqrt(np.mean(np.square(mono[start : start + window]))))
        for start in range(0, len(mono) - window + 1, stride)
    ]
    return _dbfs(max(values) if values else 0.0)


def _zero_crossing_rate(mono: np.ndarray) -> float:
    if len(mono) < 2:
        return 0.0
    return float(np.mean(np.signbit(mono[1:]) != np.signbit(mono[:-1])))


def _onset_strength(rms_frames: np.ndarray) -> np.ndarray:
    if rms_frames.size < 2:
        return np.zeros(1)
    diffs = np.maximum(0.0, np.diff(rms_frames, prepend=rms_frames[0]))
    scale = float(np.max(rms_frames)) or 1.0
    return diffs / scale


def _count_onsets(onset_strength: np.ndarray) -> int:
    if onset_strength.size < 3:
        return int(np.max(onset_strength) > 0.05)
    threshold = max(0.035, float(np.mean(onset_strength) + np.std(onset_strength)))
    peaks = 0
    for index in range(1, len(onset_strength) - 1):
        if onset_strength[index] >= threshold and onset_strength[index] >= onset_strength[index - 1] and onset_strength[index] > onset_strength[index + 1]:
            peaks += 1
    return peaks


def _smooth_envelope(mono: np.ndarray, sample_rate: int) -> np.ndarray:
    window = max(1, int(sample_rate * 0.01))
    kernel = np.ones(window) / float(window)
    return np.convolve(np.abs(mono), kernel, mode="same")


def _attack_ms(mono: np.ndarray, sample_rate: int) -> float:
    peak = float(np.max(np.abs(mono)))
    if peak <= 1e-8:
        return 0.0
    active = np.flatnonzero(np.abs(mono) >= peak * 0.1)
    if active.size == 0:
        return 0.0
    start = int(active[0])
    search_end = min(len(mono), start + int(sample_rate * 0.75))
    peak_index = start + int(np.argmax(np.abs(mono[start:search_end])))
    return max(0.0, (peak_index - start) * 1000.0 / float(sample_rate))


def _decay_ms(envelope: np.ndarray, sample_rate: int) -> float:
    peak_index = int(np.argmax(envelope))
    peak = float(envelope[peak_index])
    if peak <= 1e-8:
        return 0.0
    tail = envelope[peak_index:]
    below = np.flatnonzero(tail <= peak * 0.2)
    if below.size:
        return float(below[0]) * 1000.0 / float(sample_rate)
    return float(len(tail)) * 1000.0 / float(sample_rate)


def _stereo_correlation(samples: np.ndarray) -> float:
    if samples.shape[1] < 2:
        return 1.0
    left = samples[:, 0]
    right = samples[:, 1]
    if np.std(left) <= 1e-9 or np.std(right) <= 1e-9:
        return 1.0
    return float(np.corrcoef(left, right)[0, 1])


def _mono_low_end_ratio(samples: np.ndarray, sample_rate: int) -> float:
    if samples.shape[1] < 2:
        return 1.0
    mono = samples.mean(axis=1)
    side = (samples[:, 0] - samples[:, 1]) * 0.5
    mono_energy = _low_energy(mono, sample_rate)
    side_energy = _low_energy(side, sample_rate)
    return mono_energy / max(mono_energy + side_energy, 1e-12)


def _low_energy(signal: np.ndarray, sample_rate: int) -> float:
    if len(signal) < 2048:
        signal = np.pad(signal, (0, 2048 - len(signal)))
    spectrum = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
    freqs = np.fft.rfftfreq(len(signal), 1.0 / sample_rate)
    mask = (freqs >= 20.0) & (freqs < 140.0)
    return float(np.sum(np.square(spectrum[mask])))


def _modulation_depth(values: np.ndarray) -> float:
    mean = float(np.mean(values))
    if mean <= 1e-9:
        return 0.0
    return float((np.percentile(values, 95) - np.percentile(values, 5)) / max(np.percentile(values, 95), 1e-9))


def _dominant_modulation_rate(values: np.ndarray, hop: int, sample_rate: int) -> float:
    if values.size < 4 or float(np.std(values)) <= 1e-9:
        return 0.0
    centered = values - np.mean(values)
    spectrum = np.abs(np.fft.rfft(centered * np.hanning(len(centered))))
    freqs = np.fft.rfftfreq(len(centered), float(hop) / float(sample_rate))
    mask = (freqs >= 0.25) & (freqs <= 16.0)
    if not np.any(mask):
        return 0.0
    masked = spectrum[mask]
    return float(freqs[mask][int(np.argmax(masked))])


def _spectral_flux(spectrum: np.ndarray) -> float:
    if spectrum.shape[0] < 2:
        return 0.0
    norm = spectrum / np.maximum(np.linalg.norm(spectrum, axis=1, keepdims=True), 1e-12)
    diffs = np.maximum(0.0, np.diff(norm, axis=0))
    return float(np.mean(np.sum(diffs, axis=1)))


def _relative_modulation(values: np.ndarray) -> float:
    mean = float(np.mean(values))
    if mean <= 1e-9:
        return 0.0
    return float(np.std(values) / mean)
