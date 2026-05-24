"""Parser setup for clip-envelope convenience commands."""

from .arg_types import bool_arg, float_list_arg, json_arg, track_value, warp_mode_value
from .parser_args import add_app_arg, add_clip_automation_device_args, add_clip_ref_args, add_registry_arg, add_stock_root_arg


def add_clip_envelope_commands(sub):
    targets = sub.add_parser("clip-envelope-targets", help="List supported clip envelope and audio clip property targets.")
    add_clip_ref_args(targets)

    get_cmd = sub.add_parser("clip-envelope-get", help="Read a clip envelope through a device, stock control, or CC Control lane.")
    _add_target_args(get_cmd)
    get_cmd.add_argument("--times", type=float_list_arg, help="Comma-separated or JSON list of clip times to sample.")

    set_cmd = sub.add_parser("clip-envelope-set", help="Write a clip envelope through a device, stock control, or CC Control lane.")
    _add_target_args(set_cmd)
    set_cmd.add_argument("--steps", type=json_arg, help="JSON list of {time,duration,value|normalized} objects.")
    set_cmd.add_argument("--events", type=json_arg, help="JSON list of breakpoint {time,value|normalized,curve_coefficients?} objects.")
    set_cmd.add_argument("--clear", action="store_true", help="Clear this lane before inserting automation.")
    set_cmd.add_argument("--ensure-midi-cc-device", action="store_true", help="Load CC Control onto the clip track if --target midi-cc has no matching device.")

    clear_cmd = sub.add_parser("clip-envelope-clear", help="Clear a clip envelope lane or all lanes on a clip.")
    _add_target_args(clear_cmd)
    clear_cmd.add_argument("--all", action="store_true", help="Clear every automation envelope in the clip.")

    audio = sub.add_parser("clip-audio-set", help="Set audio clip gain, pitch, warp mode, segment BPM, or reverse the focused sample.")
    add_app_arg(audio)
    add_clip_ref_args(audio)
    audio.add_argument("--gain", type=float)
    audio.add_argument("--pitch-coarse", type=int)
    audio.add_argument("--pitch-fine", type=float)
    audio.add_argument("--ram-mode", type=bool_arg)
    audio.add_argument("--warping", type=bool_arg)
    audio.add_argument("--warp-mode", type=warp_mode_value)
    audio.add_argument("--clip-bpm", type=float, help="Set the first warped segment tempo by pinning beat 1 to the requested BPM.")
    audio.add_argument("--reverse", action="store_true", help="Focus the clip and run Live's Reverse Sample menu action.")


def _add_target_args(parser):
    add_clip_ref_args(parser)
    add_clip_automation_device_args(parser)
    add_registry_arg(parser)
    add_stock_root_arg(parser)
    parser.add_argument("--target", choices=("device", "stock", "midi-cc", "native"), default="device")
    parser.add_argument("--param", type=track_value, help="Device parameter for --target device.")
    parser.add_argument("--stock-device", help="Registry device name/path/slug for --target stock.")
    parser.add_argument("--control", help="Stock control or CC Control lane name.")
    parser.add_argument("--midi-control", help="CC Control lane name for --target midi-cc, e.g. pitch-bend, mod-wheel, pressure.")
