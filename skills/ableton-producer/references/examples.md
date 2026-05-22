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
python3 abletonctl.py status
python3 abletonctl.py tracks
python3 abletonctl.py devices --track "Kick"
python3 abletonctl.py devices --track "Sub"
python3 abletonctl.py devices --track "Drum Bus"
python3 abletonctl.py clips --track "Sub"
python3 abletonctl.py midi-get-notes --track "Sub" --slot 0 --start 0 --end 16
python3 abletonctl.py midi-transform-notes --track "Sub" --slot 0 --start 0 --end 16 --duration-scale 0.92
python3 abletonctl.py device-add-stock --target-track "Drum Bus" --path "audio_effects/Drum Buss"
python3 abletonctl.py device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
python3 abletonctl.py devices --track "Drum Bus"
python3 abletonctl.py devices --track "Bass Bus"
```

Producer reasoning: tighten the sub first, then add transient and controlled saturation. This makes the drop feel louder without flattening the master.

## "Create Tension Before The Buildup"

Intent: automate spectral, rhythmic, and spatial lift over the pre-drop range.

Assumptions: buildup is beat 48 to 64, drop starts at 64.

```sh
python3 abletonctl.py create-track --type audio --name "FX Riser"
python3 abletonctl.py device-add-stock --target-track "Build Bus" --path "audio_effects/Auto Filter"
python3 abletonctl.py stock-controls --device "Auto Filter" --control frequency
python3 abletonctl.py clip-stock-automation-set --track "Build Bus" --arrangement-start 48 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":4,"normalized":0.2},{"time":4,"duration":4,"normalized":0.55},{"time":8,"duration":4,"normalized":0.8},{"time":12,"duration":4,"normalized":0.95}]'
python3 abletonctl.py set-send --track "Snare Build" --send "A" --value 0.25
```

If no `Build Bus` clip exists at that arrangement start, create a new automation target clip or use track/device parameters instead.

## "Layer A Wide Supersaw Under This Lead"

Intent: create a support layer that widens the lead without masking sub or vocal.

```sh
python3 abletonctl.py create-track --type midi --name "Lead Wide Support"
python3 abletonctl.py device-add-stock --target-track "Lead Wide Support" --path "instruments/Instrument Rack"
python3 abletonctl.py device-add-stock --target-track "Lead Wide Support" --path "audio_effects/EQ Eight"
python3 abletonctl.py device-add-stock --target-track "Lead Wide Support" --path "audio_effects/Chorus-Ensemble"
python3 abletonctl.py clip-create-midi --track "Lead Wide Support" --slot 0 --length 8 --name "Wide Support Chords"
python3 abletonctl.py set-track --track "Lead Wide Support" --volume 0.58
```

Then copy or generate chord notes from the lead key. High-pass with EQ Eight after reading controls/params.

## "Make The Kick Cut Through The Sub"

Intent: make transient and fundamental separation.

```sh
python3 abletonctl.py devices --track "Kick"
python3 abletonctl.py devices --track "Sub"
python3 abletonctl.py clips --track "Sub"
python3 abletonctl.py midi-get-notes --track "Sub" --slot 0 --start 0 --end 8
python3 abletonctl.py midi-transform-notes --track "Sub" --slot 0 --start 0 --end 8 --duration-scale 0.9
python3 abletonctl.py device-add-stock --target-track "Sub" --path "audio_effects/Compressor"
python3 abletonctl.py stock-controls --device "Compressor"
```

If configuring sidechain, inspect Compressor sidechain controls and available routing before setting values.

## "Add Movement To The Bass"

Intent: automate timbre while preserving sub stability.

```sh
python3 abletonctl.py device-tree --track "Mid Bass" --depth 5
python3 abletonctl.py device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
python3 abletonctl.py set-stock-control --track "Mid Bass" --device "Auto Filter" --stock-device "Auto Filter" --control resonance --normalized 0.22
python3 abletonctl.py clip-stock-automation-set --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --clear --steps '[{"time":0,"duration":0.5,"normalized":0.22},{"time":0.5,"duration":0.5,"normalized":0.76},{"time":1,"duration":1,"normalized":0.38},{"time":2,"duration":2,"normalized":0.66}]'
python3 abletonctl.py clip-stock-automation-get --track "Mid Bass" --slot 0 --device "Auto Filter" --stock-device "Auto Filter" --control frequency --times 0,0.5,1,2,3
```

## "Turn This Into A Fakeout"

Intent: preserve expectation, remove the expected downbeat, then re-enter harder.

Requires approval because it may split, move, mute, or delete clips.

Dry-run commands:

```sh
python3 abletonctl.py clips --track "Drop Group"
python3 abletonctl.py clips --track "Build FX"
python3 abletonctl.py clip-copy --source-track "Build FX" --source-arrangement-start 56 --dest-track "Build FX" --dest-start 64 --length 4
python3 abletonctl.py clip-set --track "Kick" --arrangement-start 64 --muted true
python3 abletonctl.py clip-set --track "Sub" --arrangement-start 64 --muted true
```

Use clip muting before deletion so the fakeout is reversible.

## "Sidechain Everything Properly"

Intent: build or tune ducking across music/bass layers while keeping drums clear.

Plan first because this is a bulk routing/mix operation.

```sh
python3 abletonctl.py tracks
python3 abletonctl.py devices --track "Bass Bus"
python3 abletonctl.py devices --track "Music Bus"
python3 abletonctl.py device-add-stock --target-track "Bass Bus" --path "audio_effects/Compressor"
python3 abletonctl.py device-add-stock --target-track "Music Bus" --path "audio_effects/Compressor"
python3 abletonctl.py stock-controls --device "Compressor"
```

Then set sidechain controls only after identifying exact controls and source route.

## "Make The Drums Punchier"

Intent: transient shape and bus cohesion, not only volume.

```sh
python3 abletonctl.py devices --track "Drum Bus"
python3 abletonctl.py device-add-stock --target-track "Drum Bus" --path "audio_effects/Drum Buss"
python3 abletonctl.py device-add-stock --target-track "Drum Bus" --path "audio_effects/Glue Compressor"
python3 abletonctl.py set-track --track "Kick" --volume 0.84
python3 abletonctl.py set-track --track "Snare" --volume 0.82
python3 abletonctl.py devices --track "Drum Bus"
```

After adding devices, use `stock-controls` and `set-stock-control` for drive, transients, threshold, or dry/wet.

## "Humanize The Hi Hats"

Intent: keep groove anchors stable while adding velocity/probability variation.

```sh
python3 abletonctl.py midi-get-notes --track "Hats" --slot 0 --start 0 --end 8
python3 abletonctl.py midi-transform-notes --track "Hats" --slot 0 --start 0 --end 8 --pitch-min 42 --pitch-max 46 --velocity-deviation 9 --probability 0.94
python3 abletonctl.py midi-get-notes --track "Hats" --slot 0 --start 0 --end 8
```

For swing, read note IDs and update only offbeat hats.

## "Create A Call And Response Bass Pattern"

Intent: generate a playable phrase with space and contrast.

```sh
python3 abletonctl.py create-track --type midi --name "Call Response Bass"
python3 abletonctl.py device-add-stock --target-track "Call Response Bass" --path "instruments/Operator"
python3 abletonctl.py device-add-stock --target-track "Call Response Bass" --path "audio_effects/Auto Filter"
python3 abletonctl.py clip-create-midi --track "Call Response Bass" --slot 0 --length 8 --name "Call Response Bass 01"
python3 abletonctl.py midi-add-notes --track "Call Response Bass" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.5,"velocity":118},{"pitch":36,"start_time":1.5,"duration":0.25,"velocity":106},{"pitch":43,"start_time":2,"duration":0.5,"velocity":112},{"pitch":41,"start_time":3.25,"duration":0.25,"velocity":104},{"pitch":36,"start_time":4,"duration":0.75,"velocity":120},{"pitch":48,"start_time":6,"duration":0.25,"velocity":110},{"pitch":46,"start_time":6.5,"duration":0.25,"velocity":102},{"pitch":43,"start_time":7,"duration":0.5,"velocity":114}]'
python3 abletonctl.py midi-get-notes --track "Call Response Bass" --slot 0
```

Producer reasoning: the lower notes are the call and the higher, shorter notes answer it. The gaps leave space for drums and make the bass feel intentional.
