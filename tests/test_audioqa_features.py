from __future__ import annotations

import tempfile
import unittest

from audioqa.ableton_audioqa.features import extract_features
from tests.audioqa_test_utils import valid_kick, write_wav


class AudioQAFeatureTests(unittest.TestCase):
    def test_extracts_minimum_feature_set(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_wav(temp_path(temp, "kick.wav"), valid_kick())
            features = extract_features(path)
        for key in (
            "duration_seconds",
            "sample_rate",
            "peak_dbfs",
            "rms_dbfs",
            "integrated_lufs",
            "crest_factor_db",
            "spectral_centroid_mean",
            "onset_count",
            "attack_ms",
            "estimated_decay_ms",
            "mono_low_end_ratio",
            "band_energy_40_60",
            "band_energy_60_95",
            "modulation_depth",
            "spectral_flux",
        ):
            self.assertIn(key, features)
        self.assertEqual(features["sample_rate"], 48000)
        self.assertGreater(features["band_energy_40_60"] + features["band_energy_60_95"], 0.1)


def temp_path(root: str, name: str):
    from pathlib import Path

    return Path(root) / name


if __name__ == "__main__":
    unittest.main()
