#!/usr/bin/env python3
"""Fail when Python modules cross the copilot maintainability size gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from copilot_improvement.repo_scan import python_size_warnings


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    repo_root = Path(args[0]).resolve() if args else REPO_ROOT
    warnings = python_size_warnings(repo_root)
    if not warnings:
        print("size warnings: []")
        return 0
    for warning in warnings:
        print(f"{warning['severity']}: {warning['path']} has {warning['lines']} lines")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
