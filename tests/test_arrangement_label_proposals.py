import gzip
import json
import tempfile
import unittest
from pathlib import Path

from copilot_improvement.config import ImprovementConfig
from copilot_improvement.memory import default_memory, save_memory, upsert_backlog
from copilot_improvement.orchestrator import run_improvement


REPO_ROOT = Path(__file__).resolve().parents[1]


class ArrangementLabelProposalRunTests(unittest.TestCase):
    def test_run_persists_derived_arrangement_label_proposals(self):
        with tempfile.TemporaryDirectory() as state, tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as chats:
            als_path = Path(project) / "Markers.als"
            xml = """
            <Ableton>
              <LiveSet>
                <Locators>
                  <Locator><Time Value="0"/><Name Value="1"/></Locator>
                  <Locator><Time Value="64"/><Name Value="2"/></Locator>
                </Locators>
                <MidiClip Time="64"><Name Value="Kick Drums"/></MidiClip>
              </LiveSet>
            </Ableton>
            """
            with gzip.open(als_path, "wb") as handle:
                handle.write(xml.encode("utf-8"))
            memory = default_memory()
            upsert_backlog(
                memory,
                item_id="project-arrangement-evidence-thin",
                title="Add musical names to numbered arrangement markers",
                why="Markers need names.",
                expected_impact="Better section planning.",
                priority=3,
                evidence="seed",
            )
            save_memory(memory, Path(state) / "memory.json")

            run = run_improvement(
                ImprovementConfig(REPO_ROOT, Path(state), (Path(project),), (Path(chats),)),
                validate=False,
            )
            memory = json.loads((Path(state) / "memory.json").read_text(encoding="utf-8"))
            backlog = {item["id"]: item for item in memory["backlog"]}

            self.assertTrue(any(signal["category"] == "project.arrangement-label-proposal" for signal in memory["signals"]))
            self.assertEqual(backlog["project-arrangement-evidence-thin"]["status"], "resolved")
            self.assertTrue(Path(run["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
