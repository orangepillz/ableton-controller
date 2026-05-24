"""Historical project and chat evidence collection."""

from __future__ import annotations

import gzip
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from .arrangement_features import arrangement_phase_signatures, arrangement_roles, arrangement_shape, locator_marker_label
from .chat_scan import scan_chats
from .device_chain_features import device_chain_signatures
from .project_workflow_patterns import project_workflow_patterns


PROJECT_SUFFIXES = {".als", ".alp", ".adg", ".adv", ".alc"}
DEVICE_HINTS = (
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
AUTOMATION_HINTS = ("AutomationEnvelope", "ClipEnvelope", "MidiControllerEnvelope")
COMMON_NAME_TAGS = {"EffectiveName", "UserName"}
LABEL_TAGS = {"EffectiveName", "UserName", "Name", "DisplayName", "Target"}
TRACK_TAGS = {"AudioTrack", "MidiTrack", "GroupTrack", "ReturnTrack"}
NON_MUSICAL_LABELS = {"true", "false", "on", "off", "lane", "straight", "s-shaped"}


def _existing_roots(roots: tuple[Path, ...]) -> list[Path]:
    return [root for root in roots if root.exists()]


def _iter_files(root: Path, suffixes: set[str], limit: int) -> list[Path]:
    paths = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes]
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def _read_als_text(path: Path, max_bytes: int = 8_000_000) -> str:
    with gzip.open(path, "rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
    return raw.decode("utf-8", errors="ignore")


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _value(element: ET.Element) -> str:
    return str(element.attrib.get("Value") or element.attrib.get("value") or "").strip()


def _looks_named(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(
        value
        and len(value) > 1
        and any(char.isalpha() for char in value)
        and normalized not in NON_MUSICAL_LABELS
    )


def _first_label(element: ET.Element) -> str | None:
    for child in element.iter():
        if _local_name(child) in LABEL_TAGS and _looks_named(_value(child)):
            return _value(child)
    for child in element.iter():
        if _looks_named(_value(child)):
            return _value(child)
    return None


def _regex_features(text: str) -> dict[str, Any]:
    track_types = Counter(re.findall(r"<(AudioTrack|MidiTrack|GroupTrack|ReturnTrack)\b", text))
    names = Counter(re.findall(r'<EffectiveName Value="([^"]+)"', text))
    devices = Counter()
    for hint in DEVICE_HINTS:
        count = len(re.findall(rf"<{re.escape(hint)}\b", text))
        if count:
            devices[hint] = count
    automation = Counter()
    for hint in AUTOMATION_HINTS:
        count = len(re.findall(rf"<{re.escape(hint)}\b", text))
        if count:
            automation[hint] = count
    arrangement = Counter(_regex_block_labels(text, ("Locator", "Scene")))
    markers = Counter(_regex_locator_markers(text))
    routing = Counter(_regex_block_labels(text, ("AudioOutputRouting", "AudioInputRouting", "MidiOutputRouting", "MidiInputRouting")))
    scene_count = len(re.findall(r"<Scene\b", text))
    locator_count = len(re.findall(r"<Locator\b", text))
    shape = arrangement_shape(scene_count, locator_count, [], [])
    return {
        "track_types": track_types,
        "common_names": names,
        "devices": devices,
        "automation_features": automation,
        "arrangement_sections": arrangement,
        "arrangement_markers": markers,
        "arrangement_shape": shape,
        "arrangement_roles": Counter(),
        "arrangement_phases": Counter(),
        "device_chains": Counter(),
        "routing_targets": routing,
    }


def _regex_block_labels(text: str, tags: tuple[str, ...]) -> list[str]:
    labels: list[str] = []
    for tag in tags:
        for block in re.findall(rf"<{tag}\b.*?</{tag}>", text, flags=re.DOTALL):
            for value in re.findall(r'<(?:EffectiveName|UserName|Name|DisplayName|Target) Value="([^"]+)"', block):
                if _looks_named(value):
                    labels.append(value)
                    break
    return labels


def _regex_locator_markers(text: str) -> list[str]:
    markers: list[str] = []
    for block in re.findall(r"<Locator\b.*?</Locator>", text, flags=re.DOTALL):
        name = _regex_value(block, "Name")
        time = _float_or_none(_regex_value(block, "Time"))
        marker = locator_marker_label(name, time)
        if marker:
            markers.append(marker)
    return markers


def _regex_value(text: str, tag: str) -> str | None:
    match = re.search(rf"<{re.escape(tag)}\b[^>]*\bValue=\"([^\"]*)\"", text)
    return match.group(1).strip() if match else None


def _xml_features(text: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None

    track_types: Counter[str] = Counter()
    names: Counter[str] = Counter()
    devices: Counter[str] = Counter()
    automation: Counter[str] = Counter()
    arrangement: Counter[str] = Counter()
    markers: Counter[str] = Counter()
    clip_lengths: list[float] = []
    clip_times: list[float] = []
    clips: list[tuple[float, str]] = []
    locators = 0
    routing: Counter[str] = Counter()
    device_chains = device_chain_signatures(root, _local_name)
    scenes = 0

    for element in root.iter():
        tag = _local_name(element)
        value = _value(element)
        if tag in TRACK_TAGS:
            track_types[tag] += 1
        if tag in COMMON_NAME_TAGS and _looks_named(value):
            names[value] += 1
        if tag in DEVICE_HINTS:
            devices[tag] += 1
        if tag in AUTOMATION_HINTS:
            automation[tag] += 1
        if tag == "Scene":
            scenes += 1
            label = _first_label(element)
            if label:
                arrangement[label] += 1
        if tag == "Locator":
            locators += 1
            label = _first_label(element)
            if label:
                arrangement[label] += 1
            marker = locator_marker_label(_marker_label_value(element), _float_child(element, "Time"))
            if marker:
                markers[marker] += 1
        if tag in {"MidiClip", "AudioClip"}:
            clip_time = _float_or_none(element.attrib.get("Time")) or 0.0
            clip_times.append(clip_time)
            start = _float_child(element, "CurrentStart")
            end = _float_child(element, "CurrentEnd")
            if start is not None and end is not None and end > start:
                clip_lengths.append(end - start)
            label = _first_clip_name(element)
            if label:
                clips.append((clip_time, label))
        if "Routing" in tag or "Route" in tag:
            label = _first_label(element)
            if label:
                routing[label] += 1

    return {
        "track_types": track_types,
        "common_names": names,
        "devices": devices,
        "automation_features": automation,
        "arrangement_sections": arrangement,
        "arrangement_markers": markers,
        "arrangement_shape": arrangement_shape(scenes, locators, clip_times, clip_lengths),
        "arrangement_roles": arrangement_roles(clips),
        "arrangement_phases": arrangement_phase_signatures(clips),
        "device_chains": device_chains,
        "routing_targets": routing,
    }


def _float_child(element: ET.Element, tag_name: str) -> float | None:
    child = next((child for child in element if _local_name(child) == tag_name), None)
    if child is None:
        return None
    try:
        return float(_value(child))
    except ValueError:
        return None


def _float_or_none(raw: str | None) -> float | None:
    try:
        return float(raw or "0")
    except ValueError:
        return None


def _marker_label_value(element: ET.Element) -> str | None:
    for child in element.iter():
        if _local_name(child) in LABEL_TAGS and _value(child):
            return _value(child)
    return None


def _first_clip_name(element: ET.Element) -> str | None:
    for child in element:
        if _local_name(child) == "Name" and _looks_named(_value(child)):
            return _value(child)
    return None


def _count_project_signals(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".als":
        return {"path": str(path), "kind": path.suffix.lower(), "parsed": False}
    try:
        text = _read_als_text(path)
    except (OSError, EOFError):
        return {"path": str(path), "kind": ".als", "parsed": False}

    features = _xml_features(text) or _regex_features(text)
    automation = features["automation_features"]
    return {
        "path": str(path),
        "kind": ".als",
        "parsed": True,
        "track_types": dict(features["track_types"].most_common(12)),
        "common_names": dict(features["common_names"].most_common(20)),
        "devices": dict(features["devices"].most_common(20)),
        "automation_features": dict(automation.most_common(12)),
        "automation_mentions": sum(automation.values()),
        "arrangement_sections": dict(features["arrangement_sections"].most_common(16)),
        "arrangement_markers": dict(features["arrangement_markers"].most_common(16)),
        "arrangement_shape": dict(features["arrangement_shape"].most_common(16)),
        "arrangement_roles": dict(features["arrangement_roles"].most_common(16)),
        "arrangement_phases": dict(features["arrangement_phases"].most_common(12)),
        "device_chains": dict(features["device_chains"].most_common(16)),
        "routing_targets": dict(features["routing_targets"].most_common(16)),
        "workflows": project_workflow_patterns(features),
    }


def scan_projects(roots: tuple[Path, ...], limit: int = 30) -> dict[str, Any]:
    existing = _existing_roots(roots)
    files: list[Path] = []
    for root in existing:
        files.extend(_iter_files(root, PROJECT_SUFFIXES, limit))
    files = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    return {
        "roots": [str(root) for root in roots],
        "existing_roots": [str(root) for root in existing],
        "files_seen": len(files),
        "projects": [_count_project_signals(path) for path in files],
    }
