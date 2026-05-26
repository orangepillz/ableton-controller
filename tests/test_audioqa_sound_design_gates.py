from __future__ import annotations

import tempfile
import unittest

from audioqa.ableton_audioqa.analysis import analyze_file
from tests.audioqa_test_utils import (
    dense_glitch,
    drop_missing_kick,
    drop_valid_basic,
    falling_noise,
    plain_sine,
    rising_noise,
    sparse_glitch,
    valid_growl,
    write_wav,
)


class AudioQASoundDesignGateTests(unittest.TestCase):
    def test_growl_gate_fails_plain_sine_and_passes_formant_motion(self):
        with tempfile.TemporaryDirectory() as temp:
            sine = write_wav(path(temp, "sine.wav"), plain_sine())
            growl = write_wav(path(temp, "growl.wav"), valid_growl())
            sine_report = analyze_file(sine, "growl")
            growl_report = analyze_file(growl, "growl")
        self.assertFalse(sine_report["pass"])
        self.assertIn("no_formant_motion", sine_report["problems"])
        self.assertTrue(growl_report["pass"], growl_report)

    def test_riser_and_downlifter_detect_sweep_direction(self):
        with tempfile.TemporaryDirectory() as temp:
            rising = write_wav(path(temp, "rising.wav"), rising_noise())
            falling = write_wav(path(temp, "falling.wav"), 0.48 * falling_noise())
            riser_report = analyze_file(rising, "riser")
            bad_riser_report = analyze_file(falling, "riser")
            down_report = analyze_file(falling, "downlifter")
        self.assertTrue(riser_report["pass"], riser_report)
        self.assertFalse(bad_riser_report["pass"])
        self.assertIn("riser_does_not_rise", bad_riser_report["problems"])
        self.assertTrue(down_report["pass"], down_report)

    def test_glitch_gate_detects_sparse_versus_dense_micro_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            sparse = write_wav(path(temp, "sparse.wav"), sparse_glitch())
            dense = write_wav(path(temp, "dense.wav"), dense_glitch())
            sparse_report = analyze_file(sparse, "glitch")
            dense_report = analyze_file(dense, "glitch")
        self.assertFalse(sparse_report["pass"])
        self.assertIn("glitch_density_too_low", sparse_report["problems"])
        self.assertTrue(dense_report["pass"], dense_report)

    def test_drop_gate_fails_missing_kick_and_passes_basic_drop(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = write_wav(path(temp, "missing.wav"), drop_missing_kick())
            valid = write_wav(path(temp, "drop.wav"), drop_valid_basic())
            missing_report = analyze_file(missing, "drop")
            valid_report = analyze_file(valid, "drop")
        self.assertFalse(missing_report["pass"])
        self.assertIn("kick_missing_in_drop", missing_report["problems"])
        self.assertTrue(valid_report["pass"], valid_report)


def path(root: str, name: str):
    from pathlib import Path

    return Path(root) / name


if __name__ == "__main__":
    unittest.main()
