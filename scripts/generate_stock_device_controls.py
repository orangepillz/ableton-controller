#!/usr/bin/env python3
"""Generate explicit stock Ableton device controls from the live browser."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abletonctl import DEFAULT_HOST, DEFAULT_PORT, send  # noqa: E402
from stock_device_controls import DEFAULT_REGISTRY_PATH, slugify  # noqa: E402
from stock_device_generator_lib import build_controls, detect_live_version, track_kind  # noqa: E402


ROOTS = ("instruments", "audio_effects", "midi_effects", "max_for_live")
TEMP_AUDIO_TRACK = "__Codex Stock Controls Audio__"
TEMP_MIDI_TRACK = "__Codex Stock Controls MIDI__"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--root", choices=ROOTS, action="append", help="Limit to one or more browser roots.")
    parser.add_argument("--device", help="Limit generation to devices whose browser path/name contains this text.")
    parser.add_argument("--limit", type=int, help="Only process the first N matching devices.")
    parser.add_argument("--browser-depth", type=int, default=8)
    parser.add_argument("--max-items", type=int, default=10000)
    parser.add_argument("--allow-failures", action="store_true", help="Write a registry even if some devices fail to load.")
    parser.add_argument("--keep-temp-tracks", action="store_true", help="Leave generated temp tracks in the Live set for debugging.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots = tuple(args.root or ROOTS)
    ping = request(args, {"command": "ping"})
    inventory = collect_inventory(args, roots)
    if args.device:
        needle = args.device.lower()
        inventory = [
            device
            for device in inventory
            if needle in device["name"].lower() or needle in device["path"].lower()
        ]
    if args.limit is not None:
        inventory = inventory[: max(0, args.limit)]

    print("Found %d built-in stock devices to inspect." % len(inventory), file=sys.stderr)
    devices: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    tracks: dict[str, str] = {}

    try:
        tracks = ensure_temp_tracks(args, inventory)
        for index, browser_device in enumerate(inventory, 1):
            print("[%d/%d] %s" % (index, len(inventory), browser_device["path"]), file=sys.stderr)
            try:
                devices.append(inspect_stock_device(args, browser_device, tracks))
            except Exception as exc:
                failures.append({"path": browser_device["path"], "name": browser_device["name"], "error": str(exc)})
                print("  failed: %s" % exc, file=sys.stderr)
                cleanup_temp_devices(args, tracks.get(track_kind(browser_device["root"])))
                if not args.allow_failures:
                    raise
    finally:
        if not args.keep_temp_tracks:
            cleanup_temp_tracks(args, tracks.values())

    registry = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/generate_stock_device_controls.py",
        "bridge": ping,
        "live_version": detect_live_version(),
        "source": "Ableton Live browser Built-in device items",
        "roots": list(roots),
        "device_count": len(devices),
        "parameter_count": sum(len(device.get("controls", [])) for device in devices),
        "devices": devices,
        "failures": failures,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(registry, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(
        "Wrote %d devices / %d controls to %s"
        % (registry["device_count"], registry["parameter_count"], args.output),
        file=sys.stderr,
    )
    if failures:
        print("%d devices failed; see registry failures." % len(failures), file=sys.stderr)
        return 1
    return 0


def request(args: argparse.Namespace, payload: dict[str, Any]) -> Any:
    response = send(payload, args.host, args.port, args.timeout)
    return response.get("result", response)


def collect_inventory(args: argparse.Namespace, roots: tuple[str, ...]) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    seen_paths = set()
    for root in roots:
        tree = request(
            args,
            {
                "command": "browser_tree",
                "item": root,
                "depth": args.browser_depth,
                "max_items": args.max_items,
            },
        )
        for node in walk_browser_nodes(tree.get("roots", [])):
            item = node.get("item", {})
            if not (item.get("is_device") and item.get("is_loadable") and item.get("source") == "Built-in"):
                continue
            path = node.get("path")
            if not path or path in seen_paths:
                continue
            seen_paths.add(path)
            devices.append(
                {
                    "root": root,
                    "name": item.get("name"),
                    "path": path,
                    "uri": item.get("uri"),
                    "source": item.get("source"),
                    "children_count": item.get("children_count"),
                }
            )
    devices.sort(key=lambda device: (device["root"], device["name"].lower(), device["path"].lower()))
    return devices


def walk_browser_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    stack = list(reversed(nodes))
    while stack:
        node = stack.pop()
        found.append(node)
        for child in reversed(node.get("children", [])):
            stack.append(child)
    return found


def ensure_temp_tracks(args: argparse.Namespace, inventory: list[dict[str, Any]]) -> dict[str, str]:
    needed = {track_kind(device) for device in inventory}
    tracks: dict[str, str] = {}
    if "audio" in needed:
        delete_tracks_named(args, TEMP_AUDIO_TRACK)
        request(args, {"command": "create_track", "type": "audio", "name": TEMP_AUDIO_TRACK})
        tracks["audio"] = TEMP_AUDIO_TRACK
    if "midi" in needed:
        delete_tracks_named(args, TEMP_MIDI_TRACK)
        request(args, {"command": "create_track", "type": "midi", "name": TEMP_MIDI_TRACK})
        tracks["midi"] = TEMP_MIDI_TRACK
    return tracks


def delete_tracks_named(args: argparse.Namespace, name: str) -> None:
    while True:
        status = request(args, {"command": "status"})
        matches = [
            track["index"]
            for track in status.get("tracks", [])
            if track.get("kind") == "track" and track.get("name") == name
        ]
        if not matches:
            return
        for index in reversed(matches):
            request(args, {"command": "delete_track", "track": int(index)})


def cleanup_temp_tracks(args: argparse.Namespace, names: Any) -> None:
    for name in list(names):
        if name:
            try:
                delete_tracks_named(args, str(name))
            except Exception as exc:
                print("Could not delete temp track %s: %s" % (name, exc), file=sys.stderr)


def cleanup_temp_devices(args: argparse.Namespace, track: str | None) -> None:
    if not track:
        return
    try:
        devices = request(args, {"command": "devices", "track": track}).get("devices", [])
        for device in reversed(devices):
            request(args, {"command": "device_delete", "track": track, "device": int(device["index"])})
    except Exception as exc:
        print("Could not clean devices on %s: %s" % (track, exc), file=sys.stderr)


def inspect_stock_device(
    args: argparse.Namespace,
    browser_device: dict[str, Any],
    tracks: dict[str, str],
) -> dict[str, Any]:
    track = tracks[track_kind(browser_device)]
    cleanup_temp_devices(args, track)
    request(
        args,
        {
            "command": "device_add_stock",
            "target_track": track,
            "path": browser_device["path"],
            "target_index": 0,
        },
    )
    params = request(args, {"command": "params", "track": track, "device": 0})
    device_info = params.get("device", {})
    controls = build_controls(params.get("parameters", []))
    cleanup_temp_devices(args, track)
    slug = slugify(browser_device["name"])
    return {
        "id": "%s/%s" % (browser_device["root"], slug),
        "root": browser_device["root"],
        "name": browser_device["name"],
        "slug": slug,
        "path": browser_device["path"],
        "uri": browser_device.get("uri"),
        "source": browser_device.get("source"),
        "loaded_name": device_info.get("name"),
        "class_name": device_info.get("class_name"),
        "can_have_chains": device_info.get("can_have_chains"),
        "parameter_count": len(controls),
        "controls": controls,
    }


if __name__ == "__main__":
    raise SystemExit(main())
