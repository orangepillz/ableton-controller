"""Arrangement-oriented producer workflow templates."""

from __future__ import annotations

import argparse
from typing import Any

from .arrangement_labels import fallback_marker_label_proposals, load_memory, marker_label_proposals


PHASE_SCENES = (
    ("01 Early - Drum FX Kick Setup", "Establish the learned early-section role blend without committing to a drop."),
    ("02 Main - Drum FX Kick Drop", "Mark the primary impact section where drums, FX, and kick reinforce each other."),
    ("03 Late - Drum FX Kick Variation", "Reserve a later variation lane for density, fills, or call-response changes."),
    ("04 Reset - Tail Or Transition", "Leave a named recovery section for tails, fakeouts, or the next handoff."),
)


def arrangement_phase_scaffold(args: argparse.Namespace) -> dict[str, Any]:
    commands: list[dict[str, Any]] = [
        {
            "why": "Read the current set before adding semantic scene labels.",
            "args": ["session-snapshot", "--no-selected-devices", "--no-target-devices", "--no-clips"],
        }
    ]
    for offset, (name, why) in enumerate(PHASE_SCENES):
        scene_args: list[Any] = ["create-scene", "--name", name]
        if args.scene_index is not None:
            scene_args.extend(["--index", args.scene_index + offset])
        commands.append({"why": why, "args": scene_args})
    commands.append(
        {
            "why": "Verify the set after creating the semantic arrangement scaffold.",
            "args": ["session-snapshot", "--no-selected-devices", "--no-target-devices", "--no-clips"],
        }
    )
    return {
        "summary": "Create named scenes from learned arrangement phase signatures so future production work has explicit section labels.",
        "assumptions": [
            "Historical shape evidence favors grid-aligned sections.",
            "Historical role evidence shows drum, FX, and kick material co-occurring across early, main, and late phases.",
            "The scenes are labels and planning anchors; they do not move or delete existing clips.",
        ],
        "commands": commands,
    }


def arrangement_marker_naming(args: argparse.Namespace) -> dict[str, Any]:
    markers, marker_source = _marker_section_names(args)
    commands: list[dict[str, Any]] = [
        {
            "why": "Read existing Arrangement locators before renaming marker-style anchors.",
            "args": ["locators"],
        }
    ]
    for marker in markers:
        commands.append(
            {
                "why": f"Rename the learned marker at beat {marker['beat']:g} to a musical section anchor.",
                "args": ["set-locator", "--time", marker["beat"], "--name", marker["name"]],
            }
        )
    commands.append(
        {
            "why": "Verify locator names after applying the musical section map.",
            "args": ["locators"],
        }
    )
    return {
        "summary": "Rename numbered Arrangement locators into musical section anchors based on learned marker timing evidence.",
        "assumptions": [
            marker_source,
            "Section label names are derived proposals, not historically learned locator labels.",
            "Names are intentionally descriptive planning anchors, not direct imitation of any reference artist.",
            "Review the rendered plan before executing because locator renaming mutates the Live set.",
        ],
        "commands": commands,
    }


def _marker_section_names(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    markers = marker_label_proposals(load_memory(getattr(args, "memory", None)))
    if markers:
        return markers, "persisted project.arrangement-marker memory was found; section label proposals were derived from marker timing plus arrangement role/phase memory."
    return fallback_marker_label_proposals(), "No persisted marker memory was found, so the plan uses the default learned marker map."
