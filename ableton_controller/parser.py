"""Top-level parser assembly for abletonctl."""

import argparse

from .parser_args import add_common
from .parser_browser_lom import add_browser_lom_commands
from .parser_clips import add_clip_commands
from .parser_core import add_core_commands
from .parser_devices import add_device_commands
from .parser_local import add_local_commands
from .parser_mixer_transport import add_mixer_transport_commands
from .parser_midi import add_midi_commands
from .parser_stock import add_stock_commands
from .parser_tracks import add_track_scene_commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Ableton Live through Codex_AI.")
    add_common(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    add_core_commands(sub)
    add_device_commands(sub)
    add_stock_commands(sub)
    add_mixer_transport_commands(sub)
    add_local_commands(sub)
    add_browser_lom_commands(sub)
    add_track_scene_commands(sub)
    add_clip_commands(sub)
    add_midi_commands(sub)

    raw = sub.add_parser("raw", help="Send a raw JSON request.")
    raw.add_argument("json_payload")

    return parser
