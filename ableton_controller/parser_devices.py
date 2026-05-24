"""Parser setup for device commands."""

from .arg_types import midi_note_value, track_value
from .config import STOCK_DEVICE_ROOTS
from .parser_args import add_container_ref_args, add_device_ref_args

def add_device_commands(sub):
    devices = sub.add_parser("devices", help="List devices for a track.")
    devices.add_argument("--track", required=True, type=track_value)

    device_tree = sub.add_parser("device-tree", help="List a track's devices, rack chains, nested devices, and LOM paths.")
    device_tree.add_argument("--track", required=True, type=track_value)
    device_tree.add_argument("--depth", type=int, default=4)

    device_add = sub.add_parser("device-add-stock", help="Add a stock Ableton device/effect to a track or rack chain.")
    add_container_ref_args(device_add, "target")
    device_source = device_add.add_mutually_exclusive_group(required=True)
    device_source.add_argument("--path", help="Browser path, e.g. 'audio_effects/EQ Eight'.")
    device_source.add_argument("--name", help="Built-in device name, e.g. 'EQ Eight'.")
    device_add.add_argument("--root", choices=STOCK_DEVICE_ROOTS, help="Browser root to search when using --name.")
    device_add.add_argument("--target-index", type=int, help="Device-chain index to place the device at.")
    device_add.add_argument("--allow-presets", action="store_true", help="Allow loading non-device presets when resolving by browser path.")

    device_move = sub.add_parser("device-move", help="Move/reorder a device on a track or into a rack chain.")
    add_device_ref_args(device_move, "source")
    add_container_ref_args(device_move, "target")
    device_move.add_argument("--target-index", required=True, type=int)

    device_delete = sub.add_parser("device-delete", help="Delete a top-level or rack-chain device.")
    add_device_ref_args(device_delete)

    drum_pad_load = sub.add_parser("drum-pad-load", help="Load a browser item onto a Drum Rack pad.")
    rack_ref = drum_pad_load.add_mutually_exclusive_group(required=True)
    rack_ref.add_argument("--track", type=track_value, help="Track containing the Drum Rack.")
    rack_ref.add_argument("--device-path", help="LOM path to the Drum Rack device.")
    drum_pad_load.add_argument("--device", type=track_value, default="Drum Rack", help="Drum Rack name/index on --track. Defaults to 'Drum Rack'.")
    drum_pad_load.add_argument("--pad", required=True, type=midi_note_value, help="Pad note as 0..127 or note name, e.g. C1.")
    drum_pad_load.add_argument("--item", required=True, help="Live browser path to a sample, instrument, or preset.")
    drum_pad_load.add_argument("--clear", action="store_true", help="Clear existing chains on the pad before loading.")

    params = sub.add_parser("params", help="List parameters for a device.")
    add_device_ref_args(params)
