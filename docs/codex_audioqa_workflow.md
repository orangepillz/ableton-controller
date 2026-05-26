# Codex AudioQA Workflow

For sound design and mix-impact work, Codex must use rendered reports as the
completion evidence.

`abletonctl render-audio` creates those files by recording a temporary Live
resampling track, converting the recording to the requested WAV path, writing a
manifest, deleting the temporary track, cleaning up the temporary recording
source, and restoring set state.

1. Inspect the Live set with `abletonctl session-snapshot`.
2. Identify the target section, track, group, or sound.
3. Create or modify the set.
4. Render a solo probe.
5. Run `ableton-audioqa analyze` on the solo probe.
6. If the solo probe fails, patch the sound and re-render.
7. Render the sound in bus or drop context.
8. Run `ableton-audioqa compare` against the context render.
9. If masked or too loud, patch gain staging, EQ, ducking, or arrangement.
10. Render the full section.
11. Run `drop` or `full-mix` gates.
12. Summarize reports with `summarize-section`.
13. Only mark the task complete if critical gates pass or remaining failures are
    explicitly disclosed.

## Whole-Track Audit Skeleton

```sh
abletonctl render-audio --start-bar 65 --bars 32 \
  --output .ableton-audits/renders/drop_1_full_mix.wav
abletonctl render-audio --solo-group Drums --start-bar 65 --bars 32 \
  --output .ableton-audits/renders/drop_1_drums_bus.wav
abletonctl render-audio --solo-group Sub --start-bar 65 --bars 32 \
  --output .ableton-audits/renders/drop_1_bass_bus.wav
abletonctl render-audio --solo-track Kick --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_kick_solo.wav
abletonctl render-audio --solo-track Snare --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_snare_solo.wav

bin/ableton-audioqa analyze --file .ableton-audits/renders/drop_1_kick_solo.wav \
  --target kick --output .ableton-audits/reports/drop_1_kick_solo.audioqa.json
bin/ableton-audioqa analyze --file .ableton-audits/renders/drop_1_snare_solo.wav \
  --target snare --output .ableton-audits/reports/drop_1_snare_solo.audioqa.json
bin/ableton-audioqa analyze --file .ableton-audits/renders/drop_1_full_mix.wav \
  --target drop --output .ableton-audits/reports/drop_1_full_mix.audioqa.json

bin/ableton-audioqa summarize-section --section "Drop 1" --bars "65-97" \
  --reports ".ableton-audits/reports/drop_1_*.json" \
  --output .ableton-audits/reports/drop_1_summary.audioqa.json
```

The optional `llm-critic` command may add musical notes after deterministic
analysis, but it never overrides hard gate failures.
