"""Parser setup for initial status/selection/render commands."""

from .arg_types import bool_arg, track_value

def add_core_commands(sub):
    sub.add_parser("ping", help="Check bridge connectivity.")
    sub.add_parser("status", help="Show Live set status.")
    sub.add_parser("tracks", help="List tracks, returns, and master.")

    snapshot = sub.add_parser("session-snapshot", help="Run standard read-only probes for production planning.")
    snapshot.add_argument("--track", dest="tracks", action="append", type=track_value, help="Additional target track to inspect.")
    snapshot.add_argument("--no-selected-devices", dest="selected_devices", action="store_false", help="Do not include devices in the selected-track probe.")
    snapshot.add_argument("--no-target-devices", dest="target_devices", action="store_false", help="Do not run device probes for selected/additional targets.")
    snapshot.add_argument("--no-clips", dest="include_clips", action="store_false", help="Do not run clip probes for selected/additional targets.")
    snapshot.add_argument("--device-tree-depth", type=int, default=0, help="Also include target device trees up to this depth.")
    snapshot.set_defaults(selected_devices=True, target_devices=True, include_clips=True)

    selected = sub.add_parser("selected", help="Show selected track.")
    selected.add_argument("--devices", action="store_true", help="Include selected track devices.")

    select_track = sub.add_parser("select-track", help="Select a track by index or name.")
    select_track.add_argument("--track", required=True, type=track_value)

    render = sub.add_parser("render-audio", help="Render a deterministic WAV probe from the Arrangement.")
    render.add_argument("--start-bar", required=True, type=float)
    render.add_argument("--bars", required=True, type=float)
    render.add_argument("--output", required=True)
    render.add_argument("--solo-track", action="append", type=track_value)
    render.add_argument("--solo-tracks", help="Comma-separated track names or indexes.")
    render.add_argument("--solo-group", action="append", type=track_value)
    render.add_argument("--mute-track", action="append", type=track_value)
    render.add_argument("--mute-group", action="append", type=track_value)
    render.add_argument("--include-returns", type=bool_arg, default=True)
    render.add_argument("--sample-rate", type=int, choices=(44100, 48000), default=48000)
    render.add_argument("--bit-depth", type=int, choices=(16, 24, 32), default=24)
    render.add_argument("--normalize", type=bool_arg, default=False)
    render.add_argument("--create-manifest", type=bool_arg, default=True)
    render.add_argument("--restore-state", type=bool_arg, default=True)
    render.add_argument("--request-timeout", type=float, default=180.0, help="Bridge wait time for long exports.")
