"""Parser setup for Serum plug-in commands."""

from pathlib import Path

from .arg_types import json_arg, track_value
from .parser_args import add_container_ref_args

SERUM_PLUGIN_FORMATS = ("vst", "vst3", "vst2", "au", "any")


def add_serum_commands(sub):
    serum_add = sub.add_parser("serum-add", help="Add the Serum VST plug-in to a MIDI track or rack chain.")
    add_container_ref_args(serum_add, "target")
    source = serum_add.add_mutually_exclusive_group()
    source.add_argument("--path", help="Exact Live browser plug-in path, e.g. 'plugins/VST3/Serum'.")
    source.add_argument("--name", help="Plug-in name to search for under the Plugins browser. Defaults to Serum.")
    serum_add.add_argument("--format", choices=SERUM_PLUGIN_FORMATS, default="vst", help="Preferred plug-in format.")
    serum_add.add_argument("--target-index", type=int, help="Device-chain index to place Serum at.")

    serum_params = sub.add_parser("serum-params", help="List exposed parameters for a Serum instance.")
    add_serum_device_args(serum_params)

    serum_names = sub.add_parser("serum-names", help="List Serum plug-in parameter names reported by the plug-in.")
    add_serum_device_args(serum_names)
    serum_names.add_argument("--start", type=int, default=0, help="First parameter-name index to return.")
    serum_names.add_argument("--end", type=int, default=-1, help="End parameter-name index, exclusive. -1 returns all names.")

    serum_set = sub.add_parser("serum-set", help="Set one exposed parameter on a Serum instance.")
    add_serum_device_args(serum_set)
    serum_set.add_argument("--param", required=True, type=track_value)
    add_serum_value_args(serum_set)

    serum_set_many = sub.add_parser("serum-set-many", help="Set multiple exposed parameters on a Serum instance.")
    add_serum_device_args(serum_set_many)
    serum_set_many.add_argument("--controls", required=True, type=json_arg, help="JSON list of param/value objects.")

    serum_build = sub.add_parser("serum-build-preset", help="Build a Serum VST3 preset from AU parameters without opening Serum UI.")
    serum_build.add_argument("--name", required=True, help="Patch name to embed in the Serum state.")
    serum_build.add_argument("--controls", required=True, type=json_arg, help="JSON list of Serum AU param/value objects.")
    serum_build.add_argument("--output", type=Path, help="Destination .vstpreset path. Defaults to /private/tmp/<name>.vstpreset.")
    serum_build.add_argument("--template", type=Path, help="Existing Serum .vstpreset used for VST3 metadata.")


def add_serum_device_args(parser):
    parser.add_argument("--device-path", help="LOM path to a Serum device, including devices inside racks.")
    parser.add_argument("--track", type=track_value, help="Track containing Serum. Defaults to selected track.")
    parser.add_argument("--device", type=track_value, help="Device name/index when you do not want automatic Serum matching.")
    parser.add_argument("--instance", type=int, help="Zero-based Serum instance on the target track when multiple exist.")


def add_serum_value_args(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", type=float, help="Absolute parameter value.")
    group.add_argument("--normalized", type=float, help="0..1 value across the parameter range.")
    group.add_argument("--delta", type=float, help="Relative change from current value.")
