# Drums, Breaks, Kits, And Percussion

These recipes cover drum sounds, break processing, kit construction, and
percussion layers. Default placement is `Drums`. When a recipe requires samples,
use `browser-search` first and replace placeholder paths with actual browser
results.

## Core Drum Rack Workflow

```sh
abletonctl device-add-stock --target-track "Drop Drums" --path "instruments/Drum Rack"
abletonctl browser-search "kick" --item samples --depth 5 --max-results 12
abletonctl browser-search "snare" --item samples --depth 5 --max-results 12
abletonctl drum-pad-load --track "Drop Drums" --pad C1 --item "samples/Kick.wav"
abletonctl drum-pad-load --track "Drop Drums" --pad D1 --item "samples/Snare.wav"
abletonctl device-tree --track "Drop Drums" --depth 5
```

Core bus punch:

```sh
abletonctl device-add-stock --target-track "Drums" --path "audio_effects/Drum Buss"
abletonctl device-add-stock --target-track "Drums" --path "audio_effects/Glue Compressor"
abletonctl stock-controls --device "Drum Buss"
abletonctl stock-controls --device "Glue Compressor"
```

## Breakbeats

Chopped funk drum loops rearranged into new rhythms.

CLI moves:
- Load the break as an audio clip and warp in `beats` first.
- Use warp markers to correct only the moments that drift.
- Split, copy, reverse, and rearrange small segments for new phrasing.

```sh
abletonctl clip-create-audio --track "Breaks" --file "/absolute/path/break.wav" --start 64 --warping true --warp-mode beats
abletonctl clip-warp --track "Breaks" --arrangement-start 64 --clip-bpm 140 --warp-mode beats
```

## Amen-style Chops

Rapidly sliced jungle/breakcore edits inspired by the Amen break approach.

CLI moves:
- Slice into 1/8, 1/16, and 1/32 regions.
- Duplicate snare fragments into cascades and add reverse hits before impacts.
- Keep source licensing clear; use user-owned or royalty-cleared breaks.

Creative parameters:
- Jungle: rolling snare cascades, ghost notes, high tempo.
- Glitch hop: fewer slices, heavier swing, more room for bass.
- Deep dub: one or two break fills, not constant Amen density.

## Halftime Grooves

Feels like 70 BPM over a 140 BPM grid, with heavy spacious kick/snare emphasis.

CLI moves:
- Program kick around beat 1 and snare on beat 3.
- Add ghost hats and percussion in the gaps.
- Keep bass notes away from kick/snare transients.

```json
[
  {"pitch":36,"start_time":0,"duration":0.25,"velocity":118},
  {"pitch":38,"start_time":2,"duration":0.25,"velocity":120},
  {"pitch":42,"start_time":0.5,"duration":0.125,"velocity":72},
  {"pitch":42,"start_time":1.5,"duration":0.125,"velocity":62},
  {"pitch":42,"start_time":2.75,"duration":0.125,"velocity":78}
]
```

## Glitch Drums

Stuttered, repeated, granular, or digitally fragmented percussion.

CLI moves:
- Use short MIDI retriggers in Drum Rack for deterministic repeats.
- Add Beat Repeat, Redux, Spectral Time, or Shifter on a fill track.
- Automate glitch devices only for fill moments.

## Percussive Fills

Rapid-fire drum embellishments, often heavily edited.

CLI moves:
- Use 1/16 to 1/32 toms, snares, rims, clicks, or zaps.
- Raise velocity into the transition, then leave space before the hit.
- Use `midi-add-notes` for new clips; use `midi-update-notes` after reading note
  IDs if editing existing material.

## Drum Fills

Transitional rapid percussion phrases before section changes.

CLI moves:
- Combine snare/tom movement, reverse cymbal, and a final gap.
- Use `clip-automation-set-many` on Auto Filter or Drum Buss for intensity.
- Avoid destructive clearing unless the fill clip was just created.

## Rolls

Fast repeated hits, especially snares and hats.

CLI moves:
- Write repeated MIDI notes at 1/16, 1/32, or triplet subdivisions.
- Increase velocity toward the transition for a rush.
- Shorten duration so hits do not blur.

## Snare Rushes

Accelerating snare rolls into drops or transitions.

CLI moves:
- Start at 1/8 or 1/16, then densify to 1/32 near the boundary.
- Automate filter high-pass or send level upward.
- Leave the final 1/16 or 1/8 empty before impact when a fakeout helps.

## Hat Trills

Ultra-fast hi-hat repetitions.

CLI moves:
- Add short 1/32 or 1/64 notes at lower velocity than main hats.
- Pan or alternate velocities for shimmer.
- Do not place every trill on top of a vocal or lead transient.

## Ghost Hats

Quiet secondary hi-hats for groove texture.

CLI moves:
- Use velocities 35 to 75 against main hats at 80 to 110.
- Add probability around 0.75 to 0.95 for human variation.
- Keep main offbeat hats stable in tech house.

## Offbeat Hats

Hats emphasizing the upbeat groove.

CLI moves:
- In tech house, place open hats on offbeats and keep them short.
- Layer a quieter closed hat or acoustic hat loop for motion.
- High-pass and avoid over-wide hats if the mix is dense.

## Shaker Layers

Organic high-frequency groove movement.

CLI moves:
- Use 1/16 patterns with velocity waves and light swing.
- Load a shaker loop as audio, warp gently, or program Drum Rack hits.
- Keep it low enough that it is felt more than heard.

## Percussion Loops

Continuous auxiliary rhythmic textures.

CLI moves:
- Load as audio and warp to the set tempo.
- High-pass, compress lightly, and tuck behind kick/snare.
- Split/copy only the best 1 or 2 bars if the loop gets repetitive.

## Rimshots

Sharp woody snare-adjacent hits.

CLI moves:
- Load to Drum Rack pad, often D#1 or nearby.
- Use as syncopated answers to the main snare.
- Add small room reverb or short delay for character.

## Clicks / Ticks

Hyper-detailed micro percussion. Tiny transient noises that create groove
texture.

CLI moves:
- Use foley taps, closed hats, rim edge samples, or short zaps.
- Put them at low velocity and pan subtly.
- In experimental bass, use clicks to imply groove while the main drums leave
  space.

## Clicks / Taps

Tiny transient percussion artifacts. Treat similarly to clicks/ticks, but more
organic and less digital.

CLI moves:
- Use paper, keys, mouth clicks, table taps, or mechanical one-shots.
- Layer under hats or before bass hits for tactile detail.
- Gate or shorten tails.

## Foley Percussion

Found-sound percussion from objects or mechanical noises.

CLI moves:
- Load one-shots into Drum Rack pads.
- Use velocity variation and slight timing offsets.
- Add Redux, Corpus, or Resonators for non-literal textures.

## Transient Percussion

Extremely attack-heavy short drum sounds.

CLI moves:
- Use Drum Buss `Transients`, Saturator, or tight EQ.
- Keep tails short and leave headroom.
- Use as top layers on kicks/snares or as tiny fill hits.

## Textural Percussion

Percussion more about texture than punch.

CLI moves:
- Use foley, noise, shakers, filtered loops, or quiet glitch artifacts.
- High-pass and tuck low in the mix.
- Automate panning or filter for motion.

## Subby Kicks

Low-end heavy kicks that merge into bass.

CLI moves:
- Use only when sub part leaves room for the kick tail.
- Tune the kick fundamental to the key when possible.
- Avoid stacking with a long sub note on the same transient.

## Punch Kicks

Tight transient-focused kicks cutting through dense mixes.

CLI moves:
- Layer click/top and body only if needed.
- Use Drum Buss transient and mild drive, not just volume.
- Verify kick/sub relationship before raising levels.

## Layered Snares

Multiple snare textures stacked together.

CLI moves:
- Combine body, crack, clap/noise, and optional tonal layer.
- Align starts tightly unless a flam is intended.
- Use short reverb; long tails can soften drop impact.

## Neuro Percussion

Synthesized metallic or robotic drum textures.

CLI moves:
- Use Operator FM, Corpus, Resonators, Redux, or Shifter.
- Program as sparse answers to normal percussion.
- Resample long design passes and keep only the best hits.

## Glitched Fills

Hyper-edited fills with stutters, reverses, and chops.

CLI moves:
- Render a `glitch-drum-transition` macro preview when helpful.
- Use Drum Rack for zaps/clicks and audio split/copy for break fragments.
- Add one reverse hit before the downbeat and cut the tail at impact.

```sh
abletonctl workflow-macro render glitch-drum-transition --track "Zap Rack" --secondary-track "Perc Rack" --synth-track "Lead Synth" --length 8
```

## Reverse Snares

Reversed snare tails leading into impacts.

CLI moves:
- Reverse a copied snare sample if focus is safe, or load a prepared reverse.
- Fade/filter into the downbeat.
- Keep the hit itself clean and centered.

## Reverse Cymbals

Swelling cymbals before transitions.

CLI moves:
- Load a reverse cymbal sample or reverse a cymbal clip.
- High-pass and automate volume so it supports without washing the mix.
- Pair with a crash or silence at the target beat.

## Crash Washes

Long noisy cymbal tails filling space.

CLI moves:
- Use after impacts or section starts.
- High-pass and lower volume under vocals/leads.
- Shorten with clip gain or split if it masks groove.

## Ride Grooves

Continuous ride cymbal pulse patterns.

CLI moves:
- Use repeated ride notes with velocity accents.
- Common in high-energy breaks, DnB, and some house sections.
- Keep ride wash controlled with EQ.

## Jungle Rolls

Rapid breakbeat snare cascades.

CLI moves:
- Duplicate snare segments or write fast Drum Rack snare notes.
- Use 1/16, 1/32, and triplet placements.
- Combine with ghost kicks for authentic break energy.

## Skitter Patterns

Insect-like high-frequency percussion movement.

CLI moves:
- Use 1/32 hats/clicks with low velocity and panning variation.
- Add probability so they flicker.
- Works well over sparse halftime or psybass.

## Hybrid Acoustic/Electronic Drums

Organic breaks layered with synthetic percussion.

CLI moves:
- Use audio breaks for human swing and Drum Rack one-shots for punch.
- Align only the anchors; preserve some break feel.
- Bus process lightly with Drum Buss/Glue Compressor after checking phase and
  transient impact.
