from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


SAMPLE_RATE = 48000


def write_wav(path: Path, samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> Path:
    audio = np.asarray(samples, dtype=np.float64)
    if audio.ndim == 1:
        audio = audio[:, None]
    audio = np.clip(audio, -0.98, 0.98)
    pcm = (audio * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(audio.shape[1])
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return path


def timebase(seconds: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    return np.arange(int(seconds * sample_rate), dtype=np.float64) / float(sample_rate)


def valid_kick(seconds: float = 0.9) -> np.ndarray:
    t = timebase(seconds)
    body = np.sin(2 * np.pi * (58 + 42 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.19)
    click = np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.004)
    return 0.82 * body + 0.38 * click


def weak_kick_no_sub(seconds: float = 0.35) -> np.ndarray:
    t = timebase(seconds)
    return 0.15 * np.sin(2 * np.pi * 950 * t) * np.exp(-t / 0.018)


def valid_snare(seconds: float = 0.7) -> np.ndarray:
    rng = np.random.default_rng(7)
    t = timebase(seconds)
    body = 0.48 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.11)
    crack = 0.42 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.025)
    tail = 0.18 * rng.standard_normal(len(t)) * np.exp(-t / 0.16)
    return body + crack + tail


def white_noise_snare(seconds: float = 0.5) -> np.ndarray:
    rng = np.random.default_rng(11)
    t = timebase(seconds)
    return 0.55 * rng.standard_normal(len(t)) * np.exp(-t / 0.16)


def static_bass(seconds: float = 2.0) -> np.ndarray:
    t = timebase(seconds)
    return 0.55 * np.sin(2 * np.pi * 74 * t)


def valid_wub(seconds: float = 2.0) -> np.ndarray:
    t = timebase(seconds)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)
    sub = 0.42 * np.sin(2 * np.pi * 65 * t)
    moving = (0.16 + 0.34 * lfo) * np.sin(2 * np.pi * 260 * t)
    vowel = (lfo**2) * 0.22 * np.sin(2 * np.pi * 760 * t)
    return (sub + moving + vowel) * (0.55 + 0.45 * lfo)


def plain_sine(seconds: float = 1.5) -> np.ndarray:
    t = timebase(seconds)
    return 0.55 * np.sin(2 * np.pi * 85 * t)


def valid_growl(seconds: float = 1.5) -> np.ndarray:
    t = timebase(seconds)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)
    carrier = 0.28 * np.sin(2 * np.pi * 72 * t)
    formant_a = (0.15 + 0.25 * lfo) * np.sin(2 * np.pi * (420 + 220 * lfo) * t)
    formant_b = (0.12 + 0.20 * (1.0 - lfo)) * np.sin(2 * np.pi * (1050 + 380 * (1.0 - lfo)) * t)
    return (carrier + formant_a + formant_b) * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * t))


def rising_noise(seconds: float = 2.0) -> np.ndarray:
    rng = np.random.default_rng(13)
    t = timebase(seconds)
    noise = rng.standard_normal(len(t))
    sweep = np.sin(2 * np.pi * (200 + 3400 * (t / seconds) ** 2) * t)
    return 0.25 * noise * (t / seconds) + 0.3 * sweep * (t / seconds)


def falling_noise(seconds: float = 2.0) -> np.ndarray:
    return rising_noise(seconds)[::-1]


def sparse_glitch(seconds: float = 2.0) -> np.ndarray:
    samples = np.zeros(int(seconds * SAMPLE_RATE))
    samples[: int(0.04 * SAMPLE_RATE)] = 0.2 * np.sin(2 * np.pi * 1800 * timebase(0.04))
    return samples


def dense_glitch(seconds: float = 2.0) -> np.ndarray:
    rng = np.random.default_rng(17)
    samples = np.zeros((int(seconds * SAMPLE_RATE), 2))
    for start_seconds in np.arange(0.1, seconds, 0.18):
        start = int(start_seconds * SAMPLE_RATE)
        length = int(0.035 * SAMPLE_RATE)
        if start + length > len(samples):
            continue
        burst_t = timebase(length / SAMPLE_RATE)
        burst = 0.22 * rng.standard_normal(length) * np.hanning(length)
        burst += 0.18 * np.sin(2 * np.pi * (900 + 2200 * rng.random()) * burst_t) * np.hanning(length)
        pan = rng.uniform(-0.7, 0.7)
        samples[start : start + length, 0] += burst * (1.0 - pan) * 0.55
        samples[start : start + length, 1] += burst * (1.0 + pan) * 0.55
    return samples


def drop_missing_kick(seconds: float = 2.0) -> np.ndarray:
    t = timebase(seconds)
    snare = np.zeros_like(t)
    snare_start = int(1.0 * SAMPLE_RATE)
    snare_signal = valid_snare(0.5)
    snare[snare_start : snare_start + len(snare_signal)] += snare_signal
    hats = 0.08 * np.sin(2 * np.pi * 8000 * t)
    return 0.5 * snare + hats


def drop_valid_basic(seconds: float = 2.0) -> np.ndarray:
    t = timebase(seconds)
    signal = 0.18 * np.sin(2 * np.pi * 68 * t)
    kick = valid_kick(0.6)
    signal[: len(kick)] += 0.8 * kick
    snare = valid_snare(0.6)
    start = int(1.0 * SAMPLE_RATE)
    signal[start : start + len(snare)] += 0.55 * snare
    return signal
