"""Build Serum VST3 preset files through the headless Serum Audio Unit."""

from __future__ import annotations

import argparse
import re
import struct
import zlib
from pathlib import Path
from typing import Any

DEFAULT_SERUM_TEMPLATE = Path.home() / "Music" / "Ableton" / "User Library" / "Serum.vstpreset"


def build_serum_preset(args: argparse.Namespace) -> dict[str, Any]:
    raise SystemExit("serum-build-preset must be run through the abletonctl shell launcher.")


def default_output_path(name: str) -> Path:
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip("-") or "Serum-Preset"
    return Path("/private/tmp") / ("%s.vstpreset" % filename)


def serum_build_controls(raw_controls: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_controls, list):
        raise SystemExit("serum-build-preset --controls must be a JSON list.")
    controls: list[dict[str, Any]] = []
    for index, raw_control in enumerate(raw_controls):
        if not isinstance(raw_control, dict):
            raise SystemExit("Serum build control %s must be an object." % index)
        control = dict(raw_control)
        selectors = [name for name in ("param", "id") if name in control]
        if len(selectors) != 1:
            raise SystemExit("Serum build control %s needs exactly one of param or id." % index)
        values = [name for name in ("value", "normalized") if name in control]
        if len(values) != 1:
            raise SystemExit("Serum build control %s needs exactly one of value or normalized." % index)
        normalized: dict[str, Any] = {selectors[0]: control[selectors[0]], values[0]: float(control[values[0]])}
        controls.append(normalized)
    return controls


def build_vstpreset_from_fxp(fxp_bytes: bytes, template_bytes: bytes, name: str) -> bytes:
    component = extract_fxp_component(fxp_bytes)
    return replace_vstpreset_component(template_bytes, component)


def extract_fxp_component(fxp_bytes: bytes) -> bytes:
    if len(fxp_bytes) < 60 or fxp_bytes[:4] != b"CcnK" or fxp_bytes[8:12] != b"FPCh":
        raise ValueError("Serum AU output was not an FXP chunk preset")
    component_size = struct.unpack(">I", fxp_bytes[56:60])[0]
    component = fxp_bytes[60 : 60 + component_size]
    if len(component) != component_size:
        raise ValueError("Serum FXP component chunk is truncated")
    zlib.decompress(component)
    return component


def patch_serum_state_name(state: bytes, name: str) -> bytes:
    encoded = name.encode("ascii", errors="ignore")[:63]
    if not encoded:
        return state
    offset = state.find(b" - Init - \x00")
    if offset < 0:
        offset = state.find(b" - Init - ")
    if offset < 0:
        return state
    data = bytearray(state)
    field_size = min(128, len(data) - offset)
    data[offset : offset + field_size] = b"\x00" * field_size
    data[offset : offset + len(encoded)] = encoded
    return bytes(data)


def replace_vstpreset_component(template_bytes: bytes, component: bytes) -> bytes:
    if len(template_bytes) < 48 or template_bytes[:4] != b"VST3":
        raise ValueError("Template is not a VST3 preset")
    list_offset = struct.unpack_from("<Q", template_bytes, 40)[0]
    if list_offset + 8 > len(template_bytes) or template_bytes[list_offset : list_offset + 4] != b"List":
        raise ValueError("Template VST3 preset does not contain a chunk list")
    count = struct.unpack_from("<I", template_bytes, list_offset + 4)[0]
    entries = read_vstpreset_entries(template_bytes, list_offset, count)
    info = entries.get(b"Info")
    if info is None:
        raise ValueError("Template VST3 preset does not contain an Info chunk")

    header = bytearray(template_bytes[:48])
    info_offset = 48 + len(component)
    new_list_offset = info_offset + len(info)
    struct.pack_into("<Q", header, 40, new_list_offset)

    footer = bytearray()
    footer += b"List"
    footer += struct.pack("<I", 3)
    footer += b"Comp" + struct.pack("<Q", 48) + struct.pack("<Q", len(component))
    footer += b"Cont" + struct.pack("<Q", info_offset) + struct.pack("<Q", 0)
    footer += b"Info" + struct.pack("<Q", info_offset) + struct.pack("<Q", len(info))
    return bytes(header) + component + info + bytes(footer)


def read_vstpreset_entries(template_bytes: bytes, list_offset: int, count: int) -> dict[bytes, bytes]:
    entries: dict[bytes, bytes] = {}
    cursor = list_offset + 8
    for _ in range(count):
        if cursor + 20 > len(template_bytes):
            raise ValueError("Template VST3 preset chunk list is truncated")
        chunk_id = template_bytes[cursor : cursor + 4]
        chunk_offset = struct.unpack_from("<Q", template_bytes, cursor + 4)[0]
        chunk_size = struct.unpack_from("<Q", template_bytes, cursor + 12)[0]
        chunk_end = chunk_offset + chunk_size
        if chunk_end > len(template_bytes):
            raise ValueError("Template VST3 preset chunk points past end of file")
        entries[chunk_id] = template_bytes[chunk_offset:chunk_end]
        cursor += 20
    return entries
