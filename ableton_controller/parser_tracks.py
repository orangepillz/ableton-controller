"""Parser setup for track_scene commands."""

from .arg_types import track_value

def add_track_scene_commands(sub):
    create_track = sub.add_parser("create-track", help="Create an audio, MIDI, or return track.")
    create_track.add_argument("--type", choices=("audio", "midi", "return"), default="midi")
    create_track.add_argument("--index", type=int)
    create_track.add_argument("--name")

    delete_track = sub.add_parser("delete-track", help="Delete a track by index or name.")
    delete_track.add_argument("--track", required=True, type=track_value)

    duplicate_track = sub.add_parser("duplicate-track", help="Duplicate a regular track by index or name.")
    duplicate_track.add_argument("--track", required=True, type=track_value)

    create_scene = sub.add_parser("create-scene", help="Create a scene.")
    create_scene.add_argument("--index", type=int)
    create_scene.add_argument("--name")

    delete_scene = sub.add_parser("delete-scene", help="Delete a scene by index.")
    delete_scene.add_argument("--scene", required=True, type=int)

    duplicate_scene = sub.add_parser("duplicate-scene", help="Duplicate a scene by index.")
    duplicate_scene.add_argument("--scene", required=True, type=int)

    fire_scene = sub.add_parser("fire-scene", help="Fire a scene by index or name.")
    fire_scene.add_argument("--scene", required=True, type=track_value)

    sub.add_parser("locators", help="List Arrangement locators/cue points.")

    set_locator = sub.add_parser("set-locator", help="Rename an Arrangement locator by index, name, or beat time.")
    locator_target = set_locator.add_mutually_exclusive_group(required=True)
    locator_target.add_argument("--locator", type=track_value, help="Locator index or current name.")
    locator_target.add_argument("--time", type=float, help="Locator beat time.")
    set_locator.add_argument("--name", required=True, help="New locator name.")

    set_routing = sub.add_parser("set-routing", help="Set track input/output routing by displayed routing name.")
    set_routing.add_argument("--track", required=True, type=track_value)
    set_routing.add_argument("--direction", choices=("input", "output"), default="input")
    set_routing.add_argument("--type")
    set_routing.add_argument("--channel")
