"""Clip envelope target catalog and CLI payload helpers."""

from __future__ import annotations

import re
from typing import Any

CC_CONTROL_TARGETS = {
    "pitch_bend": {"name": "Pitch Bend", "range": [-64.0, 64.0], "cc": None},
    "mod_wheel": {"name": "Mod Wheel", "range": [0.0, 127.0], "cc": 1},
    "pressure": {"name": "Pressure", "range": [0.0, 127.0], "cc": None},
    "custom_a": {"name": "Custom A", "range": [0.0, 1.0], "cc": None},
    "custom_b": {"name": "Custom B", "range": [0.0, 127.0], "cc": None},
    "custom_c": {"name": "Custom C", "range": [0.0, 127.0], "cc": None},
    "custom_d": {"name": "Custom D", "range": [0.0, 127.0], "cc": None},
    "custom_e": {"name": "Custom E", "range": [0.0, 127.0], "cc": None},
    "custom_f": {"name": "Custom F", "range": [0.0, 127.0], "cc": None},
    "custom_g": {"name": "Custom G", "range": [0.0, 127.0], "cc": None},
    "custom_h": {"name": "Custom H", "range": [0.0, 127.0], "cc": None},
    "custom_i": {"name": "Custom I", "range": [0.0, 127.0], "cc": None},
    "custom_j": {"name": "Custom J", "range": [0.0, 127.0], "cc": None},
    "custom_k": {"name": "Custom K", "range": [0.0, 127.0], "cc": None},
    "custom_l": {"name": "Custom L", "range": [0.0, 127.0], "cc": None},
    "custom_m": {"name": "Custom M", "range": [0.0, 127.0], "cc": None},
}

COMMON_MIDI_CCS = {
    1: "Mod Wheel",
    2: "Breath Controller",
    4: "Foot Controller",
    7: "Channel Volume",
    10: "Pan",
    11: "Expression Controller",
    64: "Sustain Pedal",
}

CC_CONTROL_DEVICE = "CC Control"
CC_CONTROL_DEVICE_PATH = "midi_effects/CC Control"
CC_CONTROL_ROOT = "midi_effects"

AUDIO_CLIP_ENVELOPES = (
    {
        "id": "transposition",
        "name": "Transposition",
        "range": [-48.0, 48.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Audio Clip > Transposition envelope. Live exposes the static pitch_coarse/pitch_fine properties through LOM, but not this native envelope target.",
    },
    {
        "id": "gain",
        "name": "Gain",
        "range": [0.0, 1.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Audio Clip > Gain envelope. Live exposes the static clip gain property through LOM, but not this native envelope target.",
    },
    {
        "id": "sample_offset",
        "name": "Sample Offset",
        "range": [-8.0, 8.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Audio Clip > Sample Offset envelope, only meaningful in Beats warp mode.",
    },
    {
        "id": "grain_size",
        "name": "Grain Size",
        "range": [0.0, 1.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Audio Clip grain-size modulation target for Tones/Texture modes is not exposed as a public DeviceParameter.",
    },
    {
        "id": "flux",
        "name": "Flux",
        "range": [0.0, 1.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Audio Clip Flux modulation target for Texture mode is not exposed as a public DeviceParameter.",
    },
    {
        "id": "transient_envelope",
        "name": "Transient Envelope",
        "range": [0.0, 100.0],
        "support": "native_clip_envelope_ui_only",
        "notes": "Beats-mode transient envelope control is visible in Live's clip UI, but is not exposed through the public Clip LOM.",
    },
)

AUDIO_CLIP_PROPERTIES = (
    {"id": "gain", "name": "Clip Gain", "support": "live_lom", "command": "clip-audio-set --gain"},
    {"id": "pitch_coarse", "name": "Pitch Coarse", "support": "live_lom", "command": "clip-audio-set --pitch-coarse"},
    {"id": "pitch_fine", "name": "Pitch Fine", "support": "live_lom", "command": "clip-audio-set --pitch-fine"},
    {"id": "warping", "name": "Warp Switch", "support": "live_lom", "command": "clip-audio-set --warping"},
    {"id": "warp_mode", "name": "Warp Mode", "support": "live_lom", "command": "clip-audio-set --warp-mode"},
    {"id": "ram_mode", "name": "RAM Mode", "support": "live_lom", "command": "clip-audio-set --ram-mode"},
    {"id": "clip_bpm", "name": "Clip Segment BPM", "support": "warp_marker_lom", "command": "clip-audio-set --clip-bpm"},
    {"id": "reverse", "name": "Reverse Sample", "support": "focused_live_menu", "command": "clip-audio-set --reverse"},
    {"id": "transient_loop_mode", "name": "Transient Loop Mode", "support": "native_clip_ui_only"},
    {"id": "complex_pro_formants", "name": "Complex Pro Formants", "support": "native_clip_ui_only"},
    {"id": "complex_pro_envelope", "name": "Complex Pro Envelope", "support": "native_clip_ui_only"},
)


def midi_control_targets() -> list[dict[str, Any]]:
    targets = [
        {
            "id": key,
            "name": value["name"],
            "cc": value["cc"],
            "range": value["range"],
            "support": "cc_control_device_parameter",
        }
        for key, value in CC_CONTROL_TARGETS.items()
    ]
    targets.extend(
        {
            "id": "cc_%03d" % number,
            "name": COMMON_MIDI_CCS.get(number, "MIDI CC %d" % number),
            "cc": number,
            "range": [0.0, 127.0],
            "support": "native_midi_ctrl_ui_only",
        }
        for number in range(128)
    )
    return targets


def clip_envelope_catalog(clip_type: str | None = None) -> dict[str, Any]:
    catalog: dict[str, Any] = {
        "device_parameters": {
            "support": "live_lom",
            "commands": ["clip-automation-get", "clip-automation-set", "clip-automation-set-many", "clip-automation-clear"],
            "notes": "Live's public clip automation API accepts DeviceParameter targets, including mixer, device, rack, and stock-device parameters.",
        },
        "midi_controls": {
            "support": "mixed",
            "targets": midi_control_targets(),
            "recommended_live_route": {
                "device": CC_CONTROL_DEVICE,
                "path": CC_CONTROL_DEVICE_PATH,
                "commands": ["clip-envelope-get --target midi-cc", "clip-envelope-set --target midi-cc"],
                "direct_controls": list(CC_CONTROL_TARGETS.keys()),
            },
        },
        "audio_clip_envelopes": {
            "support": "native_clip_envelope_ui_only",
            "targets": list(AUDIO_CLIP_ENVELOPES),
        },
        "audio_clip_properties": {
            "support": "live_lom_or_focused_menu",
            "targets": list(AUDIO_CLIP_PROPERTIES),
        },
    }
    if clip_type:
        catalog["clip_type"] = clip_type
    return catalog


def native_clip_envelope_error(target: str) -> str:
    return (
        "%s is a native Clip/MIDI Ctrl envelope. Ableton's public Live Object Model "
        "does not expose that target as a DeviceParameter, so the bridge cannot write "
        "its breakpoints directly while Live is open. Use device-backed clip automation "
        "or clip-envelope-set --target midi-cc for CC Control-backed pitch bend, mod wheel, "
        "pressure, or configured Custom A-M lanes."
    ) % target


def cc_control_parameter_name(identifier: Any) -> str:
    text = str(identifier or "").strip()
    normalized = re.sub(r"[^a-z0-9]+", "", text.lower())
    aliases = {
        "pitchbend": "Pitch Bend",
        "pb": "Pitch Bend",
        "modwheel": "Mod Wheel",
        "mod": "Mod Wheel",
        "cc1": "Mod Wheel",
        "cc001": "Mod Wheel",
        "pressure": "Pressure",
        "aftertouch": "Pressure",
        "channelpressure": "Pressure",
    }
    for key, value in CC_CONTROL_TARGETS.items():
        aliases[re.sub(r"[^a-z0-9]+", "", key.lower())] = value["name"]
        aliases[re.sub(r"[^a-z0-9]+", "", value["name"].lower())] = value["name"]
    if normalized in aliases:
        return aliases[normalized]
    match = re.fullmatch(r"cc0*([0-9]{1,3})", normalized)
    if match:
        number = int(match.group(1))
        if number == 1:
            return "Mod Wheel"
        if 0 <= number <= 127:
            raise ValueError(native_clip_envelope_error("MIDI CC %d" % number))
    return text
