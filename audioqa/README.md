# Ableton AudioQA

`ableton-audioqa` analyzes rendered WAV probes from Ableton and returns stable
JSON reports for Codex patch loops. Rendered audio is the source of truth; device
settings and automation lanes are only hypotheses until the file passes gates.

## Commands

Analyze one render:

```sh
bin/ableton-audioqa analyze \
  --file .ableton-audits/renders/drop_1_kick_solo.wav \
  --target kick \
  --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_solo.audioqa.json
```

Compare a solo render against context:

```sh
bin/ableton-audioqa compare \
  --primary .ableton-audits/renders/drop_1_kick_solo.wav \
  --context .ableton-audits/renders/drop_1_full_mix.wav \
  --target kick-audibility \
  --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_context.audioqa.json
```

Learn local reference features:

```sh
bin/ableton-audioqa learn-references \
  --root .ableton-copilot/references \
  --output .ableton-copilot/reference_features.json
```

Summarize a section:

```sh
bin/ableton-audioqa summarize-section \
  --section "Drop 1" \
  --bars "65-97" \
  --reports ".ableton-audits/reports/drop_1_*.json" \
  --output .ableton-audits/reports/drop_1_summary.audioqa.json
```

## Targets

The v1 gate registry supports `kick`, `snare`, `wub`, `growl`, `yoi`,
`talking-bass`, `bass-bus`, `reese`, `glitch`, `microfill`, `riser`,
`downlifter`, `drop`, `full-mix`, and `transition`.

Comparison targets are `kick-audibility`, `snare-audibility`, `bass-masking`,
`low-end-masking`, `drop-vs-build-energy`, and `transition-impact`.
