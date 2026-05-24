"""Install the abletonctl command link into a user's PATH."""

import argparse
from pathlib import Path

from .config import PROJECT_ROOT

DEFAULT_CLI_BIN_DIR = Path.home() / ".local" / "bin"
CLI_LAUNCHER = PROJECT_ROOT / "bin" / "abletonctl"


def install_cli(args: argparse.Namespace) -> None:
    source = CLI_LAUNCHER
    if not source.exists():
        raise SystemExit(f"CLI launcher not found: {source}")

    bin_dir = Path(args.bin_dir).expanduser()
    link_path = bin_dir / args.name
    bin_dir.mkdir(parents=True, exist_ok=True)

    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink() and _points_to(link_path, source):
            print(f"{args.name} is already installed at {link_path}")
            return
        if link_path.is_dir() and not link_path.is_symlink():
            raise SystemExit(f"Refusing to replace directory: {link_path}")
        if not args.force:
            raise SystemExit(f"Refusing to replace existing path without --force: {link_path}")
        link_path.unlink()

    link_path.symlink_to(source)
    print(f"Installed {args.name} at {link_path}")
    print(f"Link target: {source}")


def _points_to(link_path: Path, source: Path) -> bool:
    try:
        return link_path.resolve() == source.resolve()
    except FileNotFoundError:
        return False
