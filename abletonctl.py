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

    params = sub.add_parser("params", help="List parameters for a device.")
    params.add_argument("--track", required=True, type=track_value)
    params.add_argument("--device", required=True, type=track_value)

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
    set_param.add_argument("--track", required=True, type=track_value)
    set_param.add_argument("--device", required=True, type=track_value)
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

    midi_get = sub.add_parser("midi-get-notes", help="Read notes from a MIDI clip by track/slot or LOM clip path.")
    midi_get.add_argument("--path")
    midi_get.add_argument("--track", type=track_value)
    midi_get.add_argument("--slot", type=int, default=0)

    midi_add = sub.add_parser("midi-add-notes", help="Add notes to a MIDI clip from a JSON list.")
    midi_add.add_argument("--path")
    midi_add.add_argument("--track", type=track_value)
    midi_add.add_argument("--slot", type=int, default=0)
    midi_add.add_argument("--notes", required=True, help="JSON list of note objects with pitch/start_time/duration/velocity.")

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
    if command == "params":
        return {"command": "params", "track": args.track, "device": args.device}
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
            "track": args.track,
            "device": args.device,
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
    if command == "midi-get-notes":
        if not args.path and args.track is None:
            raise SystemExit("midi-get-notes needs --path or --track.")
        payload = {"command": "midi_get_notes", "slot": args.slot}
        if args.path:
            payload["path"] = args.path
        if args.track is not None:
            payload["track"] = args.track
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
