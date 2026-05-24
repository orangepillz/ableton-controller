# Workflow Primitives

Compose these primitives into larger production workflows.

For repeated workflows, render an editable plan template first:

```sh
abletonctl workflow-macro list
abletonctl workflow-macro render bass-movement --track "Mid Bass" --slot 0
abletonctl workflow-macro render call-response-bass --track "Call Response Bass" --slot 0 --length 8
abletonctl workflow-macro render bass-resampling-pass --track "Mid Bass" --start 64 --length 8 --print-track "Bass Resample Print"
abletonctl workflow-macro render drum-punch-bus --memory .ableton-copilot/memory.json
abletonctl workflow-macro render personalized-space-chain --track "Vox Throw"
abletonctl workflow-macro render arrangement-marker-naming
abletonctl workflow-macro render arrangement-phase-scaffold --scene-index 0
abletonctl workflow-macro render glitch-drum-transition --track "Zap Rack" --secondary-track "Perc Rack" --synth-track "Lead Synth" --length 8
abletonctl workflow-macro render mix-bus-control --track Master --memory .ableton-copilot/memory.json
```

Treat workflow macros as starting points. Inspect the rendered commands, adjust
track names and ranges to the current set, then run the plan renderer before
execution.

Before selecting a macro for a broad natural-language request, query the
personalized intent memory:

```sh
abletonctl copilot-intent "make a shimmer riser that inhales before the drop"
```

Use `orchestration`, including `execution_plan`, `recovery_plan`, `command_sources`, `suppressed_commands`,
ranked `likely_followups`, `clarification_policy`, `safety_checks`, and `verification_steps`, plus
`profile_hints.workflow_macros`; then verify the set with `session-snapshot`.
When `drum-kit-building`, `bass-movement`, or `riser-transition` matches, prefer the recommended macros
for drum bus punch, call/response variation, or inhale riser sketches before inventing those sequences
from scratch. For arrangement requests, review `profile_hints.section_label_proposals` before renaming locators or scaffolding scenes.
When `profile_hints.revision_requests` or refinement patterns appear, treat the
message as an edit to the current plan/session context before asking fresh setup
questions. For example, pad-mapping corrections mean drum-rack plans should
explicitly verify that samples land on distinct pads.
When `orchestration.target_aliases` or `profile_hints.target_aliases` appear,
use matched aliases such as `BD`, `SD`, `SC Trigger`, `TR8S`, or return tracks
to reduce clarification, but still verify the current set before editing.
When `orchestration.device_chain_preferences` or `profile_hints` includes device
chains, treat them as confidence-scored sound-design or mixing starts, then
verify stock-device availability and current track context before adding devices.
For mix or master prep, render `mix-bus-control` first. It creates an
inspectable preview chain and reads Utility, EQ Eight, Glue Compressor, Limiter,
and Spectrum controls without setting loudness or saving the set.
For spatial chain requests, render the personalized space-chain macro first and
adapt the result to the target track:

```sh
abletonctl workflow-macro render personalized-space-chain --track "Vox Throw"
```

For broad arrangement requests with no existing section labels, render the
personalized phase scaffold first. It creates named scenes based on learned
early/main/late role signatures without moving existing clips:

```sh
abletonctl workflow-macro render arrangement-phase-scaffold --scene-index 0
```

When the set already has numbered Arrangement locators, render the marker
naming macro first. It reads persisted `project.arrangement-marker`,
`project.arrangement-phase`, and role memory, proposes confidence-scored musical
names for the learned marker beat anchors, and should be reviewed before
execution because it renames locator state:

```sh
abletonctl workflow-macro render arrangement-marker-naming
abletonctl workflow-macro render arrangement-marker-naming --memory .ableton-copilot/memory.json
```

## New Musical Part

1. Create or identify the target track.
2. Add an instrument or rack.
3. Create a clip at the target slot or arrangement start.
4. Add notes with a musically intentional rhythm and range.
5. Add basic processing.
6. Verify notes, devices, and mixer state.

Example:

```sh
abletonctl create-track --type midi --name "Call Bass"
abletonctl device-add-stock --target-track "Call Bass" --path "instruments/Operator"
abletonctl device-add-stock --target-track "Call Bass" --path "audio_effects/Auto Filter"
abletonctl clip-create-midi --track "Call Bass" --slot 0 --length 4 --name "Call Bass 01"
abletonctl midi-add-notes --track "Call Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":115},{"pitch":36,"start_time":1.5,"duration":0.25,"velocity":102}]'
abletonctl midi-get-notes --track "Call Bass" --slot 0
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
abletonctl midi-transform-notes --track "Hats" --slot 0 --start 0 --end 8 --pitch-min 42 --pitch-max 46 --velocity-deviation 8 --probability 0.94
```

If timing needs swing, update specific note starts with `midi-update-notes` after reading note IDs.

## Kick And Sub Separation

Goal: make the kick cut through without destroying sub weight.
When rendering the macro with personalized memory, default targets can resolve
from learned aliases such as `BD` for kick and `18-Basic Organ Bass` for sub:

```sh
abletonctl workflow-macro render kick-sub-separation --memory .ableton-copilot/memory.json
```

1. Probe kick, sub, and bass bus chains.
2. Put high-pass or low-shelf shaping on non-sub bass layers.
3. Add sidechain-capable compression or volume shaping to sub/bass bus.
4. Shorten or move sub MIDI notes away from kick transients where possible.
5. Verify with clip notes and parameter reads.

Practical CLI moves:

```sh
abletonctl device-add-stock --target-track "Sub" --path "audio_effects/EQ Eight"
abletonctl device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
abletonctl midi-transform-notes --track "Sub" --slot 0 --start 0 --end 16 --duration-scale 0.92
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
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
abletonctl clip-stock-automation-set --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":0.5,"normalized":0.22},{"time":0.5,"duration":0.5,"normalized":0.78},{"time":1,"duration":1,"normalized":0.35},{"time":2,"duration":2,"normalized":0.68}]'
```

For coupled Arrangement filter sweeps, write the related lanes together and verify
each lane with clip-relative times:

```sh
abletonctl arrangement-automation-set-many --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","duration":16,"from_normalized":0.2,"to_normalized":0.95,"curve":"ease-in-out","clear":true},{"param":"Resonance","duration":16,"from_normalized":0.12,"to_normalized":0.35,"steps":8,"clear":true}]'
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --times 0,4,8,12,15.5
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Resonance --times 0,4,8,12,15.5
```

For Arrangement transitions that need true Ableton curves, patch the saved set with
`arrangement-automation-file-set` while Live is closed, then reopen and verify with
sampled `arrangement-automation-get` values:

```sh
abletonctl arrangement-automation-file-set --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --clip-name "Noise Rise" --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --curve ease-in-out
abletonctl arrangement-automation-file-get --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --times 0,4,8,12,16
```

Use runtime `arrangement-automation-set --curve` or event-level `curve_coefficients`
as a breakpoint payload builder, but saved-set curve verification is the authority because
Live's runtime API can normalize hidden Arrangement curve coefficients.

## Drum Rack And Sampler Work

Use wrapped commands for the deterministic parts and browser/LOM only when needed:

1. Create or locate a MIDI track.
2. Add `Drum Rack`, `Simpler`, `Sampler`, or a preset from the browser.
3. Use `device-tree` to identify rack chains and nested devices.
4. Load exact pads with `drum-pad-load` when a browser path is known.
5. Program the MIDI pattern with exact note objects.

```sh
abletonctl create-track --type midi --name "Drop Drum Rack"
abletonctl device-add-stock --target-track "Drop Drum Rack" --path "instruments/Drum Rack"
abletonctl browser-search "Kick" --item samples --depth 5 --max-results 12
abletonctl drum-pad-load --track "Drop Drum Rack" --pad C1 --item "samples/Kick.wav"
abletonctl drum-pad-load --track "Drop Drum Rack" --pad D1 --item "samples/Snare.wav"
abletonctl device-tree --track "Drop Drum Rack" --depth 5
abletonctl clip-create-midi --track "Drop Drum Rack" --slot 0 --length 4 --name "Drop Drums 01"
abletonctl midi-add-notes --track "Drop Drum Rack" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.25,"velocity":118},{"pitch":38,"start_time":2,"duration":0.25,"velocity":120},{"pitch":42,"start_time":0.5,"duration":0.125,"velocity":82}]'
```

Use `--clear` only after approval when a pad already contains chains. Without it,
the command protects existing pad chains and reports the conflict.

For drum bus punch processing, render the macro with personalized memory so the
default target can resolve from learned aliases such as `Drums` or `TR8S`:

```sh
abletonctl workflow-macro render drum-punch-bus --memory .ableton-copilot/memory.json
```

For zap/perc glitch requests with stutters and a bar-3 handoff, render the
personalized macro first. Replace the placeholder `samples/<...>` paths with
actual `browser-search` results before executing. When personalized refinement
memory includes pad-mapping corrections, the rendered plan adds explicit
`device-tree` checks after `drum-pad-load` so each sample can be verified on a
distinct Drum Rack pad before MIDI is written:

```sh
abletonctl workflow-macro render glitch-drum-transition --track "Zap Rack" --secondary-track "Perc Rack" --synth-track "Lead Synth" --length 8 --memory .ableton-copilot/memory.json
```

For chopped audio workflows, create an audio clip first, warp it, then either keep it as arranged audio or prepare a sampler/rack target.

## Rack And Macro Setup

Rack generation is deterministic; macro mapping depends on what the Live Object Model exposes for the loaded rack.

```sh
abletonctl device-add-stock --target-track "Bass" --path "audio_effects/Audio Effect Rack"
abletonctl device-tree --track "Bass" --depth 6
abletonctl set-stock-control --track "Bass" --device "Audio Effect Rack" --stock-device "Audio Effect Rack" --control macro_1 --value 64
abletonctl lom-inspect song.tracks[0].devices[0]
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
Use `arrangement-automation-set` for long filter, distortion, send, or macro moves over an existing Arrangement clip.

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
abletonctl create-track --type audio --name "Resample Print"
abletonctl set-routing --track "Resample Print" --direction input --type "Resampling"
abletonctl set-track --track "Resample Print" --arm true
```

Plan before recording. Confirm bar range, source buses, whether to freeze current devices, and whether saving/exporting is allowed.

For a bass sound-design print pass, render the reusable macro:

```sh
abletonctl workflow-macro render bass-resampling-pass --track "Mid Bass" --start 64 --length 8 --print-track "Bass Resample Print"
```

## Cleanup And Organization

Use after creative edits:

- Name tracks by role: `DRM Kick`, `DRM Snare`, `SUB`, `BASS Mid`, `MUS Lead`, `FX Riser`.
- Place buses near source tracks.
- Mute unused scratch material instead of deleting unless approved.
- Set return names by function: `A Short Verb`, `B Dub Delay`, `C Parallel Crush`.
- Turn off accidental solos/arms.

```sh
abletonctl set-track --track "Scratch Bass" --mute true --solo false --arm false
abletonctl create-scene --name "Drop - Clean"
```
