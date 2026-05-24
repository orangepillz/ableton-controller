"""argparse value parsers used by abletonctl."""

import argparse
import json
import re
from typing import Any

NOTE_CLASSES = {
    "c": 0,
    "d": 2,
    "e": 4,
    "f": 5,
    "g": 7,
    "a": 9,
    "b": 11,
}

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


def midi_note_value(value: str) -> int:
    text = value.strip()
    try:
        note = int(text)
    except ValueError:
        match = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d+)", text)
        if not match:
            raise argparse.ArgumentTypeError("expected MIDI note 0..127 or note name like C1")
        name, accidental, octave_text = match.groups()
        note_class = NOTE_CLASSES[name.lower()]
        if accidental == "#":
            note_class += 1
        elif accidental == "b":
            note_class -= 1
        note = (int(octave_text) + 2) * 12 + note_class
    if note < 0 or note > 127:
        raise argparse.ArgumentTypeError("MIDI note must be 0..127")
    return note


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
