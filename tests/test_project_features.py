import gzip
import tempfile
import unittest
from pathlib import Path

from copilot_improvement.memory import default_memory
from copilot_improvement.project_memory import project_signal_updates
from copilot_improvement.source_scan import scan_projects


class ProjectFeatureTests(unittest.TestCase):
    def test_project_scan_reads_gzipped_als_workflow_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            als_path = root / "Style Study.als"
            xml = """
            <Ableton>
              <LiveSet>
                <Tracks>
                  <MidiTrack>
                    <Name><EffectiveName Value="SUB Bass"/></Name>
                    <AudioOutputRouting><Target Value="Bass Bus"/></AudioOutputRouting>
                  </MidiTrack>
                  <AudioTrack><Name><EffectiveName Value="Drum Bus"/></Name></AudioTrack>
                </Tracks>
                <Scenes><Scene><Name Value="Drop"/></Scene></Scenes>
                <Locators>
                  <Locator><Time Value="64"/><Name Value="Fakeout"/></Locator>
                  <Locator><Time Value="96"/><Name Value="2"/></Locator>
                  <Locator><Time Value="128"/><Name Value="true"/></Locator>
                </Locators>
                <Operator></Operator>
                <AutoFilter></AutoFilter>
                <AutomationEnvelope></AutomationEnvelope>
                <ClipEnvelope></ClipEnvelope>
                <MidiClip Time="32">
                  <CurrentStart Value="0"/>
                  <CurrentEnd Value="16"/>
                  <Name Value="Bass"/>
                </MidiClip>
              </LiveSet>
            </Ableton>
            """
            with gzip.open(als_path, "wb") as handle:
                handle.write(xml.encode("utf-8"))

            project = scan_projects((root,))["projects"][0]

            self.assertTrue(project["parsed"])
            self.assertEqual(project["track_types"]["MidiTrack"], 1)
            self.assertEqual(project["devices"]["Operator"], 1)
            self.assertEqual(project["common_names"]["SUB Bass"], 1)
            self.assertEqual(project["routing_targets"]["Bass Bus"], 1)
            self.assertEqual(project["arrangement_sections"]["Drop"], 1)
            self.assertEqual(project["arrangement_sections"]["Fakeout"], 1)
            self.assertNotIn("true", project["arrangement_sections"])
            self.assertEqual(project["arrangement_markers"]["locator-fakeout-at-64-beats"], 1)
            self.assertEqual(project["arrangement_markers"]["locator-marker-2-at-96-beats"], 1)
            self.assertNotIn("locator-true-at-128-beats", project["arrangement_markers"])
            self.assertEqual(project["arrangement_shape"]["scene-count-1"], 1)
            self.assertEqual(project["arrangement_shape"]["locator-count-3"], 1)
            self.assertEqual(project["arrangement_roles"]["clip-role-bass"], 1)
            self.assertEqual(project["arrangement_roles"]["main-section-role-bass"], 1)
            self.assertNotIn("main-section-phase-bass", project["arrangement_phases"])
            self.assertEqual(project["automation_features"]["AutomationEnvelope"], 1)
            self.assertEqual(project["automation_mentions"], 2)
            self.assertEqual(project["workflows"][0]["label"], "bass-movement-project-workflow")

    def test_project_feature_signals_are_persisted_to_memory(self):
        memory = default_memory()
        updates = project_signal_updates(
            memory,
            {
                "projects": [
                    {
                        "path": "/tmp/Style.als",
                        "common_names": {"SUB Bass": 1},
                        "devices": {"Operator": 1},
                        "track_types": {"MidiTrack": 2},
                        "arrangement_sections": {"Drop": 1},
                        "arrangement_markers": {"locator-drop-at-64-beats": 1},
                        "arrangement_shape": {"common-clip-length-16-beats": 4},
                        "arrangement_roles": {"clip-role-drums": 4},
                        "arrangement_phases": {"main-section-phase-bass-drums": 1},
                        "device_chains": {"Midi track: Operator > AutoFilter > Saturator": 1},
                        "routing_targets": {"Bass Bus": 1},
                        "automation_features": {"AutomationEnvelope": 4},
                    }
                ]
            },
        )
        categories = {update["category"] for update in updates}

        self.assertIn("project.arrangement", categories)
        self.assertIn("project.arrangement-marker", categories)
        self.assertIn("project.arrangement-shape", categories)
        self.assertIn("project.arrangement-role", categories)
        self.assertIn("project.arrangement-phase", categories)
        self.assertIn("project.device-chain", categories)
        self.assertIn("project.routing", categories)
        self.assertIn("project.automation", categories)
        self.assertIn("project.workflow", categories)
        self.assertTrue(any(signal["label"] == "Drop" for signal in memory["signals"]))
        self.assertTrue(any(signal["label"] == "bass-movement-project-workflow" for signal in memory["signals"]))

    def test_project_scan_keeps_regex_fallback_for_partial_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            als_path = root / "Partial.als"
            xml = """
            <Ableton>
              <LiveSet>
                <Locator><Time Value="48"/><Name Value="Breakdown"/></Locator>
                <AudioOutputRouting><Target Value="A-Reverb"/></AudioOutputRouting>
                <AutomationEnvelope></AutomationEnvelope>
            """
            with gzip.open(als_path, "wb") as handle:
                handle.write(xml.encode("utf-8"))

            project = scan_projects((root,))["projects"][0]

            self.assertEqual(project["arrangement_sections"]["Breakdown"], 1)
            self.assertEqual(project["arrangement_markers"]["locator-breakdown-at-48-beats"], 1)
            self.assertEqual(project["arrangement_shape"]["locator-count-1"], 1)
            self.assertEqual(project["routing_targets"]["A-Reverb"], 1)
            self.assertEqual(project["automation_features"]["AutomationEnvelope"], 1)

    def test_project_scan_extracts_arrangement_shape_from_clip_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            als_path = root / "Arrangement.als"
            xml = """
            <Ableton>
              <LiveSet>
                <Scenes><Scene Value=" 1"/><Scene Value=" 2"/></Scenes>
                <MidiClip Time="32">
                  <CurrentStart Value="0"/>
                  <CurrentEnd Value="16"/>
                  <Name Value="Drop Drums"/>
                </MidiClip>
                <MidiClip Time="48">
                  <CurrentStart Value="0"/>
                  <CurrentEnd Value="16"/>
                  <Name Value="Bass"/>
                </MidiClip>
              </LiveSet>
            </Ableton>
            """
            with gzip.open(als_path, "wb") as handle:
                handle.write(xml.encode("utf-8"))

            shape = scan_projects((root,))["projects"][0]["arrangement_shape"]

            self.assertEqual(shape["scene-count-2"], 1)
            self.assertEqual(shape["arrangement-clips-1-16"], 1)
            self.assertEqual(shape["arrangement-start-grid-16-beats"], 1)
            self.assertEqual(shape["common-clip-length-16-beats"], 2)
            roles = scan_projects((root,))["projects"][0]["arrangement_roles"]
            self.assertEqual(roles["clip-role-drums"], 1)
            self.assertEqual(roles["clip-role-bass"], 1)
            phases = scan_projects((root,))["projects"][0]["arrangement_phases"]
            self.assertEqual(phases["main-section-phase-bass-drums"], 1)

    def test_project_scan_extracts_track_device_chain_signatures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            als_path = root / "Device Chain.als"
            xml = """
            <Ableton>
              <LiveSet>
                <Tracks>
                  <MidiTrack>
                    <Name><EffectiveName Value="Mid Bass"/></Name>
                    <DeviceChain>
                      <Devices>
                        <Operator></Operator>
                        <AutoFilter></AutoFilter>
                        <Saturator></Saturator>
                      </Devices>
                    </DeviceChain>
                  </MidiTrack>
                  <AudioTrack>
                    <Name><EffectiveName Value="Short FX"/></Name>
                    <DeviceChain>
                      <Devices><Utility></Utility></Devices>
                    </DeviceChain>
                  </AudioTrack>
                </Tracks>
              </LiveSet>
            </Ableton>
            """
            with gzip.open(als_path, "wb") as handle:
                handle.write(xml.encode("utf-8"))

            project = scan_projects((root,))["projects"][0]

            self.assertEqual(project["device_chains"]["Midi track: Operator > AutoFilter > Saturator"], 1)
            self.assertNotIn("Audio track: Utility", project["device_chains"])


if __name__ == "__main__":
    unittest.main()
