"""Small XML helpers for gzipped Ableton Live Set files."""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def read_tree(path: Path) -> ET.ElementTree:
    with gzip.open(path, "rb") as handle:
        return ET.parse(handle)


def write_tree(path: Path, tree: ET.ElementTree) -> None:
    with gzip.open(path, "wb") as handle:
        tree.write(handle, encoding="utf-8", xml_declaration=True, short_empty_elements=True)


def ensure_path(parent: ET.Element, tags: tuple[str, ...]) -> ET.Element:
    current = parent
    for tag in tags:
        child = current.find("./" + tag)
        if child is None:
            child = ET.SubElement(current, tag)
        current = child
    return current


def next_child_id(parent: ET.Element, tag: str) -> int:
    ids = [int(child.attrib.get("Id", "-1")) for child in parent.findall("./" + tag) if child.attrib.get("Id", "").lstrip("-").isdigit()]
    return max(ids, default=-1) + 1


def next_event_id(events: list[ET.Element]) -> int:
    ids = [int(event.attrib.get("Id", "-1")) for event in events if event.attrib.get("Id", "").lstrip("-").isdigit()]
    return max(ids, default=0) + 1


def child_value(element: ET.Element, path: str) -> str | None:
    child = element.find(path)
    return child.attrib.get("Value") if child is not None else None


def attr_float(element: ET.Element, attr: str, default: float | None) -> float | None:
    value = element.attrib.get(attr)
    if value is None:
        return default
    return float(value)


def range_contains(start: float, end: float, value: float | None) -> bool:
    return value is not None and start - 0.000001 <= value <= end + 0.000001


def same_float(left: float | None, right: float) -> bool:
    return left is not None and abs(left - right) < 0.000001


def matches_text(query: str, candidates: list[str]) -> bool:
    normalized = norm(query)
    return any(normalized == norm(candidate) or normalized == norm(candidate).rstrip("0123456789") for candidate in candidates)


def norm(value: Any) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def format_float(value: float) -> str:
    if abs(value - round(value)) < 0.000000001:
        return str(int(round(value)))
    return ("%.10f" % value).rstrip("0").rstrip(".")
