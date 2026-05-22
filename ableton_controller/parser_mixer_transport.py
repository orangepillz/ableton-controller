"""Parser setup for mixer, parameter, and transport commands."""

from .arg_types import bool_arg, track_value
from .parser_args import add_device_ref_args


def add_mixer_transport_commands(sub):
    set_track = sub.add_parser("set-track", help="Set mixer properties on a track.")
    set_track.add_argument("--track", required=True, type=track_value)
    set_track.add_argument("--volume", type=float)
    set_track.add_argument("--pan", type=float)
    set_track.add_argument("--mute", type=bool_arg)
    set_track.add_argument("--solo", type=bool_arg)
    set_track.add_argument("--arm", type=bool_arg)

    set_send = sub.add_parser("set-send", help="Set a send level on a track.")
    set_send.add_argument("--track", required=True, type=track_value)
    set_send.add_argument("--send", required=True, type=track_value)
    set_send.add_argument("--value", required=True, type=float)

    set_param = sub.add_parser("set-param", help="Set a device parameter.")
    add_device_ref_args(set_param)
    set_param.add_argument("--param", required=True, type=track_value)
    group = set_param.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", type=float, help="Absolute parameter value.")
    group.add_argument("--normalized", type=float, help="0..1 value across the parameter range.")
    group.add_argument("--delta", type=float, help="Relative change from current value.")

    tempo = sub.add_parser("tempo", help="Set or get tempo.")
    tempo.add_argument("--set", type=float)

    sub.add_parser("play", help="Start playback.")
    sub.add_parser("stop", help="Stop playback.")
    sub.add_parser("continue", help="Continue playback.")
    sub.add_parser("undo", help="Undo in Live.")
    sub.add_parser("redo", help="Redo in Live.")
