"""Verification step suggestions for copilot orchestration."""

from __future__ import annotations


PLAYBOOK_VERIFICATION = {
    "bass-movement": (
        ("verify-playbook-device-context", "device-tree", "Read bass/sub devices before applying learned movement playbook edits."),
    ),
    "spatial-send": (
        ("verify-playbook-routing-context", "session-snapshot", "Read return/send routing before applying learned spatial throw moves."),
    ),
    "glitch-drum": (
        ("verify-drum-rack-pads", "device-tree", "Read Drum Rack chains for the learned glitch drum transition playbook."),
    ),
    "kick-sub": (
        ("verify-playbook-routing-context", "session-snapshot", "Read kick/sub/sidechain routing before low-end playbook edits."),
        ("verify-playbook-stock-controls", "stock-controls", "Read dynamics/EQ controls before kick/sub playbook tuning."),
    ),
    "mix-bus": (
        ("verify-playbook-stock-controls", "stock-controls", "Read mix-bus controls before conservative loudness playbook edits."),
    ),
    "arrangement-transition": (
        ("verify-locators", "locators", "Read locators before applying learned arrangement transition flow."),
    ),
    "riser-transition": (
        ("verify-midi-notes", "midi-get-notes", "Read MIDI notes after applying learned riser transition playbook edits."),
    ),
}


def verification_steps(
    ordered_commands: list[str],
    workflow_playbooks: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Suggest readback probes for the selected planning commands."""
    steps: list[dict[str, str]] = []
    for command in ordered_commands:
        normalized = command.lower()
        if "arrangement-marker-naming" in normalized or "set-locator" in normalized:
            _add(steps, "verify-locators", "locators", "Read Arrangement locators after section-name changes.")
        if "arrangement-phase-scaffold" in normalized or "create-scene" in normalized:
            _add(steps, "verify-scenes", "session-snapshot", "Refresh scenes and section labels after scaffolding.")
        if "drum-pad-load" in normalized or "glitch-drum-transition" in normalized:
            _add(steps, "verify-drum-rack-pads", "device-tree", "Read Drum Rack chains to confirm samples landed on intended pads.")
        if "midi-add-notes" in normalized or "call-response-bass" in normalized or "riser-transition" in normalized:
            _add(steps, "verify-midi-notes", "midi-get-notes", "Read generated MIDI notes after writing the phrase.")
        if "clip-stock-automation-set" in normalized or "bass-movement" in normalized or "riser-transition" in normalized:
            _add(steps, "verify-clip-automation", "clip-stock-automation-get", "Sample written clip automation after movement edits.")
        if "arrangement-automation-set" in normalized:
            _add(steps, "verify-arrangement-automation", "session-snapshot", "Refresh the affected arrangement track after automation edits.")
        if "device-add-stock" in normalized or "serum-add" in normalized or "personalized-space-chain" in normalized or "drum-punch-bus" in normalized or "mix-bus-control" in normalized or "riser-transition" in normalized:
            _add(steps, "verify-device-chain", "device-tree", "Read the affected track device chain after adding devices.")
        if "serum-set" in normalized:
            _add(steps, "verify-serum-params", "serum-params", "Read exposed Serum parameters before or after Serum control changes.")
        if "stock-controls" in normalized or "set-stock-control" in normalized:
            _add(steps, "verify-stock-controls", "stock-controls", "Read stock-device controls before or after parameter tuning.")
        if "set-routing" in normalized or "bass-resampling-pass" in normalized or "set-track" in normalized:
            _add(steps, "verify-routing-state", "session-snapshot", "Refresh routing, arm, and track state after setup changes.")
        if "set-send" in normalized:
            _add(steps, "verify-send-state", "session-snapshot", "Refresh return/send state after send movement.")
    for playbook in workflow_playbooks or []:
        _add_playbook_steps(steps, playbook)
    return steps


def _add_playbook_steps(steps: list[dict[str, str]], playbook: dict[str, str]) -> None:
    for label, command, why in PLAYBOOK_VERIFICATION.get(str(playbook.get("id", "")), ()):
        _add(steps, label, command, why)


def _add(steps: list[dict[str, str]], label: str, command: str, why: str) -> None:
    if any(step["label"] == label for step in steps):
        return
    steps.append({"label": label, "command": command, "why": why})
