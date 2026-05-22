"""Install path reporting command."""

import argparse
from pathlib import Path

from .config import SCRIPT_NAME, SOURCE

def show(args: argparse.Namespace) -> None:
    destination = Path(args.user_library).expanduser() / "Remote Scripts" / SCRIPT_NAME
    print(f"Script source: {SOURCE}")
    print(f"Install destination: {destination}")
    print(f"Installed: {destination.exists()}")
