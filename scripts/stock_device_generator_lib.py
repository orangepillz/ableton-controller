"""Pure helpers for stock device control registry generation."""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import Any

from stock_device_controls import slugify


LIVE_APP_INFO = Path("/Applications/Ableton Live 12 Suite.app/Contents/Info.plist")


def build_controls(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used_slugs: dict[str, int] = {}
    controls: list[dict[str, Any]] = []
    for parameter in parameters:
        name = str(parameter.get("name") or "Parameter %s" % parameter.get("index"))
        base_slug = slugify(name)
        occurrence = used_slugs.get(base_slug, 0)
        used_slugs[base_slug] = occurrence + 1
        slug = base_slug if occurrence == 0 else "%s_%s" % (base_slug, parameter.get("index"))
        controls.append(
            {
                "index": parameter.get("index"),
                "name": name,
                "slug": slug,
                "aliases": unique_strings(
                    [
                        name,
                        slug,
                        str(parameter.get("index")),
                        "%s %s" % (parameter.get("index"), name),
                        parameter.get("original_name"),
                    ]
                ),
                "parameter": {
                    "name": name,
                    "original_name": parameter.get("original_name"),
                    "min": parameter.get("min"),
                    "max": parameter.get("max"),
                    "default_value": parameter.get("default_value"),
                    "value": parameter.get("value"),
                    "display_value": parameter.get("display_value"),
                    "is_enabled": parameter.get("is_enabled"),
                    "is_quantized": parameter.get("is_quantized"),
                    "value_items": parameter.get("value_items"),
                },
            }
        )
    return controls


def unique_strings(values: list[Any]) -> list[str]:
    found: list[str] = []
    seen = set()
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text not in seen:
            found.append(text)
            seen.add(text)
    return found


def track_kind(device_or_root: dict[str, Any] | str) -> str:
    if isinstance(device_or_root, dict):
        root = str(device_or_root.get("root", ""))
        path = str(device_or_root.get("path", ""))
    else:
        root = str(device_or_root)
        path = ""
    if root == "audio_effects":
        return "audio"
    if root == "max_for_live" and "/Max Audio Effect/" in path:
        return "audio"
    return "midi"


def detect_live_version(info_path: Path = LIVE_APP_INFO) -> str | None:
    try:
        with info_path.open("rb") as handle:
            info = plistlib.load(handle)
        return str(info.get("CFBundleShortVersionString") or info.get("CFBundleVersion") or "")
    except Exception:
        return None
