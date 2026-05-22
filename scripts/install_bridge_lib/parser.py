"""argparse setup for install_bridge."""

import argparse

from .config import DEFAULT_AGENT_DIR, DEFAULT_LAUNCH_AGENTS, DEFAULT_USER_LIBRARY, PROJECT_ROOT
from .filesystem import activate, install
from .midi_agent import install_midi_agent, uninstall_midi_agent
from .restart import restart_activate
from .show import show

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install and activate the Codex_AI Ableton Remote Script.")
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="Install Remote Script into Ableton User Library.")
    install_parser.add_argument("--user-library", default=str(DEFAULT_USER_LIBRARY))
    install_parser.set_defaults(func=install)

    activate_parser = sub.add_parser("activate", help="Patch a Live Preferences.cfg control-surface slot.")
    activate_parser.add_argument("--live-version", default="Live 12.2.7")
    activate_parser.add_argument("--preferences", help="Explicit Preferences.cfg path.")
    activate_parser.add_argument("--replace", default="Alesis_V", help="Existing same-length control surface name.")
    activate_parser.set_defaults(func=activate)

    show_parser = sub.add_parser("show", help="Show install paths.")
    show_parser.add_argument("--user-library", default=str(DEFAULT_USER_LIBRARY))
    show_parser.set_defaults(func=show)

    restart_parser = sub.add_parser("restart-activate", help="Install, quit Live, patch prefs, and reopen Live.")
    restart_parser.add_argument("--user-library", default=str(DEFAULT_USER_LIBRARY))
    restart_parser.add_argument("--live-version", default="Live 12.2.7")
    restart_parser.add_argument("--preferences", help="Explicit Preferences.cfg path.")
    restart_parser.add_argument("--replace", default="Alesis_V", help="Existing same-length control surface name.")
    restart_parser.add_argument("--app-name", default="Ableton Live 12 Suite")
    restart_parser.add_argument(
        "--process-pattern",
        default="/Applications/Ableton Live 12 Suite.app/Contents/MacOS/Live",
    )
    restart_parser.add_argument("--quit-request-timeout", type=float, default=10.0)
    restart_parser.add_argument("--quit-timeout", type=float, default=90.0)
    restart_parser.add_argument("--bridge-host", default="127.0.0.1")
    restart_parser.add_argument("--bridge-port", type=int, default=37337)
    restart_parser.add_argument("--bridge-timeout", type=float, default=3.0)
    restart_parser.add_argument("--save-wait", type=float, default=2.0)
    restart_parser.add_argument("--automation-timeout", type=float, default=5.0)
    restart_parser.add_argument("--dialog-timeout", type=float, default=8.0)
    restart_parser.add_argument(
        "--unsaved-action",
        choices=("stop", "discard", "force-discard-recovery"),
        default="stop",
        help=(
            "What to do when the current set has no file path. "
            "'discard' presses a Live dialog button; "
            "'force-discard-recovery' force-quits and quarantines recovery trigger files."
        ),
    )
    restart_parser.add_argument(
        "--unsaved-dialog-button",
        type=int,
        help="Button index to press for --unsaved-action discard, as exposed by Live's current dialog API.",
    )
    restart_parser.add_argument(
        "--cleanup-track-prefix",
        action="append",
        default=[],
        help="Before discarding an unsaved set, delete regular tracks whose names start with this prefix. Can be repeated.",
    )
    restart_parser.add_argument(
        "--recovery-quarantine-dir",
        default=str(DEFAULT_AGENT_DIR / "recovery-quarantine"),
        help="Directory for recovery files moved out of Ableton preferences after unsaved force discard.",
    )
    restart_parser.set_defaults(func=restart_activate)

    midi_agent_parser = sub.add_parser("install-midi-agent", help="Install and start the CoreMIDI virtual-port LaunchAgent.")
    midi_agent_parser.add_argument("--binary", default=str(PROJECT_ROOT / "codex-midi-ports"))
    midi_agent_parser.add_argument("--agent-dir", default=str(DEFAULT_AGENT_DIR))
    midi_agent_parser.add_argument("--launch-agents", default=str(DEFAULT_LAUNCH_AGENTS))
    midi_agent_parser.add_argument("--source-name", default="V61 (Out)")
    midi_agent_parser.add_argument("--destination-name", default="V61 (In)")
    midi_agent_parser.set_defaults(func=install_midi_agent)

    uninstall_midi_agent_parser = sub.add_parser("uninstall-midi-agent", help="Stop and remove the CoreMIDI virtual-port LaunchAgent.")
    uninstall_midi_agent_parser.add_argument("--launch-agents", default=str(DEFAULT_LAUNCH_AGENTS))
    uninstall_midi_agent_parser.set_defaults(func=uninstall_midi_agent)

    return parser
