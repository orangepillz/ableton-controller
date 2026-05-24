"""Device-chain feature extraction from Ableton project XML."""

from __future__ import annotations

import re
from collections import Counter
from typing import Callable
from xml.etree.ElementTree import Element


DEVICE_TAGS = (
    "Operator",
    "DrumRack",
    "OriginalSimpler",
    "AutoFilter",
    "Eq8",
    "Compressor",
    "GlueCompressor",
    "Saturator",
    "Limiter",
    "Reverb",
    "Delay",
    "Roar",
    "Utility",
)
TRACK_TAGS = {"AudioTrack", "MidiTrack", "GroupTrack", "ReturnTrack"}


def device_chain_signatures(root: Element, local_name: Callable[[Element], str]) -> Counter[str]:
    chains: Counter[str] = Counter()
    for track in root.iter():
        track_type = local_name(track)
        if track_type not in TRACK_TAGS:
            continue
        devices = _ordered_devices(track, local_name)
        if len(devices) >= 2:
            chains[_chain_label(track_type, devices)] += 1
    return chains


def _ordered_devices(track: Element, local_name: Callable[[Element], str]) -> list[str]:
    devices: list[str] = []
    for element in track.iter():
        tag = local_name(element)
        if tag in DEVICE_TAGS and (not devices or devices[-1] != tag):
            devices.append(tag)
    return devices[:8]


def _chain_label(track_type: str, devices: list[str]) -> str:
    readable_track = re.sub(r"(?<!^)([A-Z])", r" \1", track_type).replace(" Track", " track")
    return f"{readable_track}: {' > '.join(devices)}"
