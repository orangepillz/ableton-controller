"""Higher-level bridge calls used by install/restart workflows."""

import argparse
import subprocess
import time

from .automation import run_applescript
from .bridge_core import bridge_request

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
