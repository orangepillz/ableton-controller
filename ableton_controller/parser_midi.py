"""Parser setup for midi commands."""

from .arg_types import bool_arg, int_list_arg, json_arg, track_value
from .parser_args import add_clip_ref_args, add_note_region_args

def add_midi_commands(sub):
    midi_get = sub.add_parser("midi-get-notes", help="Read notes from a MIDI clip by track/slot or LOM clip path.")
    midi_get.add_argument("--path")
    midi_get.add_argument("--track", type=track_value)
    midi_get.add_argument("--slot", type=int, default=0)
    midi_get.add_argument("--arrangement-index", type=int)
    midi_get.add_argument("--arrangement-start", type=float)
    add_note_region_args(midi_get)

    midi_add = sub.add_parser("midi-add-notes", help="Add notes to a MIDI clip from a JSON list.")
    midi_add.add_argument("--path")
    midi_add.add_argument("--track", type=track_value)
    midi_add.add_argument("--slot", type=int, default=0)
    midi_add.add_argument("--arrangement-index", type=int)
    midi_add.add_argument("--arrangement-start", type=float)
    midi_add.add_argument("--notes", required=True, help="JSON list of note objects with pitch/start_time/duration/velocity.")

    midi_replace = sub.add_parser("midi-replace-notes", help="Replace all notes in a MIDI clip with a JSON note list.")
    add_clip_ref_args(midi_replace)
    midi_replace.add_argument("--notes", required=True, type=json_arg)

    midi_update = sub.add_parser("midi-update-notes", help="Update existing notes by note_id with a JSON list of partial note objects.")
    add_clip_ref_args(midi_update)
    midi_update.add_argument("--notes", required=True, type=json_arg)

    midi_remove = sub.add_parser("midi-remove-notes", help="Remove notes by note IDs or by a pitch/time region.")
    add_clip_ref_args(midi_remove)
    midi_remove.add_argument("--note-ids", type=int_list_arg)
    add_note_region_args(midi_remove)

    midi_clear = sub.add_parser("midi-clear-notes", help="Remove all notes, or only notes in a pitch/time region.")
    add_clip_ref_args(midi_clear)
    add_note_region_args(midi_clear)

    midi_transform = sub.add_parser("midi-transform-notes", help="Transform notes in-place by region: transpose, move, resize, velocity, probability, mute.")
    add_clip_ref_args(midi_transform)
    add_note_region_args(midi_transform)
    midi_transform.add_argument("--transpose", type=int)
    midi_transform.add_argument("--time-delta", type=float)
    midi_transform.add_argument("--duration-scale", type=float)
    midi_transform.add_argument("--duration-delta", type=float)
    midi_transform.add_argument("--velocity-scale", type=float)
    midi_transform.add_argument("--velocity-delta", type=float)
    midi_transform.add_argument("--probability", type=float)
    midi_transform.add_argument("--velocity-deviation", type=float)
    midi_transform.add_argument("--release-velocity", type=float)
    midi_transform.add_argument("--mute", type=bool_arg)

    midi_duplicate = sub.add_parser("midi-duplicate-region", help="Duplicate MIDI notes in a clip region to another clip time.")
    add_clip_ref_args(midi_duplicate)
    midi_duplicate.add_argument("--start", required=True, type=float)
    region_end = midi_duplicate.add_mutually_exclusive_group(required=True)
    region_end.add_argument("--end", type=float)
    region_end.add_argument("--length", type=float)
    midi_duplicate.add_argument("--destination-time", required=True, type=float)
    midi_duplicate.add_argument("--pitch", type=int, default=-1)
    midi_duplicate.add_argument("--transpose", type=int, default=0)
