import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from ableton_controller.local_commands import run_local_command
from ableton_controller.parser import build_parser


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_plan_module():
    script = REPO_ROOT / "skills" / "ableton-producer" / "scripts" / "ableton_plan.py"
    spec = importlib.util.spec_from_file_location("ableton_plan", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowMacroTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.plan_module = load_plan_module()

    def local_result(self, *argv):
        return run_local_command(self.parser.parse_args(["workflow-macro", *argv]))

    def test_lists_available_macros(self):
        result = self.local_result("list")
        names = {macro["name"] for macro in result["macros"]}

        self.assertIn("bass-movement", names)
        self.assertIn("bass-resampling-pass", names)
        self.assertIn("kick-sub-separation", names)
        self.assertIn("arrangement-phase-scaffold", names)
        self.assertIn("arrangement-marker-naming", names)
        self.assertIn("personalized-space-chain", names)
        self.assertIn("mix-bus-control", names)
        self.assertIn("riser-transition", names)

    def test_renders_plan_validator_compatible_macro(self):
        plan = self.local_result("render", "bass-movement", "--track", "Neuro Bass", "--slot", "2")
        _steps, errors, warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertTrue(any("--clear" in step["args"] for step in plan["commands"]))
        self.assertTrue(warnings)
        self.assertEqual(plan["macro"], "bass-movement")
        self.assertEqual(plan["commands"][0]["args"][:3], ["session-snapshot", "--track", "Neuro Bass"])

    def test_render_requires_known_macro(self):
        with self.assertRaises(SystemExit):
            self.local_result("render", "unknown")

    def test_bass_resampling_macro_prepares_print_track_without_recording(self):
        plan = self.local_result(
            "render",
            "bass-resampling-pass",
            "--track",
            "Mid Bass",
            "--start",
            "64",
            "--length",
            "8",
            "--print-track",
            "Bass Print",
        )
        commands = [step["args"][0] for step in plan["commands"]]
        _steps, errors, _warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertIn("arrangement-automation-set", commands)
        self.assertIn("set-routing", commands)
        self.assertNotIn("play", commands)
        self.assertNotIn("save", commands)
        self.assertEqual(plan["macro"], "bass-resampling-pass")

    def test_riser_transition_macro_creates_non_destructive_inhale_plan(self):
        plan = self.local_result(
            "render",
            "riser-transition",
            "--track",
            "Drop Riser",
            "--slot",
            "1",
            "--length",
            "16",
        )
        commands = [step["args"] for step in plan["commands"] if step["args"]]
        _steps, errors, warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertTrue(warnings)
        self.assertEqual(plan["macro"], "riser-transition")
        self.assertIn("Riser MIDI track is 'Drop Riser'", plan["assumptions"])
        self.assertEqual(commands[1], ["create-track", "--type", "midi", "--name", "Drop Riser"])
        self.assertIn(["device-add-stock", "--target-track", "Drop Riser", "--path", "audio_effects/Auto Filter"], commands)
        self.assertIn(["device-add-stock", "--target-track", "Drop Riser", "--path", "audio_effects/Reverb"], commands)
        self.assertTrue(any(args[0] == "clip-stock-automation-set" for args in commands))
        self.assertEqual(commands[-1][:3], ["session-snapshot", "--track", "Drop Riser"])

    def test_kick_sub_macro_uses_personal_target_aliases_when_memory_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {"id": "project.name.bd", "category": "project.name", "label": "BD", "confidence": 0.4, "evidence_count": 4},
                            {
                                "id": "project.name.basic-organ-bass",
                                "category": "project.name",
                                "label": "18-Basic Organ Bass",
                                "confidence": 0.32,
                                "evidence_count": 3,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result("render", "kick-sub-separation", "--memory", str(memory_path))
            commands = [step["args"] for step in plan["commands"] if step["args"]]
            _steps, errors, warnings = self.plan_module.validate_plan(plan)

            self.assertEqual(errors, [])
            self.assertFalse(warnings)
            self.assertIn("Kick track is 'BD'", plan["assumptions"])
            self.assertIn("Sub track is '18-Basic Organ Bass'", plan["assumptions"])
            self.assertEqual(commands[0][:5], ["session-snapshot", "--track", "BD", "--track", "18-Basic Organ Bass"])

    def test_kick_sub_macro_preserves_explicit_targets_over_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps({"signals": [{"category": "project.name", "label": "BD", "confidence": 0.4, "evidence_count": 4}]}),
                encoding="utf-8",
            )

            plan = self.local_result("render", "kick-sub-separation", "--kick-track", "My Kick", "--sub-track", "My Sub", "--memory", str(memory_path))

            self.assertIn("Kick track is 'My Kick'", plan["assumptions"])
            self.assertIn("Sub track is 'My Sub'", plan["assumptions"])

    def test_glitch_drum_transition_macro_uses_chat_evidence_workflow(self):
        plan = self.local_result(
            "render",
            "glitch-drum-transition",
            "--track",
            "Zap Rack",
            "--secondary-track",
            "Perc Rack",
            "--synth-track",
            "Lead Synth",
            "--length",
            "8",
        )
        commands = [step["args"][0] for step in plan["commands"]]
        _steps, errors, warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertEqual(plan["macro"], "glitch-drum-transition")
        self.assertIn("browser-search", commands)
        self.assertIn("drum-pad-load", commands)
        self.assertIn("midi-add-notes", commands)
        self.assertFalse(warnings)
        zap_notes = next(step for step in plan["commands"] if step["why"].startswith("Write zap stutters"))["args"][-1]
        self.assertNotIn('"start_time":4', zap_notes)

    def test_arrangement_phase_scaffold_creates_named_non_destructive_scenes(self):
        plan = self.local_result("render", "arrangement-phase-scaffold", "--scene-index", "3")
        commands = [step["args"] for step in plan["commands"] if step["args"]]
        _steps, errors, warnings = self.plan_module.validate_plan(plan)

        self.assertEqual(errors, [])
        self.assertFalse(warnings)
        self.assertEqual(plan["macro"], "arrangement-phase-scaffold")
        self.assertEqual(commands[0][0], "session-snapshot")
        scene_commands = [args for args in commands if args[0] == "create-scene"]
        self.assertEqual(len(scene_commands), 4)
        self.assertEqual(scene_commands[0], ["create-scene", "--name", "01 Early - Drum FX Kick Setup", "--index", 3])
        self.assertTrue(any("Main" in str(arg) for command in scene_commands for arg in command))

    def test_drum_punch_macro_uses_personal_drum_alias_when_memory_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {"id": "project.name.drums", "category": "project.name", "label": "Drums", "confidence": 0.44, "evidence_count": 8},
                            {"id": "project.name.tr8s", "category": "project.name", "label": "TR8S", "confidence": 0.4, "evidence_count": 6},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result("render", "drum-punch-bus", "--memory", str(memory_path))
            commands = [step["args"] for step in plan["commands"] if step["args"]]
            _steps, errors, warnings = self.plan_module.validate_plan(plan)

            self.assertEqual(errors, [])
            self.assertFalse(warnings)
            self.assertIn("Drum bus track is 'Drums'", plan["assumptions"])
            self.assertEqual(commands[0], ["session-snapshot", "--track", "Drums", "--device-tree-depth", 3])
            self.assertIn(["device-add-stock", "--target-track", "Drums", "--path", "audio_effects/Drum Buss"], commands)

    def test_drum_punch_macro_preserves_explicit_track_over_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps({"signals": [{"id": "project.name.drums", "category": "project.name", "label": "Drums", "confidence": 0.44}]}),
                encoding="utf-8",
            )

            plan = self.local_result("render", "drum-punch-bus", "--track", "Parallel Drum Bus", "--memory", str(memory_path))

            self.assertIn("Drum bus track is 'Parallel Drum Bus'", plan["assumptions"])

    def test_arrangement_marker_naming_renames_learned_locator_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {"category": "project.arrangement-marker", "label": "locator-marker-3-at-128-beats", "confidence": 0.3},
                            {"category": "project.arrangement-marker", "label": "locator-marker-1-at-0-beats", "confidence": 0.3},
                            {"category": "project.arrangement-marker", "label": "locator-marker-2-at-64-beats", "confidence": 0.3},
                            {"id": "project.arrangement-phase.main-section-phase-drums-kick", "category": "project.arrangement-phase", "label": "main-section-phase-drums-kick", "confidence": 0.3},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result("render", "arrangement-marker-naming", "--memory", str(memory_path))
            commands = [step["args"] for step in plan["commands"] if step["args"]]
            _steps, errors, warnings = self.plan_module.validate_plan(plan)

            self.assertEqual(errors, [])
            self.assertTrue(warnings)
            self.assertEqual(plan["macro"], "arrangement-marker-naming")
            self.assertIn("persisted project.arrangement-marker", plan["assumptions"][0])
            self.assertEqual(commands[0], ["locators"])
            locator_commands = [args for args in commands if args[0] == "set-locator"]
            self.assertEqual(len(locator_commands), 3)
            self.assertEqual(locator_commands[1], ["set-locator", "--time", 64.0, "--name", "02 Main Drop - Drum Kick Impact (marker 2)"])
        self.assertEqual(commands[-1], ["locators"])

    def test_personalized_space_chain_uses_learned_delay_reverb_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = Path(tmp) / "memory.json"
            memory_path.write_text(
                json.dumps(
                    {
                        "signals": [
                            {
                                "id": "project.device-chain.midi-track-delay-reverb",
                                "category": "project.device-chain",
                                "label": "Midi track: Delay > Reverb",
                                "confidence": 0.4,
                                "evidence_count": 2,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plan = self.local_result("render", "personalized-space-chain", "--track", "Vox Throw", "--memory", str(memory_path))
            commands = [step["args"] for step in plan["commands"] if step["args"]]
            _steps, errors, warnings = self.plan_module.validate_plan(plan)

            self.assertEqual(errors, [])
            self.assertFalse(warnings)
            self.assertEqual(plan["macro"], "personalized-space-chain")
            self.assertIn("project.device-chain.midi-track-delay-reverb", plan["assumptions"][1])
            self.assertIn(["device-add-stock", "--target-track", "Vox Throw", "--path", "audio_effects/Delay"], commands)
            self.assertIn(["device-add-stock", "--target-track", "Vox Throw", "--path", "audio_effects/Reverb"], commands)
            self.assertEqual(commands[-1][:3], ["session-snapshot", "--track", "Vox Throw"])


if __name__ == "__main__":
    unittest.main()
