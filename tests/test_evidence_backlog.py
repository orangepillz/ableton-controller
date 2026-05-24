import unittest

from copilot_improvement.evidence_backlog import add_evidence_backlog
from copilot_improvement.memory import default_memory, upsert_backlog


class EvidenceBacklogTests(unittest.TestCase):
    def test_adds_missing_evidence_backlog_items(self):
        memory = default_memory()

        updates = add_evidence_backlog(
            memory,
            {"files_seen": 0, "roots": ["/missing/projects"], "existing_roots": []},
            {"files_seen": 0, "roots": ["/missing/chats"], "existing_roots": []},
        )

        ids = {item["id"] for item in updates}
        self.assertIn("project-evidence-missing", ids)
        self.assertIn("chat-history-evidence-missing", ids)
        self.assertTrue(all(item["status"] == "open" for item in updates))

    def test_resolves_evidence_backlog_when_files_are_found(self):
        memory = default_memory()
        upsert_backlog(
            memory,
            item_id="chat-history-evidence-missing",
            title="Connect ableton-chats history to personalization scan",
            why="Missing chat evidence.",
            expected_impact="Better intent mapping.",
            priority=2,
            evidence="seed",
        )

        updates = add_evidence_backlog(
            memory,
            {"files_seen": 1, "roots": ["/projects"], "existing_roots": ["/projects"], "projects": [{"arrangement_sections": {"Drop": 1}}]},
            {"files_seen": 2, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        resolved = next(item for item in updates if item["id"] == "chat-history-evidence-missing")
        self.assertEqual(resolved["status"], "resolved")

    def test_marks_thin_arrangement_evidence_when_project_files_have_no_sections(self):
        memory = default_memory()

        updates = add_evidence_backlog(
            memory,
            {"files_seen": 2, "roots": ["/projects"], "existing_roots": ["/projects"], "projects": [{"arrangement_sections": {}}]},
            {"files_seen": 1, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        item = next(update for update in updates if update["id"] == "project-arrangement-evidence-thin")
        self.assertEqual(item["status"], "open")
        self.assertIn("section flow", item["expected_impact"])

    def test_marks_only_named_arrangement_evidence_thin_when_shape_exists(self):
        memory = default_memory()

        updates = add_evidence_backlog(
            memory,
            {
                "files_seen": 2,
                "roots": ["/projects"],
                "existing_roots": ["/projects"],
                "projects": [{"arrangement_sections": {}, "arrangement_shape": {"common-clip-length-16-beats": 4}}],
            },
            {"files_seen": 1, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        item = next(update for update in updates if update["id"] == "project-arrangement-evidence-thin")
        self.assertEqual(item["status"], "open")
        self.assertIn("shape is learned", item["why"])
        self.assertIn("semantic section labels", item["expected_impact"])

    def test_marks_only_explicit_labels_thin_when_shape_and_roles_exist(self):
        memory = default_memory()

        updates = add_evidence_backlog(
            memory,
            {
                "files_seen": 2,
                "roots": ["/projects"],
                "existing_roots": ["/projects"],
                "projects": [
                    {
                        "arrangement_sections": {},
                        "arrangement_shape": {"common-clip-length-16-beats": 4},
                        "arrangement_roles": {"clip-role-bass": 2},
                    }
                ],
            },
            {"files_seen": 1, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        item = next(update for update in updates if update["id"] == "project-arrangement-evidence-thin")
        self.assertEqual(item["title"], "Improve explicit scene and locator labels")
        self.assertIn("shape and clip roles are learned", item["why"])

    def test_marks_numbered_markers_as_needing_musical_names(self):
        memory = default_memory()

        updates = add_evidence_backlog(
            memory,
            {
                "files_seen": 2,
                "roots": ["/projects"],
                "existing_roots": ["/projects"],
                "projects": [
                    {
                        "arrangement_sections": {},
                        "arrangement_markers": {"locator-marker-2-at-64-beats": 1},
                        "arrangement_shape": {"arrangement-start-grid-32-beats": 1},
                        "arrangement_roles": {"main-section-role-kick": 1},
                    }
                ],
            },
            {"files_seen": 1, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        item = next(update for update in updates if update["id"] == "project-arrangement-evidence-thin")
        self.assertEqual(item["title"], "Add musical names to numbered arrangement markers")
        self.assertIn("locator markers", item["why"])

    def test_resolves_numbered_marker_backlog_when_label_proposals_exist(self):
        memory = default_memory()
        memory["signals"].append(
            {
                "id": "project.arrangement-label-proposal.beat-64-main-drop",
                "category": "project.arrangement-label-proposal",
                "label": "beat 64: 02 Main Drop - Drum FX Kick Impact",
            }
        )
        upsert_backlog(
            memory,
            item_id="project-arrangement-evidence-thin",
            title="Add musical names to numbered arrangement markers",
            why="Markers need names.",
            expected_impact="Better section planning.",
            priority=3,
            evidence="seed",
        )

        updates = add_evidence_backlog(
            memory,
            {
                "files_seen": 2,
                "roots": ["/projects"],
                "existing_roots": ["/projects"],
                "projects": [
                    {
                        "arrangement_sections": {},
                        "arrangement_markers": {"locator-marker-2-at-64-beats": 1},
                        "arrangement_shape": {"arrangement-start-grid-32-beats": 1},
                        "arrangement_roles": {"main-section-role-kick": 1},
                    }
                ],
            },
            {"files_seen": 1, "roots": ["/chats"], "existing_roots": ["/chats"]},
        )

        item = next(update for update in updates if update["id"] == "project-arrangement-evidence-thin")
        self.assertEqual(item["status"], "resolved")
        self.assertIn("Derived arrangement label proposals", item["evidence"][-1])


if __name__ == "__main__":
    unittest.main()
