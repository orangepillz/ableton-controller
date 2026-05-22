"""Parser setup for initial status/selection commands."""

from .arg_types import track_value

def add_core_commands(sub):
    sub.add_parser("ping", help="Check bridge connectivity.")
    sub.add_parser("status", help="Show Live set status.")
    sub.add_parser("tracks", help="List tracks, returns, and master.")

    selected = sub.add_parser("selected", help="Show selected track.")
    selected.add_argument("--devices", action="store_true", help="Include selected track devices.")

    select_track = sub.add_parser("select-track", help="Select a track by index or name.")
    select_track.add_argument("--track", required=True, type=track_value)
