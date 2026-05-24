import tempfile
import unittest
from pathlib import Path

from copilot_improvement.config import ImprovementConfig
from copilot_improvement.goal_coverage import AUTOMATION_ID, audit_goal_coverage


class GoalCoverageTests(unittest.TestCase):
    def test_goal_coverage_proves_scheduler_from_automation_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            state = root / "state"
            automation_dir = root / ".codex" / "automations" / AUTOMATION_ID
            repo.mkdir()
            state.mkdir()
            automation_dir.mkdir(parents=True)
            (automation_dir / "automation.toml").write_text(
                '\n'.join(
                    [
                        'status = "ACTIVE"',
                        'rrule = "FREQ=HOURLY;INTERVAL=6"',
                        f'cwds = ["{repo}"]',
                        'prompt = "python3 scripts/copilot_improvement.py run --validate --note x && python3 -m compileall -q ableton_controller copilot_improvement remote_scripts scripts tests"',
                    ]
                ),
                encoding="utf-8",
            )
            config = ImprovementConfig(repo_root=repo, state_dir=state, project_roots=(), chat_roots=())
            coverage = audit_goal_coverage(config, _run(repo, state), _memory(), codex_home=root / ".codex")
            scheduler = next(item for item in coverage["items"] if item["id"] == "scheduler")

            self.assertEqual(scheduler["status"], "proven")

    def test_goal_coverage_marks_missing_evidence_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            state = root / "state"
            repo.mkdir()
            state.mkdir()
            config = ImprovementConfig(repo_root=repo, state_dir=state, project_roots=(), chat_roots=())
            run = _run(repo, state)
            run["projects"]["files_seen"] = 0
            run["chats"]["files_seen"] = 0

            coverage = audit_goal_coverage(config, run, _memory(), codex_home=root / ".codex")
            statuses = {item["id"]: item["status"] for item in coverage["items"]}

            self.assertEqual(statuses["historical-projects"], "missing")
            self.assertEqual(statuses["historical-chats"], "missing")
            self.assertGreaterEqual(coverage["summary"]["missing"], 2)


def _run(repo: Path, state: Path) -> dict:
    profile = state / "personal-workflow-profile.md"
    profile.write_text("profile", encoding="utf-8")
    (state / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    return {
        "repository": {
            "cli_commands": ["copilot-intent", "workflow-macro", "session-snapshot", "drum-pad-load"],
            "size_warnings": [],
            "planner_missing_commands": [],
            "planner_stale_commands": [],
        },
        "projects": {"files_seen": 2},
        "chats": {"files_seen": 1},
        "validation": [{"command": "python3 -m unittest discover -s tests", "returncode": 0}],
        "profile_path": str(profile),
        "report_path": str(state / "runs" / "run" / "improvement-report.md"),
        "reasoning_log_path": str(state / "runs" / "run" / "reasoning-log.json"),
        "memory_backup": str(state / "backups" / "memory-run.json"),
    }


def _memory() -> dict:
    return {
        "signals": [{"id": "chat.intent.bass"}],
        "runs": [{"run_id": "run"}],
        "intent_mappings": [{"id": "bass-movement"}],
    }


if __name__ == "__main__":
    unittest.main()
