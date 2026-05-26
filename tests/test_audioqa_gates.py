from __future__ import annotations

import tempfile
import unittest

from audioqa.ableton_audioqa.analysis import analyze_file
from tests.audioqa_test_utils import (
    static_bass,
    valid_kick,
    valid_snare,
    valid_wub,
    weak_kick_no_sub,
    white_noise_snare,
    write_wav,
)


class AudioQAGateTests(unittest.TestCase):
    def test_kick_gate_fails_weak_kick_and_passes_valid_kick(self):
        with tempfile.TemporaryDirectory() as temp:
            weak = write_wav(path(temp, "weak.wav"), weak_kick_no_sub())
            valid = write_wav(path(temp, "valid.wav"), valid_kick())
            weak_report = analyze_file(weak, "kick")
            valid_report = analyze_file(valid, "kick")
        self.assertFalse(weak_report["pass"])
        self.assertIn("kick_sub_energy_too_low", weak_report["problems"])
        self.assertTrue(valid_report["pass"], valid_report)

    def test_snare_gate_fails_white_noise_and_passes_layered_snare(self):
        with tempfile.TemporaryDirectory() as temp:
            noise = write_wav(path(temp, "noise.wav"), white_noise_snare())
            valid = write_wav(path(temp, "snare.wav"), valid_snare())
            noise_report = analyze_file(noise, "snare")
            valid_report = analyze_file(valid, "snare")
        self.assertFalse(noise_report["pass"])
        self.assertIn("snare_body_missing", noise_report["problems"])
        self.assertTrue(valid_report["pass"], valid_report)

    def test_wub_gate_fails_static_bass_and_passes_modulated_bass(self):
        with tempfile.TemporaryDirectory() as temp:
            static = write_wav(path(temp, "static.wav"), static_bass())
            wub = write_wav(path(temp, "wub.wav"), valid_wub())
            static_report = analyze_file(static, "wub")
            wub_report = analyze_file(wub, "wub")
        self.assertFalse(static_report["pass"])
        self.assertIn("wub_has_no_modulation", static_report["problems"])
        self.assertTrue(wub_report["pass"], wub_report)


def path(root: str, name: str):
    from pathlib import Path

    return Path(root) / name


if __name__ == "__main__":
    unittest.main()
