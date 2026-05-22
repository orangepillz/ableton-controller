#!/usr/bin/env python3
"""CLI for the Codex_AI Ableton Live bridge."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 37337
DEFAULT_APP_NAME = "Ableton Live 12 Suite"


LOCAL_COMMANDS = {"hotkey", "key-sequence", "type-text", "menu-search", "save"}
MODIFIER_NAMES = {
    "cmd": "command down",
    "command": "command down",
    "meta": "command down",
    "option": "option down",
    "opt": "option down",
    "alt": "option down",
    "shift": "shift down",
    "control": "control down",
    "ctrl": "control down",
}
KEY_CODES = {
    "return": 36,
    "enter": 36,
    "tab": 48,
    "space": 49,
    "delete": 51,
    "backspace": 51,
    "escape": 53,
    "esc": 53,
    "left": 123,
    "right": 124,
    "down": 125,
    "up": 126,
    "home": 115,
    "end": 119,
    "pageup": 116,
    "pagedown": 121,
    "forwarddelete": 117,
    "f1": 122,
    "f2": 120,
    "f3": 99,
    "f4": 118,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f8": 100,
    "f9": 101,
    "f10": 109,
    "f11": 103,
    "f12": 111,
    "f13": 105,
    "f14": 107,
    "f15": 113,
    "f16": 106,
    "f17": 64,
    "f18": 79,
    "f19": 80,
    "f20": 90,
}


def send(payload: dict[str, Any], host: str, port: int, timeout: float) -> dict[str, Any]:
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(data)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
    except OSError as exc:
        raise SystemExit(
            f"Could not connect to Ableton bridge at {host}:{port}: {exc}\n"
            "Is the Codex_AI control surface loaded in Live?"
        )

    raw = b"".join(chunks).strip()
    if not raw:
        raise SystemExit("Ableton bridge returned an empty response.")
    try:
        response = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise SystemExit(f"Ableton bridge returned invalid JSON: {exc}: {raw!r}")
    if not response.get("ok", False):
        message = response.get("error") or response
        raise SystemExit(f"Ableton bridge error: {message}")
    return response


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=8.0)


def bool_arg(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false, yes/no, on/off, or 1/0")


def track_value(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def json_arg(value: str) -> Any:
    try:
        return json.loads(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("invalid JSON: %s" % exc)


def int_list_arg(value: str) -> list[int]:
    if value.strip().startswith("["):
        parsed = json_arg(value)
        if not isinstance(parsed, list):
            raise argparse.ArgumentTypeError("expected a JSON list of note IDs")
        return [int(item) for item in parsed]
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def float_list_arg(value: str) -> list[float]:
    if value.strip().startswith("["):
        parsed = json_arg(value)
        if not isinstance(parsed, list):
            raise argparse.ArgumentTypeError("expected a JSON list of times")
        return [float(item) for item in parsed]
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def warp_mode_value(value: str) -> int:
    modes = {
        "beats": 0,
        "beat": 0,
        "tones": 1,
        "tone": 1,
        "texture": 2,
        "textures": 2,
        "repitch": 3,
        "re-pitch": 3,
        "re_pitch": 3,
        "complex": 4,
        "rex": 5,
        "complexpro": 6,
        "complex-pro": 6,
        "complex_pro": 6,
        "complex pro": 6,
    }
    normalized = value.strip().lower()
    if normalized in modes:
        return modes[normalized]
    try:
        mode = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a warp mode name or index 0..6")
    if mode < 0 or mode > 6:
        raise argparse.ArgumentTypeError("warp mode index must be 0..6")
    return mode


def add_clip_ref_args(parser: argparse.ArgumentParser, prefix: str = "") -> None:
    flag = "--%s" if not prefix else "--%s-%%s" % prefix
    parser.add_argument(flag % "path")
    parser.add_argument(flag % "track", type=track_value)
    parser.add_argument(flag % "slot", type=int)
    parser.add_argument(flag % "arrangement-index", type=int)
    parser.add_argument(flag % "arrangement-start", type=float)


def add_device_ref_args(parser: argparse.ArgumentParser, prefix: str = "") -> None:
    flag = "--%s" if not prefix else "--%s-%%s" % prefix
    parser.add_argument(flag % "device-path", help="LOM path to a device, including devices inside racks.")
    parser.add_argument(flag % "track", type=track_value)
    parser.add_argument(flag % "device", type=track_value)


def add_clip_automation_device_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device-path", help="LOM path to a device, including devices inside racks.")
    parser.add_argument("--device-track", type=track_value, help="Track containing the device. Defaults to the clip track when possible.")
    parser.add_argument("--device", type=track_value, help="Device name/index on the clip track or --device-track.")


def add_container_ref_args(parser: argparse.ArgumentParser, prefix: str = "target") -> None:
    flag = "--%s-%%s" % prefix
    parser.add_argument(flag % "path", help="LOM path to a Track or Rack Chain.")
    parser.add_argument(flag % "track", type=track_value, help="Target track when no target path is supplied.")


def add_note_region_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=float, help="Clip beat where the note region starts.")
    parser.add_argument("--end", type=float, help="Clip beat where the note region ends.")
    parser.add_argument("--length", type=float, help="Length of the note region in beats.")
    parser.add_argument("--pitch-min", type=int)
    parser.add_argument("--pitch-max", type=int)


def add_clip_range_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=float, help="Arrangement beat where the clip starts.")
    parser.add_argument("--end", type=float, help="Arrangement beat where the clip ends.")
    parser.add_argument("--length", type=float, help="Clip length in beats.")
    parser.add_argument("--from-loop", action="store_true", help="Use Live's current Arrangement loop start/length.")


def add_app_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--app", default=DEFAULT_APP_NAME, help="macOS app name for local keyboard/menu commands.")
    parser.add_argument("--delay", type=float, default=0.08, help="Delay after activating Live, in seconds.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Ableton Live through Codex_AI.")
    add_common(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="Check bridge connectivity.")
    sub.add_parser("status", help="Show Live set status.")
    sub.add_parser("tracks", help="List tracks, returns, and master.")

    selected = sub.add_parser("selected", help="Show selected track.")
    selected.add_argument("--devices", action="store_true", help="Include selected track devices.")

    select_track = sub.add_parser("select-track", help="Select a track by index or name.")
    select_track.add_argument("--track", required=True, type=track_value)

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
    device_add.add_argument("--root", choices=("audio_effects", "midi_effects", "instruments"), help="Browser root to search when using --name.")
    device_add.add_argument("--target-index", type=int, help="Device-chain index to place the device at.")
    device_add.add_argument("--allow-presets", action="store_true", help="Allow loading non-device presets when resolving by browser path.")

    device_move = sub.add_parser("device-move", help="Move/reorder a device on a track or into a rack chain.")
    add_device_ref_args(device_move, "source")
    add_container_ref_args(device_move, "target")
    device_move.add_argument("--target-index", required=True, type=int)

    device_delete = sub.add_parser("device-delete", help="Delete a top-level or rack-chain device.")
    add_device_ref_args(device_delete)

    params = sub.add_parser("params", help="List parameters for a device.")
    add_device_ref_args(params)

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

    hotkey = sub.add_parser("hotkey", help="Send any keyboard shortcut to Ableton, e.g. cmd+s or shift+tab.")
    add_app_arg(hotkey)
    hotkey.add_argument("combo", help="Key combo using + separators, e.g. cmd+option+b, cmd+shift+r, f11, tab.")

    key_sequence = sub.add_parser("key-sequence", help="Send multiple key combos in order.")
    add_app_arg(key_sequence)
    key_sequence.add_argument("combos", nargs="+", help="One or more combos accepted by `hotkey`.")
    key_sequence.add_argument("--between", type=float, default=0.1, help="Delay between combos, in seconds.")

    type_text = sub.add_parser("type-text", help="Type text into Ableton's focused field.")
    add_app_arg(type_text)
    type_text.add_argument("text")

    menu_search = sub.add_parser("menu-search", help="Use macOS menu search to run a Live menu command by name.")
    add_app_arg(menu_search)
    menu_search.add_argument("query", help="Menu command to search, e.g. Export Audio/Video.")
    menu_search.add_argument("--search-delay", type=float, default=0.35, help="Delay after typing the menu query.")

    save = sub.add_parser("save", help="Save the current Live set via Cmd+S.")
    add_app_arg(save)

    lom_get = sub.add_parser("lom-get", help="Read a Live Object Model path.")
    lom_get.add_argument("path")

    lom_set = sub.add_parser("lom-set", help="Set a Live Object Model property.")
    lom_set.add_argument("path")
    lom_set.add_argument("value")
    lom_set.add_argument("--json", action="store_true", help="Parse value as JSON.")

    lom_call = sub.add_parser("lom-call", help="Call a Live Object Model method.")
    lom_call.add_argument("path")
    lom_call.add_argument("--args", default="[]", help="JSON array of positional arguments.")
    lom_call.add_argument("--kwargs", default="{}", help="JSON object of keyword arguments.")

    lom_inspect = sub.add_parser("lom-inspect", help="Inspect attributes and methods at a Live Object Model path.")
    lom_inspect.add_argument("path")

    show_view = sub.add_parser("show-view", help="Show a Live view, e.g. Browser, Session, Arranger, Detail/Clip.")
    show_view.add_argument("view")

    hide_view = sub.add_parser("hide-view", help="Hide a Live view.")
    hide_view.add_argument("view")

    focus_view = sub.add_parser("focus-view", help="Focus a Live view.")
    focus_view.add_argument("view")

    sub.add_parser("toggle-browse", help="Toggle Live browser browse mode.")

    sub.add_parser("browser-roots", help="List available browser roots.")

    browser_children = sub.add_parser("browser-children", help="List browser children by path, e.g. 'audio_effects/EQ Eight'.")
    browser_children.add_argument("item")

    browser_tree = sub.add_parser("browser-tree", help="Read a recursive Live browser tree.")
    browser_tree.add_argument("item", nargs="?", help="Optional root/path, e.g. instruments or 'audio_effects/EQ Eight'. Defaults to all roots.")
    browser_tree.add_argument("--depth", type=int, default=2, help="How many child levels to read.")
    browser_tree.add_argument("--max-items", type=int, default=500, help="Stop after this many browser items.")

    browser_search = sub.add_parser("browser-search", help="Search Live browser items by name/source/path/URI.")
    browser_search.add_argument("query")
    browser_search.add_argument("--item", help="Optional root/path to search under. Defaults to all roots.")
    browser_search.add_argument("--depth", type=int, default=6, help="How many child levels to search.")
    browser_search.add_argument("--max-results", type=int, default=100)
    browser_search.add_argument("--max-items", type=int, default=5000, help="Stop after scanning this many browser items.")

    browser_load = sub.add_parser("browser-load", help="Load a browser item into Live by path.")
    browser_load.add_argument("item")

    browser_preview = sub.add_parser("browser-preview", help="Preview a browser item by path.")
    browser_preview.add_argument("item")

    sub.add_parser("browser-stop-preview", help="Stop browser preview playback.")

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

    set_routing = sub.add_parser("set-routing", help="Set track input/output routing by displayed routing name.")
    set_routing.add_argument("--track", required=True, type=track_value)
    set_routing.add_argument("--direction", choices=("input", "output"), default="input")
    set_routing.add_argument("--type")
    set_routing.add_argument("--channel")

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

    automation_set = sub.add_parser("clip-automation-set", help="Create/update a clip automation envelope with step values.")
    add_clip_ref_args(automation_set)
    add_clip_automation_device_args(automation_set)
    automation_set.add_argument("--param", required=True, type=track_value)
    automation_set.add_argument("--steps", required=True, type=json_arg, help="JSON list of {time,duration,value|normalized} objects.")
    automation_set.add_argument("--clear", action="store_true", help="Clear this parameter's existing envelope before inserting steps.")

    automation_clear = sub.add_parser("clip-automation-clear", help="Clear a clip automation envelope for one parameter or all parameters.")
    add_clip_ref_args(automation_clear)
    add_clip_automation_device_args(automation_clear)
    automation_clear.add_argument("--param", type=track_value, help="Parameter to clear. Omit with --all.")
    automation_clear.add_argument("--all", action="store_true", help="Clear every automation envelope in the clip.")

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

    clip_slots = sub.add_parser("clip-slots", help="List clip slots for a track.")
    clip_slots.add_argument("--track", required=True, type=track_value)

    fire_clip = sub.add_parser("fire-clip", help="Fire a clip slot on a track.")
    fire_clip.add_argument("--track", required=True, type=track_value)
    fire_clip.add_argument("--slot", required=True, type=int)

    stop_track = sub.add_parser("stop-track-clips", help="Stop all clips on a track.")
    stop_track.add_argument("--track", required=True, type=track_value)

    raw = sub.add_parser("raw", help="Send a raw JSON request.")
    raw.add_argument("json_payload")

    return parser


def add_if_not_none(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value


def clip_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    names = ("path", "track", "slot", "arrangement_index", "arrangement_start")
    found = False
    for name in names:
        value = getattr(args, ("%s_%s" % (prefix, name)) if prefix else name, None)
        if value is not None:
            payload[("%s_%s" % (prefix, name)) if prefix else name] = value
            found = True
    if not found:
        label = "%s " % prefix if prefix else ""
        raise SystemExit("Command needs a %sclip reference: --path, --track/--slot, --track/--arrangement-index, or --track/--arrangement-start." % label)
    return payload


def device_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    names = ("device_path", "track", "device")
    found = False
    for name in names:
        arg_name = ("%s_%s" % (prefix, name)) if prefix else name
        value = getattr(args, arg_name, None)
        if value is not None:
            payload[arg_name] = value
            found = True
    if not found:
        label = "%s " % prefix if prefix else ""
        raise SystemExit("Command needs a %sdevice reference: --device-path or --track/--device." % label)
    return payload


def optional_device_ref_payload(args: argparse.Namespace, prefix: str = "") -> dict[str, Any]:
    try:
        return device_ref_payload(args, prefix)
    except SystemExit:
        return {}


def clip_automation_device_ref_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if getattr(args, "device_path", None) is not None:
        payload["device_path"] = args.device_path
    if getattr(args, "device_track", None) is not None:
        payload["track"] = args.device_track
    elif getattr(args, "track", None) is not None:
        payload["track"] = args.track
    if getattr(args, "device", None) is not None:
        payload["device"] = args.device
    if "device_path" not in payload and "device" not in payload:
        raise SystemExit("Command needs --device-path or --device.")
    return payload


def container_ref_payload(args: argparse.Namespace, prefix: str = "target") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("path", "track"):
        arg_name = "%s_%s" % (prefix, name)
        value = getattr(args, arg_name, None)
        if value is not None:
            payload[arg_name] = value
    if not payload:
        raise SystemExit("Command needs a %s container reference: --%s-path or --%s-track." % (prefix, prefix, prefix))
    return payload


def note_region_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("start", "end", "length", "pitch_min", "pitch_max"):
        add_if_not_none(payload, name, getattr(args, name, None))
    return payload


def clip_range_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in ("start", "end", "length"):
        add_if_not_none(payload, name, getattr(args, name, None))
    if getattr(args, "from_loop", False):
        payload["from_loop"] = True
    return payload


def command_payload(args: argparse.Namespace) -> dict[str, Any]:
    command = args.command
    if command == "ping":
        return {"command": "ping"}
    if command == "status":
        return {"command": "status"}
    if command == "tracks":
        return {"command": "tracks"}
    if command == "selected":
        return {"command": "selected", "devices": args.devices}
    if command == "select-track":
        return {"command": "select_track", "track": args.track}
    if command == "devices":
        return {"command": "devices", "track": args.track}
    if command == "device-tree":
        return {"command": "device_tree", "track": args.track, "depth": args.depth}
    if command == "device-add-stock":
        payload = {"command": "device_add_stock", **container_ref_payload(args, "target")}
        add_if_not_none(payload, "path", args.path)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "root", args.root)
        add_if_not_none(payload, "target_index", args.target_index)
        if args.allow_presets:
            payload["allow_presets"] = True
        return payload
    if command == "device-move":
        return {
            "command": "device_move",
            **device_ref_payload(args, "source"),
            **container_ref_payload(args, "target"),
            "target_index": args.target_index,
        }
    if command == "device-delete":
        return {"command": "device_delete", **device_ref_payload(args)}
    if command == "params":
        return {"command": "params", **device_ref_payload(args)}
    if command == "set-track":
        fields = {
            key: getattr(args, key)
            for key in ("volume", "pan", "mute", "solo", "arm")
            if getattr(args, key) is not None
        }
        if not fields:
            raise SystemExit("set-track needs at least one of --volume, --pan, --mute, --solo, --arm.")
        return {"command": "set_track", "track": args.track, **fields}
    if command == "set-send":
        return {"command": "set_send", "track": args.track, "send": args.send, "value": args.value}
    if command == "set-param":
        payload = {
            "command": "set_param",
            **device_ref_payload(args),
            "param": args.param,
        }
        if args.value is not None:
            payload["value"] = args.value
        elif args.normalized is not None:
            payload["normalized"] = args.normalized
        else:
            payload["delta"] = args.delta
        return payload
    if command == "tempo":
        payload = {"command": "tempo"}
        if args.set is not None:
            payload["value"] = args.set
        return payload
    if command in {"play", "stop", "continue", "undo", "redo"}:
        return {"command": command}
    if command == "lom-get":
        return {"command": "lom_get", "path": args.path}
    if command == "lom-set":
        if args.json:
            try:
                value = json.loads(args.value)
            except ValueError as exc:
                raise SystemExit(f"Invalid JSON value: {exc}")
        else:
            value = scalar_value(args.value)
        return {"command": "lom_set", "path": args.path, "value": value}
    if command == "lom-call":
        try:
            call_args = json.loads(args.args)
            call_kwargs = json.loads(args.kwargs)
        except ValueError as exc:
            raise SystemExit(f"Invalid call JSON: {exc}")
        return {"command": "lom_call", "path": args.path, "args": call_args, "kwargs": call_kwargs}
    if command == "lom-inspect":
        return {"command": "lom_inspect", "path": args.path}
    if command in {"show-view", "hide-view", "focus-view"}:
        return {"command": "view", "action": command.split("-", 1)[0], "view": args.view}
    if command == "toggle-browse":
        return {"command": "view", "action": "toggle-browse"}
    if command == "browser-roots":
        return {"command": "browser_roots"}
    if command == "browser-children":
        return {"command": "browser_children", "item": args.item}
    if command == "browser-tree":
        payload = {"command": "browser_tree", "depth": args.depth, "max_items": args.max_items}
        if args.item:
            payload["item"] = args.item
        return payload
    if command == "browser-search":
        payload = {
            "command": "browser_search",
            "query": args.query,
            "depth": args.depth,
            "max_results": args.max_results,
            "max_items": args.max_items,
        }
        if args.item:
            payload["item"] = args.item
        return payload
    if command == "browser-load":
        return {"command": "browser_load", "item": args.item}
    if command == "browser-preview":
        return {"command": "browser_preview", "item": args.item}
    if command == "browser-stop-preview":
        return {"command": "browser_stop_preview"}
    if command == "create-track":
        payload = {"command": "create_track", "type": args.type}
        if args.index is not None:
            payload["index"] = args.index
        if args.name:
            payload["name"] = args.name
        return payload
    if command == "delete-track":
        return {"command": "delete_track", "track": args.track}
    if command == "duplicate-track":
        return {"command": "duplicate_track", "track": args.track}
    if command == "create-scene":
        payload = {"command": "create_scene"}
        if args.index is not None:
            payload["index"] = args.index
        if args.name:
            payload["name"] = args.name
        return payload
    if command == "delete-scene":
        return {"command": "delete_scene", "scene": args.scene}
    if command == "duplicate-scene":
        return {"command": "duplicate_scene", "scene": args.scene}
    if command == "fire-scene":
        return {"command": "fire_scene", "scene": args.scene}
    if command == "set-routing":
        if args.type is None and args.channel is None:
            raise SystemExit("set-routing needs --type, --channel, or both.")
        payload = {"command": "set_routing", "track": args.track, "direction": args.direction}
        if args.type is not None:
            payload["type"] = args.type
        if args.channel is not None:
            payload["channel"] = args.channel
        return payload
    if command == "clips":
        return {"command": "clips", "track": args.track}
    if command == "clip-create-midi":
        payload = {"command": "clip_create_midi", "track": args.track, **clip_range_payload(args)}
        add_if_not_none(payload, "slot", args.slot)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "color", args.color)
        add_if_not_none(payload, "color_index", args.color_index)
        if args.replace:
            payload["replace"] = True
        if "slot" not in payload and not any(key in payload for key in ("start", "end", "length", "from_loop")):
            raise SystemExit("Arrangement clip-create-midi needs --start/--length, --start/--end, or --from-loop.")
        if "slot" in payload and not any(key in payload for key in ("end", "length", "from_loop")):
            raise SystemExit("Session clip-create-midi needs --length or --from-loop.")
        return payload
    if command == "clip-create-audio":
        payload = {"command": "clip_create_audio", "track": args.track, "file": args.file, **clip_range_payload(args)}
        add_if_not_none(payload, "slot", args.slot)
        add_if_not_none(payload, "name", args.name)
        add_if_not_none(payload, "color", args.color)
        add_if_not_none(payload, "color_index", args.color_index)
        add_if_not_none(payload, "warping", args.warping)
        add_if_not_none(payload, "warp_mode", args.warp_mode)
        if args.replace:
            payload["replace"] = True
        if "slot" not in payload and "start" not in payload and not payload.get("from_loop", False):
            raise SystemExit("Arrangement clip-create-audio needs --start or --from-loop.")
        return payload
    if command == "clip-set":
        payload = {"command": "clip_set", **clip_ref_payload(args)}
        for name in (
            "name",
            "color",
            "color_index",
            "muted",
            "looping",
            "loop_start",
            "loop_end",
            "start_marker",
            "end_marker",
            "position",
            "launch_mode",
            "launch_quantization",
            "legato",
            "velocity_amount",
            "signature_numerator",
            "signature_denominator",
            "gain",
            "pitch_coarse",
            "pitch_fine",
            "ram_mode",
            "warping",
            "warp_mode",
        ):
            add_if_not_none(payload, name, getattr(args, name))
        if len(payload) == 1 + len(clip_ref_payload(args)):
            raise SystemExit("clip-set needs at least one property to set.")
        return payload
    if command == "clip-warp":
        payload = {"command": "clip_warp", **clip_ref_payload(args)}
        for name in ("warping", "warp_mode", "gain", "pitch_coarse", "pitch_fine", "ram_mode"):
            add_if_not_none(payload, name, getattr(args, name))
        return payload
    if command == "clip-warp-marker-add":
        payload = {"command": "clip_warp_marker_add", **clip_ref_payload(args), "beat_time": args.beat_time}
        add_if_not_none(payload, "sample_time", args.sample_time)
        return payload
    if command == "clip-warp-marker-move":
        payload = {"command": "clip_warp_marker_move", **clip_ref_payload(args), "beat_time": args.beat_time}
        if args.to_beat is not None:
            payload["to_beat"] = args.to_beat
        else:
            payload["distance"] = args.distance
        return payload
    if command == "clip-warp-marker-remove":
        return {"command": "clip_warp_marker_remove", **clip_ref_payload(args), "beat_time": args.beat_time}
    if command == "clip-automation-get":
        payload = {
            "command": "clip_automation_get",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": args.param,
        }
        add_if_not_none(payload, "times", args.times)
        return payload
    if command == "clip-automation-set":
        if not isinstance(args.steps, list):
            raise SystemExit("clip-automation-set --steps must be a JSON list.")
        return {
            "command": "clip_automation_set",
            **clip_ref_payload(args),
            **clip_automation_device_ref_payload(args),
            "param": args.param,
            "steps": args.steps,
            "clear": args.clear,
        }
    if command == "clip-automation-clear":
        payload = {"command": "clip_automation_clear", **clip_ref_payload(args)}
        if args.all:
            payload["all"] = True
        else:
            if args.param is None:
                raise SystemExit("clip-automation-clear needs --param or --all.")
            payload.update(clip_automation_device_ref_payload(args))
            payload["param"] = args.param
        return payload
    if command == "clip-delete":
        return {"command": "clip_delete", **clip_ref_payload(args)}
    if command in {"clip-copy", "clip-move"}:
        payload = {
            "command": "clip_copy" if command == "clip-copy" else "clip_move",
            **clip_ref_payload(args, "source"),
        }
        add_if_not_none(payload, "dest_track", args.dest_track)
        add_if_not_none(payload, "dest_slot", args.dest_slot)
        add_if_not_none(payload, "dest_start", args.dest_start)
        add_if_not_none(payload, "dest_end", args.dest_end)
        add_if_not_none(payload, "length", args.length)
        if args.dest_from_loop:
            payload["dest_from_loop"] = True
        if args.replace:
            payload["replace"] = True
        if args.dest_slot is None and args.dest_start is None and args.dest_end is None and not args.dest_from_loop:
            raise SystemExit("%s needs --dest-slot, --dest-start/--dest-end, or --dest-from-loop." % command)
        return payload
    if command == "clip-split":
        return {"command": "clip_split", **clip_ref_payload(args), "time": args.time, "relative": args.relative}
    if command == "midi-get-notes":
        if not args.path and args.track is None:
            raise SystemExit("midi-get-notes needs --path or --track.")
        payload = {"command": "midi_get_notes", "slot": args.slot, **note_region_payload(args)}
        if args.path:
            payload["path"] = args.path
        if args.track is not None:
            payload["track"] = args.track
        add_if_not_none(payload, "arrangement_index", args.arrangement_index)
        add_if_not_none(payload, "arrangement_start", args.arrangement_start)
        return payload
    if command == "midi-add-notes":
        if not args.path and args.track is None:
            raise SystemExit("midi-add-notes needs --path or --track.")
        try:
            notes = json.loads(args.notes)
        except ValueError as exc:
            raise SystemExit(f"Invalid notes JSON: {exc}")
        payload = {"command": "midi_add_notes", "slot": args.slot, "notes": notes}
        if args.path:
            payload["path"] = args.path
        if args.track is not None:
            payload["track"] = args.track
        add_if_not_none(payload, "arrangement_index", args.arrangement_index)
        add_if_not_none(payload, "arrangement_start", args.arrangement_start)
        return payload
    if command == "midi-replace-notes":
        return {"command": "midi_replace_notes", **clip_ref_payload(args), "notes": args.notes}
    if command == "midi-update-notes":
        return {"command": "midi_update_notes", **clip_ref_payload(args), "notes": args.notes}
    if command == "midi-remove-notes":
        payload = {"command": "midi_remove_notes", **clip_ref_payload(args), **note_region_payload(args)}
        add_if_not_none(payload, "note_ids", args.note_ids)
        if "note_ids" not in payload and not any(key in payload for key in ("start", "end", "length", "pitch_min", "pitch_max")):
            raise SystemExit("midi-remove-notes needs --note-ids or a region/pitch filter.")
        return payload
    if command == "midi-clear-notes":
        return {"command": "midi_clear_notes", **clip_ref_payload(args), **note_region_payload(args)}
    if command == "midi-transform-notes":
        payload = {"command": "midi_transform_notes", **clip_ref_payload(args), **note_region_payload(args)}
        for name in (
            "transpose",
            "time_delta",
            "duration_scale",
            "duration_delta",
            "velocity_scale",
            "velocity_delta",
            "probability",
            "velocity_deviation",
            "release_velocity",
            "mute",
        ):
            add_if_not_none(payload, name, getattr(args, name))
        if not any(key in payload for key in ("transpose", "time_delta", "duration_scale", "duration_delta", "velocity_scale", "velocity_delta", "probability", "velocity_deviation", "release_velocity", "mute")):
            raise SystemExit("midi-transform-notes needs at least one transform option.")
        return payload
    if command == "midi-duplicate-region":
        payload = {
            "command": "midi_duplicate_region",
            **clip_ref_payload(args),
            "start": args.start,
            "destination_time": args.destination_time,
            "pitch": args.pitch,
            "transpose": args.transpose,
        }
        add_if_not_none(payload, "end", args.end)
        add_if_not_none(payload, "length", args.length)
        return payload
    if command == "clip-slots":
        return {"command": "clip_slots", "track": args.track}
    if command == "fire-clip":
        return {"command": "fire_clip", "track": args.track, "slot": args.slot}
    if command == "stop-track-clips":
        return {"command": "stop_track_clips", "track": args.track}
    if command == "raw":
        try:
            payload = json.loads(args.json_payload)
        except ValueError as exc:
            raise SystemExit(f"Invalid JSON payload: {exc}")
        if not isinstance(payload, dict):
            raise SystemExit("Raw payload must be a JSON object.")
        return payload
    raise SystemExit(f"Unknown command: {command}")


def run_local_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "save":
        run_hotkey(args.app, "cmd+s", args.delay)
        return {"command": "save", "app": args.app, "hotkey": "cmd+s", "done": True}
    if args.command == "hotkey":
        run_hotkey(args.app, args.combo, args.delay)
        return {"command": "hotkey", "app": args.app, "combo": args.combo, "done": True}
    if args.command == "key-sequence":
        for index, combo in enumerate(args.combos):
            run_hotkey(args.app, combo, args.delay if index == 0 else 0.0)
            if index < len(args.combos) - 1:
                time.sleep(max(0.0, args.between))
        return {"command": "key-sequence", "app": args.app, "combos": args.combos, "done": True}
    if args.command == "type-text":
        run_applescript(
            [
                'tell application %s to activate' % applescript_string(args.app),
                "delay %.3f" % max(0.0, args.delay),
                "tell application \"System Events\"",
                "  keystroke %s" % applescript_string(args.text),
                "end tell",
            ]
        )
        return {"command": "type-text", "app": args.app, "characters": len(args.text), "done": True}
    if args.command == "menu-search":
        run_menu_search(args.app, args.query, args.delay, args.search_delay)
        return {"command": "menu-search", "app": args.app, "query": args.query, "done": True}
    raise SystemExit(f"Unknown local command: {args.command}")


def run_hotkey(app: str, combo: str, activation_delay: float) -> None:
    action = applescript_key_action(combo)
    run_applescript(
        [
            'tell application %s to activate' % applescript_string(app),
            "delay %.3f" % max(0.0, activation_delay),
            "tell application \"System Events\"",
            "  %s" % action,
            "end tell",
        ]
    )


def run_menu_search(app: str, query: str, activation_delay: float, search_delay: float) -> None:
    run_applescript(
        [
            'tell application %s to activate' % applescript_string(app),
            "delay %.3f" % max(0.0, activation_delay),
            "tell application \"System Events\"",
            "  keystroke \"/\" using {command down, shift down}",
            "  delay 0.150",
            "  keystroke %s" % applescript_string(query),
            "  delay %.3f" % max(0.0, search_delay),
            "  key code 125",
            "  delay 0.050",
            "  key code 36",
            "end tell",
        ]
    )


def applescript_key_action(combo: str) -> str:
    key, modifiers = parse_combo(combo)
    suffix = ""
    if modifiers:
        suffix = " using {%s}" % ", ".join(modifiers)
    key_name = key.lower()
    if key_name in KEY_CODES:
        return "key code %d%s" % (KEY_CODES[key_name], suffix)
    if len(key) == 1:
        return "keystroke %s%s" % (applescript_string(key), suffix)
    raise SystemExit("Unknown key %r. Use a single character, a function key, arrows, tab, return, escape, space, delete, home/end, or pageup/pagedown." % key)


def parse_combo(combo: str) -> tuple[str, list[str]]:
    parts = [part.strip().lower() for part in combo.split("+") if part.strip()]
    if not parts:
        raise SystemExit("Empty key combo.")
    key = parts[-1]
    modifiers = []
    for part in parts[:-1]:
        modifier = MODIFIER_NAMES.get(part)
        if modifier is None:
            raise SystemExit("Unknown modifier %r in combo %r." % (part, combo))
        if modifier not in modifiers:
            modifiers.append(modifier)
    return key, modifiers


def applescript_string(value: str) -> str:
    return json.dumps(value)


def run_applescript(lines: list[str]) -> None:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown osascript failure"
        raise SystemExit(
            "macOS keyboard/menu automation failed: %s\n"
            "Grant Accessibility permission to the terminal/Codex app if macOS blocks System Events." % detail
        )


def scalar_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in LOCAL_COMMANDS:
        print_json(run_local_command(args))
        return 0
    payload = command_payload(args)
    response = send(payload, args.host, args.port, args.timeout)
    print_json(response.get("result", response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
