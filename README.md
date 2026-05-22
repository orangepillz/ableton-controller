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
```

List parameters on a device:

```sh
python3 abletonctl.py params --track "Synth" --device "EQ Eight"
```

Set a device parameter:

```sh
python3 abletonctl.py set-param --track "Synth" --device "EQ Eight" --param "1 Frequency A" --value 180
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
