"""Aggregate read-only Ableton session probes for planning."""

from __future__ import annotations

import argparse
from typing import Any, Callable


BridgeSender = Callable[[dict[str, Any]], dict[str, Any]]


def _targets(args: argparse.Namespace) -> list[Any]:
    targets: list[Any] = ["selected"]
    for track in args.tracks or []:
        key = repr(track)
        if all(repr(existing) != key for existing in targets):
            targets.append(track)
    return targets


def _probe(
    snapshot: dict[str, Any],
    sender: BridgeSender,
    *,
    name: str,
    payload: dict[str, Any],
    required: bool,
) -> dict[str, Any] | None:
    try:
        return sender(payload)
    except SystemExit as exc:
        if required:
            raise
        snapshot["errors"].append({"probe": name, "payload": payload, "error": str(exc)})
        return None


def collect_session_snapshot(args: argparse.Namespace, sender: BridgeSender) -> dict[str, Any]:
    """Collect the standard context probes used before creative edits."""
    snapshot: dict[str, Any] = {
        "command": "session-snapshot",
        "probes": {},
        "targets": [],
        "errors": [],
    }
    snapshot["probes"]["status"] = _probe(snapshot, sender, name="status", payload={"command": "status"}, required=True)
    snapshot["probes"]["tracks"] = _probe(snapshot, sender, name="tracks", payload={"command": "tracks"}, required=True)
    snapshot["probes"]["selected"] = _probe(
        snapshot,
        sender,
        name="selected",
        payload={"command": "selected", "devices": args.selected_devices},
        required=True,
    )

    for track in _targets(args):
        target: dict[str, Any] = {"track": track}
        if args.target_devices:
            devices = _probe(
                snapshot,
                sender,
                name="devices",
                payload={"command": "devices", "track": track},
                required=False,
            )
            if devices is not None:
                target["devices"] = devices
        if args.include_clips:
            clips = _probe(
                snapshot,
                sender,
                name="clips",
                payload={"command": "clips", "track": track},
                required=False,
            )
            if clips is not None:
                target["clips"] = clips
        if args.device_tree_depth > 0:
            tree = _probe(
                snapshot,
                sender,
                name="device-tree",
                payload={"command": "device_tree", "track": track, "depth": args.device_tree_depth},
                required=False,
            )
            if tree is not None:
                target["device_tree"] = tree
        if len(target) > 1:
            snapshot["targets"].append(target)
    return snapshot

