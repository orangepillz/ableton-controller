import unittest
import gzip
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from ableton_controller import local_commands
from ableton_controller.parser import build_parser


class ArrangementAutomationLocalTests(unittest.TestCase):
    def test_arrangement_get_samples_hidden_arrangement_automation_with_round_trips(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "arrangement-automation-get",
                "--track",
                "40-Operator",
                "--arrangement-start",
                "8",
                "--device",
                "Auto Filter",
                "--param",
                "Frequency",
                "--times",
                "0,6,12",
            ]
        )
        calls = []
        state = {"time": 20.0}
        samples = {8.0: 0.2, 14.0: 0.4, 20.0: 0.6}

        def fake_send(payload, _host, _port, _timeout):
            calls.append(payload)
            command = payload["command"]
            if command == "arrangement_automation_get":
                return {
                    "result": {
                        "location": {"start_time": 8.0},
                        "parameter": {"name": "Frequency", "value": samples[state["time"]]},
                        "has_automation": True,
                        "has_envelope": False,
                        "values": [],
                    }
                }
            if command == "lom_get":
                return {"result": state["time"]}
            if command == "lom_set":
                state["time"] = float(payload["value"])
                return {"result": {"path": payload["path"], "value": state["time"]}}
            raise AssertionError(command)

        original_send = local_commands.send
        local_commands.send = fake_send
        try:
            result = local_commands.run_local_command(args)
        finally:
            local_commands.send = original_send

        self.assertEqual(result["read_source"], "client_playhead_sample")
        self.assertEqual(
            result["values"],
            [{"time": 0.0, "value": 0.2}, {"time": 6.0, "value": 0.4}, {"time": 12.0, "value": 0.6}],
        )
        self.assertEqual(state["time"], 20.0)
        self.assertEqual([call["command"] for call in calls].count("arrangement_automation_get"), 4)

    def test_arrangement_file_set_writes_float_event_curve_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            als_path = Path(tmp) / "Curve Test.als"
            self.write_als(als_path)
            parser = build_parser()
            args = parser.parse_args(
                [
                    "arrangement-automation-file-set",
                    "--set-file",
                    str(als_path),
                    "--track",
                    "40-Operator",
                    "--arrangement-start",
                    "8",
                    "--device",
                    "Auto Filter",
                    "--param",
                    "Frequency",
                    "--duration",
                    "24",
                    "--from-normalized",
                    "0.2",
                    "--to-normalized",
                    "0.9",
                    "--curve",
                    "ease-in-out",
                    "--no-backup",
                ]
            )

            result = local_commands.run_local_command(args)
            events = self.frequency_events(als_path)

            self.assertTrue(result["done"])
            self.assertEqual([event.attrib["Time"] for event in events], ["-63072000", "8", "8", "32", "32"])
            self.assertAlmostEqual(float(events[2].attrib["Value"]), 79.621429, places=5)
            self.assertAlmostEqual(float(events[3].attrib["Value"]), 10023.7441, delta=0.01)
            self.assertEqual(events[2].attrib["CurveControl1X"], "0.42")
            self.assertEqual(events[2].attrib["CurveControl1Y"], "0")
            self.assertEqual(events[2].attrib["CurveControl2X"], "0.58")
            self.assertEqual(events[2].attrib["CurveControl2Y"], "1")
            self.assertEqual(self.resonance_values(als_path), ["0", "0.1", "0.35"])

    def test_arrangement_file_get_reads_saved_curve_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            als_path = Path(tmp) / "Curve Test.als"
            self.write_als(als_path, curved=True)
            parser = build_parser()
            args = parser.parse_args(
                [
                    "arrangement-automation-file-get",
                    "--set-file",
                    str(als_path),
                    "--track",
                    "40-Operator",
                    "--arrangement-start",
                    "8",
                    "--device",
                    "Auto Filter",
                    "--param",
                    "Cutoff",
                ]
            )

            result = local_commands.run_local_command(args)

            curved = [event for event in result["events"] if event.get("control_coefficients")]
            self.assertEqual(result["parameter"]["tag"], "Filter_Frequency")
            self.assertEqual(curved[0]["time"], 0.0)
            self.assertEqual(curved[0]["control_coefficients"], {"x1": 0.42, "y1": 0.0, "x2": 0.58, "y2": 1.0})

    def write_als(self, path: Path, curved: bool = False):
        curve_attrs = (
            ' CurveControl1X="0.42" CurveControl1Y="0" CurveControl2X="0.58" CurveControl2Y="1"'
            if curved
            else ""
        )
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Ableton>
  <LiveSet>
    <Tracks>
      <MidiTrack Id="155">
        <Name><EffectiveName Value="40-Operator" /></Name>
        <AutomationEnvelopes>
          <Envelopes>
            <AutomationEnvelope Id="0">
              <EnvelopeTarget><PointeeId Value="70059" /></EnvelopeTarget>
              <Automation><Events>
                <FloatEvent Id="0" Time="-63072000" Value="9999.99805" />
                <FloatEvent Id="10" Time="8" Value="9999.99805" />
                <FloatEvent Id="11" Time="8" Value="79.6214294"{curve_attrs} />
                <FloatEvent Id="12" Time="20" Value="500" />
                <FloatEvent Id="13" Time="32" Value="10023.7441" />
                <FloatEvent Id="14" Time="32" Value="9999.99805" />
              </Events><AutomationTransformViewState /></Automation>
            </AutomationEnvelope>
            <AutomationEnvelope Id="1">
              <EnvelopeTarget><PointeeId Value="70061" /></EnvelopeTarget>
              <Automation><Events>
                <FloatEvent Id="0" Time="-63072000" Value="0" />
                <FloatEvent Id="1" Time="8" Value="0.1" />
                <FloatEvent Id="2" Time="32" Value="0.35" />
              </Events><AutomationTransformViewState /></Automation>
            </AutomationEnvelope>
          </Envelopes>
        </AutomationEnvelopes>
        <ClipTimeable><ArrangerAutomation><Events>
          <MidiClip Id="3" Time="8">
            <CurrentStart Value="8" />
            <CurrentEnd Value="32" />
            <Name Value="Noise Rise" />
          </MidiClip>
        </Events></ArrangerAutomation></ClipTimeable>
        <DeviceChain><Devices>
          <Operator Id="0" />
          <AutoFilter2 Id="1">
            <LastPresetRef><Value><AbletonDefaultPresetRef><DeviceId Name="AutoFilter2" /></AbletonDefaultPresetRef></Value></LastPresetRef>
            <UserName Value="" />
            <Filter_Frequency>
              <Manual Value="9999.99805" />
              <MidiControllerRange><Min Value="19.9999981" /><Max Value="19999.9961" /></MidiControllerRange>
              <AutomationTarget Id="70059"><LockEnvelope Value="0" /></AutomationTarget>
            </Filter_Frequency>
            <Filter_Resonance>
              <Manual Value="0" />
              <MidiControllerRange><Min Value="0" /><Max Value="1" /></MidiControllerRange>
              <AutomationTarget Id="70061"><LockEnvelope Value="0" /></AutomationTarget>
            </Filter_Resonance>
          </AutoFilter2>
        </Devices></DeviceChain>
      </MidiTrack>
    </Tracks>
  </LiveSet>
</Ableton>
"""
        with gzip.open(path, "wb") as handle:
            handle.write(xml.encode("utf-8"))

    def frequency_events(self, path: Path):
        with gzip.open(path, "rb") as handle:
            root = ET.parse(handle).getroot()
        return root.findall(".//AutomationEnvelope[@Id='0']/Automation/Events/FloatEvent")

    def resonance_values(self, path: Path):
        with gzip.open(path, "rb") as handle:
            root = ET.parse(handle).getroot()
        return [event.attrib["Value"] for event in root.findall(".//AutomationEnvelope[@Id='1']/Automation/Events/FloatEvent")]


if __name__ == "__main__":
    unittest.main()
