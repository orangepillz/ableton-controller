# Bass And Synth Articulations

These recipes assume the target has already been resolved to `Sub` for pure low
end or `Synths` for moving bass layers. For all parameter work, run
`stock-controls` first and prefer normalized ranges unless a quantized value is
known from the control listing.

## Core Bass Chain

Use this for most mid-bass sounds:

```sh
abletonctl device-add-stock --target-track "Mid Bass" --path "instruments/Operator"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Auto Filter"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/Roar"
abletonctl device-add-stock --target-track "Mid Bass" --path "audio_effects/EQ Eight"
abletonctl stock-controls --device "Operator"
abletonctl stock-controls --device "Auto Filter"
abletonctl stock-controls --device "Roar"
```

Safe default tuning:

```sh
abletonctl set-stock-control --track "Mid Bass" --device "Auto Filter" --stock-device "Auto Filter" --control resonance --normalized 0.24
abletonctl set-stock-control --track "Mid Bass" --device "Auto Filter" --stock-device "Auto Filter" --control drive --normalized 0.28
abletonctl set-stock-control --track "Mid Bass" --device "Roar" --stock-device "Roar" --control drive --normalized 0.55
abletonctl set-stock-control --track "Mid Bass" --device "Roar" --stock-device "Roar" --control dry_wet --normalized 0.42
```

For quantized controls, read choices first:

```sh
abletonctl stock-controls --device "Auto Filter" --control filter_type
abletonctl stock-controls --device "Roar" --control shaper_1_type
```

## Wubs

Low-frequency vowel-like bass modulations. Build from a sine/saw Operator tone,
Auto Filter in vowel or morph territory, and Roar for harmonics.

CLI moves:
- Write stepped Auto Filter `Frequency` movement at 1/4, 1/8, dotted 1/8, and
  triplet rates.
- Automate `Resonance` modestly; too much masks the sub.
- Keep a separate mono sub note under the mid movement.

Variation ideas:
- Slow "wahh": 1-bar or 1/2-bar filter ramps, lower resonance.
- Articulated neuro wub: 1/16 steps, alternating `frequency` and `formant`.
- Deep dub wub: less Roar, more Echo send, more empty space.

```sh
abletonctl clip-automation-set-many --track "Mid Bass" --slot 0 --device "Auto Filter" --lanes '[{"param":"Frequency","steps":[{"time":0,"duration":0.5,"normalized":0.20},{"time":0.5,"duration":0.5,"normalized":0.70},{"time":1,"duration":1,"normalized":0.32},{"time":2,"duration":2,"normalized":0.62}],"clear":true},{"param":"Resonance","steps":[{"time":0,"duration":4,"normalized":0.28}],"clear":true}]'
```

## Squelches

Wet, rubbery resonant bass sounds. Start with Operator or Meld, band-pass or
vowel filtering, short pitch glide, and Roar at a restrained mix.

CLI moves:
- Use Auto Filter `filter_type` as band-pass, morph, or vowel after confirming
  quantized values with `stock-controls`.
- Automate filter `Frequency` quickly upward then down.
- Add pitch bend or short MIDI notes with glide for liquid pops.

Creative parameters:
- More acid: higher `resonance`, lower `frequency`, more Overdrive/Roar.
- More alien: add `Shifter`, `Corpus`, or `Spectral Resonator` after Roar.
- More Tipper-like: resample a long pass and keep only the best burps.

## Reeses

Detuned multi-voice basses with movement and phase. Use Wavetable, Drift, Meld,
or two Operator layers, then keep the sub mono and widen only above low mids.

CLI moves:
- Add `Wavetable` or `Drift`, then `Chorus-Ensemble`, `Phaser-Flanger`,
  `Auto Filter`, and `Utility`.
- Use `Utility` or EQ to keep lows controlled; avoid stereo widening the sub.
- Automate filter or phaser rate subtly for motion.

```sh
abletonctl device-add-stock --target-track "Reese Bass" --path "instruments/Wavetable"
abletonctl device-add-stock --target-track "Reese Bass" --path "audio_effects/Chorus-Ensemble"
abletonctl device-add-stock --target-track "Reese Bass" --path "audio_effects/Phaser-Flanger"
abletonctl device-add-stock --target-track "Reese Bass" --path "audio_effects/Utility"
```

Variation ideas:
- Neuro: add Roar and automate filter notches.
- Deep dub: slower chorus, less distortion, more low-pass.
- DnB: shorter notes, stronger high-mid layer, tighter sidechain.

## Growls

Aggressive talking basses with formant movement. Start from Operator FM or Meld,
then shape with Auto Filter vowel/morph and Roar.

CLI moves:
- Use Operator algorithm and oscillator ratios for FM bite.
- Automate Auto Filter `Formant`, `Frequency`, and `Resonance` together.
- Add `clip-envelope-set --target midi-cc` for pitch-bend gestures if the part
  needs bends or yells.

Creative parameters:
- Throatier: lower filter frequency, higher Roar drive, slower attack.
- Robotic: add Redux or Shifter before Auto Filter.
- Cleaner: move distortion after the filter and reduce dry/wet.

## FM Screeches

Metallic frequency-modulated high-end sounds. Use Operator as the default source.

CLI moves:
- Add Operator, turn up modulator levels, use short notes, and high-pass if the
  sound is not meant to carry low end.
- Automate pitch bend or Operator transpose for rising/falling screams.
- Add Roar or Overdrive lightly, then Echo for tails.

```sh
abletonctl device-add-stock --target-track "FM Screech" --path "instruments/Operator"
abletonctl device-add-stock --target-track "FM Screech" --path "audio_effects/Roar"
abletonctl device-add-stock --target-track "FM Screech" --path "audio_effects/Echo"
abletonctl clip-envelope-set --track "FM Screech" --slot 0 --target midi-cc --ensure-midi-cc-device --midi-control pitch-bend --clear --events '[{"time":0,"value":0},{"time":1,"value":12},{"time":2,"value":-5},{"time":4,"value":0}]'
```

Variation ideas:
- Laser screech: faster pitch event, short note, no reverb.
- Rave screech: add Delay/Echo and wider chorus.
- Alien screech: add Spectral Time or Spectral Resonator.

## Blorps / Bloops

Cartoony plucks or liquid bass pops. Use short Operator notes, filter envelope,
and mild pitch drop.

CLI moves:
- Create 1/16 to 1/8 MIDI notes with varied pitches and velocities.
- Add Auto Filter with short envelope-like automation.
- Add Corpus or Resonators if the blorp should feel hollow or toy-like.

Creative parameters:
- Bubble: high resonance, quick downward pitch bend, short decay.
- Plop: low note, faster filter close, less distortion.
- Cartoon: wider pitch jumps and more Echo feedback.

## Yois

Dubstep-style "yo-yoy" bass articulations. Use formant/vowel movement and a
two-syllable automation shape.

CLI moves:
- Write Auto Filter `Frequency` and `Formant` as alternating low/high steps.
- Use short note pairs: first note longer and lower, second shorter and brighter.
- Keep the sub simple underneath.

Pattern idea:

```json
[
  {"pitch":36,"start_time":0,"duration":0.5,"velocity":118},
  {"pitch":43,"start_time":0.75,"duration":0.25,"velocity":108},
  {"pitch":36,"start_time":1.5,"duration":0.5,"velocity":116},
  {"pitch":48,"start_time":2.25,"duration":0.25,"velocity":110}
]
```

## Sub Drops

Descending sine-wave low-end drops for impact. Use pure Operator sine on a
`Sub` track, pitch bend, and no stereo widening.

CLI moves:
- Create a MIDI clip with one long low note.
- Use pitch bend or note descent to fall from root/fifth down an octave.
- Keep processing minimal: EQ Eight/Utility only, optional limiter for safety.

```sh
abletonctl device-add-stock --target-track "Sub Drop" --path "instruments/Operator"
abletonctl clip-create-midi --track "Sub Drop" --slot 0 --length 4 --name "Sub Drop 01"
abletonctl midi-add-notes --track "Sub Drop" --slot 0 --notes '[{"pitch":48,"start_time":0,"duration":4,"velocity":110}]'
abletonctl clip-envelope-set --track "Sub Drop" --slot 0 --target midi-cc --ensure-midi-cc-device --midi-control pitch-bend --clear --events '[{"time":0,"value":12},{"time":3.75,"value":-12}]'
```

## Neuro Bass Phrases

Highly articulated bass sequences where each note can have unique modulation.
Treat this as a resampling workflow, not a single preset.

CLI moves:
- Create 4 or 8 bars of sparse call-and-response MIDI.
- Add Operator/Wavetable/Meld plus Auto Filter, Roar, Phaser-Flanger, Redux.
- Write different automation shapes per phrase.
- Render or prepare a resampling pass, then chop the best hits.

Creative parameters:
- Alternate filter type, resonance, drive, and stereo width per 1/2 bar.
- Use velocity to control note brightness where the instrument supports it.
- Leave rests before the snare and before the heaviest bass answer.

## Psybass Movement

Rolling hypnotic bass modulation focused on groove rather than aggression.

CLI moves:
- Use shorter root/fifth notes, 1/16 or dotted syncopation, and restrained
  filter movement.
- Keep Roar lower and let Auto Filter or Shifter create motion.
- Add small delay throws only on phrase endings.

Creative parameters:
- More hypnotic: repeat a 1-bar groove while automating only one parameter.
- More psychedelic: add Spectral Resonator or Phaser-Flanger at low dry/wet.
- More dubby: delay the final note of every 2 bars.

## Percussive Bass Hits

Bass sounds functioning rhythmically like drums. Use short MIDI notes, fast
filter envelopes, and controlled transients.

CLI moves:
- Program notes as if they were toms or kicks, with rests around the real kick.
- Use Operator or Wavetable plus Drum Buss or Roar.
- Shorten note durations aggressively and verify with `midi-get-notes`.

```sh
abletonctl midi-add-notes --track "Bass Perc" --slot 0 --notes '[{"pitch":36,"start_time":0.75,"duration":0.125,"velocity":118},{"pitch":43,"start_time":1.25,"duration":0.125,"velocity":104},{"pitch":36,"start_time":2.75,"duration":0.25,"velocity":120}]'
abletonctl midi-get-notes --track "Bass Perc" --slot 0 --start 0 --end 4
```
