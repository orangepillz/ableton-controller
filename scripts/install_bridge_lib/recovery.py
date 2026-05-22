"""Unsaved-set recovery quarantine helpers."""

import argparse
import datetime as _datetime
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from .config import DEFAULT_PREFS_ROOT, RECOVERY_TRIGGER_NAMES

def force_discard_unsaved_project(args: argparse.Namespace) -> None:
    before = recovery_snapshot(args)
    existing_triggers = sorted(path for path in before if path.parent == live_preferences_dir(args))
    if existing_triggers:
        raise SystemExit(
            "Live already has pending recovery trigger files before force quit, so refusing to discard them: %s"
            % ", ".join(str(path) for path in existing_triggers)
        )
    print("Force quitting unsaved Live set, then quarantining recovery trigger files before reopen.")
    force_quit_live(args.process_pattern, args.quit_timeout)
    quarantined = quarantine_new_recovery_files(args, before)
    if quarantined:
        print("Quarantined Live recovery files:")
        for source, destination in quarantined:
            print(f"  {source} -> {destination}")
    else:
        print("No new Live recovery files were found to quarantine.")


def live_preferences_dir(args: argparse.Namespace) -> Path:
    if args.preferences:
        return Path(args.preferences).expanduser().resolve().parent
    return DEFAULT_PREFS_ROOT / args.live_version


def recovery_snapshot(args: argparse.Namespace) -> set[Path]:
    return set(recovery_candidates(live_preferences_dir(args)))


def recovery_candidates(preferences_dir: Path) -> list[Path]:
    candidates = [preferences_dir / name for name in RECOVERY_TRIGGER_NAMES]
    crash_dir = preferences_dir / "Crash"
    if crash_dir.exists():
        candidates.extend(crash_dir.iterdir())
    return [path for path in candidates if path.exists()]


def quarantine_new_recovery_files(args: argparse.Namespace, before: set[Path]) -> list[tuple[Path, Path]]:
    preferences_dir = live_preferences_dir(args)
    timestamp = _datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    quarantine_root = Path(args.recovery_quarantine_dir).expanduser() / f"{args.live_version}-{timestamp}"
    moved = []
    for source in sorted(recovery_candidates(preferences_dir), key=lambda path: str(path)):
        if source in before:
            continue
        destination = quarantine_root / source.relative_to(preferences_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        moved.append((source, destination))
    return moved


def force_quit_live(pattern: str, timeout: float) -> None:
    pids = live_process_ids(pattern)
    if not pids:
        return
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if not wait_for_live_to_quit(pattern, timeout):
        raise SystemExit("Live did not exit after force quit.")


def live_process_ids(pattern: str) -> list[int]:
    result = subprocess.run(["pgrep", "-fl", pattern], capture_output=True, text=True)
    pids = []
    for line in result.stdout.splitlines():
        if "Ableton Index" in line:
            continue
        parts = line.split(maxsplit=1)
        if not parts:
            continue
        try:
            pids.append(int(parts[0]))
        except ValueError:
            pass
    return pids


def wait_for_live_to_quit(pattern: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(["pgrep", "-fl", pattern], capture_output=True, text=True)
        lines = [line for line in result.stdout.splitlines() if "Ableton Index" not in line]
        if not lines:
            return True
        time.sleep(1.0)
    return False
