from __future__ import annotations

import tempfile
import unittest

from audioqa.ableton_audioqa.compare import compare_files
from tests.audioqa_test_utils import static_bass, valid_kick, valid_snare, white_noise_snare, write_wav


class AudioQACompareTests(unittest.TestCase):
    def test_compare_detects_kick_masked_by_bass(self):
        with tempfile.TemporaryDirectory() as temp:
            kick = valid_kick()
            bass = static_bass(seconds=len(kick) / 48000)
            primary = write_wav(path(temp, "kick.wav"), kick)
            context = write_wav(path(temp, "context.wav"), 0.18 * kick + 0.9 * bass)
            report = compare_files(primary, context, "kick-audibility")
        self.assertFalse(report["pass"])
        self.assertIn("kick_masked_by_bass", report["problems"])

    def test_compare_detects_snare_masked_by_noise(self):
        with tempfile.TemporaryDirectory() as temp:
            snare = valid_snare()
            noise = white_noise_snare(seconds=len(snare) / 48000)
            primary = write_wav(path(temp, "snare.wav"), snare)
            context = write_wav(path(temp, "context.wav"), 0.12 * snare + noise)
            report = compare_files(primary, context, "snare-audibility")
        self.assertFalse(report["pass"])
        self.assertTrue(set(report["problems"]) & {"snare_crack_masked", "snare_masked_by_noise_or_glitches"})


def path(root: str, name: str):
    from pathlib import Path

    return Path(root) / name


if __name__ == "__main__":
    unittest.main()
