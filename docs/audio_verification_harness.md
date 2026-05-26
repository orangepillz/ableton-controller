# Audio Verification Harness

The harness closes the loop between Ableton edits and rendered-audio evidence.
Codex should not call a kick, snare, wub, transition, drop, or mix complete
because a rack or automation lane looks plausible. It must render a WAV probe,
analyze the file, patch the set if the gate fails, and repeat until the relevant
solo and context gates pass.

## Render Probes

Use `abletonctl render-audio` to export deterministic Arrangement probes:

```sh
abletonctl render-audio --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_full_mix.wav

abletonctl render-audio --solo-track Kick --start-bar 65 --bars 4 \
  --output .ableton-audits/renders/drop_1_kick_solo.wav

abletonctl render-audio --solo-group Drums --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_drums_bus.wav

abletonctl render-audio --solo-tracks "Kick,BASS" --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_kick_bass_context.wav
```

Defaults are 48 kHz, 24-bit, no normalization, returns included, manifest on,
and state restoration on. The bridge saves mute, solo, loop, selected-track,
transport, and playhead state, applies the requested solo/mute range, exports,
validates that a readable WAV exists, writes a sibling manifest, then restores
state. If Live does not expose a callable export method or no WAV appears, the
command exits nonzero.

Known limitation: the MIDI Remote Script can only render when the running Live
version exposes a callable export method to Python. Sample-rate, bit-depth, and
normalization options are passed to that method when supported; otherwise the
command fails rather than silently producing unverifiable output.

## Required Drop Render Set

For each major drop render:

- `drop_N_full_mix.wav`
- `drop_N_drums_bus.wav`
- `drop_N_bass_bus.wav`
- `drop_N_kick_solo.wav`
- `drop_N_snare_solo.wav`
- `drop_N_kick_bass_context.wav`
- `drop_N_snare_drums_context.wav`
- `drop_N_transition_in.wav`
- `drop_N_transition_out.wav`

For one-off sound design, render `<sound>_solo.wav`, `<sound>_context.wav`, and
`<sound>_audioqa.json`.

## Analyze And Compare

Use deterministic gates first:

```sh
bin/ableton-audioqa analyze --file .ableton-audits/renders/drop_1_kick_solo.wav \
  --target kick --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_solo.audioqa.json

bin/ableton-audioqa compare --primary .ableton-audits/renders/drop_1_kick_solo.wav \
  --context .ableton-audits/renders/drop_1_full_mix.wav \
  --target kick-audibility --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_context.audioqa.json
```

Reference files under `.ableton-copilot/references` are feature-only. Do not
sample, copy, or recreate them.

## Priority Rules

Fix failures in this order:

1. Clipping or broken render
2. Missing kick in drop
3. Missing or weak snare in drop
4. Low-end masking between kick, sub, reese, and wub layers
5. Bass movement and articulation
6. Drop energy versus build energy
7. Transition impact
8. Microfills and glitches
9. Stereo ear candy
10. Atmospheric polish

Do not add decorative layers while critical drum or low-end gates are failing.
