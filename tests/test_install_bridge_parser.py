import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.install_bridge_lib.parser import build_parser


class InstallBridgeParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_restart_activate_defaults_and_repeated_cleanup_prefixes(self):
        args = self.parser.parse_args(
            [
                "restart-activate",
                "--replace",
                "Alesis_V",
                "--cleanup-track-prefix",
                "Codex ",
                "--cleanup-track-prefix",
                "Temp ",
            ]
        )
        self.assertEqual(args.func.__name__, "restart_activate")
        self.assertEqual(args.cleanup_track_prefix, ["Codex ", "Temp "])
        self.assertEqual(args.bridge_port, 37337)
        self.assertEqual(args.unsaved_action, "stop")

    def test_midi_agent_parser(self):
        args = self.parser.parse_args(
            ["install-midi-agent", "--binary", "/tmp/codex-midi-ports", "--source-name", "Out", "--destination-name", "In"]
        )
        self.assertEqual(args.func.__name__, "install_midi_agent")
        self.assertEqual(args.source_name, "Out")
        self.assertEqual(args.destination_name, "In")

    def test_install_cli_parser_defaults(self):
        args = self.parser.parse_args(["install-cli"])

        self.assertEqual(args.func.__name__, "install_cli")
        self.assertEqual(args.name, "abletonctl")
        self.assertFalse(args.force)
        self.assertTrue(args.bin_dir.endswith(".local/bin"))

    def test_install_cli_creates_command_symlink(self):
        with TemporaryDirectory() as bin_dir:
            args = self.parser.parse_args(["install-cli", "--bin-dir", bin_dir])

            args.func(args)

            link_path = Path(bin_dir) / "abletonctl"
            launcher = Path(__file__).resolve().parents[1] / "bin" / "abletonctl"
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(link_path.resolve(), launcher.resolve())


if __name__ == "__main__":
    unittest.main()
