#!/usr/bin/env python3
"""Install and activate the Codex_AI Ableton Remote Script."""

from __future__ import annotations

import argparse
import datetime as _datetime
import os
import plistlib
import shutil
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = "Codex_AI"
SOURCE = PROJECT_ROOT / "remote_scripts" / SCRIPT_NAME
DEFAULT_USER_LIBRARY = Path.home() / "Music" / "Ableton" / "User Library"
DEFAULT_PREFS_ROOT = Path.home() / "Library" / "Preferences" / "Ableton"
DEFAULT_AGENT_DIR = Path.home() / "Library" / "Application Support" / "CodexAbleton"
DEFAULT_LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
MIDI_AGENT_LABEL = "com.codex.ableton-midi-ports"


def copytree_replace(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def install(args: argparse.Namespace) -> None:
    destination_root = Path(args.user_library).expanduser() / "Remote Scripts"
    destination = destination_root / SCRIPT_NAME
    destination_root.mkdir(parents=True, exist_ok=True)
    copytree_replace(SOURCE, destination)
    print(f"Installed {SCRIPT_NAME} to {destination}")


def activate(args: argparse.Namespace) -> None:
    prefs = Path(args.preferences).expanduser() if args.preferences else DEFAULT_PREFS_ROOT / args.live_version / "Preferences.cfg"
    if not prefs.exists():
        raise SystemExit(f"Preferences file not found: {prefs}")

    old = args.replace
    new = SCRIPT_NAME
    if len(old) != len(new):
        raise SystemExit(f"Replacement must be same length: {old!r} vs {new!r}")

    old_bytes = old.encode("utf-16le")
    new_bytes = new.encode("utf-16le")
    data = prefs.read_bytes()
    offset = find_pref_string(data, old, old_bytes)
    if offset < 0:
        raise SystemExit(f"Could not find standalone control-surface value {old!r} in {prefs}")

    timestamp = _datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = prefs.with_name(f"{prefs.name}.codex-backup-{timestamp}")
    backup.write_bytes(data)
    prefs.write_bytes(data[:offset] + new_bytes + data[offset + len(old_bytes):])
    print(f"Updated first {old!r} control-surface preference to {new!r}")
    print(f"Backup: {backup}")


def find_pref_string(data: bytes, text: str, encoded: bytes) -> int:
    """Find a UTF-16LE Ableton string value, not a substring inside a longer value."""
    length_prefix = len(text).to_bytes(4, "little")
    start = 0
    while True:
        offset = data.find(encoded, start)
        if offset < 0:
            return -1
        if offset >= 4 and data[offset - 4:offset] == length_prefix:
            return offset
        start = offset + 1


def show(args: argparse.Namespace) -> None:
    destination = Path(args.user_library).expanduser() / "Remote Scripts" / SCRIPT_NAME
    print(f"Script source: {SOURCE}")
    print(f"Install destination: {destination}")
    print(f"Installed: {destination.exists()}")


def restart_activate(args: argparse.Namespace) -> None:
    install(args)
    print(f"Requesting quit for {args.app_name}...")
    try:
        quit_result = subprocess.run(
            ["osascript", "-e", f'tell application "{args.app_name}" to quit'],
            check=False,
            timeout=args.quit_request_timeout,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(
            "Timed out requesting Live to quit. If Live is showing an unsaved-changes dialog, "
            "handle it and run this command again."
        )
    if quit_result.returncode != 0:
        detail = quit_result.stderr.strip() or quit_result.stdout.strip() or "unknown osascript error"
        raise SystemExit(
            "Live declined the quit request: %s\n"
            "If Live is showing an unsaved-changes dialog, handle it and run this command again." % detail
        )
    if not wait_for_live_to_quit(args.process_pattern, args.quit_timeout):
        raise SystemExit(
            "Live did not quit before the timeout. If Live is showing an unsaved-changes dialog, "
            "handle it and run this command again."
        )
    activate(args)
    print(f"Reopening {args.app_name}...")
    subprocess.run(["open", "-a", args.app_name], check=True)
    print("Live reopened. Wait for startup, then run: python3 abletonctl.py ping")


def install_midi_agent(args: argparse.Namespace) -> None:
    binary = Path(args.binary).expanduser().resolve()
    if not binary.exists():
        raise SystemExit(
            f"Binary not found: {binary}. "
            "Compile it with: swiftc -module-cache-path .build/ModuleCache "
            "scripts/codex_midi_ports.swift -o codex-midi-ports"
        )

    agent_dir = Path(args.agent_dir).expanduser()
    launch_agents = Path(args.launch_agents).expanduser()
    agent_dir.mkdir(parents=True, exist_ok=True)
    launch_agents.mkdir(parents=True, exist_ok=True)

    target = agent_dir / "codex-midi-ports"
    shutil.copy2(binary, target)
    target.chmod(0o755)

    plist_path = launch_agents / f"{MIDI_AGENT_LABEL}.plist"
    plist = {
        "Label": MIDI_AGENT_LABEL,
        "ProgramArguments": [str(target), args.source_name, args.destination_name],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(agent_dir / "midi-ports.out.log"),
        "StandardErrorPath": str(agent_dir / "midi-ports.err.log"),
        "WorkingDirectory": str(agent_dir),
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=False)

    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(plist_path)], check=False, capture_output=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(plist_path)], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{MIDI_AGENT_LABEL}"], check=False)
    print(f"Installed and started {MIDI_AGENT_LABEL}")
    print(f"Binary: {target}")
    print(f"Plist: {plist_path}")


def uninstall_midi_agent(args: argparse.Namespace) -> None:
    plist_path = Path(args.launch_agents).expanduser() / f"{MIDI_AGENT_LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(plist_path)], check=False, capture_output=True)
    if plist_path.exists():
        plist_path.unlink()
    print(f"Uninstalled {MIDI_AGENT_LABEL}")


def wait_for_live_to_quit(pattern: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(["pgrep", "-fl", pattern], capture_output=True, text=True)
        lines = [line for line in result.stdout.splitlines() if "Ableton Index" not in line]
        if not lines:
            return True
        time.sleep(1.0)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
