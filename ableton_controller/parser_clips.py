"""Parser setup for clip commands."""

from .arg_types import bool_arg, float_list_arg, json_arg, track_value, warp_mode_value
from .arrangement_automation import CURVE_PRESETS
from .parser_args import add_clip_automation_device_args, add_clip_range_args, add_clip_ref_args, add_registry_arg, add_stock_root_arg

def add_clip_commands(sub):
    clips = sub.add_parser("clips", help="List Session slots and Arrangement clips for a track.")
    clips.add_argument("--track", required=True, type=track_value)

    clip_create = sub.add_parser("clip-create-midi", help="Create a MIDI clip in Arrangement or a Session slot.")
    clip_create.add_argument("--track", required=True, type=track_value)
    clip_create.add_argument("--slot", type=int, help="Create in this Session slot. Omit for Arrangement.")
    add_clip_range_args(clip_create)
    clip_create.add_argument("--name")
    clip_create.add_argument("--color", type=int)
    clip_create.add_argument("--color-index", type=int)
    clip_create.add_argument("--replace", action="store_true", help="Replace an existing Session clip in the target slot.")

    clip_create_audio = sub.add_parser("clip-create-audio", help="Create an audio clip from a file in Arrangement or a Session slot.")
    clip_create_audio.add_argument("--track", required=True, type=track_value)
    clip_create_audio.add_argument("--file", required=True, help="Absolute path to an audio file.")
    clip_create_audio.add_argument("--slot", type=int, help="Create in this Session slot. Omit for Arrangement.")
    add_clip_range_args(clip_create_audio)
    clip_create_audio.add_argument("--name")
    clip_create_audio.add_argument("--color", type=int)
    clip_create_audio.add_argument("--color-index", type=int)
    clip_create_audio.add_argument("--replace", action="store_true", help="Replace an existing Session clip in the target slot.")
    clip_create_audio.add_argument("--warping", type=bool_arg)
    clip_create_audio.add_argument("--warp-mode", type=warp_mode_value)

    clip_set = sub.add_parser("clip-set", help="Set clip properties like name, loop range, markers, mute, launch, and audio settings.")
    add_clip_ref_args(clip_set)
    clip_set.add_argument("--name")
    clip_set.add_argument("--color", type=int)
    clip_set.add_argument("--color-index", type=int)
    clip_set.add_argument("--muted", type=bool_arg)
    clip_set.add_argument("--looping", type=bool_arg)
    clip_set.add_argument("--loop-start", type=float)
    clip_set.add_argument("--loop-end", type=float)
    clip_set.add_argument("--start-marker", type=float)
    clip_set.add_argument("--end-marker", type=float)
    clip_set.add_argument("--position", type=float)
    clip_set.add_argument("--launch-mode", type=int)
    clip_set.add_argument("--launch-quantization", type=int)
    clip_set.add_argument("--legato", type=bool_arg)
    clip_set.add_argument("--velocity-amount", type=float)
    clip_set.add_argument("--signature-numerator", type=int)
    clip_set.add_argument("--signature-denominator", type=int)
    clip_set.add_argument("--gain", type=float)
    clip_set.add_argument("--pitch-coarse", type=int)
    clip_set.add_argument("--pitch-fine", type=float)
    clip_set.add_argument("--ram-mode", type=bool_arg)
    clip_set.add_argument("--warping", type=bool_arg)
    clip_set.add_argument("--warp-mode", type=warp_mode_value)

    clip_warp = sub.add_parser("clip-warp", help="Read or set audio clip warp state, mode, pitch, gain, and markers.")
    add_clip_ref_args(clip_warp)
    clip_warp.add_argument("--warping", type=bool_arg)
    clip_warp.add_argument("--warp-mode", type=warp_mode_value)
    clip_warp.add_argument("--gain", type=float)
    clip_warp.add_argument("--pitch-coarse", type=int)
    clip_warp.add_argument("--pitch-fine", type=float)
    clip_warp.add_argument("--ram-mode", type=bool_arg)
    clip_warp.add_argument("--clip-bpm", type=float, help="Set the first warped segment tempo by pinning beat 1 to the requested BPM.")

    warp_add = sub.add_parser("clip-warp-marker-add", help="Add a warp marker to a warped audio clip.")
    add_clip_ref_args(warp_add)
    warp_add.add_argument("--beat-time", required=True, type=float, help="Clip beat to pin.")
    warp_add.add_argument("--sample-time", type=float, help="Sample-file time in seconds. Omit to preserve current playback timing by interpolation.")

    warp_move = sub.add_parser("clip-warp-marker-move", help="Move an existing warp marker by beat distance or to a beat.")
    add_clip_ref_args(warp_move)
    warp_move.add_argument("--beat-time", required=True, type=float, help="Current beat time of the marker to move.")
    move_group = warp_move.add_mutually_exclusive_group(required=True)
    move_group.add_argument("--distance", type=float, help="Beat distance to move the marker.")
    move_group.add_argument("--to-beat", type=float, help="Destination beat time for the marker.")

    warp_remove = sub.add_parser("clip-warp-marker-remove", help="Remove a warp marker at a beat time.")
    add_clip_ref_args(warp_remove)
    warp_remove.add_argument("--beat-time", required=True, type=float)

    automation_get = sub.add_parser("clip-automation-get", help="Read a clip automation envelope for any device parameter.")
    add_clip_ref_args(automation_get)
    add_clip_automation_device_args(automation_get)
    automation_get.add_argument("--param", required=True, type=track_value)
    automation_get.add_argument("--times", type=float_list_arg, help="Comma-separated or JSON list of clip times to sample.")

    automation_set = sub.add_parser("clip-automation-set", help="Create/update a clip automation envelope with steps or breakpoint events.")
    add_clip_ref_args(automation_set)
    add_clip_automation_device_args(automation_set)
    automation_set.add_argument("--param", required=True, type=track_value)
    automation_set.add_argument("--steps", type=json_arg, help="JSON list of {time,duration,value|normalized} objects.")
    automation_set.add_argument("--events", type=json_arg, help="JSON list of breakpoint {time,value|normalized,curve_coefficients?} objects.")
    automation_set.add_argument("--clear", action="store_true", help="Clear this parameter's existing envelope before inserting automation.")

    automation_set_many = sub.add_parser(
        "clip-automation-set-many",
        help="Write multiple clip automation lanes in one pass.",
    )
    add_clip_ref_args(automation_set_many)
    add_clip_automation_device_args(automation_set_many)
    automation_set_many.add_argument(
        "--lanes",
        required=True,
        type=json_arg,
        help="JSON list of lane specs with param plus steps, events, or duration/from/to ramp fields.",
    )

    arrangement_automation_get = sub.add_parser("arrangement-automation-get", help="Read an Arrangement clip automation lane.")
    arrangement_automation_get.add_argument("--track", required=True, type=track_value)
    arrangement_automation_get.add_argument("--arrangement-start", required=True, type=float)
    add_clip_automation_device_args(arrangement_automation_get)
    arrangement_automation_get.add_argument("--param", required=True, type=track_value)
    arrangement_automation_get.add_argument("--times", type=float_list_arg, help="Comma-separated or JSON list of clip-relative times to sample.")

    arrangement_automation_set = sub.add_parser("arrangement-automation-set", help="Write automation over an Arrangement clip range.")
    arrangement_automation_set.add_argument("--track", required=True, type=track_value)
    arrangement_automation_set.add_argument("--arrangement-start", required=True, type=float)
    add_clip_automation_device_args(arrangement_automation_set)
    arrangement_automation_set.add_argument("--param", required=True, type=track_value)
    arrangement_automation_set.add_argument("--duration", type=float, help="Automation duration in clip beats.")
    start_value = arrangement_automation_set.add_mutually_exclusive_group()
    start_value.add_argument("--from-normalized", type=float, help="Starting 0..1 normalized value.")
    start_value.add_argument("--from-value", type=float, help="Starting raw parameter value.")
    end_value = arrangement_automation_set.add_mutually_exclusive_group()
    end_value.add_argument("--to-normalized", type=float, help="Ending 0..1 normalized value for a generated ramp.")
    end_value.add_argument("--to-value", type=float, help="Ending raw parameter value for a generated ramp.")
    arrangement_automation_set.add_argument("--steps", type=int, default=8, help="Number of generated segments when an ending value is supplied.")
    arrangement_automation_set.add_argument("--events", type=json_arg, help="JSON list of breakpoint {time,value|normalized,curve_coefficients?} objects.")
    arrangement_automation_set.add_argument("--curve", choices=CURVE_PRESETS, help="Write two breakpoint events with this curve between them.")
    arrangement_automation_set.add_argument("--curve-coefficients", type=json_arg, help="Bezier control object {x1,y1,x2,y2} for the first generated breakpoint.")
    arrangement_automation_set.add_argument("--clear", action="store_true", help="Clear this parameter's existing envelope before inserting automation.")

    arrangement_automation_set_many = sub.add_parser(
        "arrangement-automation-set-many",
        help="Write multiple Arrangement clip automation lanes in one pass.",
    )
    arrangement_automation_set_many.add_argument("--track", required=True, type=track_value)
    arrangement_automation_set_many.add_argument("--arrangement-start", required=True, type=float)
    add_clip_automation_device_args(arrangement_automation_set_many)
    arrangement_automation_set_many.add_argument(
        "--lanes",
        required=True,
        type=json_arg,
        help="JSON list of lane specs with param plus steps, events, or duration/from/to ramp fields.",
    )

    automation_clear = sub.add_parser("clip-automation-clear", help="Clear a clip automation envelope for one parameter or all parameters.")
    add_clip_ref_args(automation_clear)
    add_clip_automation_device_args(automation_clear)
    automation_clear.add_argument("--param", type=track_value, help="Parameter to clear. Omit with --all.")
    automation_clear.add_argument("--all", action="store_true", help="Clear every automation envelope in the clip.")

    stock_automation_get = sub.add_parser("clip-stock-automation-get", help="Read clip automation using a stock-device control alias.")
    add_registry_arg(stock_automation_get)
    add_clip_ref_args(stock_automation_get)
    add_clip_automation_device_args(stock_automation_get)
    add_stock_root_arg(stock_automation_get)
    stock_automation_get.add_argument("--stock-device", help="Registry device name/path/slug. Defaults to --device when that is a name.")
    stock_automation_get.add_argument("--control", required=True, help="Control name, slug, alias, or parameter index.")
    stock_automation_get.add_argument("--times", type=float_list_arg, help="Comma-separated or JSON list of clip times to sample.")

    stock_automation_set = sub.add_parser("clip-stock-automation-set", help="Create/update clip automation using a stock-device control alias.")
    add_registry_arg(stock_automation_set)
    add_clip_ref_args(stock_automation_set)
    add_clip_automation_device_args(stock_automation_set)
    add_stock_root_arg(stock_automation_set)
    stock_automation_set.add_argument("--stock-device", help="Registry device name/path/slug. Defaults to --device when that is a name.")
    stock_automation_set.add_argument("--control", required=True, help="Control name, slug, alias, or parameter index.")
    stock_automation_set.add_argument("--steps", type=json_arg, help="JSON list of {time,duration,value|normalized} objects.")
    stock_automation_set.add_argument("--events", type=json_arg, help="JSON list of breakpoint {time,value|normalized,curve_coefficients?} objects.")
    stock_automation_set.add_argument("--clear", action="store_true", help="Clear this parameter's existing envelope before inserting steps.")

    stock_automation_clear = sub.add_parser("clip-stock-automation-clear", help="Clear clip automation using a stock-device control alias.")
    add_registry_arg(stock_automation_clear)
    add_clip_ref_args(stock_automation_clear)
    add_clip_automation_device_args(stock_automation_clear)
    add_stock_root_arg(stock_automation_clear)
    stock_automation_clear.add_argument("--stock-device", help="Registry device name/path/slug. Defaults to --device when that is a name.")
    stock_automation_clear.add_argument("--control", help="Control name, slug, alias, or parameter index. Omit with --all.")
    stock_automation_clear.add_argument("--all", action="store_true", help="Clear every automation envelope in the clip.")

    clip_delete = sub.add_parser("clip-delete", help="Delete a clip by path, Session slot, or Arrangement index/start.")
    add_clip_ref_args(clip_delete)

    clip_copy = sub.add_parser("clip-copy", help="Copy a MIDI clip to an Arrangement time or Session slot.")
    add_clip_ref_args(clip_copy, "source")
    clip_copy.add_argument("--dest-track", type=track_value)
    clip_copy.add_argument("--dest-slot", type=int)
    clip_copy.add_argument("--dest-start", type=float)
    clip_copy.add_argument("--dest-end", type=float)
    clip_copy.add_argument("--dest-from-loop", action="store_true")
    clip_copy.add_argument("--length", type=float)
    clip_copy.add_argument("--replace", action="store_true")

    clip_move = sub.add_parser("clip-move", help="Move a MIDI clip by copying it to a target and deleting the source.")
    add_clip_ref_args(clip_move, "source")
    clip_move.add_argument("--dest-track", type=track_value)
    clip_move.add_argument("--dest-slot", type=int)
    clip_move.add_argument("--dest-start", type=float)
    clip_move.add_argument("--dest-end", type=float)
    clip_move.add_argument("--dest-from-loop", action="store_true")
    clip_move.add_argument("--length", type=float)
    clip_move.add_argument("--replace", action="store_true")

    clip_split = sub.add_parser("clip-split", help="Split an Arrangement MIDI clip at an Arrangement beat.")
    add_clip_ref_args(clip_split)
    clip_split.add_argument("--time", required=True, type=float)
    clip_split.add_argument("--relative", action="store_true", help="Treat --time as clip-relative instead of Arrangement time.")

    clip_slots = sub.add_parser("clip-slots", help="List clip slots for a track.")
    clip_slots.add_argument("--track", required=True, type=track_value)

    fire_clip = sub.add_parser("fire-clip", help="Fire a clip slot on a track.")
    fire_clip.add_argument("--track", required=True, type=track_value)
    fire_clip.add_argument("--slot", required=True, type=int)

    stop_track = sub.add_parser("stop-track-clips", help="Stop all clips on a track.")
    stop_track.add_argument("--track", required=True, type=track_value)
