# Ableton Controller

Local bridge for controlling Ableton Live from a CLI without screen automation.

The bridge has these pieces:

- `remote_scripts/Codex_AI`: an Ableton MIDI Remote Script that runs inside Live and exposes a localhost JSON socket.
- `bin/abletonctl`: a PATH-friendly launcher for the CLI that resolves this checkout and selects Python 3.10+.
- `abletonctl.py`: a compatibility wrapper for the modular CLI implementation.
- `codex-midi-ports`: a small CoreMIDI helper that advertises the MIDI ports Live expects for this control surface slot.

Ableton's supported install location for third-party Remote Scripts is:

```text
~/Music/Ableton/User Library/Remote Scripts
```

## Quick Start

Install the Remote Script:

```sh
python3 scripts/install_bridge.py install
```

Build and install the MIDI port helper LaunchAgent before opening Live:

```sh
swiftc -module-cache-path .build/ModuleCache scripts/codex_midi_ports.swift -o codex-midi-ports
python3 scripts/install_bridge.py install-midi-agent
```

Install the CLI command into PATH:

```sh
python3 scripts/install_bridge.py install-cli
```

This creates `~/.local/bin/abletonctl` as a symlink to `bin/abletonctl`. The launcher
works from any directory and avoids macOS/Xcode Python 3.9 by choosing Python 3.10+
when it runs the controller.

Then activate the `Codex_AI` control surface in Live, or use the restart activator:

```sh
python3 scripts/install_bridge.py restart-activate --replace Alesis_V
```

`restart-activate` saves already-saved Live sets before requesting a normal quit. If the
current set has no file path, it refuses to guess by default. For a throwaway unsaved
set, it can clean up scratch tracks, force quit Live, quarantine Live's recovery trigger
files, and reopen without the recovery prompt:

```sh
python3 scripts/install_bridge.py restart-activate --replace Alesis_V \
  --cleanup-track-prefix "Codex " \
  --unsaved-action force-discard-recovery
```

That force-discard path only runs when Live reports an empty `song.file_path`; if a set
has already been saved, the helper saves it and uses the normal quit path instead.
Recovery files are moved to `~/Library/Application Support/CodexAbleton/recovery-quarantine/`.

The LaunchAgent keeps `V61 (Out)` and `V61 (In)` available for the control-surface slot.

Verify:

```sh
abletonctl ping
abletonctl status
abletonctl tracks
abletonctl session-snapshot
```

`session-snapshot` runs the standard read-only planning probes in one command:
status, tracks, selected track, and selected-track devices/clips. Add repeated
`--track` flags to include extra target tracks, and `--device-tree-depth` when a
rack-aware workflow needs nested device paths.

Match a new request against personalized copilot memory before choosing a plan:

```sh
abletonctl copilot-intent "make a glitchy zap transition into the synth"
abletonctl copilot-intent "tighten the kick and sub before the drop" --limit 2
```

`copilot-intent` reads `.ableton-copilot/memory.json` and returns confidence-scored
intent mappings, planning biases, likely follow-ups, recommended commands, and
compact project-profile hints for arrangement phase signatures, roles, shape,
routing, and automation. Use the result as a planning hint, then verify the
current Live set before editing.

Render reusable dry-run plan templates for common producer workflows:

```sh
abletonctl workflow-macro list
abletonctl workflow-macro render bass-movement --track "Mid Bass" --slot 0
abletonctl workflow-macro render kick-sub-separation --kick-track Kick --track Sub --start 0 --length 8
abletonctl workflow-macro render bass-resampling-pass --track "Mid Bass" --start 64 --length 8 --print-track "Bass Resample Print"
abletonctl workflow-macro render arrangement-marker-naming
abletonctl workflow-macro render arrangement-phase-scaffold --scene-index 0
abletonctl workflow-macro render glitch-drum-transition --track "Zap Rack" --secondary-track "Perc Rack" --synth-track "Lead Synth" --length 8
```

Personalized arrangement macros read `.ableton-copilot/memory.json` by default
when it exists. Use `--memory` to render against a specific memory snapshot.

The rendered output is plain plan JSON compatible with:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json
```

## Examples

Set a track volume:

```sh
abletonctl set-track --track "Synth" --volume 0.72
```

List devices on a track:

```sh
abletonctl devices --track "Synth"
abletonctl device-tree --track "Synth" --depth 4
```

Add, move, delete, and inspect stock Live devices:

```sh
abletonctl device-add-stock --target-track "Vox" --name "EQ Eight" --root audio_effects --target-index 0
abletonctl device-add-stock --target-track "Vox" --path "audio_effects/Auto Filter" --target-index 1
abletonctl device-move --source-track "Vox" --source-device "Auto Filter" --target-track "Vox" --target-index 0
abletonctl device-delete --track "Vox" --device "Auto Filter"
abletonctl params --track "Synth" --device "EQ Eight"
```

Load browser items onto exact Drum Rack pads:

```sh
abletonctl device-add-stock --target-track "Drums" --path "instruments/Drum Rack"
abletonctl drum-pad-load --track "Drums" --pad C1 --item "samples/Kick.wav"
abletonctl drum-pad-load --track "Drums" --device "Main Rack" --pad D1 --item "samples/Snare.wav" --clear
```

`drum-pad-load` refuses to replace a populated pad unless `--clear` is provided.
Pad notes accept either MIDI numbers or note names such as `C1`.

Use `device-tree` paths to target devices inside racks and rack chains:

```sh
abletonctl device-tree --track "Vox"
abletonctl device-add-stock --target-path "song.tracks[30].devices[0].chains[0]" --path "audio_effects/Compressor" --target-index 0
abletonctl device-move --source-device-path "song.tracks[30].devices[0].chains[0].devices[1]" --target-path "song.tracks[30].devices[0].chains[0]" --target-index 0
abletonctl params --device-path "song.tracks[30].devices[0].chains[0].devices[0]"
```

Set a device parameter:

```sh
abletonctl set-param --track "Synth" --device "EQ Eight" --param "1 Frequency A" --value 180
abletonctl set-param --device-path "song.tracks[30].devices[0].chains[0].devices[0]" --param Threshold --normalized 0.35
```

The repository also includes a generated Live 12 stock-device controls registry
at `data/stock_device_controls.live12.json`. It is generated from Live's own
browser and loaded-device parameter lists, so each Built-in instrument, audio
effect, and MIDI effect has explicit control names, ranges, value items, and
aliases:

```sh
abletonctl stock-devices --summary
abletonctl stock-devices --root audio_effects --query filter
abletonctl stock-controls --device "Auto Filter"
abletonctl stock-controls --device "EQ Eight" --control "1 Frequency A"
abletonctl set-stock-control --track "Synth" --device "Auto Filter" --control frequency --normalized 0.5
```

Refresh the registry after updating Live:

```sh
python3 scripts/generate_stock_device_controls.py --output data/stock_device_controls.live12.json
abletonctl stock-coverage
```

Inspect and use raw Live Object Model paths:

```sh
abletonctl lom-inspect song
abletonctl lom-get song.tempo
abletonctl lom-set song.metronome true
abletonctl lom-call song.tap_tempo
```

Browse and load Live content:

```sh
abletonctl browser-roots
abletonctl browser-children audio_effects
abletonctl browser-tree instruments --depth 2 --max-items 200
abletonctl browser-search "EQ Eight" --item audio_effects --depth 3
abletonctl browser-load "audio_effects/EQ Eight"
```

Show, hide, or focus Live views:

```sh
abletonctl show-view Browser
abletonctl focus-view Session
abletonctl hide-view Detail
```

Send keyboard shortcuts and menu commands to Live:

```sh
abletonctl hotkey cmd+s
abletonctl hotkey cmd+shift+r
abletonctl key-sequence cmd+option+b tab space
abletonctl type-text "My Set Name"
abletonctl menu-search "Export Audio/Video"
abletonctl save
```

These local keyboard/menu commands use macOS `osascript` and `System Events`, so macOS may require
Accessibility permission for the terminal or Codex app that launches them.

Create scenes/tracks and work with Session clips:

```sh
abletonctl create-track --type midi --name "Codex MIDI"
abletonctl create-scene --name "Drop"
abletonctl clip-slots --track "Codex MIDI"
abletonctl fire-scene --scene "Drop"
```

Read and write MIDI notes in a MIDI clip:

```sh
abletonctl clip-create-midi --track "Codex MIDI" --slot 0 --length 4 --name "Bass Loop"
abletonctl clip-create-midi --track "Codex MIDI" --start 64 --end 72 --name "Arrangement Bass"
abletonctl clips --track "Codex MIDI"
abletonctl midi-add-notes --track "Codex MIDI" --slot 0 --notes '[{"pitch":60,"start_time":0,"duration":1,"velocity":96}]'
abletonctl midi-get-notes --track "Codex MIDI" --slot 0
abletonctl midi-update-notes --track "Codex MIDI" --slot 0 --notes '[{"note_id":1,"pitch":62,"velocity":110}]'
abletonctl midi-transform-notes --track "Codex MIDI" --slot 0 --start 0 --end 4 --transpose 12
abletonctl clip-copy --source-track "Codex MIDI" --source-slot 0 --dest-track "Codex MIDI" --dest-start 80
abletonctl clip-split --track "Codex MIDI" --arrangement-start 80 --time 82
abletonctl clip-set --track "Codex MIDI" --slot 0 --loop-start 0 --loop-end 2 --end-marker 2
```

The public Live API supports MIDI note pitch, timing, velocity, mute, probability,
velocity deviation, and release velocity. MIDI Ctrl/Pitch Bend clip-envelope drawing is
not exposed by the supported Live Object Model, so use device/parameter automation or
recorded MIDI controller data for pitch-bend envelopes.

Create and warp audio clips:

```sh
abletonctl create-track --type audio --name "Codex Audio"
abletonctl clip-create-audio --track "Codex Audio" --file "/absolute/path/to/loop.wav" --start 96 --warping true --warp-mode beats
abletonctl clip-warp --track "Codex Audio" --arrangement-start 96
abletonctl clip-warp --track "Codex Audio" --arrangement-start 96 --warping true --warp-mode complex-pro --pitch-coarse -12
abletonctl clip-warp-marker-add --track "Codex Audio" --arrangement-start 96 --beat-time 4 --sample-time 3.85
abletonctl clip-warp-marker-move --track "Codex Audio" --arrangement-start 96 --beat-time 4 --to-beat 4.25
abletonctl clip-warp-marker-remove --track "Codex Audio" --arrangement-start 96 --beat-time 4.25
```

Warp modes can be passed by name (`beats`, `tones`, `texture`, `repitch`,
`complex`, `rex`, `complex-pro`) or by their Live API index (`0` through `6`).
For marker adds, `--sample-time` is optional; when omitted, the bridge
interpolates from the current marker map to preserve playback timing. Marker
commands require the clip's Warp switch to already be on.

Automate device parameters inside Session or Arrangement clips:

```sh
abletonctl clip-automation-set --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency --clear --steps '[{"time":0,"duration":1,"normalized":0.15},{"time":1,"duration":1,"normalized":0.85}]'
abletonctl arrangement-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --steps 8 --clear
abletonctl arrangement-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --curve ease-in-out --clear
abletonctl arrangement-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --events '[{"time":0,"normalized":0.2,"curve_coefficients":{"x1":0.42,"y1":0,"x2":0.58,"y2":1}},{"time":16,"normalized":0.95}]' --clear
abletonctl arrangement-automation-set-many --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","duration":16,"from_normalized":0.2,"to_normalized":0.95,"curve":"ease-in-out","clear":true},{"param":"Resonance","duration":16,"from_normalized":0.12,"to_normalized":0.35,"steps":8,"clear":true}]'
abletonctl arrangement-automation-file-set --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --clip-name "Noise Rise" --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --curve ease-in-out
abletonctl arrangement-automation-file-get --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --times 0,4,8,12,15.5
abletonctl clip-automation-get --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency --times 0,0.25,1.25
abletonctl clip-automation-clear --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency
abletonctl clip-stock-automation-set --track "Codex MIDI" --slot 0 --device Pitch --stock-device "midi_effects/Pitch" --control Pitch --clear --steps '[{"time":0,"duration":1,"value":12},{"time":1,"duration":1,"value":-12}]'
abletonctl clip-stock-automation-get --track "Codex MIDI" --slot 0 --device Pitch --stock-device "midi_effects/Pitch" --control Pitch --times 0,0.5,1.5
```

Automation steps and breakpoint events accept raw `value` or normalized `0..1` values.
Breakpoint events may include `curve_coefficients` with `x1`, `y1`, `x2`, and `y2`.
When those curve handles must be committed exactly as Ableton `CurveControl*` saved-set
fields, use `arrangement-automation-file-set` on a saved `.als` while the set is not open
in Live, then reopen it. Use `arrangement-automation-file-get` to inspect saved breakpoint
events and curve coefficients. Nested rack devices can be automated with `--device-path`,
or with `--device-track` plus a top-level device name.
`arrangement-automation-set` writes Arrangement clip lanes through the bridge's dedicated
Arrangement automation path. On MIDI Arrangement clips, the bridge can create a missing
lane by staging a temporary Session clip, duplicating it back to Arrangement, and cleaning
up the temporary slot. Use `arrangement-automation-set-many` when multiple missing lanes
must be created together on the same MIDI Arrangement clip, so the materialization pass can
write all intended lanes at once. `arrangement-automation-get` samples the lane with
clip-relative times.

Send a raw JSON command:

```sh
abletonctl raw '{"command":"status"}'
```

## Manual Audit

The Live 12 feature-control audit document lives at:

```text
docs/live12-feature-control-audit.md
```

The extraction cache and downloaded PDF are intentionally ignored by Git:

```text
audit/
data/
```

To regenerate the audit seed after downloading the manual PDF:

```sh
python3 -m pip install -r requirements.txt
python3 scripts/audit_manual.py extract
python3 scripts/update_audit_coverage.py
```

## Architecture

Code ownership, module boundaries, and maintainability conventions are documented in
`docs/architecture.md`. Repository-wide standards for future agents and contributors
are in `AGENTS.md`.
