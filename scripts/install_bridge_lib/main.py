"""Entrypoint for scripts/install_bridge.py."""

from .parser import build_parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0
