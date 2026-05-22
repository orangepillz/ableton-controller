# Sound Design And Mixing Heuristics

## Producer Phrase Translation

- "Make this drop hit harder": increase pre-drop contrast, tighten kick/sub timing, strengthen drum transient, add controlled bass harmonics, avoid master-only gain.
- "Create tension before the buildup": automate filter, pitch, density, space, and noise/riser motion across the setup range.
- "Layer a wide supersaw under this lead": create a quieter wide support layer, high-pass it, preserve lead focus, keep lows mono.
- "Make the kick cut through the sub": shorten or duck sub around kick, reduce masking low mids, add sidechain or envelope shaping.
- "Add movement to the bass": automate mid-bass filter, formant, distortion, phaser, chorus, or macro values while keeping sub stable.
- "Turn this into a fakeout": mute/delay expected impact, preserve expectation, insert silence or sparse ear candy, re-enter with stronger contrast.
- "Make this transition more cinematic": combine riser/noise, filtered tails, reverb/delay throws, pitch movement, and a low-end cut before the hit.
- "Sidechain everything properly": identify kick source and buses, add ducking to bass/music layers, avoid over-ducking drums and vocal anchors.
- "Make the drums punchier": transient shaping, bus saturation/compression, tail cleanup, velocity accents.
- "Humanize the hi hats": velocity deviation, light probability, optional offbeat timing shift, stable main accents.
- "Create a call and response bass pattern": lower/stronger phrase answered by brighter/higher or rhythmically denser phrase, with rests for drums.

## Bass Layering

Stable bass music low end usually separates:

- Sub: mono sine/triangle/fundamental, minimal saturation, predictable MIDI, sidechained to kick.
- Mid bass: movement, distortion, filters, stereo content above roughly 120 Hz.
- Top/noise layer: transient, texture, air, often short or automated.

When asked to make bass heavier, do not only raise volume. Prefer:

1. Check kick and sub rhythm overlap.
2. Tighten MIDI lengths.
3. Add harmonic saturation to a duplicate or mid layer.
4. Use EQ to keep sub clear and let mids carry aggression.
5. Automate movement on the mid layer.

## Drop Impact

To make a drop hit harder:

- Remove energy before the drop: short silence, filtered breakdown, reduced low end.
- Add transient contrast: stronger kick/snare, shorter reverb tails at impact.
- Preserve headroom: lower pre-drop elements rather than clipping the master.
- Layer controlled noise/impact only at the downbeat.
- Keep sub simple on the first hit.

Useful commands:

```sh
python3 abletonctl.py clip-set --track "Build FX" --arrangement-start 60 --gain -3
python3 abletonctl.py set-track --track "Kick" --volume 0.86
python3 abletonctl.py device-add-stock --target-track "Drum Bus" --path "audio_effects/Drum Buss"
```

## Kick/Sub Relationship

If the kick lacks cut:

- Shorten sub notes around kick hits.
- High-pass mid bass and music layers.
- Use sidechain compression or clip volume automation on sub/bass bus.
- Add click/top transient to kick only if it fits the genre.
- Do not stereo-widen the sub.

If the sub lacks weight:

- Center pitch around the key root or fifth.
- Avoid too many fast note changes below 60 Hz.
- Add saturation on a parallel/mid layer, not necessarily the sub itself.
- Check that limiter/compressor is not flattening the transient.

## Drums

Punchier drums:

- Strengthen transient device chain: `Drum Buss`, `Compressor`, `Saturator`, `EQ Eight`.
- Shorten long tails that mask groove.
- Use velocity accents on hats and percussion.
- Keep snare/clap around the genre anchor; dubstep often half-time snare on beat 3, DnB on 2 and 4.

Humanized drums:

- Keep kick/snare anchors stable.
- Vary hats and percussion velocity by 5 to 15.
- Use probability lightly on ghost hits, not main groove anchors.
- Shift off-grid only when the groove requests swing, shuffle, or looseness.

## Supersaws And Leads

"Layer a wide supersaw under this lead" means:

1. Duplicate or create a MIDI/instrument track.
2. Use an instrument suited to saw stacks or load a relevant preset.
3. Keep it lower in level than the lead.
4. High-pass enough to avoid fighting sub and bass.
5. Add width with chorus/unison or Utility above low mids.
6. Sidechain or duck if it masks snare/vocal.

Do not put wide stereo content below the bass fundamental.

## Movement

Movement types:

- Wobble: rhythmic filter or volume movement, often 1/4, 1/8, triplet, or dotted.
- Growl: formant/filter movement plus distortion/resonance.
- Talking bass: vowel/formant/filter morph gestures.
- Neuro movement: fast filtered distortion modulation, careful transient control.
- Future bass pump: sidechain-shaped volume plus bright chord layer.

Use `clip-stock-automation-set` for repeatable clip-tied movement. Use parameter setting for static tone.

## Transitions

Cinematic transition:

- Start with filtering and space.
- Add riser/noise/reverse texture.
- Increase density or pitch near the section boundary.
- Cut low end before impact.
- Leave a short breath before the downbeat.

Fakeout:

- Promise the drop with the buildup.
- Remove or delay the expected first hit.
- Insert a sparse vocal, fill, or silence.
- Re-enter with stronger low-end and transient contrast.

## Mix Bus And Master Prep

For modern electronic mixing:

- Leave headroom before the limiter; avoid solving balance by master gain.
- Use buses: drums, bass, music, FX, vocals when available.
- Keep low end mostly mono.
- Use return effects for shared space instead of many unrelated reverbs.
- Use limiting only for preview loudness unless the user asks for mastering.
- For mastering prep, request reference loudness/style and whether the goal is streaming, club, or demo.

Useful devices:

- Drum bus: `Drum Buss`, `EQ Eight`, `Glue Compressor`, `Saturator`.
- Bass bus: `EQ Eight`, `Compressor`, `Roar` or `Saturator`, `Utility`.
- Music bus: `EQ Eight`, light compression, sidechain/ducking as needed.
- Master preview: `EQ Eight`, `Glue Compressor`, `Limiter`, `Spectrum`.

## Tempo And Key Defaults

Ask or infer from genre when absent:

- Dubstep/riddim: 140 to 150 BPM, half-time feel.
- Experimental bass: 80 to 150 BPM, often half-time or broken grid.
- Glitch hop: 90 to 110 BPM.
- Future bass: 140 to 160 BPM or 70 to 80 half-time.
- DnB: 170 to 176 BPM.
- Breakbeat: 125 to 145 BPM.
- Tech house: 124 to 128 BPM.

If key is unknown, avoid committing melodic content beyond root/fifth/octave until the user names a key or existing notes reveal one.
