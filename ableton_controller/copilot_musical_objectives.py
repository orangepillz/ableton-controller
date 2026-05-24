"""Musical success targets for copilot orchestration plans."""

from __future__ import annotations

from typing import Any

from .copilot_musical_objective_support import PlanningContext
from .copilot_musical_objective_support import add_if_supported
from .copilot_musical_objective_support import has_any
from .copilot_musical_objective_support import objective


def musical_objectives(
    query: str,
    matches: list[dict[str, Any]],
    focus_axes: list[str],
    ordered_commands: list[str],
    target_aliases: list[dict[str, Any]],
    device_chains: list[dict[str, Any]],
    section_labels: list[dict[str, Any]],
    safety_checks: list[dict[str, str]],
    verification_steps: list[dict[str, str]],
    workflow_habits: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Translate command planning evidence into musical goals and success criteria."""
    context = PlanningContext(
        query=query,
        matches=matches,
        focus_axes=focus_axes,
        ordered_commands=ordered_commands,
        target_aliases=target_aliases,
        device_chains=device_chains,
        section_labels=section_labels,
        safety_checks=safety_checks,
        verification_steps=verification_steps,
        workflow_habits=workflow_habits or [],
    )
    objectives: list[dict[str, Any]] = []
    for builder in (
        _drop_impact_objective, _low_end_objective, _bass_movement_objective, _resampling_objective,
        _arrangement_objective, _transition_objective, _space_objective, _groove_objective, _mix_objective,
    ):
        add_if_supported(objectives, builder(context), context)
    return objectives


def _drop_impact_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("drop-impact", "drop impact", "drop hit", "hit harder", "slam", "punchier drop")):
        return None
    return objective(
        context,
        "drop-impact",
        "Make the drop land harder through contrast, transient clarity, low-end fit, and controlled headroom.",
        [
            "Inspect kick/sub timing and bus chains before changing impact processing.",
            "Use drum punch and bass movement as coordinated support, not disconnected loudness boosts.",
            "Verify the affected devices or stock controls after impact edits.",
        ],
        ["Do not solve drop impact by pushing master loudness before kick, sub, drums, and headroom are known."],
        ["drop impact", "tension/release", "low-end clarity", "drum punch", "mix translation"],
        ("drop-impact",),
    )


def _low_end_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("kick-sub-sidechain", "kick-sub-separation", "sidechain", "low end", "low-end", "sub")):
        return None
    criteria = [
        "Verify kick and sub targets against the current set before changing timing or ducking.",
        "Read low-end devices or stock controls before sidechain parameter tuning.",
        "Preserve sub stability while making room for the kick transient.",
    ]
    if context.target_aliases:
        criteria.insert(0, "Resolve matched personal target aliases before asking broad setup questions.")
    return objective(
        context,
        "low-end-translation",
        "Keep kick impact and sub weight separated enough to translate on a sound system.",
        criteria,
        ["Do not add wide modulation or heavy saturation to the sub anchor without a separate mid-bass target."],
        ["low-end clarity", "kick-bass fit"],
        ("kick-sub-sidechain",),
    )


def _bass_movement_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("bass-movement", "bass movement", "liquid bass", "movement")):
        return None
    return objective(
        context,
        "bass-motion",
        "Create audible mid-bass motion while keeping the fundamental low end controlled.",
        [
            "Read the target chain before adding or tuning the movement device.",
            "Write deterministic automation rather than vague freehand movement.",
            "Verify movement automation with readback samples after editing.",
        ],
        ["Keep the musical contour original when artist references are present."],
        ["sound design", "automation movement", "low-end clarity"],
        ("bass-movement",),
    )


def _resampling_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("bass-resampling-pass", "resampling", "resample", "print")):
        return None
    criteria = [
        "Preview routing, automation range, and print-track state before recording.",
        "Require explicit approval before starting any record/export/save action.",
        "Read back source movement and print routing after setup changes.",
    ]
    if "arrangement-automation-range" in context.safety_labels:
        criteria.insert(0, "Confirm the arrangement beat range before writing the resampling gesture.")
    return objective(
        context,
        "resampling-readiness",
        "Prepare expressive bass print options without committing an irreversible recording pass.",
        criteria,
        ["Do not record the pass until the user approves the previewed plan."],
        ["resampling", "tension/release", "sound design"],
        ("bass-movement",),
    )


def _arrangement_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("arrangement-flow", "arrangement-marker-naming", "arrangement-phase-scaffold", "marker", "locator", "section")):
        return None
    criteria = [
        "Use learned section-label proposals as a draft instead of inventing labels from scratch.",
        "Preview locator or scene names before mutating Arrangement state.",
        "Read back locators or scenes after applying arrangement changes.",
    ]
    if context.section_labels:
        criteria.insert(0, "Preserve the learned early/main/late flow implied by historical arrangements.")
    return objective(
        context,
        "arrangement-flow",
        "Make the session structure easier to navigate while preserving learned build, drop, and transition tendencies.",
        criteria,
        ["Do not rename arrangement anchors without a reviewable preview."],
        ["arrangement flow", "tension/release"],
        ("arrangement-flow",),
    )


def _transition_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("glitch-drum-transition", "riser-transition", "transition", "handoff", "stutter", "zap", "riser", "swell", "inhale")):
        return None
    return objective(
        context,
        "transition-contrast",
        "Build contrast and forward motion with editable transition elements that leave a clean handoff.",
        [
            "Inspect or choose transition samples before loading pads.",
            "Verify Drum Rack pad mapping before writing MIDI when sample placement is involved.",
            "Keep the final handoff clear enough for the next section to land.",
        ],
        ["Use glitch detail as punctuation, not constant density."],
        ["contrast", "groove/rhythm design", "tension/release"],
        ("glitch-drum-transition",),
    )


def _space_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("space-delay-rides", "personalized-space-chain", "reverb", "delay", "space", "spatial")):
        return None
    return objective(
        context,
        "spatial-motion",
        "Add spatial depth and movement without washing out the dry rhythmic focus.",
        [
            "Read the target chain before adding learned delay or reverb devices.",
            "Inspect wet, time, feedback, and decay controls before parameter tuning.",
            "Verify the resulting device chain after adding spatial processors.",
        ],
        ["Favor throws and controlled rides over permanent blur unless the user asks for wash."],
        ["spatial processing", "automation movement"],
        ("space-delay-rides",),
    )


def _groove_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("hat-humanize", "humanize", "human", "hats", "groove", "velocity", "probability")):
        return None
    return objective(
        context,
        "groove-humanization",
        "Make repeated hat patterns feel less mechanical while preserving the rhythmic anchors.",
        [
            "Read the existing hat notes before applying probability or velocity variation.",
            "Keep kick and snare anchors stable while humanizing hat lanes.",
            "Verify note readback after the transform so accents and dropouts stay intentional.",
        ],
        ["Do not randomize timing blindly before inspecting the existing phrase."],
        ["groove/rhythm design", "drum feel"],
        ("hat-humanize",),
    )


def _mix_objective(context: PlanningContext) -> dict[str, Any] | None:
    if not has_any(context, ("mix-bus-control", "drum-punch-bus", "mix", "master", "punch", "loudness")):
        return None
    return objective(
        context,
        "mix-translation",
        "Expose conservative mix controls while preserving headroom, punch, and translation.",
        [
            "Read the target bus chain before adding processing.",
            "Add inspection or control devices before committing gain, EQ, dynamics, or loudness moves.",
            "Verify the resulting chain without saving or exporting.",
        ],
        ["Do not chase loudness before the current headroom and routing are known."],
        ["mix translation", "drum punch"],
        ("mix-bus-control", "drum-kit-building"),
    )
