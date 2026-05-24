# FX, Textures, Atmospheres, And Ear Candy

Use these recipes for transition design, stereo detail, ambience, and small
sounds that make a track feel alive. Default placement is `FX`, unless the sound
belongs to a specific musical source.

## Core FX Chains

Clean sweep chain:

```sh
abletonctl device-add-stock --target-track "FX Sweep" --path "audio_effects/Auto Filter"
abletonctl device-add-stock --target-track "FX Sweep" --path "audio_effects/Echo"
abletonctl device-add-stock --target-track "FX Sweep" --path "audio_effects/Hybrid Reverb"
```

Glitch/detail chain:

```sh
abletonctl device-add-stock --target-track "FX Glitch" --path "audio_effects/Beat Repeat"
abletonctl device-add-stock --target-track "FX Glitch" --path "audio_effects/Redux"
abletonctl device-add-stock --target-track "FX Glitch" --path "audio_effects/Spectral Time"
abletonctl stock-controls --device "Beat Repeat"
abletonctl stock-controls --device "Redux"
```

## Glitches

Tiny chopped digital artifacts, stutters, buffer-repeat effects, and rhythmic
micro-cuts.

CLI moves:
- For deterministic edits, split/copy very short audio or MIDI fragments.
- For device-driven glitches, add Beat Repeat, Redux, Spectral Time, or Shifter.
- Use `clip-automation-set-many` to turn the effect up only on the fill.

Variation ideas:
- G Jones-style contrast: hard silence, one glitch burst, then impact.
- Tipper/Detox detail: many tiny edits at low level around a sparse groove.
- Tech house: one or two small vocal/percussion stutters, not constant chaos.

## Zaps

Short electric laser/transient sounds. Build with Operator pitch envelopes or a
short audio one-shot plus Shifter/Redux.

CLI moves:
- Create a short MIDI note on Operator.
- Add Auto Filter, Roar, and Echo.
- Use pitch bend that falls or rises within 1/16 to 1/8.

```sh
abletonctl device-add-stock --target-track "Zap" --path "instruments/Operator"
abletonctl device-add-stock --target-track "Zap" --path "audio_effects/Roar"
abletonctl clip-create-midi --track "Zap" --slot 0 --length 1 --name "Zap 01"
abletonctl midi-add-notes --track "Zap" --slot 0 --notes '[{"pitch":72,"start_time":0,"duration":0.125,"velocity":118}]'
abletonctl clip-envelope-set --track "Zap" --slot 0 --target midi-cc --ensure-midi-cc-device --midi-control pitch-bend --clear --events '[{"time":0,"value":12},{"time":0.125,"value":-12}]'
```

## Risers

Sweeps that build tension upward in pitch, noise, filter energy, density, or
space.

CLI moves:
- Use an existing FX clip or create an audio/MIDI riser clip.
- Automate Auto Filter `Frequency`, resonance, send level, and optional pitch.
- Use Arrangement automation for section-length transitions.

```sh
abletonctl arrangement-automation-set-many --track "FX Riser" --arrangement-start 48 --device "Auto Filter" --lanes '[{"param":"Frequency","duration":16,"from_normalized":0.18,"to_normalized":0.92,"curve":"ease-in-out","clear":true},{"param":"Resonance","duration":16,"from_normalized":0.10,"to_normalized":0.36,"steps":8,"clear":true}]'
```

Variation ideas:
- Noise riser: Auto Filter plus Hybrid Reverb.
- Tonal riser: Operator with pitch bend and filter.
- Fakeout riser: rise fully, cut 1/4 bar before the downbeat, then re-enter.

## Downlifters / Fallers

The opposite of risers: pitch, filter, or noise energy sweeps downward after a
transition.

CLI moves:
- Reverse a riser if focus is safe, or write downward filter/pitch automation.
- Use low-pass closing plus reverb tail after impacts.
- Keep sub drops separate from noisy fallers to avoid low-end mud.

## Granular Textures

Cloudy fragmented audio grains that shimmer or smear spatially.

CLI moves:
- Warp an audio clip with `--warp-mode texture` or `complex-pro`.
- Add Grain Delay, Spectral Time, Echo, and Hybrid Reverb.
- Automate dry/wet and filter so texture appears only where useful.

```sh
abletonctl clip-warp --track "Texture" --arrangement-start 32 --warping true --warp-mode texture
abletonctl device-add-stock --target-track "Texture" --path "audio_effects/Grain Delay"
abletonctl device-add-stock --target-track "Texture" --path "audio_effects/Spectral Time"
```

## Foley Layers

Organic recorded sounds like paper, water, taps, crunches, and mechanical noises.

CLI moves:
- Load as audio clips or Drum Rack pads.
- High-pass and shorten tails so foley does not fight drums.
- Add Redux, Corpus, or Resonators when it should become less literal.

Creative parameters:
- Organic groove: low velocity, off-grid, short room reverb.
- Mechanical: tight gate, Redux, Shifter, no long reverb.
- Psychedelic: Spectral Time and panning automation.

## Atmospheric Pads

Huge ambient harmonic layers underneath the chaos.

CLI moves:
- Use Wavetable, Drift, or Meld on a `Synths` track.
- Add Auto Filter, Chorus-Ensemble, Hybrid Reverb, and Utility.
- High-pass or keep lows controlled if a sub/bass part exists.

Variation ideas:
- Deep dub: darker low-pass and long delay.
- Glitch hop: chord pad with micro reverse tails.
- Experimental bass: pad is quiet, textured, and sidechained lightly.

## Soundscapes

Environmental ambience, drones, field recordings, and psychedelic space textures.

CLI moves:
- Load long audio into `FX`; warp only when the tempo relationship matters.
- Add Spectral Time, Hybrid Reverb, EQ Eight, and Auto Filter.
- Automate filter movement over arrangement sections.

## Reverse FX

Reversed cymbals, basses, vocals, or impacts used for transitions.

CLI moves:
- Use `clip-audio-set --reverse` only when Live focus is safe.
- Safer alternative: prepare reversed source externally, then load as audio.
- Add Auto Filter and volume automation to tuck it behind the transition.

```sh
abletonctl clip-audio-set --track "Reverse FX" --arrangement-start 60 --reverse
```

## Impacts / Slams

Big cinematic hits for section changes.

CLI moves:
- Layer a transient hit, low thump, short noise burst, and room/reverb tail.
- Use Drum Rack pads or separate audio clips depending on source material.
- Keep the first drop kick/sub clean; impacts should support, not mask.

Creative parameters:
- Club slam: short tail, strong transient, little low wash.
- Cinematic slam: longer Hybrid Reverb, low thump, filtered noise.
- Glitch slam: pre-hit stutter, reverse swell, then short impact.

## Vocal Chops

Tiny manipulated vocal snippets used rhythmically.

CLI moves:
- Load a licensed or user-provided vocal sample.
- Warp with `complex-pro` for pitched phrases or `beats` for rhythmic chops.
- Use pitch, clip split/copy, Echo throws, and formant-style filtering.

```sh
abletonctl clip-warp --track "Vocal Chop" --arrangement-start 32 --warping true --warp-mode complex-pro --pitch-coarse -7
abletonctl device-add-stock --target-track "Vocal Chop" --path "audio_effects/Echo"
```

## Stereo Ear Candy

Small sounds flying around the stereo field with automation and panning.

CLI moves:
- Use short one-shots, zaps, foley, or vocal bits at low volume.
- Automate pan with `set-track` for static placement or clip/device automation
  when movement is available.
- Keep important drums, sub, and lead hooks more centered.

## Phasey Textures

Flangers and phasers creating moving psychedelic motion.

CLI moves:
- Add Phaser-Flanger after the source and before big reverb.
- Use slow movement for pads; faster movement for zaps or resampled bass.
- Keep dry/wet moderate to preserve punch.

```sh
abletonctl device-add-stock --target-track "Texture" --path "audio_effects/Phaser-Flanger"
abletonctl stock-controls --device "Phaser-Flanger"
```

## Bitcrushed Artifacts

Intentionally degraded digital textures.

CLI moves:
- Add Redux or Roar with Bit Crusher shaper type after confirming controls.
- Automate dry/wet for only the last 1/8 or 1/4 of a fill.
- Pair with EQ Eight so harsh highs are deliberate.

## Transient Smacks

Very sharp attack-heavy percussion or FX layers.

CLI moves:
- Use one-shot clicks, rimshots, short noise, or a filtered zap.
- Add Drum Buss or Saturator, then trim the tail.
- Use velocity accents instead of simply raising volume.

## Swells

Gradual volume or filter blooms used for emotional lift.

CLI moves:
- Use Arrangement automation for Auto Filter and track volume/sends.
- Use Hybrid Reverb and Echo to grow space, then cut before the downbeat.
- For musical swells, add a sustained pad or vocal texture.

## Tonal Percussion

Percussion elements pitched melodically.

CLI moves:
- Load one-shots into Drum Rack or Simpler.
- Tune with clip pitch, sample device controls, or MIDI pitch.
- Keep notes short and use a root/fifth/octave vocabulary unless key is known.

## Spectral FX

Weird frequency-selective movement sounds that feel holographic.

CLI moves:
- Add Spectral Time or Spectral Resonator to foley, vocals, pads, or breaks.
- Automate dry/wet and filter so the spectral layer does not flatten the mix.
- Render/resample the best pass when the gesture is complex.

```sh
abletonctl device-add-stock --target-track "Spectral FX" --path "audio_effects/Spectral Time"
abletonctl device-add-stock --target-track "Spectral FX" --path "audio_effects/Spectral Resonator"
abletonctl stock-controls --device "Spectral Time"
```

## Delay Throws

Sudden dub-style echoes on isolated hits or sounds.

CLI moves:
- Add Echo to the source or use return `B-Delay`.
- Automate send/dry-wet only on the target hit.
- Filter delay return to keep low end clean.

```sh
abletonctl set-send --track "Vocal Chop" --send "B" --value 0.22
```

## Filtered Noise Washes

White or shaped noise sweeps used for transitions.

CLI moves:
- Use Operator noise, Wavetable noise, or a sample.
- Add Auto Filter and automate `Frequency`.
- Add Hybrid Reverb for width but cut low end.

## Mechanical Textures

Sounds resembling servos, hydraulics, robots, or machinery.

CLI moves:
- Start from foley, zaps, Operator FM, or short percussion.
- Add Redux, Shifter, Corpus, Spectral Resonator, and tight gating.
- Use repeated 1/32 or 1/16 notes with velocity variation.

## Pitched Ambience

Atmospheres that subtly imply harmony or melody.

CLI moves:
- Load ambience or field audio, pitch to root/fifth/octave, and tuck behind the
  track.
- Use EQ Eight/Auto Filter to remove mud.
- Add slow Chorus-Ensemble or Hybrid Reverb for width above low mids.
