# Workflow Primitives

Compose these primitives into larger production workflows.

## New Musical Part

1. Create or identify the target track.
2. Add an instrument or rack.
3. Create a clip at the target slot or arrangement start.
4. Add notes with a musically intentional rhythm and range.
5. Add basic processing.
6. Verify notes, devices, and mixer state.

Example:

```sh
python3 abletonctl.py create-track --type midi --name "Call Bass"
python3 abletonctl.py device-add-stock --target-track "Call Bass" --path "instruments/Operator"
python3 abletonctl.py device-add-stock --target-track "Call Bass" --path "audio_effects/Auto Filter"
python3 abletonctl.py clip-create-midi --track "Call Bass" --slot 0 --length 4 --name "Call Bass 01"
python3 abletonctl.py midi-add-notes --track "Call Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":115},{"pitch":36,"start_time":1.5,"duration":0.25,"velocity":102}]'
python3 abletonctl.py midi-get-notes --track "Call Bass" --slot 0
```

## Call And Response Bass Pattern

Use two phrases with contrast:

- Call: lower, more stable, starts on strong beat.
- Response: higher or timbrally brighter, later in the bar, often with shorter notes.
- Leave holes for kick and snare. Do not fill every 1/16 unless the genre calls for machine-gun density.

4-bar dubstep pattern at 140:

```json
[
  {"pitch":36,"start_time":0,"duration":0.5,"velocity":118},
  {"pitch":36,"start_time":1.5,"duration":0.25,"velocity":106},
  {"pitch":43,"start_time":2.0,"duration":0.5,"velocity":112},
  {"pitch":41,"start_time":3.25,"duration":0.25,"velocity":104},
  {"pitch":36,"start_time":4.0,"duration":0.75,"velocity":120},
  {"pitch":48,"start_time":6.0,"duration":0.25,"velocity":110},
  {"pitch":46,"start_time":6.5,"duration":0.25,"velocity":102},
  {"pitch":43,"start_time":7.0,"duration":0.5,"velocity":114},
  {"pitch":36,"start_time":8.0,"duration":0.5,"velocity":118},
  {"pitch":43,"start_time":10.0,"duration":0.5,"velocity":112},
  {"pitch":41,"start_time":11.5,"duration":0.25,"velocity":106},
  {"pitch":36,"start_time":12.0,"duration":1.0,"velocity":120},
  {"pitch":48,"start_time":14.0,"duration":0.25,"velocity":112},
  {"pitch":43,"start_time":14.5,"duration":0.25,"velocity":108},
  {"pitch":36,"start_time":15.5,"duration":0.25,"velocity":120}
]
```

Transpose to the requested key by moving root notes while preserving contour.

## Humanize Hats

1. Read the target notes.
2. Apply small velocity deviation and probability to hats, not kick/snare anchors.
3. For a new clip, directly write varied velocities and small timing offsets.
4. Keep the groove intentional: late offbeats for swing, tight downbeats for energy.

```sh
python3 abletonctl.py midi-transform-notes --track "Hats" --slot 0 --start 0 --end 8 --pitch-min 42 --pitch-max 46 --velocity-deviation 8 --probability 0.94
```

If timing needs swing, update specific note starts with `midi-update-notes` after reading note IDs.

## Kick And Sub Separation

Goal: make the kick cut through without destroying sub weight.

1. Probe kick, sub, and bass bus chains.
2. Put high-pass or low-shelf shaping on non-sub bass layers.
3. Add sidechain-capable compression or volume shaping to sub/bass bus.
4. Shorten or move sub MIDI notes away from kick transients where possible.
5. Verify with clip notes and parameter reads.

Practical CLI moves:

```sh
python3 abletonctl.py device-add-stock --target-track "Sub" --path "audio_effects/EQ Eight"
python3 abletonctl.py device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
python3 abletonctl.py midi-transform-notes --track "Sub" --slot 0 --start 0 --end 16 --duration-scale 0.92
```

Use sidechain controls from `stock-controls --device "Compressor"` when configuring exact sidechain parameters.

## Movement Automation

Use automation when the request says movement, evolving, talking, vowel, wobble, growl, sweep, tension, fakeout, or cinematic transition.

1. Add or find movement device: `Auto Filter`, `Roar`, `Phaser-Flanger`, `Chorus-Ensemble`, `Echo`, or rack macro.
2. Read controls.
3. Set base tone.
4. Write clip automation with stepped or ramped values.
5. Read back automation samples.

```sh
python3 abletonctl.py device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
python3 abletonctl.py clip-stock-automation-set --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":0.5,"normalized":0.22},{"time":0.5,"duration":0.5,"normalized":0.78},{"time":1,"duration":1,"normalized":0.35},{"time":2,"duration":2,"normalized":0.68}]'
```

## Drum Rack And Sampler Work

Use wrapped commands for the deterministic parts and browser/LOM only when needed:

1. Create or locate a MIDI track.
2. Add `Drum Rack`, `Simpler`, `Sampler`, or a preset from the browser.
3. Use `device-tree` to identify rack chains and nested devices.
4. Program the MIDI pattern with exact note objects.
5. For pad/sample loading, use `browser-search` and `browser-load` when the sample/preset path is visible. If direct sample-to-pad placement is not exposed, state that the plan creates the rack/pattern and needs a future CLI extension or focused UI action for exact pad loading.

```sh
python3 abletonctl.py create-track --type midi --name "Drop Drum Rack"
python3 abletonctl.py device-add-stock --target-track "Drop Drum Rack" --path "instruments/Drum Rack"
python3 abletonctl.py device-tree --track "Drop Drum Rack" --depth 5
python3 abletonctl.py clip-create-midi --track "Drop Drum Rack" --slot 0 --length 4 --name "Drop Drums 01"
python3 abletonctl.py midi-add-notes --track "Drop Drum Rack" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.25,"velocity":118},{"pitch":38,"start_time":2,"duration":0.25,"velocity":120},{"pitch":42,"start_time":0.5,"duration":0.125,"velocity":82}]'
```

For chopped audio workflows, create an audio clip first, warp it, then either keep it as arranged audio or prepare a sampler/rack target.

## Rack And Macro Setup

Rack generation is deterministic; macro mapping depends on what the Live Object Model exposes for the loaded rack.

```sh
python3 abletonctl.py device-add-stock --target-track "Bass" --path "audio_effects/Audio Effect Rack"
python3 abletonctl.py device-tree --track "Bass" --depth 6
python3 abletonctl.py set-stock-control --track "Bass" --device "Audio Effect Rack" --stock-device "Audio Effect Rack" --control macro_1 --value 64
python3 abletonctl.py lom-inspect song.tracks[0].devices[0]
```

If macro mapping methods are available from `lom-inspect`, use `lom-call` in a dry-run plan first. If not, create the rack skeleton, add devices, set sensible macro values, and clearly state that exact macro mapping is not yet exposed by the current CLI wrapper.

## Buildup Tension

Layer tension in several dimensions:

- Rhythm density: duplicate or add 1/8 to 1/16 percussion.
- Pitch: risers, pitch automation, transposed fills.
- Spectrum: high-pass, low-pass opening, noise or reverb tail.
- Space: increasing reverb/delay send, then cut before impact.
- Silence: remove the last 1/4 to 1 bar before the drop for a fakeout.

Use scene names and arrangement starts to avoid losing section context.

## Fakeout

1. Identify expected impact bar.
2. Copy or split the pre-drop material.
3. Mute/remove the expected downbeat hit or delay it by 1/2 to 1 bar.
4. Add silence, vocal chop, reverse crash, or filtered tail.
5. Bring the real drop back with stronger transient contrast.

Any delete or clear step requires approval unless editing a newly created scratch clip.

## Resampling Prep

The CLI can set up resampling tracks and routing, but recording and export may need UI/menu automation.

```sh
python3 abletonctl.py create-track --type audio --name "Resample Print"
python3 abletonctl.py set-routing --track "Resample Print" --direction input --type "Resampling"
python3 abletonctl.py set-track --track "Resample Print" --arm true
```

Plan before recording. Confirm bar range, source buses, whether to freeze current devices, and whether saving/exporting is allowed.

## Cleanup And Organization

Use after creative edits:

- Name tracks by role: `DRM Kick`, `DRM Snare`, `SUB`, `BASS Mid`, `MUS Lead`, `FX Riser`.
- Place buses near source tracks.
- Mute unused scratch material instead of deleting unless approved.
- Set return names by function: `A Short Verb`, `B Dub Delay`, `C Parallel Crush`.
- Turn off accidental solos/arms.

```sh
python3 abletonctl.py set-track --track "Scratch Bass" --mute true --solo false --arm false
python3 abletonctl.py create-scene --name "Drop - Clean"
```
