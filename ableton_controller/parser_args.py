"""Reusable argparse argument groups."""

import argparse

from stock_device_controls import DEFAULT_REGISTRY_PATH

from .arg_types import track_value
from .config import DEFAULT_APP_NAME, DEFAULT_HOST, DEFAULT_PORT, STOCK_DEVICE_ROOTS

def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=8.0)


def add_clip_ref_args(parser: argparse.ArgumentParser, prefix: str = "") -> None:
    flag = "--%s" if not prefix else "--%s-%%s" % prefix
    parser.add_argument(flag % "path")
    parser.add_argument(flag % "track", type=track_value)
    parser.add_argument(flag % "slot", type=int)
    parser.add_argument(flag % "arrangement-index", type=int)
    parser.add_argument(flag % "arrangement-start", type=float)


def add_device_ref_args(parser: argparse.ArgumentParser, prefix: str = "") -> None:
    flag = "--%s" if not prefix else "--%s-%%s" % prefix
    parser.add_argument(flag % "device-path", help="LOM path to a device, including devices inside racks.")
    parser.add_argument(flag % "track", type=track_value)
    parser.add_argument(flag % "device", type=track_value)


def add_clip_automation_device_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device-path", help="LOM path to a device, including devices inside racks.")
    parser.add_argument("--device-track", type=track_value, help="Track containing the device. Defaults to the clip track when possible.")
    parser.add_argument("--device", type=track_value, help="Device name/index on the clip track or --device-track.")


def add_container_ref_args(parser: argparse.ArgumentParser, prefix: str = "target") -> None:
    flag = "--%s-%%s" % prefix
    parser.add_argument(flag % "path", help="LOM path to a Track or Rack Chain.")
    parser.add_argument(flag % "track", type=track_value, help="Target track when no target path is supplied.")


def add_note_region_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=float, help="Clip beat where the note region starts.")
    parser.add_argument("--end", type=float, help="Clip beat where the note region ends.")
    parser.add_argument("--length", type=float, help="Length of the note region in beats.")
    parser.add_argument("--pitch-min", type=int)
    parser.add_argument("--pitch-max", type=int)


def add_clip_range_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=float, help="Arrangement beat where the clip starts.")
    parser.add_argument("--end", type=float, help="Arrangement beat where the clip ends.")
    parser.add_argument("--length", type=float, help="Clip length in beats.")
    parser.add_argument("--from-loop", action="store_true", help="Use Live's current Arrangement loop start/length.")


def add_app_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--app", default=DEFAULT_APP_NAME, help="macOS app name for local keyboard/menu commands.")
    parser.add_argument("--delay", type=float, default=0.08, help="Delay after activating Live, in seconds.")


def add_registry_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH), help="Stock device controls registry JSON.")


def add_stock_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", choices=STOCK_DEVICE_ROOTS, help="Restrict stock-device lookup to this browser root.")


def add_stock_control_value_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", type=float, help="Absolute parameter value.")
    group.add_argument("--normalized", type=float, help="0..1 value across the parameter range.")
    group.add_argument("--delta", type=float, help="Relative change from current value.")
