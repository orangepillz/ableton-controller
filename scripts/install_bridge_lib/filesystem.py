"""Remote Script installation and preference-file activation."""

import argparse
import datetime as _datetime
import shutil
from pathlib import Path

from .config import DEFAULT_PREFS_ROOT, SCRIPT_NAME, SOURCE

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
