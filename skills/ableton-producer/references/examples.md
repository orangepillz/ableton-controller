# Examples

Each example shows intent translation, not a fixed recipe. Probe first and adjust names, bars, and devices to the current set.

## "Make This Drop Hit Harder"

Intent: increase contrast and low-end/transient impact without just raising master level.

Plan:
1. Probe tempo, tracks, and drop section clips.
2. Inspect kick, sub, bass bus, drum bus, and build FX chains.
3. Tighten kick/sub overlap.
4. Add or tune drum/bass bus processing.
5. Reduce pre-drop low end or tail.
6. Verify touched state.

Commands:

```sh
abletonctl status
abletonctl tracks
abletonctl devices --track "Kick"
abletonctl devices --track "Sub"
abletonctl devices --track "Drum Bus"
abletonctl clips --track "Sub"
abletonctl midi-get-notes --track "Sub" --slot 0 --start 0 --end 16
abletonctl midi-transform-notes --track "Sub" --slot 0 --start 0 --end 16 --duration-scale 0.92
abletonctl device-add-stock --target-track "Drum Bus" --path "audio_effects/Drum Buss"
abletonctl device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
abletonctl devices --track "Drum Bus"
abletonctl devices --track "Bass Bus"
```

Producer reasoning: tighten the sub first, then add transient and controlled saturation. This makes the drop feel louder without flattening the master.

## "Create Tension Before The Buildup"

Intent: automate spectral, rhythmic, and spatial lift over the pre-drop range.

Assumptions: buildup is beat 48 to 64, drop starts at 64.

```sh
abletonctl create-track --type audio --name "FX Riser"
abletonctl device-add-stock --target-track "Build Bus" --path "audio_effects/Auto Filter"
abletonctl stock-controls --device "Auto Filter" --control frequency
abletonctl arrangement-automation-set-many --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","duration":16,"from_normalized":0.2,"to_normalized":0.95,"curve":"ease-in-out","clear":true},{"param":"Resonance","duration":16,"from_normalized":0.12,"to_normalized":0.35,"steps":8,"clear":true}]'
abletonctl arrangement-automation-file-set --set-file "/path/to/project.als" --track "Build Bus" --arrangement-start 48 --clip-name "Noise Rise" --device "Auto Filter" --param Frequency --duration 16 --from-normalized 0.2 --to-normalized 0.95 --curve ease-in-out
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Frequency --times 0,4,8,12,15.5
abletonctl arrangement-automation-get --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --param Resonance --times 0,4,8,12,15.5
abletonctl set-send --track "Snare Build" --send "A" --value 0.25
```

If no `Build Bus` clip exists at that arrangement start, create a new automation target clip or use track/device parameters instead.

## "Layer A Wide Supersaw Under This Lead"

Intent: create a support layer that widens the lead without masking sub or vocal.

```sh
abletonctl create-track --type midi --name "Lead Wide Support"
abletonctl device-add-stock --target-track "Lead Wide Support" --path "instruments/Instrument Rack"
abletonctl device-add-stock --target-track "Lead Wide Support" --path "audio_effects/EQ Eight"
abletonctl device-add-stock --target-track "Lead Wide Support" --path "audio_effects/Chorus-Ensemble"
abletonctl clip-create-midi --track "Lead Wide Support" --slot 0 --length 8 --name "Wide Support Chords"
abletonctl set-track --track "Lead Wide Support" --volume 0.58
```

Then copy or generate chord notes from the lead key. High-pass with EQ Eight after reading controls/params.

## "Make The Kick Cut Through The Sub"

Intent: make transient and fundamental separation.

```sh
abletonctl devices --track "Kick"
abletonctl devices --track "Sub"
abletonctl clips --track "Sub"
abletonctl midi-get-notes --track "Sub" --slot 0 --start 0 --end 8
abletonctl midi-transform-notes --track "Sub" --slot 0 --start 0 --end 8 --duration-scale 0.9
abletonctl device-add-stock --target-track "Sub" --path "audio_effects/Compressor"
abletonctl stock-controls --device "Compressor"
```

If configuring sidechain, inspect Compressor sidechain controls and available routing before setting values.

## "Add Movement To The Bass"

Intent: automate timbre while preserving sub stability.

```sh
abletonctl device-tree --track "Mid Bass" --depth 5
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
abletonctl set-stock-control --track "Mid Bass" --device "Auto Filter" --stock-device "Auto Filter" --control resonance --normalized 0.22
abletonctl clip-stock-automation-set --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":0.5,"normalized":0.22},{"time":0.5,"duration":0.5,"normalized":0.76},{"time":1,"duration":1,"normalized":0.38},{"time":2,"duration":2,"normalized":0.66}]'
abletonctl clip-stock-automation-get --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --times 0,0.5,1,2,3
```

## "Turn This Into A Fakeout"

Intent: preserve expectation, remove the expected downbeat, then re-enter harder.

Requires approval because it may split, move, mute, or delete clips.

Dry-run commands:

```sh
abletonctl clips --track "Drop Group"
abletonctl clips --track "Build FX"
abletonctl clip-copy --source-track "Build FX" --source-arrangement-start 56 --dest-track "Build FX" --dest-start 64 --length 4
abletonctl clip-set --track "Kick" --arrangement-start 64 --muted true
abletonctl clip-set --track "Sub" --arrangement-start 64 --muted true
```

Use clip muting before deletion so the fakeout is reversible.

## "Sidechain Everything Properly"

Intent: build or tune ducking across music/bass layers while keeping drums clear.

Plan first because this is a bulk routing/mix operation.

```sh
abletonctl tracks
abletonctl devices --track "Bass Bus"
abletonctl devices --track "Music Bus"
abletonctl device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
abletonctl device-add-stock --target-track "Music Bus" --path "audio_effects/Compressor"
abletonctl stock-controls --device "Compressor"
```

Then set sidechain controls only after identifying exact controls and source route.

## "Make The Drums Punchier"

Intent: transient shape and bus cohesion, not only volume.

```sh
abletonctl devices --track "Drum Bus"
abletonctl device-add-stock --target-track "Drum Bus" --path "audio_effects/Drum Buss"
abletonctl device-add-stock --target-track "Drum Bus" --path "audio_effects/Glue Compressor"
abletonctl set-track --track "Kick" --volume 0.84
abletonctl set-track --track "Snare" --volume 0.82
abletonctl devices --track "Drum Bus"
```

After adding devices, use `stock-controls` and `set-stock-control` for drive, transients, threshold, or dry/wet.

## "Humanize The Hi Hats"

Intent: keep groove anchors stable while adding velocity/probability variation.

```sh
abletonctl midi-get-notes --track "Hats" --slot 0 --start 0 --end 8
abletonctl midi-transform-notes --track "Hats" --slot 0 --start 0 --end 8 --pitch-min 42 --pitch-max 46 --velocity-deviation 9 --probability 0.94
abletonctl midi-get-notes --track "Hats" --slot 0 --start 0 --end 8
```

For swing, read note IDs and update only offbeat hats.

## "Create A Call And Response Bass Pattern"

Intent: generate a playable phrase with space and contrast.

```sh
abletonctl create-track --type midi --name "Call Response Bass"
abletonctl device-add-stock --target-track "Call Response Bass" --path "instruments/Operator"
abletonctl device-add-stock --target-track "Call Response Bass" --path "audio_effects/Auto Filter"
abletonctl clip-create-midi --track "Call Response Bass" --slot 0 --length 8 --name "Call Response Bass 01"
abletonctl midi-add-notes --track "Call Response Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":118},{"pitch":36,"start_time":1.5,"duration":0.25,"velocity":106},{"pitch":43,"start_time":2,"duration":0.5,"velocity":112},{"pitch":41,"start_time":3.25,"duration":0.25,"velocity":104},{"pitch":36,"start_time":4,"duration":0.75,"velocity":120},{"pitch":48,"start_time":6,"duration":0.25,"velocity":110},{"pitch":46,"start_time":6.5,"duration":0.25,"velocity":102},{"pitch":43,"start_time":7,"duration":0.5,"velocity":114}]'
abletonctl midi-get-notes --track "Call Response Bass" --slot 0
```

Producer reasoning: the lower notes are the call and the higher, shorter notes answer it. The gaps leave space for drums and make the bass feel intentional.
