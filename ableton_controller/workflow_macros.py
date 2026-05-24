"""Reusable producer workflow plan templates."""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from .arrangement_workflows import arrangement_marker_naming, arrangement_phase_scaffold
from .drum_workflow_macros import drum_punch_bus, hat_humanize
from .mix_workflow_macros import mix_bus_control
from .transition_workflow_macros import riser_transition
from .workflow_personalization import DEVICE_PATHS, has_refinement, load_macro_memory, personalized_macro_track, personalized_target_source, space_chain_from_memory


def _track(args: argparse.Namespace, default: str) -> str | int:
    return args.track if args.track is not None else default


def _range(args: argparse.Namespace) -> tuple[float, float]:
    start = float(args.start)
    end = float(args.end) if args.end is not None else start + float(args.length)
    return start, end


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def _target_flags(*tracks: str | int) -> list[Any]:
    flags: list[Any] = []
    for track in tracks:
        flags.extend(["--track", track])
    return flags


def _kick_sub(args: argparse.Namespace) -> dict[str, Any]:
    memory = load_macro_memory(getattr(args, "memory", None))
    kick = personalized_macro_track(args.kick_track, "Kick", "kick", memory)
    sub = personalized_macro_track(_track(args, args.sub_track), "Sub", "sub-bass", memory)
    start, end = _range(args)
    return {
        "summary": "Separate kick and sub by reading context, tightening sub note lengths, and preparing ducking control.",
        "assumptions": [
            f"Kick track is {kick!r}",
            f"Sub track is {sub!r}",
            personalized_target_source(memory),
            f"Session clip slot {args.slot} covers the target bass pattern",
        ],
        "commands": [
            {"why": "Read planning context for the two low-end anchors.", "args": ["session-snapshot", *_target_flags(kick, sub), "--device-tree-depth", 3]},
            {"why": "Inspect current sub MIDI before shortening anything.", "args": ["midi-get-notes", "--track", sub, "--slot", args.slot, "--start", start, "--end", end]},
            {"why": "Leave small transient gaps for kick impact.", "args": ["midi-transform-notes", "--track", sub, "--slot", args.slot, "--start", start, "--end", end, "--duration-scale", 0.92]},
            {"why": "Prepare controllable kick ducking on the sub if needed.", "args": ["device-add-stock", "--target-track", sub, "--path", "audio_effects/Compressor"]},
            {"why": "Read exact Compressor controls before configuring sidechain values.", "args": ["stock-controls", "--device", "Compressor"]},
        ],
    }


def _bass_movement(args: argparse.Namespace) -> dict[str, Any]:
    track = _track(args, "Mid Bass")
    steps = [
        {"time": 0, "duration": 0.5, "normalized": 0.22},
        {"time": 0.5, "duration": 0.5, "normalized": 0.76},
        {"time": 1, "duration": 1, "normalized": 0.38},
        {"time": 2, "duration": 2, "normalized": 0.66},
    ]
    return {
        "summary": "Add repeatable clip-tied filter movement to a mid-bass layer while preserving sub stability.",
        "assumptions": [f"Target mid-bass track is {track!r}", f"Movement clip is in slot {args.slot}"],
        "commands": [
            {"why": "Read the target chain and clip context before adding movement.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 5]},
            {"why": "Add a stock movement device if one is not already present.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Auto Filter"]},
            {"why": "Keep resonance controlled so movement does not become harsh.", "args": ["set-stock-control", "--track", track, "--device", "Auto Filter", "--stock-device", "Auto Filter", "--control", "resonance", "--normalized", 0.22]},
            {"why": "Write deterministic clip automation for talking/wobble motion.", "args": ["clip-stock-automation-set", "--track", track, "--slot", args.slot, "--device", "Auto Filter", "--stock-device", "Auto Filter", "--control", "frequency", "--clear", "--steps", _json(steps)]},
            {"why": "Read back automation samples for verification.", "args": ["clip-stock-automation-get", "--track", track, "--slot", args.slot, "--device", "Auto Filter", "--stock-device", "Auto Filter", "--control", "frequency", "--times", "0,0.5,1,2,3"]},
        ],
    }


def _call_response_bass(args: argparse.Namespace) -> dict[str, Any]:
    track = _track(args, "Call Response Bass")
    notes = [
        {"pitch": 36, "start_time": 0, "duration": 0.5, "velocity": 118},
        {"pitch": 36, "start_time": 1.5, "duration": 0.25, "velocity": 106},
        {"pitch": 43, "start_time": 2, "duration": 0.5, "velocity": 112},
        {"pitch": 41, "start_time": 3.25, "duration": 0.25, "velocity": 104},
        {"pitch": 36, "start_time": 4, "duration": 0.75, "velocity": 120},
        {"pitch": 48, "start_time": 6, "duration": 0.25, "velocity": 110},
        {"pitch": 46, "start_time": 6.5, "duration": 0.25, "velocity": 102},
        {"pitch": 43, "start_time": 7, "duration": 0.5, "velocity": 114},
    ]
    return {
        "summary": "Create a simple call-and-response bass sketch with space for kick and snare.",
        "assumptions": [f"New MIDI track name is {track!r}", "Root defaults to C until the current set reveals a key."],
        "commands": [
            {"why": "Create a dedicated editable bass sketch track.", "args": ["create-track", "--type", "midi", "--name", track]},
            {"why": "Use a stock instrument for deterministic playback.", "args": ["device-add-stock", "--target-track", track, "--path", "instruments/Operator"]},
            {"why": "Add a filter target for later movement.", "args": ["device-add-stock", "--target-track", track, "--path", "audio_effects/Auto Filter"]},
            {"why": "Create the MIDI clip container.", "args": ["clip-create-midi", "--track", track, "--slot", args.slot, "--length", args.length, "--name", args.name or "Call Response Bass 01"]},
            {"why": "Write a spaced call-and-response phrase.", "args": ["midi-add-notes", "--track", track, "--slot", args.slot, "--notes", _json(notes)]},
            {"why": "Verify the generated phrase.", "args": ["midi-get-notes", "--track", track, "--slot", args.slot]},
        ],
    }


def _personalized_space_chain(args: argparse.Namespace) -> dict[str, Any]:
    track = _track(args, "Space Texture")
    chain, source = space_chain_from_memory(getattr(args, "memory", None))
    devices = [device for device in chain if device in DEVICE_PATHS]
    commands: list[dict[str, Any]] = [
        {"why": "Read the target track before adding a personalized spatial chain.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 5]},
    ]
    for device in devices:
        commands.append(
            {"why": f"Add learned spatial chain component {device}.", "args": ["device-add-stock", "--target-track", track, "--path", DEVICE_PATHS[device]]}
        )
    for device in devices:
        commands.append(
            {"why": f"Read {device} controls before making wet/time/decay tuning decisions.", "args": ["stock-controls", "--device", device]}
        )
    commands.append(
        {"why": "Verify the resulting personalized space chain.", "args": ["session-snapshot", "--track", track, "--device-tree-depth", 6]}
    )
    return {
        "summary": "Add a personalized space chain from learned historical device-chain preferences.",
        "assumptions": [
            f"Target track is {track!r}",
            source,
            "The macro adds devices only; exact wet/time/decay values should be chosen after reading stock controls and current set context.",
        ],
        "commands": commands,
    }


def _bass_resampling_pass(args: argparse.Namespace) -> dict[str, Any]:
    source = _track(args, "Mid Bass")
    print_track = args.print_track
    start, end = _range(args)
    duration = end - start
    return {
        "summary": "Prepare a bass movement resampling pass by automating motion and routing the full output to a print track.",
        "assumptions": [
            f"Source bass track is {source!r}",
            f"Arrangement clip starts at beat {start}",
            f"Print track is {print_track!r}",
            "Recording the pass still needs explicit approval.",
        ],
        "commands": [
            {"why": "Read the bass chain before adding movement or print routing.", "args": ["session-snapshot", "--track", source, "--device-tree-depth", 5]},
            {"why": "Add a reliable motion target if one is not already present.", "args": ["device-add-stock", "--target-track", source, "--path", "audio_effects/Auto Filter"]},
            {"why": "Sweep the movement over the Arrangement clip with a curved breakpoint envelope.", "args": ["arrangement-automation-set", "--track", source, "--arrangement-start", start, "--device", "Auto Filter", "--param", "Frequency", "--duration", duration, "--from-normalized", 0.2, "--to-normalized", 0.9, "--curve", "ease-in-out", "--clear"]},
            {"why": "Create a dedicated audio print target for the resampling pass.", "args": ["create-track", "--type", "audio", "--name", print_track]},
            {"why": "Route Main output into the print track for a full-context resample.", "args": ["set-routing", "--track", print_track, "--direction", "input", "--type", "Resampling"]},
            {"why": "Arm the print track, but do not start recording without approval.", "args": ["set-track", "--track", print_track, "--arm", "true", "--solo", "false", "--mute", "false"]},
            {"why": "Verify source movement and print routing before recording.", "args": ["session-snapshot", "--track", source, "--track", print_track, "--device-tree-depth", 3]},
        ],
    }


def _glitch_drum_transition(args: argparse.Namespace) -> dict[str, Any]:
    memory = load_macro_memory(getattr(args, "memory", None))
    zap_track = _track(args, "Zap Glitch Rack")
    perc_track = args.secondary_track
    synth_track = args.synth_track
    start, end = _range(args)
    bar_three = start + 8.0
    zap_notes = [
        {"pitch": 36, "start_time": 0, "duration": 0.125, "velocity": 116},
        {"pitch": 38, "start_time": 0.5, "duration": 0.125, "velocity": 92},
        {"pitch": 40, "start_time": 0.75, "duration": 0.0625, "velocity": 86},
        {"pitch": 36, "start_time": 1.5, "duration": 0.125, "velocity": 108},
        {"pitch": 43, "start_time": 1.75, "duration": 0.0625, "velocity": 84},
        {"pitch": 38, "start_time": 2.5, "duration": 0.125, "velocity": 104},
        {"pitch": 40, "start_time": 3.0, "duration": 0.0625, "velocity": 90},
        {"pitch": 36, "start_time": 3.5, "duration": 0.0625, "velocity": 82},
    ]
    perc_notes = [
        {"pitch": 36, "start_time": 5.5, "duration": 0.125, "velocity": 86},
        {"pitch": 38, "start_time": 6.0, "duration": 0.125, "velocity": 100},
        {"pitch": 40, "start_time": 6.5, "duration": 0.0625, "velocity": 92},
        {"pitch": 43, "start_time": 6.75, "duration": 0.0625, "velocity": 88},
        {"pitch": 38, "start_time": 7.0, "duration": 0.125, "velocity": 112},
        {"pitch": 45, "start_time": 7.5, "duration": 0.0625, "velocity": 96},
        {"pitch": 47, "start_time": 7.75, "duration": 0.0625, "velocity": 104},
    ]
    assumptions = [
        f"Zap rack track is {zap_track!r}",
        f"Perc transition rack track is {perc_track!r}",
        f"Synth handoff target is {synth_track!r}",
        f"Bar 3 starts at beat {bar_three}",
        "Replace placeholder sample paths with browser-search results before executing drum-pad-load steps.",
    ]
    verify_pad_mapping = has_refinement(memory, "pad-mapping-correction")
    if verify_pad_mapping:
        assumptions.append("Historical correction memory says to verify that samples land on distinct Drum Rack pads.")
    commands = [
        {"why": "Read current context and the synth handoff target.", "args": ["session-snapshot", "--track", synth_track, "--device-tree-depth", 3]},
        {"why": "Find candidate zap samples in the Samples browser root.", "args": ["browser-search", args.zap_query, "--item", "samples", "--depth", 6, "--max-results", 12]},
        {"why": "Find candidate percussion samples for the transition rack.", "args": ["browser-search", args.perc_query, "--item", "samples", "--depth", 6, "--max-results", 12]},
        {"why": "Create the zap Drum Rack track.", "args": ["create-track", "--type", "midi", "--name", zap_track]},
        {"why": "Create the percussion transition Drum Rack track.", "args": ["create-track", "--type", "midi", "--name", perc_track]},
        {"why": "Load Drum Rack on the zap track.", "args": ["device-add-stock", "--target-track", zap_track, "--path", "instruments/Drum Rack"]},
        {"why": "Load Drum Rack on the perc transition track.", "args": ["device-add-stock", "--target-track", perc_track, "--path", "instruments/Drum Rack"]},
        {"why": "Replace this placeholder with a chosen zap browser path.", "args": ["drum-pad-load", "--track", zap_track, "--pad", "C1", "--item", "samples/<zap-1>"]},
        {"why": "Replace this placeholder with a contrasting zap browser path.", "args": ["drum-pad-load", "--track", zap_track, "--pad", "D1", "--item", "samples/<zap-2>"]},
        {"why": "Replace this placeholder with a short perc browser path.", "args": ["drum-pad-load", "--track", perc_track, "--pad", "C1", "--item", "samples/<perc-1>"]},
        {"why": "Replace this placeholder with a brighter perc browser path.", "args": ["drum-pad-load", "--track", perc_track, "--pad", "D1", "--item", "samples/<perc-2>"]},
    ]
    if verify_pad_mapping:
        commands.extend(
            [
                {"why": "Verify zap samples are on distinct Drum Rack pads before writing MIDI.", "args": ["device-tree", "--track", zap_track, "--depth", 6]},
                {"why": "Verify percussion samples are on distinct Drum Rack pads before writing MIDI.", "args": ["device-tree", "--track", perc_track, "--depth", 6]},
            ]
        )
    commands.extend(
        [
            {"why": "Add global filter motion to the zap rack.", "args": ["device-add-stock", "--target-track", zap_track, "--path", "audio_effects/Auto Filter"]},
            {"why": "Add echo for glitch throws on the perc transition rack.", "args": ["device-add-stock", "--target-track", perc_track, "--path", "audio_effects/Echo"]},
            {"why": "Create an eight-beat zap clip with a full bar of silence before bar 3.", "args": ["clip-create-midi", "--track", zap_track, "--slot", args.slot, "--length", end - start, "--name", args.name or "Zap Glitch Cutout"]},
            {"why": "Write zap stutters only in the first bar, leaving beats 4-8 empty.", "args": ["midi-add-notes", "--track", zap_track, "--slot", args.slot, "--notes", _json(zap_notes)]},
            {"why": "Create an eight-beat perc transition clip.", "args": ["clip-create-midi", "--track", perc_track, "--slot", args.slot, "--length", end - start, "--name", "Perc Glitch Into Synth"]},
            {"why": "Write perc stutters into the bar-3 handoff.", "args": ["midi-add-notes", "--track", perc_track, "--slot", args.slot, "--notes", _json(perc_notes)]},
            {"why": "Verify the two rack chains and transition clips.", "args": ["session-snapshot", "--track", zap_track, "--track", perc_track, "--track", synth_track, "--device-tree-depth", 5]},
        ]
    )
    return {
        "summary": "Sketch a two-rack glitch transition: zaps stutter then leave a one-bar hole before bar 3 while perc fills into the synth.",
        "assumptions": assumptions,
        "commands": commands,
    }


MacroRenderer = Callable[[argparse.Namespace], dict[str, Any]]

MACROS: dict[str, tuple[str, tuple[str, ...], MacroRenderer]] = {
    "kick-sub-separation": ("Tighten kick/sub timing and prepare controlled ducking.", ("mixing", "bass"), _kick_sub),
    "bass-movement": ("Add deterministic mid-bass filter movement.", ("sound-design", "automation"), _bass_movement),
    "bass-resampling-pass": ("Prepare a movement-heavy bass resampling print pass.", ("sound-design", "resampling"), _bass_resampling_pass),
    "call-response-bass": ("Create an editable call-and-response bass phrase.", ("composition", "bass"), _call_response_bass),
    "drum-punch-bus": ("Prepare a punch-focused drum bus chain.", ("mixing", "drums"), drum_punch_bus),
    "hat-humanize": ("Humanize hat timing feel with controlled velocity and probability variation.", ("groove", "drums"), hat_humanize),
    "personalized-space-chain": ("Add the learned Delay/Reverb-style space chain to a target track.", ("mixing", "spatial", "personalized"), _personalized_space_chain),
    "glitch-drum-transition": ("Sketch zap/perc Drum Racks with stutters and a pre-bar-3 cutout.", ("drums", "transition", "glitch"), _glitch_drum_transition),
    "riser-transition": ("Create an inhale riser with filter and space automation before a drop.", ("transition", "sound-design", "automation"), riser_transition),
    "mix-bus-control": ("Prepare a conservative mix/master preview chain.", ("mixing", "mastering"), mix_bus_control),
    "arrangement-phase-scaffold": ("Create named scenes from learned early/main/late phase signatures.", ("arrangement", "personalized"), arrangement_phase_scaffold),
    "arrangement-marker-naming": ("Rename numbered locators into musical section anchors.", ("arrangement", "personalized"), arrangement_marker_naming),
}


def list_workflow_macros() -> dict[str, Any]:
    return {
        "macros": [
            {"name": name, "description": description, "tags": list(tags)}
            for name, (description, tags, _renderer) in sorted(MACROS.items())
        ]
    }


def render_workflow_macro(args: argparse.Namespace) -> dict[str, Any]:
    if not args.macro:
        raise SystemExit("workflow-macro render needs a macro name.")
    try:
        _description, _tags, renderer = MACROS[args.macro]
    except KeyError:
        raise SystemExit("Unknown workflow macro %r. Run `workflow-macro list`." % args.macro)
    plan = renderer(args)
    plan["macro"] = args.macro
    return plan
