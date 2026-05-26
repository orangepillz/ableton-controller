from __future__ import annotations

import json
import tempfile
import unittest

from audioqa.ableton_audioqa.analysis import analyze_file
from audioqa.ableton_audioqa.references import learn_references
from audioqa.ableton_audioqa.reports import dumps, summarize_section
from tests.audioqa_test_utils import valid_kick, weak_kick_no_sub, write_wav


class AudioQAReportTests(unittest.TestCase):
    def test_report_json_is_stable_for_repeated_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            file_path = write_wav(path(temp, "kick.wav"), weak_kick_no_sub())
            first = dumps(analyze_file(file_path, "kick"))
            second = dumps(analyze_file(file_path, "kick"))
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertIn("pass", parsed)
        self.assertIn("recommended_actions", parsed)

    def test_reference_learning_and_section_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            refs = path(temp, "refs")
            (refs / "kicks").mkdir(parents=True)
            write_wav(refs / "kicks" / "kick_ref.wav", valid_kick())
            learned = learn_references(refs)
            self.assertEqual(learned["version"], 1)
            self.assertEqual(len(learned["classes"]["kick"]), 1)
            report_path = path(temp, "kick.audioqa.json")
            report_path.write_text(dumps(analyze_file(refs / "kicks" / "kick_ref.wav", "kick")), encoding="utf-8")
            summary = summarize_section("Drop 1", [str(report_path)], "65-97")
        self.assertTrue(summary["overall_pass"])
        self.assertEqual(summary["section"], "Drop 1")


def path(root: str, name: str):
    from pathlib import Path

    return Path(root) / name


if __name__ == "__main__":
    unittest.main()
