# CLI Command Map

Prefer these wrapped commands before using raw LOM or UI automation.

## Core And State

```sh
abletonctl ping
abletonctl status
abletonctl tracks
abletonctl selected --devices
abletonctl select-track --track "Bass"
abletonctl copilot-intent "make the drop bass move more"
abletonctl tempo
abletonctl tempo --set 140
abletonctl play
abletonctl stop
abletonctl continue
abletonctl undo
abletonctl redo
```

`copilot-intent` is local and read-only. It matches a request against
`.ableton-copilot/memory.json` and returns personalized planning hints before you
choose probes, macros, or edit commands. Its `profile_hints` summarize learned
arrangement phase signatures, roles, shape, routing, and automation evidence
from historical projects.

## Tracks, Scenes, And Routing

```sh
abletonctl create-track --type midi --name "Drop Bass"
abletonctl create-track --type audio --name "Resample Print"
abletonctl create-track --type return --name "Short Verb"
abletonctl duplicate-track --track "Lead"
abletonctl delete-track --track "Scratch"
abletonctl create-scene --name "Drop"
abletonctl fire-scene --scene "Drop"
abletonctl locators
abletonctl set-locator --time 64 --name "02 Main Drop"
abletonctl set-routing --track "Resample Print" --direction input --type "Resampling"
abletonctl set-routing --track "Bass" --direction output --type "Bass Bus"
```

Use `set-routing` after reading available route names from a failed attempt or Live state. Routing names are matched by displayed name.
Use `locators` before `set-locator`; renaming locators changes the Live set, so
prefer a rendered plan for multi-locator edits.

For grouping, first try a LOM-backed plan:

```sh
abletonctl lom-inspect song
abletonctl lom-call song.create_group_track --args '[0]'
abletonctl lom-set song.tracks[0].name "Drum Bus"
```

Only use UI grouping with `menu-search "Group Tracks"` or `hotkey cmd+g` when selection is known.

## Mixer And Sends

```sh
abletonctl set-track --track "Kick" --volume 0.82 --pan 0
abletonctl set-track --track "Bass" --mute false --solo false --arm false
abletonctl set-send --track "Snare" --send "A" --value 0.18
```

Use conservative values. In Ableton API mixer values are often normalized, so prefer small deltas or probe returned parameter ranges when exact gain in dB matters.

## Devices And Stock Controls

```sh
abletonctl devices --track "Bass"
abletonctl device-tree --track "Bass" --depth 5
abletonctl device-add-stock --target-track "Bass" --path "audio_effects/EQ Eight" --target-index 0
abletonctl device-add-stock --target-track "Bass" --name "Auto Filter" --root audio_effects
abletonctl device-move --source-track "Bass" --source-device "Auto Filter" --target-track "Bass" --target-index 0
abletonctl device-delete --track "Bass" --device "Auto Filter"
abletonctl drum-pad-load --track "Drums" --device "Drum Rack" --pad C1 --item "samples/Kick.wav"
abletonctl params --track "Bass" --device "EQ Eight"
```

Nested racks require `device-tree` paths:

```sh
abletonctl device-add-stock --target-path "song.tracks[3].devices[0].chains[0]" --path "audio_effects/Compressor"
abletonctl set-param --device-path "song.tracks[3].devices[0].chains[0].devices[0]" --param Threshold --normalized 0.35
```

For Drum Rack kit building, use `drum-pad-load` after `browser-search` identifies
a loadable sample, instrument, or preset path. It targets the requested pad note
and refuses to overwrite existing pad chains unless `--clear` is present.

Stock registry commands:

```sh
abletonctl stock-devices --summary
abletonctl stock-devices --root audio_effects --query filter
abletonctl stock-controls --device "Auto Filter" --control frequency
abletonctl set-stock-control --track "Bass" --device "Auto Filter" --stock-device "Auto Filter" --control frequency --normalized 0.42
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
abletonctl clip-create-midi --track "Bass" --slot 0 --length 4 --name "Call Bass"
abletonctl clip-create-midi --track "Bass" --start 64 --length 8 --name "Drop Bass"
abletonctl clip-create-audio --track "Riser" --file "/absolute/path/riser.wav" --start 56 --warping true --warp-mode complex-pro
abletonctl clip-set --track "Bass" --slot 0 --looping true --loop-start 0 --loop-end 4 --end-marker 4
abletonctl clip-copy --source-track "Bass" --source-slot 0 --dest-track "Bass" --dest-start 64
abletonctl clip-split --track "Bass" --arrangement-start 64 --time 68
```

Audio warp:

```sh
abletonctl clip-warp --track "Vocal Chop" --arrangement-start 32 --warping true --warp-mode complex-pro --pitch-coarse -12
abletonctl clip-warp-marker-add --track "Break" --arrangement-start 16 --beat-time 4 --sample-time 3.85
abletonctl clip-warp-marker-move --track "Break" --arrangement-start 16 --beat-time 4 --to-beat 4.25
```

Warp modes: `beats`, `tones`, `texture`, `repitch`, `complex`, `rex`, `complex-pro`.

## MIDI Notes

Note objects support pitch, start_time, duration, velocity, mute, probability, velocity_deviation, and release_velocity.

```sh
abletonctl midi-add-notes --track "Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":112}]'
abletonctl midi-get-notes --track "Bass" --slot 0 --start 0 --end 4
abletonctl midi-replace-notes --track "Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":1,"velocity":112}]'
abletonctl midi-transform-notes --track "Hats" --slot 0 --start 0 --end 4 --pitch-min 42 --pitch-max 46 --velocity-deviation 10 --probability 0.92
abletonctl midi-duplicate-region --track "Bass" --slot 0 --start 0 --length 2 --destination-time 2 --transpose 7
```

Use `midi-replace-notes` only after approval unless the clip was just created for the workflow.

## Automation

Automation steps and breakpoint events use clip time. Use `value` for raw parameter values
and `normalized` for 0..1 movement. Runtime `--curve` and event-level
`curve_coefficients` create true Ableton breakpoint curves in the open set; no close/reopen
cycle is required. Use saved-set commands only for offline inspection or repair.

```sh
abletonctl clip-stock-automation-set --track "Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":1,"normalized":0.18},{"time":1,"duration":1,"normalized":0.72}]'
abletonctl arrangement-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --steps 8 --clear
abletonctl arrangement-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --events '[{"time":0,"normalized":0.2,"curve_coefficients":{"x1":0.42,"y1":0,"x2":0.58,"y2":1}},{"time":16,"normalized":0.95}]' --clear
abletonctl arrangement-automation-set-many --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","duration":16,"from_normalized":0.2,"to_normalized":0.95,"curve":"ease-in-out","clear":true},{"param":"Resonance","duration":16,"from_normalized":0.12,"to_normalized":0.35,"steps":8,"clear":true}]'
abletonctl arrangement-automation-set-many --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","events":[{"time":0,"normalized":0.2,"curve_coefficients":{"x1":0.42,"y1":0,"x2":0.58,"y2":1}},{"time":8,"normalized":0.45,"curve_coefficients":{"x1":0.55,"y1":0,"x2":1,"y2":1}},{"time":16,"normalized":0.95}],"clear":true},{"param":"Resonance","duration":16,"from_normalized":0.12,"to_normalized":0.35,"steps":8,"clear":true}]'
abletonctl arrangement-automation-file-set --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --clip-name "Noise Rise" --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --curve ease-in-out
abletonctl arrangement-automation-file-get --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --times 0,4,8,12,15.5
abletonctl clip-automation-get --track "Bass" --slot 0 --device "Auto Filter" --param Frequency --times 0,0.5,1,1.5
abletonctl clip-stock-automation-clear --track "Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency
```

Clip automation is preferred for repeatable bass movement, filter sweeps, fakeouts, fills, and transitions.
Use `arrangement-automation-set` when the request describes a buildup, drop, fakeout, or transition over an Arrangement range and a clip already exists at `--arrangement-start`.
Use `arrangement-automation-set-many` for coupled lanes on the same MIDI Arrangement clip, especially cutoff plus resonance, because missing or hidden Arrangement lanes can be materialized together without discarding the first lane.
For a request like "add a curve at bar 17" on a clip starting at beat 8, convert to clip-relative time `9` in the event JSON.
Use `arrangement-automation-file-set` only for offline saved-set repair; do normal curve creation and editing through runtime Arrangement commands while Live is open.
Use `arrangement-automation-get` after every Arrangement automation write. Times are clip-relative: if a clip starts at Arrangement beat 48, `--times 0,8,15.5` samples beats 48, 56, and 63.5.
Run multiple sampled Arrangement automation reads sequentially, not in parallel, because hidden Arrangement lanes are read by briefly moving and restoring Live's playhead.

## Browser And Local UI

```sh
abletonctl browser-roots
abletonctl browser-search "Operator" --item instruments --depth 4
abletonctl browser-load "instruments/Operator"
abletonctl show-view Browser
abletonctl focus-view Session
abletonctl hotkey cmd+s
abletonctl hotkey cmd+g
abletonctl hotkey cmd+shift+r
abletonctl menu-search "Export Audio/Video"
```

Local UI commands need macOS Accessibility permissions and correct focus. Prefer bridge commands when possible.

## LOM Fallback

Use LOM when the CLI has no wrapper:

```sh
abletonctl lom-inspect song.tracks[0]
abletonctl lom-get song.tracks[0].name
abletonctl lom-set song.tracks[0].color_index 5
abletonctl lom-call song.create_scene --args '[1]'
```

Probe with `lom-inspect` before setting unknown properties. If a LOM operation is uncertain or destructive, dry-run and ask.
