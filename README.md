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
```
