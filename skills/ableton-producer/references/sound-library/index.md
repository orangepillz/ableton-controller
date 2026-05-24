# Sound Library Index

Use this library when a request asks for a named sound, loop, kit, drum break,
transition, ear-candy layer, or artist-adjacent bass music vocabulary. It is a
recipe catalog for building original sounds in Ableton Live with
`abletonctl`; it is not a request to clone any artist or copyrighted track.

## How To Load It

1. Load this index first.
2. Load `research-notes.md` when the request references Tipper, G Jones,
   Shlump, Detox Unit, Chris Lake, dubstep, tech house, glitch hop, or deep dub.
3. Load only the family file that contains the requested term.
4. Before executing, run `abletonctl session-snapshot`, resolve the correct
   template group, inspect target devices, and use `stock-controls` for exact
   parameter names or quantized values.

## Shared CLI Building Blocks

Probe and place:

```sh
abletonctl session-snapshot
abletonctl tracks
abletonctl devices --track "Mid Bass"
abletonctl stock-controls --device "Auto Filter"
```

Stock sound-design chain:

```sh
abletonctl device-add-stock --target-track "Mid Bass" --path "instruments/Operator"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Roar"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/EQ Eight"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Utility"
```

Repeatable movement:

```sh
abletonctl clip-automation-set-many --track "Mid Bass" --slot 0 --device "Auto Filter" --lanes '[{"param":"Frequency","steps":[{"time":0,"duration":0.5,"normalized":0.22},{"time":0.5,"duration":0.5,"normalized":0.78},{"time":1,"duration":1,"normalized":0.34},{"time":2,"duration":2,"normalized":0.66}],"clear":true},{"param":"Resonance","steps":[{"time":0,"duration":4,"normalized":0.32}],"clear":true}]'
```

Drum rack and sample workflow:

```sh
abletonctl browser-search "kick" --item samples --depth 5 --max-results 12
abletonctl device-add-stock --target-track "Drum Rack" --path "instruments/Drum Rack"
abletonctl drum-pad-load --track "Drum Rack" --pad C1 --item "samples/Kick.wav"
abletonctl clip-create-midi --track "Drum Rack" --slot 0 --length 4 --name "Drum Loop 01"
abletonctl midi-add-notes --track "Drum Rack" --slot 0 --notes '[{"pitch":36,"start_time":0,"duration":0.25,"velocity":118}]'
```

Audio chop and transition workflow:

```sh
abletonctl clip-create-audio --track "Breaks" --file "/absolute/path/source.wav" --start 64 --warping true --warp-mode beats
abletonctl clip-warp --track "Breaks" --arrangement-start 64 --warping true --warp-mode beats --clip-bpm 140
abletonctl clip-split --track "Breaks" --arrangement-start 64 --time 65
abletonctl clip-copy --source-track "Breaks" --source-arrangement-start 64 --dest-track "Breaks" --dest-start 68
```

## Term Map

### Bass And Synth Articulations

Load `bass-synths.md` for:

- Wubs
- Squelches
- Reeses
- Growls
- FM Screeches
- Blorps / Bloops
- Yois
- Sub Drops
- Neuro Bass Phrases
- Psybass Movement
- Percussive Bass Hits

### FX, Textures, Atmospheres, And Ear Candy

Load `fx-textures.md` for:

- Glitches
- Zaps
- Risers
- Downlifters / Fallers
- Granular Textures
- Foley Layers
- Atmospheric Pads
- Soundscapes
- Reverse FX
- Impacts / Slams
- Vocal Chops
- Stereo Ear Candy
- Phasey Textures
- Bitcrushed Artifacts
- Transient Smacks
- Swells
- Tonal Percussion
- Spectral FX
- Delay Throws
- Filtered Noise Washes
- Mechanical Textures
- Pitched Ambience

### Drums, Breaks, Kits, And Percussion

Load `drums-breaks.md` for:

- Breakbeats
- Amen-style Chops
- Halftime Grooves
- Glitch Drums
- Percussive Fills
- Drum Fills
- Rolls
- Snare Rushes
- Hat Trills
- Ghost Hats
- Offbeat Hats
- Shaker Layers
- Percussion Loops
- Rimshots
- Clicks / Ticks
- Clicks / Taps
- Foley Percussion
- Transient Percussion
- Textural Percussion
- Subby Kicks
- Punch Kicks
- Layered Snares
- Neuro Percussion
- Glitched Fills
- Reverse Snares
- Reverse Cymbals
- Crash Washes
- Ride Grooves
- Jungle Rolls
- Skitter Patterns
- Hybrid Acoustic/Electronic Drums

### Groove, Editing, And Arrangement Moves

Load `groove-structures.md` for:

- Percussive Fills
- Shuffles / Ghost Hats
- Ghost Notes
- Shuffle / Swing
- Microtiming Push/Pull
- Syncopation
- Polyrhythms
- Tuplet Fills
- Microfills
- Call-and-Response Drumming
- Question/Answer Fills
- Stop-Time Edits
- Fake Drops
- Stutter Edits
- Retriggers
- Ratchets
- Broken Beat Grooves
- IDM Programming
- Boom-Bap Influence
- Trip-Hop Grooves
- Funk Pocket Drumming
- Humanized Velocity
- Dynamic Accenting
- Percussive Ear Candy
- Stereo Percussion Movement
- Calligraphic Editing
- Breathing Grooves
- Elastic Timing

## Placement Defaults

- Bass source, mid-bass, leads, pads, and tonal synths: `Synths`.
- Pure sine/triangle low end and 808-style fundamentals: `Sub`.
- Drum racks, breaks, percussion loops, hats, snares, fills: `Drums`.
- Risers, impacts, sweeps, ambience, zaps, vocal ear candy: `FX`, unless the
  layer is source-specific.
- Vocal chops: `Vox` when they are the feature, `FX` when they are transitional
  one-shots.

Always compute `create-track --index` from the current `tracks` output before
executing. Never create top-level tracks outside the known template groups
without user approval.
