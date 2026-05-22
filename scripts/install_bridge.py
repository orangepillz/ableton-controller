#!/usr/bin/env python3
"""Install and activate the Codex_AI Ableton Remote Script."""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import os
import plistlib
import shutil
import socket
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
        new_offset = find_pref_string(data, new, new_bytes)
        if new_offset >= 0:
            print(f"{new!r} is already configured in {prefs}")
            return
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
    live_set_path = live_set_file_path(args)
    if live_set_path:
        print(f"Live set has a saved path; saving before quit: {live_set_path}")
        try:
            save_live_set(args)
        except RuntimeError as error:
            raise SystemExit(f"Could not save the existing Live set, so Live was not quit: {error}")
    elif live_set_path == "":
        print("Live set has no saved path.")
        cleanup_unsaved_project(args)
        if args.unsaved_action == "stop":
            raise SystemExit(
                "Refusing to restart an unsaved Live set without force quitting. "
                "Save the set first, or rerun with --unsaved-action discard "
                "and --unsaved-dialog-button after confirming the button index."
            )
    else:
        raise SystemExit("Could not determine whether the Live set has a saved path, so Live was not quit.")

    print(f"Requesting quit for {args.app_name}...")
    request_live_quit(args)
    if live_set_path == "" and args.unsaved_action == "discard":
        discard_unsaved_dialog(args)
    if not wait_for_live_to_quit(args.process_pattern, args.quit_timeout):
        raise SystemExit("Live did not quit normally; refusing to force quit because it would trigger recovery on next launch.")
    activate(args)
    print(f"Reopening {args.app_name}...")
    subprocess.run(["open", "-a", args.app_name], check=True)
    print("Live reopened. Wait for startup, then run: python3 abletonctl.py ping")


def live_set_file_path(args: argparse.Namespace) -> str | None:
    try:
        value = bridge_request(
            {"command": "lom_get", "path": "song.file_path"},
            args.bridge_host,
            args.bridge_port,
            args.bridge_timeout,
        )
    except Exception as error:
        print(f"Could not read Live set file path from bridge: {error}")
        return None
    if value is None:
        return ""
    return str(value)


def bridge_request(payload: dict, host: str, port: int, timeout: float):
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(data)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    if not chunks:
        raise RuntimeError("empty bridge response")
    response = json.loads(b"".join(chunks).decode("utf-8"))
    if not response.get("ok", False):
        raise RuntimeError(response.get("error", "unknown bridge error"))
    return response.get("result")


def save_live_set(args: argparse.Namespace) -> None:
    subprocess.run(["open", "-a", args.app_name], check=True)
    run_applescript(
        [
            "delay 0.150",
            'tell application "System Events"',
            '  keystroke "s" using {command down}',
            "end tell",
        ],
        args.automation_timeout,
    )
    time.sleep(max(0.0, args.save_wait))


def cleanup_unsaved_project(args: argparse.Namespace) -> None:
    prefixes = [prefix for prefix in args.cleanup_track_prefix if prefix]
    if not prefixes:
        return
    tracks = bridge_request(
        {"command": "tracks"},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    ).get("tracks", [])
    matches = [
        track
        for track in tracks
        if any(str(track.get("name", "")).startswith(prefix) for prefix in prefixes)
    ]
    for track in sorted(matches, key=lambda item: int(item["index"]), reverse=True):
        bridge_request(
            {"command": "delete_track", "track": int(track["index"])},
            args.bridge_host,
            args.bridge_port,
            args.bridge_timeout,
        )
        print(f"Deleted unsaved scratch track: {track['name']}")


def request_live_quit(args: argparse.Namespace) -> None:
    try:
        quit_result = subprocess.run(
            ["osascript", "-e", f'tell application "{args.app_name}" to quit'],
            check=False,
            timeout=args.quit_request_timeout,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        print("Timed out while requesting normal quit; checking Live dialogs.")
        return
    if quit_result.returncode != 0:
        detail = quit_result.stderr.strip() or quit_result.stdout.strip() or "unknown osascript error"
        print(f"Normal quit request returned an error; checking Live dialogs: {detail}")


def discard_unsaved_dialog(args: argparse.Namespace) -> None:
    if args.unsaved_dialog_button is None:
        message = current_dialog_message(args)
        count = current_dialog_button_count(args)
        raise SystemExit(
            "Unsaved discard requested, but --unsaved-dialog-button was not provided. "
            "Live dialog button count: %s. Message: %r" % (count, message)
        )
    if not wait_for_live_dialog(args, args.dialog_timeout):
        print("No Live dialog appeared after quit request; continuing to wait for normal quit.")
        return
    count = current_dialog_button_count(args)
    index = int(args.unsaved_dialog_button)
    if index < 0 or index >= count:
        raise SystemExit("Dialog button index %s is outside the current button count %s." % (index, count))
    bridge_request(
        {"command": "lom_call", "path": "application.press_current_dialog_button", "args": [index]},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    )


def wait_for_live_dialog(args: argparse.Namespace, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if current_dialog_button_count(args) > 0:
            return True
        time.sleep(0.25)
    return False


def current_dialog_message(args: argparse.Namespace) -> str:
    return bridge_request(
        {"command": "lom_get", "path": "application.current_dialog_message"},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    )


def current_dialog_button_count(args: argparse.Namespace) -> int:
    return int(bridge_request(
        {"command": "lom_get", "path": "application.current_dialog_button_count"},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    ))


def run_applescript(lines: list[str], timeout: float) -> None:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("osascript timed out")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown osascript failure"
        raise RuntimeError(detail)

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
    restart_parser.add_argument("--bridge-host", default="127.0.0.1")
    restart_parser.add_argument("--bridge-port", type=int, default=37337)
    restart_parser.add_argument("--bridge-timeout", type=float, default=3.0)
    restart_parser.add_argument("--save-wait", type=float, default=2.0)
    restart_parser.add_argument("--automation-timeout", type=float, default=5.0)
    restart_parser.add_argument("--dialog-timeout", type=float, default=8.0)
    restart_parser.add_argument(
        "--unsaved-action",
        choices=("stop", "discard"),
        default="stop",
        help="What to do when the current set has no file path. 'discard' presses a Live dialog button; never force-quits.",
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
