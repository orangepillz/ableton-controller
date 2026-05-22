"""argparse value parsers used by abletonctl."""

import argparse
import json
from typing import Any

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
