# Ableton Controller

Local bridge for controlling Ableton Live from a CLI without screen automation.

The bridge has two pieces:

- `remote_scripts/Codex_AI`: an Ableton MIDI Remote Script that runs inside Live and exposes a localhost JSON socket.
- `abletonctl.py`: a stdlib-only CLI that sends commands to the bridge.
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
python3 abletonctl.py ping
python3 abletonctl.py status
python3 abletonctl.py tracks
```

## Examples

Set a track volume:

```sh
python3 abletonctl.py set-track --track "Synth" --volume 0.72
```

List devices on a track:

```sh
python3 abletonctl.py devices --track "Synth"
python3 abletonctl.py device-tree --track "Synth" --depth 4
```

Add, move, delete, and inspect stock Live devices:

```sh
python3 abletonctl.py device-add-stock --target-track "Vox" --name "EQ Eight" --root audio_effects --target-index 0
python3 abletonctl.py device-add-stock --target-track "Vox" --path "audio_effects/Auto Filter" --target-index 1
python3 abletonctl.py device-move --source-track "Vox" --source-device "Auto Filter" --target-track "Vox" --target-index 0
python3 abletonctl.py device-delete --track "Vox" --device "Auto Filter"
python3 abletonctl.py params --track "Synth" --device "EQ Eight"
```

Use `device-tree` paths to target devices inside racks and rack chains:

```sh
python3 abletonctl.py device-tree --track "Vox"
python3 abletonctl.py device-add-stock --target-path "song.tracks[30].devices[0].chains[0]" --path "audio_effects/Compressor" --target-index 0
python3 abletonctl.py device-move --source-device-path "song.tracks[30].devices[0].chains[0].devices[1]" --target-path "song.tracks[30].devices[0].chains[0]" --target-index 0
python3 abletonctl.py params --device-path "song.tracks[30].devices[0].chains[0].devices[0]"
```

Set a device parameter:

```sh
python3 abletonctl.py set-param --track "Synth" --device "EQ Eight" --param "1 Frequency A" --value 180
python3 abletonctl.py set-param --device-path "song.tracks[30].devices[0].chains[0].devices[0]" --param Threshold --normalized 0.35
```

The repository also includes a generated Live 12 stock-device controls registry
at `data/stock_device_controls.live12.json`. It is generated from Live's own
browser and loaded-device parameter lists, so each Built-in instrument, audio
effect, and MIDI effect has explicit control names, ranges, value items, and
aliases:

```sh
python3 abletonctl.py stock-devices --summary
python3 abletonctl.py stock-devices --root audio_effects --query filter
python3 abletonctl.py stock-controls --device "Auto Filter"
python3 abletonctl.py stock-controls --device "EQ Eight" --control "1 Frequency A"
python3 abletonctl.py set-stock-control --track "Synth" --device "Auto Filter" --control frequency --normalized 0.5
```

Refresh the registry after updating Live:

```sh
python3 scripts/generate_stock_device_controls.py --output data/stock_device_controls.live12.json
python3 abletonctl.py stock-coverage
```

Inspect and use raw Live Object Model paths:

```sh
python3 abletonctl.py lom-inspect song
python3 abletonctl.py lom-get song.tempo
python3 abletonctl.py lom-set song.metronome true
python3 abletonctl.py lom-call song.tap_tempo
```

Browse and load Live content:

```sh
python3 abletonctl.py browser-roots
python3 abletonctl.py browser-children audio_effects
python3 abletonctl.py browser-tree instruments --depth 2 --max-items 200
python3 abletonctl.py browser-search "EQ Eight" --item audio_effects --depth 3
python3 abletonctl.py browser-load "audio_effects/EQ Eight"
```

Show, hide, or focus Live views:

```sh
python3 abletonctl.py show-view Browser
python3 abletonctl.py focus-view Session
python3 abletonctl.py hide-view Detail
```

Send keyboard shortcuts and menu commands to Live:

```sh
python3 abletonctl.py hotkey cmd+s
python3 abletonctl.py hotkey cmd+shift+r
python3 abletonctl.py key-sequence cmd+option+b tab space
python3 abletonctl.py type-text "My Set Name"
python3 abletonctl.py menu-search "Export Audio/Video"
python3 abletonctl.py save
```

These local keyboard/menu commands use macOS `osascript` and `System Events`, so macOS may require
Accessibility permission for the terminal or Codex app that launches them.

Create scenes/tracks and work with Session clips:

```sh
python3 abletonctl.py create-track --type midi --name "Codex MIDI"
python3 abletonctl.py create-scene --name "Drop"
python3 abletonctl.py clip-slots --track "Codex MIDI"
python3 abletonctl.py fire-scene --scene "Drop"
```

Read and write MIDI notes in a MIDI clip:

```sh
python3 abletonctl.py clip-create-midi --track "Codex MIDI" --slot 0 --length 4 --name "Bass Loop"
python3 abletonctl.py clip-create-midi --track "Codex MIDI" --start 64 --end 72 --name "Arrangement Bass"
python3 abletonctl.py clips --track "Codex MIDI"
python3 abletonctl.py midi-add-notes --track "Codex MIDI" --slot 0 --notes '[{"pitch":60,"start_time":0,"duration":1,"velocity":96}]'
python3 abletonctl.py midi-get-notes --track "Codex MIDI" --slot 0
python3 abletonctl.py midi-update-notes --track "Codex MIDI" --slot 0 --notes '[{"note_id":1,"pitch":62,"velocity":110}]'
python3 abletonctl.py midi-transform-notes --track "Codex MIDI" --slot 0 --start 0 --end 4 --transpose 12
python3 abletonctl.py clip-copy --source-track "Codex MIDI" --source-slot 0 --dest-track "Codex MIDI" --dest-start 80
python3 abletonctl.py clip-split --track "Codex MIDI" --arrangement-start 80 --time 82
python3 abletonctl.py clip-set --track "Codex MIDI" --slot 0 --loop-start 0 --loop-end 2 --end-marker 2
```

The public Live API supports MIDI note pitch, timing, velocity, mute, probability,
velocity deviation, and release velocity. MIDI Ctrl/Pitch Bend clip-envelope drawing is
not exposed by the supported Live Object Model, so use device/parameter automation or
recorded MIDI controller data for pitch-bend envelopes.

Create and warp audio clips:

```sh
python3 abletonctl.py create-track --type audio --name "Codex Audio"
python3 abletonctl.py clip-create-audio --track "Codex Audio" --file "/absolute/path/to/loop.wav" --start 96 --warping true --warp-mode beats
python3 abletonctl.py clip-warp --track "Codex Audio" --arrangement-start 96
python3 abletonctl.py clip-warp --track "Codex Audio" --arrangement-start 96 --warping true --warp-mode complex-pro --pitch-coarse -12
python3 abletonctl.py clip-warp-marker-add --track "Codex Audio" --arrangement-start 96 --beat-time 4 --sample-time 3.85
python3 abletonctl.py clip-warp-marker-move --track "Codex Audio" --arrangement-start 96 --beat-time 4 --to-beat 4.25
python3 abletonctl.py clip-warp-marker-remove --track "Codex Audio" --arrangement-start 96 --beat-time 4.25
```

Warp modes can be passed by name (`beats`, `tones`, `texture`, `repitch`,
`complex`, `rex`, `complex-pro`) or by their Live API index (`0` through `6`).
For marker adds, `--sample-time` is optional; when omitted, the bridge
interpolates from the current marker map to preserve playback timing. Marker
commands require the clip's Warp switch to already be on.

Automate device parameters inside Session or Arrangement clips:

```sh
python3 abletonctl.py clip-automation-set --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency --clear --steps '[{"time":0,"duration":1,"normalized":0.15},{"time":1,"duration":1,"normalized":0.85}]'
python3 abletonctl.py clip-automation-get --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency --times 0,0.25,1.25
python3 abletonctl.py clip-automation-clear --track "Codex Audio" --slot 0 --device "Auto Filter" --param Frequency
python3 abletonctl.py clip-stock-automation-set --track "Codex MIDI" --slot 0 --device Pitch --stock-device "midi_effects/Pitch" --control Pitch --clear --steps '[{"time":0,"duration":1,"value":12},{"time":1,"duration":1,"value":-12}]'
python3 abletonctl.py clip-stock-automation-get --track "Codex MIDI" --slot 0 --device Pitch --stock-device "midi_effects/Pitch" --control Pitch --times 0,0.5,1.5
```

Automation steps accept raw `value` or normalized `0..1` values. Nested rack devices can
be automated with `--device-path`, or with `--device-track` plus a top-level device name.

Send a raw JSON command:

```sh
python3 abletonctl.py raw '{"command":"status"}'
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
