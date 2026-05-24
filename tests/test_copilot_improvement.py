import json
import tempfile
import unittest
from pathlib import Path

from copilot_improvement.config import ImprovementConfig
from copilot_improvement.memory import default_memory, save_memory, upsert_backlog, upsert_signal
from copilot_improvement.orchestrator import run_improvement
from copilot_improvement.repo_scan import scan_repository
from copilot_improvement.source_scan import scan_chats


REPO_ROOT = Path(__file__).resolve().parents[1]


class CopilotImprovementTests(unittest.TestCase):
    def test_duplicate_signal_evidence_does_not_inflate_confidence(self):
        memory = default_memory()

        first = upsert_signal(
            memory,
            category="chat.intent",
            label="bass",
            evidence="Appeared in session.md.",
            source="session.md",
        )
        first_confidence = first["confidence"]
        second = upsert_signal(
            memory,
            category="chat.intent",
            label="bass",
            evidence="Appeared in session.md.",
            source="session.md",
        )

        self.assertEqual(first_confidence, second["confidence"])
        self.assertEqual(second["evidence_count"], 1)
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])

    def test_repository_scan_matches_plan_validator(self):
        scan = scan_repository(REPO_ROOT)
        runtime_gap_ids = {gap["id"] for gap in scan["runtime_capability_gaps"]}

        self.assertIn("clip-create-midi", scan["cli_commands"])
        self.assertEqual(scan["planner_missing_commands"], [])
        self.assertEqual(scan["planner_stale_commands"], [])
        self.assertEqual(scan["size_warnings"], [])
        self.assertIn("approval-before-execution", runtime_gap_ids)
        self.assertIn("preview-before-execution", runtime_gap_ids)
        self.assertIn("macro-inputs-before-execution", runtime_gap_ids)
        self.assertIn("verification-before-execution", runtime_gap_ids)

    def test_chat_scan_extracts_terms_and_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "session.md").write_text(
                "Actually make the drop bass movement more instead of sitting still. abletonctl clip-create-midi",
                encoding="utf-8",
            )

            scan = scan_chats((root,))
            chat = scan["chats"][0]

            self.assertEqual(chat["terms"]["drop"], 1)
            self.assertEqual(chat["terms"]["bass"], 1)
            self.assertEqual(chat["commands"]["clip-create-midi"], 1)
            self.assertEqual(chat["workflows"][0]["label"], "bass-movement-workflow")
            self.assertEqual(chat["refinements"]["correction-actually"], 1)
            self.assertEqual(chat["refinements"]["correction-instead-of"], 1)
            self.assertEqual(chat["refinements"]["increase-intensity-more"], 1)

    def test_chat_scan_discovers_relevant_codex_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            chat_root = home / "Documents" / "ableton-chats"
            session_dir = home / ".codex" / "sessions" / "2026" / "05" / "22"
            chat_root.mkdir(parents=True)
            session_dir.mkdir(parents=True)
            session_id = "019e4dec-1642-7950-834a-87a345f5b3c0"
            (home / ".codex" / "session_index.jsonl").write_text(
                json.dumps({"id": session_id, "thread_name": "Build glitchy drum racks"}) + "\n",
                encoding="utf-8",
            )
            session_file = session_dir / f"rollout-2026-05-22T00-22-58-{session_id}.jsonl"
            session_file.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "session_meta", "payload": {"id": session_id, "cwd": str(chat_root)}}),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": "Make a glitchy drum rack with zap samples and cut out before bar 3.",
                                        }
                                    ],
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "output_text",
                                            "text": "abletonctl drum-pad-load --track Drums --pad C1 --item samples/Zap.wav",
                                        }
                                    ],
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": "Actually put each zap on its own pad instead of stacking everything on one pad.",
                                        }
                                    ],
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            scan = scan_chats((chat_root,))
            chat = scan["chats"][0]

            self.assertEqual(scan["files_seen"], 1)
            self.assertEqual(chat["kind"], "codex-session")
            self.assertEqual(chat["terms"]["glitchy"], 1)
            self.assertGreaterEqual(chat["terms"]["zap"], 1)
            self.assertEqual(chat["commands"]["drum-pad-load"], 1)
            self.assertEqual(chat["workflows"][0]["label"], "glitch-drum-transition")
            self.assertEqual(chat["refinements"]["pad-mapping-correction"], 2)

    def test_run_writes_memory_report_and_changelog(self):
        with tempfile.TemporaryDirectory() as state, tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as chats:
            chat_path = Path(chats) / "ableton.md"
            chat_path.write_text("Actually add more sidechain movement to the bass drop instead of a static duck.", encoding="utf-8")
            config = ImprovementConfig(
                repo_root=REPO_ROOT,
                state_dir=Path(state),
                project_roots=(Path(project),),
                chat_roots=(Path(chats),),
            )

            run = run_improvement(
                config,
                validate=False,
                note="Recorded a test improvement.",
                why="The report should carry explicit reasoning.",
                expected_impact="Reviewers can audit intent.",
            )
            memory = json.loads((Path(state) / "memory.json").read_text(encoding="utf-8"))
            report = Path(run["report_path"]).read_text(encoding="utf-8")
            profile = (Path(state) / "personal-workflow-profile.md").read_text(encoding="utf-8")

            self.assertTrue(Path(run["report_path"]).exists())
            self.assertTrue((Path(state) / "CHANGELOG.md").exists())
            self.assertTrue(Path(run["profile_path"]).exists())
            self.assertIn("Recorded a test improvement.", report)
            self.assertIn("Personalized Profile", report)
            self.assertIn("Goal Coverage", report)
            self.assertIn("Planner Gap Coverage", report)
            self.assertIn("approval-before-execution", report)
            self.assertIn("python3 scripts/copilot_size_gate.py", report)
            self.assertIn("Workflow macros tracked", report)
            self.assertIn("goal_coverage", run)
            self.assertTrue(memory["workflow_macros"])
            self.assertIn("Derived Intent Mappings", profile)
            self.assertIn("Reusable Workflow Macros", profile)
            self.assertIn("Personalized Workflow Playbooks", profile)
            self.assertIn("Project Workflow Evidence", profile)
            self.assertTrue(any(signal["category"] == "chat.intent" for signal in memory["signals"]))
            self.assertTrue(any(signal["category"] == "chat.workflow" for signal in memory["signals"]))
            self.assertTrue(any(signal["category"] == "chat.refinement" for signal in memory["signals"]))
            self.assertTrue(any(signal["label"] == "drum-pad-load" for signal in memory["signals"]))
            self.assertIn("chat.workflow", profile)
            self.assertTrue(any(mapping["id"] == "bass-movement" for mapping in memory["intent_mappings"]))

    def test_run_marks_satisfied_capability_backlog_resolved(self):
        with tempfile.TemporaryDirectory() as state:
            memory = default_memory()
            upsert_backlog(
                memory,
                item_id="session-snapshot-command",
                title="Add an aggregate session snapshot command",
                why="Repeated probes are slow.",
                expected_impact="Faster context reads.",
                priority=3,
                evidence="Seeded before implementation.",
            )
            save_memory(memory, Path(state) / "memory.json")
            config = ImprovementConfig(
                repo_root=REPO_ROOT,
                state_dir=Path(state),
                project_roots=(),
                chat_roots=(),
            )

            run = run_improvement(config, validate=False)
            updated = json.loads((Path(state) / "memory.json").read_text(encoding="utf-8"))
            item = next(item for item in updated["backlog"] if item["id"] == "session-snapshot-command")
            report = Path(run["report_path"]).read_text(encoding="utf-8")

            self.assertEqual(item["status"], "resolved")
            self.assertIn("## Resolved Backlog", report)
            self.assertNotIn("## Improvement Opportunities\n- P3 `session-snapshot-command`", report)
            self.assertIn("chat-history-evidence-missing", report)

    def test_run_marks_artist_research_synthesis_resolved(self):
        with tempfile.TemporaryDirectory() as state:
            memory = default_memory()
            upsert_backlog(
                memory,
                item_id="research-tipper-gjones-chrislake-synthesis",
                title="Synthesize non-imitative references from Tipper, G Jones, and Chris Lake",
                why="Artist research should inform planning.",
                expected_impact="Better original musical heuristics.",
                priority=5,
                evidence="Seeded before synthesis.",
            )
            save_memory(memory, Path(state) / "memory.json")
            config = ImprovementConfig(
                repo_root=REPO_ROOT,
                state_dir=Path(state),
                project_roots=(),
                chat_roots=(),
            )

            run_improvement(config, validate=False)
            updated = json.loads((Path(state) / "memory.json").read_text(encoding="utf-8"))
            item = next(item for item in updated["backlog"] if item["id"] == "research-tipper-gjones-chrislake-synthesis")

            self.assertEqual(item["status"], "resolved")

    def test_run_marks_bass_movement_research_resolved(self):
        with tempfile.TemporaryDirectory() as state:
            memory = default_memory()
            upsert_backlog(
                memory,
                item_id="research-bass-movement",
                title="Research modern bass movement and resampling workflows",
                why="Bass movement research should inform planning.",
                expected_impact="Better movement and resampling plans.",
                priority=4,
                evidence="Seeded before synthesis.",
            )
            save_memory(memory, Path(state) / "memory.json")
            config = ImprovementConfig(
                repo_root=REPO_ROOT,
                state_dir=Path(state),
                project_roots=(),
                chat_roots=(),
            )

            run_improvement(config, validate=False)
            updated = json.loads((Path(state) / "memory.json").read_text(encoding="utf-8"))
            item = next(item for item in updated["backlog"] if item["id"] == "research-bass-movement")

            self.assertEqual(item["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
