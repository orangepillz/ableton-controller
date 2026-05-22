# CLI Command Map

Prefer these wrapped commands before using raw LOM or UI automation.

## Core And State

```sh
python3 abletonctl.py ping
python3 abletonctl.py status
python3 abletonctl.py tracks
python3 abletonctl.py selected --devices
python3 abletonctl.py select-track --track "Bass"
python3 abletonctl.py tempo
python3 abletonctl.py tempo --set 140
python3 abletonctl.py play
python3 abletonctl.py stop
python3 abletonctl.py continue
python3 abletonctl.py undo
python3 abletonctl.py redo
```

## Tracks, Scenes, And Routing

```sh
python3 abletonctl.py create-track --type midi --name "Drop Bass"
python3 abletonctl.py create-track --type audio --name "Resample Print"
python3 abletonctl.py create-track --type return --name "Short Verb"
python3 abletonctl.py duplicate-track --track "Lead"
python3 abletonctl.py delete-track --track "Scratch"
python3 abletonctl.py create-scene --name "Drop"
python3 abletonctl.py fire-scene --scene "Drop"
python3 abletonctl.py set-routing --track "Resample Print" --direction input --type "Resampling"
python3 abletonctl.py set-routing --track "Bass" --direction output --type "Bass Bus"
```

Use `set-routing` after reading available route names from a failed attempt or Live state. Routing names are matched by displayed name.

For grouping, first try a LOM-backed plan:

```sh
python3 abletonctl.py lom-inspect song
python3 abletonctl.py lom-call song.create_group_track --args '[0]'
python3 abletonctl.py lom-set song.tracks[0].name "Drum Bus"
```

Only use UI grouping with `menu-search "Group Tracks"` or `hotkey cmd+g` when selection is known.

## Mixer And Sends

```sh
python3 abletonctl.py set-track --track "Kick" --volume 0.82 --pan 0
python3 abletonctl.py set-track --track "Bass" --mute false --solo false --arm false
python3 abletonctl.py set-send --track "Snare" --send "A" --value 0.18
```

Use conservative values. In Ableton API mixer values are often normalized, so prefer small deltas or probe returned parameter ranges when exact gain in dB matters.

## Devices And Stock Controls

```sh
python3 abletonctl.py devices --track "Bass"
python3 abletonctl.py device-tree --track "Bass" --depth 5
python3 abletonctl.py device-add-stock --target-track "Bass" --path "audio_effects/EQ Eight" --target-index 0
python3 abletonctl.py device-add-stock --target-track "Bass" --name "Auto Filter" --root audio_effects
python3 abletonctl.py device-move --source-track "Bass" --source-device "Auto Filter" --target-track "Bass" --target-index 0
python3 abletonctl.py device-delete --track "Bass" --device "Auto Filter"
python3 abletonctl.py params --track "Bass" --device "EQ Eight"
```

Nested racks require `device-tree` paths:

```sh
python3 abletonctl.py device-add-stock --target-path "song.tracks[3].devices[0].chains[0]" --path "audio_effects/Compressor"
python3 abletonctl.py set-param --device-path "song.tracks[3].devices[0].chains[0].devices[0]" --param Threshold --normalized 0.35
```

Stock registry commands:

```sh
python3 abletonctl.py stock-devices --summary
python3 abletonctl.py stock-devices --root audio_effects --query filter
python3 abletonctl.py stock-controls --device "Auto Filter" --control frequency
python3 abletonctl.py set-stock-control --track "Bass" --device "Auto Filter" --stock-device "Auto Filter" --control frequency --normalized 0.42
```

Common useful devices:
- Dynamics: `Compressor`, `Drum Buss`, `Glue Compressor`, `Limiter`, `Gate`.
- Tone: `EQ Eight`, `Auto Filter`, `Roar`, `Saturator`, `Overdrive`, `Redux`.
- Space and motion: `Echo`, `Delay`, `Hybrid Reverb`, `Reverb`, `Chorus-Ensemble`, `Phaser-Flanger`.
- Utility and imaging: `Utility`, `Spectrum`, `Tuner`.
- Racks: `Audio Effect Rack`, `Instrument Rack`, `Drum Rack`, `MIDI Effect Rack`.
- MIDI: `Scale`, `Pitch`, `Random`, `Arpeggiator`, `Note Length`, `Velocity`.

## Clips

Clip reference styles:

```sh
--track "Bass" --slot 0
--track "Bass" --arrangement-start 64
--track "Bass" --arrangement-index 0
--path "song.tracks[3].clip_slots[0].clip"
```

Create and edit:

```sh
python3 abletonctl.py clip-create-midi --track "Bass" --slot 0 --length 4 --name "Call Bass"
python3 abletonctl.py clip-create-midi --track "Bass" --start 64 --length 8 --name "Drop Bass"
python3 abletonctl.py clip-create-audio --track "Riser" --file "/absolute/path/riser.wav" --start 56 --warping true --warp-mode complex-pro
python3 abletonctl.py clip-set --track "Bass" --slot 0 --looping true --loop-start 0 --loop-end 4 --end-marker 4
python3 abletonctl.py clip-copy --source-track "Bass" --source-slot 0 --dest-track "Bass" --dest-start 64
python3 abletonctl.py clip-split --track "Bass" --arrangement-start 64 --time 68
```

Audio warp:

```sh
python3 abletonctl.py clip-warp --track "Vocal Chop" --arrangement-start 32 --warping true --warp-mode complex-pro --pitch-coarse -12
python3 abletonctl.py clip-warp-marker-add --track "Break" --arrangement-start 16 --beat-time 4 --sample-time 3.85
python3 abletonctl.py clip-warp-marker-move --track "Break" --arrangement-start 16 --beat-time 4 --to-beat 4.25
```

Warp modes: `beats`, `tones`, `texture`, `repitch`, `complex`, `rex`, `complex-pro`.

## MIDI Notes

Note objects support pitch, start_time, duration, velocity, mute, probability, velocity_deviation, and release_velocity.

```sh
python3 abletonctl.py midi-add-notes --track "Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":112}]'
python3 abletonctl.py midi-get-notes --track "Bass" --slot 0 --start 0 --end 4
python3 abletonctl.py midi-replace-notes --track "Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":1,"velocity":112}]'
python3 abletonctl.py midi-transform-notes --track "Hats" --slot 0 --start 0 --end 4 --pitch-min 42 --pitch-max 46 --velocity-deviation 10 --probability 0.92
python3 abletonctl.py midi-duplicate-region --track "Bass" --slot 0 --start 0 --length 2 --destination-time 2 --transpose 7
```

Use `midi-replace-notes` only after approval unless the clip was just created for the workflow.

## Automation

Automation steps use clip time. Use `value` for raw parameter values and `normalized` for 0..1 movement.

```sh
python3 abletonctl.py clip-stock-automation-set --track "Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":1,"normalized":0.18},{"time":1,"duration":1,"normalized":0.72}]'
python3 abletonctl.py clip-automation-get --track "Bass" --slot 0 --device "Auto Filter" --param Frequency --times 0,0.5,1,1.5
python3 abletonctl.py clip-stock-automation-clear --track "Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency
```

Clip automation is preferred for repeatable bass movement, filter sweeps, fakeouts, fills, and transitions.

## Browser And Local UI

```sh
python3 abletonctl.py browser-roots
python3 abletonctl.py browser-search "Operator" --item instruments --depth 4
python3 abletonctl.py browser-load "instruments/Operator"
python3 abletonctl.py show-view Browser
python3 abletonctl.py focus-view Session
python3 abletonctl.py hotkey cmd+s
python3 abletonctl.py hotkey cmd+g
python3 abletonctl.py hotkey cmd+shift+r
python3 abletonctl.py menu-search "Export Audio/Video"
```

Local UI commands need macOS Accessibility permissions and correct focus. Prefer bridge commands when possible.

## LOM Fallback

Use LOM when the CLI has no wrapper:

```sh
python3 abletonctl.py lom-inspect song.tracks[0]
python3 abletonctl.py lom-get song.tracks[0].name
python3 abletonctl.py lom-set song.tracks[0].color_index 5
python3 abletonctl.py lom-call song.create_scene --args '[1]'
```

Probe with `lom-inspect` before setting unknown properties. If a LOM operation is uncertain or destructive, dry-run and ask.
