#!/usr/bin/env python3
"""Run or recover the Ableton producer copilot improvement cycle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from copilot_improvement.config import load_config
from copilot_improvement.memory import restore_memory
from copilot_improvement.orchestrator import run_improvement


def run_command(args: argparse.Namespace) -> int:
    run = run_improvement(
        load_config(),
        validate=args.validate,
        note=args.note,
        why=args.why,
        expected_impact=args.impact,
    )
    print(f"report: {run['report_path']}")
    print(f"memory: {run['memory_path']}")
    if args.validate and any(item["returncode"] != 0 for item in run.get("validation", [])):
        return 1
    return 0


def rollback_command(args: argparse.Namespace) -> int:
    config = load_config()
    backup = config.state_dir / "backups" / f"memory-{args.run_id}.json"
    restore_memory(backup, config.state_dir / "memory.json")
    print(f"restored memory from {backup}")
    return 0


def latest_command(_args: argparse.Namespace) -> int:
    config = load_config()
    latest = config.state_dir / "latest-report.md"
    if not latest.exists():
        print("no improvement report has been written yet")
        return 1
    print(latest.read_text(encoding="utf-8"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Analyze current state and write memory, logs, and report.")
    run.add_argument("--validate", action="store_true", help="Run compileall, unittest, and size gates during the run.")
    run.add_argument("--note", help="Human-readable summary of source, skill, or workflow changes made this execution.")
    run.add_argument("--why", help="Reason the noted change was worth making.")
    run.add_argument("--impact", help="Expected user-facing or maintenance impact of the noted change.")
    run.set_defaults(func=run_command)

    rollback = sub.add_parser("rollback", help="Restore memory from the backup captured before a run.")
    rollback.add_argument("--run-id", required=True)
    rollback.set_defaults(func=rollback_command)

    latest = sub.add_parser("latest", help="Print the latest improvement report.")
    latest.set_defaults(func=latest_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
