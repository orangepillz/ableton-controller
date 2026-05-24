import unittest

from ableton_controller.arrangement_labels import marker_label_proposals


class ArrangementLabelTests(unittest.TestCase):
    def test_marker_label_proposals_combine_marker_and_phase_evidence(self):
        memory = {
            "signals": [
                {
                    "id": "project.arrangement-marker.locator-marker-2-at-64-beats",
                    "category": "project.arrangement-marker",
                    "label": "locator-marker-2-at-64-beats",
                    "confidence": 0.3,
                },
                {
                    "id": "project.arrangement-marker.locator-marker-1-at-0-beats",
                    "category": "project.arrangement-marker",
                    "label": "locator-marker-1-at-0-beats",
                    "confidence": 0.25,
                },
                {
                    "id": "project.arrangement-marker.locator-marker-3-at-128-beats",
                    "category": "project.arrangement-marker",
                    "label": "locator-marker-3-at-128-beats",
                    "confidence": 0.22,
                },
                {
                    "id": "project.arrangement-phase.main-section-phase-drums-fx-kick",
                    "category": "project.arrangement-phase",
                    "label": "main-section-phase-drums-fx-kick",
                    "confidence": 0.23,
                },
            ]
        }

        proposals = marker_label_proposals(memory)

        self.assertEqual([proposal["beat"] for proposal in proposals], [0.0, 64.0, 128.0])
        self.assertEqual(proposals[1]["name"], "02 Main Drop - Drum FX Kick Impact (marker 2)")
        self.assertGreater(proposals[1]["confidence"], 0.3)
        self.assertIn("project.arrangement-phase.main-section-phase-drums-fx-kick", proposals[1]["evidence_signal_ids"])


if __name__ == "__main__":
    unittest.main()
