from __future__ import annotations

import aifc
import tempfile
import unittest
import wave
from argparse import Namespace
from pathlib import Path

from ableton_controller.render_audio import cleanup_recorded_source, convert_recording, render_audio, verify_wav


class RenderAudioLocalTests(unittest.TestCase):
    def test_convert_recorded_aiff_to_wav(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "recorded.aif"
            output = Path(directory) / "render.wav"
            with aifc.open(str(source), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(48000)
                audio.writeframes(bytes([0x00, 0x00, 0x7F, 0xFF, 0x80, 0x00]))

            convert_recording(source, output)

            info = verify_wav(output)
            self.assertEqual(info["sample_rate"], 48000)
            self.assertEqual(info["channels"], 1)
            self.assertEqual(info["bit_depth"], 16)
            with wave.open(str(output), "rb") as wav:
                self.assertEqual(wav.readframes(3), bytes([0x00, 0x00, 0xFF, 0x7F, 0x00, 0x80]))

    def test_render_requires_wav_output(self):
        args = Namespace(output="render.aif")
        with self.assertRaisesRegex(ValueError, r"\.wav"):
            render_audio(args, lambda _args, _payload: {})

    def test_cleanup_only_removes_codex_recording_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Codex AudioQA Render 1234.aif"
            sidecar = Path(directory) / "Codex AudioQA Render 1234.aif.asd"
            foreign = Path(directory) / "artist_take.aif"
            output = Path(directory) / "render.wav"
            for path in (source, sidecar, foreign, output):
                path.write_bytes(b"x")

            self.assertTrue(cleanup_recorded_source(source, output))
            self.assertFalse(source.exists())
            self.assertFalse(sidecar.exists())
            self.assertTrue(foreign.exists())
            self.assertFalse(cleanup_recorded_source(foreign, output))


if __name__ == "__main__":
    unittest.main()
