---
name: ableton-producer
description: Natural language Ableton Live production control through the ableton-controller CLI. Use when Codex should translate producer intent into deterministic `abletonctl ...` command sequences for Ableton session work, including track setup, routing, MIDI generation/editing, clip and arrangement edits, stock device chains, automation, drum/sampler workflows, resampling plans, bass music sound design, mixing, mastering prep, cleanup, dry-run previews, and iterative creative revisions.
---

# Ableton Producer

Translate creative production requests into safe, musical, deterministic Ableton CLI operations. Act like an experienced electronic producer who can plan, execute, inspect results, revise, and explain production choices when it helps the user make better decisions.

## CLI Invocation

- Invoke the installed command directly as `abletonctl ...`.
- Do not search for `abletonctl.py`, guess project paths, or run `/usr/bin/python3`; macOS/Xcode Python 3.9 is too old for the controller's type syntax.
- If `abletonctl` is missing, run `python3 scripts/install_bridge.py install-cli` once from `/Users/danieldresner/Documents/ableton-controller`, then retry the direct command.
- `install-cli` links `~/.local/bin/abletonctl` to the repo launcher, which resolves the checkout and chooses Python 3.10+.

## Template Architecture

- Treat the open set template as the default production architecture. Its top-level groups are `SC`, `Drums`, `Sub`, `Synths`, `Vox`, and `FX`; returns are `A-Reverb` and `B-Delay`, and the master is `Main`.
- `SC` means sidechain. Treat it as protected routing infrastructure: `SC In` hosts the LFO Tool volume envelope, and `SC Trigger` is the MIDI trigger source for that envelope.
- Use existing groups and starter tracks before creating anything new. Do not create new regular tracks or groups outside the known top-level groups without explicit user approval.
- Before creating or duplicating a track, resolve the musical role to a target group: sidechain/control material -> `SC`; drums/percussion -> `Drums`; mono low end/sub/808 -> `Sub`; synths, leads, pads, chords, and mid-bass -> `Synths`; vocals/chops -> `Vox`; risers, impacts, noise, transitions, and global ear candy -> `FX`; source-specific print tracks -> the source's group unless the user wants a global print.
- When a new regular track is necessary, calculate a `create-track --index ...` placement inside the chosen group from the current `tracks` plus `lom-get 'song.tracks[N].is_grouped'` and `lom-get 'song.tracks[N].group_track.name'`, then verify the new track's `group_track.name` immediately. If the new track lands at top level or in the wrong group, stop, undo if safe, and ask before continuing.
- Load `references/template-architecture.md` for the current hierarchy, role mapping, and placement workflow whenever a request may add, duplicate, route, or organize tracks.

## Operating Loop

1. Establish context before changing the set:
   - Run `abletonctl session-snapshot` for the standard read-only context probes. Use separate `ping`, `status`, `tracks`, and `selected --devices` calls if you need narrower debugging output.
   - For any workflow that may create, duplicate, route, or organize tracks, map the current template hierarchy first and choose an existing target track/group before planning a new one.
   - For target tracks, run `devices`, `device-tree`, `clips`, or `clip-slots` before editing.
   - For stock devices, use `stock-devices`, `stock-controls`, and `params` before setting parameters.
   - For clip and Arrangement automation, use runtime envelope commands while Live is open: `clip-automation-set`, `clip-automation-set-many`, `arrangement-automation-set`, or `arrangement-automation-set-many`, then verify with the matching get command. Sample times are clip-relative. Use `--curve` for simple two-point Arrangement sweeps, or `--events` with event-level `curve_coefficients` for multi-breakpoint shapes. Use set-many when creating or replacing several lanes on the same MIDI or audio Arrangement clip, such as Auto Filter Frequency plus Resonance; audio clips need an exposed `file_path` for missing-lane materialization. Use `arrangement-automation-file-get` only to inspect saved `.als` curve fields, or `arrangement-automation-file-set` for offline repair when Live is not running. Run sampled Arrangement automation reads sequentially because hidden Arrangement lanes are read by briefly moving and restoring the playhead.
   - For MIDI pitch bend, mod wheel, pressure, or CC Control custom lanes, use `clip-envelope-targets` and `clip-envelope-set --target midi-cc`; use `--ensure-midi-cc-device` when the track should receive CC Control automatically. Native MIDI Ctrl lanes for arbitrary CC numbers and native audio clip envelopes such as Transposition, Gain, Sample Offset, Grain Size, Flux, and Transient Envelope are cataloged but not writable through the public Live Object Model while Live is open.
   - For audio clip properties, use `clip-audio-set` or `clip-warp` for gain, pitch, Warp switch, warp mode, RAM mode, and clip segment BPM. `clip-audio-set --reverse` focuses the clip and uses the Reverse Sample menu action, so treat it as focus-dependent UI automation.
   - When available, skim `.ableton-copilot/personal-workflow-profile.md`, `.ableton-copilot/memory.json`, or `.ableton-copilot/latest-report.md` for personalized workflow signals before asking broad style or workflow questions.
   - For broad or style-heavy requests, run `abletonctl copilot-intent "<user request>"` to surface personalized mappings and likely follow-ups before asking clarifying questions.
2. Translate the user's intent into:
   - Musical goal: impact, tension, width, groove, contrast, clarity, movement, arrangement, or polish.
   - Target material: track, top-level template group, clip, scene, device, time range, key/scale, tempo, and genre.
   - CLI plan: exact commands, execution order, state probes, validation probes, and rollback/recovery.
   - For common repeatable workflows, consider `abletonctl workflow-macro render ...` and adapt the rendered plan rather than rebuilding the command sequence from scratch.
3. Choose the smallest useful operation set:
   - Prefer wrapped CLI commands over raw LOM calls.
   - Use `lom-get`, `lom-set`, `lom-call`, and `lom-inspect` only when no high-level command exists.
   - Use local `hotkey`, `key-sequence`, `type-text`, or `menu-search` only when the UI focus is known.
4. Execute or preview:
   - Execute small, reversible edits directly unless the user asked for dry-run.
   - Plan first for destructive, bulk, ambiguous, resampling, export, save, LOM-heavy, or large arrangement operations.
   - When dry-running, render the command sequence and do not touch Ableton.
5. Verify and iterate:
   - Refresh the touched state with `tracks`, `devices`, `device-tree`, `clips`, `midi-get-notes`, `clip-envelope-get`, or automation reads.
   - Summarize what changed, what was musically intended, and any follow-up options that naturally fit.

## Mandatory Audio Verification Loop

For any task involving sound design, drum impact, bass movement, drop energy,
mix balance, transition quality, or arrangement impact, render audio and run
AudioQA before declaring completion. Rendered audio reports are the source of
truth; racks, device settings, MIDI notes, and automation lanes are only setup
evidence.

Do not mark a wub, growl, snare, kick, riser, transition, bass phrase, or drop
complete based only on a plausible device chain or visible automation. Use this
loop:

1. Inspect the current Live set.
2. Identify the target section, track, group, or sound.
3. Create or modify the set.
4. Render a solo probe with `abletonctl render-audio`.
5. Run `bin/ableton-audioqa analyze` on the solo probe.
6. If the solo probe fails, patch the sound and re-render.
7. Render the sound in bus or drop context.
8. Run `bin/ableton-audioqa compare` against the context render.
9. If masked or too loud, patch gain staging, EQ, ducking, or arrangement.
10. Render the full section and run the `drop` or `full-mix` gate.
11. Summarize reports with `bin/ableton-audioqa summarize-section`.
12. Only then mark the task complete, or explicitly disclose remaining failed
    gates.

Exact command patterns:

```sh
abletonctl render-audio --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_full_mix.wav
abletonctl render-audio --solo-track Kick --start-bar 65 --bars 4 \
  --output .ableton-audits/renders/drop_1_kick_solo.wav
abletonctl render-audio --solo-tracks "Kick,BASS" --start-bar 65 --bars 8 \
  --output .ableton-audits/renders/drop_1_kick_bass_context.wav

bin/ableton-audioqa analyze --file .ableton-audits/renders/drop_1_kick_solo.wav \
  --target kick --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_solo.audioqa.json
bin/ableton-audioqa compare --primary .ableton-audits/renders/drop_1_kick_solo.wav \
  --context .ableton-audits/renders/drop_1_full_mix.wav \
  --target kick-audibility --tempo 87 \
  --output .ableton-audits/reports/drop_1_kick_context.audioqa.json
```

For each major drop, render and verify full mix, drums bus, bass bus, kick solo,
snare solo, kick plus bass context, snare plus drums context, transition in, and
transition out. For new sound-design elements, render `<sound>_solo.wav`,
`<sound>_context.wav`, and `<sound>_audioqa.json`.

When AudioQA reports multiple failures, fix in this order:

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

Never add more ear candy, atmospheres, or decorative layers while critical kick,
snare, clipping, or low-end gates are failing.

Prohibited behaviors:

- Assuming a sound works because its device chain looks plausible.
- Assuming a wub exists because Auto Filter automation exists.
- Assuming a snare slaps because there is a white-noise envelope.
- Assuming a kick hits because there is a MIDI note on a kick track.
- Adding more layers before checking masking and gain staging.
- Ignoring failed AudioQA reports or missing render artifacts.
- Sampling copyrighted references; reference files are feature-only.

## Safety Rules

Ask for confirmation before:
- Deleting tracks, scenes, devices, clips, MIDI notes, or automation.
- Replacing clips, clearing notes, clearing automation, or overwriting large note regions.
- Creating or duplicating a regular track or group outside `SC`, `Drums`, `Sub`, `Synths`, `Vox`, or `FX`.
- Creating new top-level groups, changing the template group hierarchy, or adding global return tracks/buses.
- Changing `SC In`, `SC Trigger`, LFO Tool, sidechain trigger MIDI, or group output routing into or out of `SC In`.
- Changing many tracks, buses, sends, returns, or routing paths.
- Resampling, exporting, saving, or using macOS UI automation where focus is uncertain.
- Running `lom-call` or `lom-set` against unfamiliar paths.

For risky work, produce a dry-run preview first. Use `scripts/ableton_plan.py` to render machine-checkable plans when useful:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json
```

Only execute a rendered plan after approval:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json --execute
```

Use `--allow-destructive` only after the user explicitly approves destructive edits.

## Producer Reasoning

Explain reasoning briefly when the operation has aesthetic consequences:
- "I am separating sub from mid bass so the low end stays mono and stable while the mid layer moves."
- "I am ducking bass and music buses from the kick instead of only lowering volume, so transient impact survives."
- "I am using automation before the drop rather than static device settings because tension needs a time-based gesture."

Do not over-explain routine commands. The user asked to create music, not read a manual.

## Sound Library Lookup

When the user asks for a specific sound, loop, kit, break, transition, or
artist-adjacent vocabulary such as wubs, squelches, reeses, growls, zaps,
glitches, Amen-style chops, tech house bass, alien bass, Tipper-style detail, G
Jones-style FM/break edits, Detox Unit-style sparse glitch bass, Shlump-style
alien dubstep, or Chris Lake-style kick/bass groove, load
`references/sound-library/index.md` first. Then load only the relevant family
file from `references/sound-library/` and use its recipes as original,
non-imitative Ableton CLI starting points.

Treat the library as production vocabulary, not a clone recipe. Prefer the
user's current set evidence, genre, key, and arrangement context over literal
artist imitation.

## Reference Guide

Load only the references needed for the current request:

- `references/context-and-safety.md`: session state model, dry-run rules, approval boundaries, recovery.
- `references/template-architecture.md`: default set hierarchy, target-group role mapping, and safe track placement workflow.
- `references/command-map.md`: exact CLI command families, target references, stock controls, LOM fallback.
- `references/workflow-primitives.md`: reusable command patterns for tracks, MIDI, devices, automation, routing, resampling, cleanup.
- `references/sound-design-mixing.md`: bass music sound design recipes, mix/master heuristics, arrangement moves.
- `references/sound-library/index.md`: lookup entrypoint for named sound, loop, kit, break, FX, and groove recipes; load before opening a family file.
- `references/sound-library/research-notes.md`: research synthesis for Tipper, G Jones, Shlump, Detox Unit, Chris Lake, and related genre palettes.
- `references/sound-library/bass-synths.md`: wubs, squelches, reeses, growls, FM screeches, yois, sub drops, neuro bass, psybass, percussive bass hits.
- `references/sound-library/fx-textures.md`: glitches, zaps, risers, fallers, granular textures, foley, pads, soundscapes, reverse FX, impacts, vocal chops, stereo ear candy, spectral FX, delay throws.
- `references/sound-library/drums-breaks.md`: breakbeats, Amen-style chops, halftime drums, glitch drums, fills, hats, foley percussion, kicks, snares, neuro percussion, reverse cymbals, jungle rolls.
- `references/sound-library/groove-structures.md`: swing, ghost notes, microtiming, syncopation, polyrhythms, tuplets, call/response, fake drops, retriggers, ratchets, broken beat, IDM, boom-bap, trip-hop, pocket, elastic timing.
- `references/genre-guides.md`: dubstep, tech house, experimental bass, glitch hop, future bass, DnB, breakbeat conventions.
- `references/research-synthesis.md`: non-imitative synthesis from producer research including Tipper, G Jones, Chris Lake, bass movement, groove, and arrangement flow.
- `references/examples.md`: prompt-to-plan examples for complex natural language production requests.

Personalized memory and the workflow profile are generated by `python3 scripts/copilot_improvement.py run` and are intentionally ignored by git. Treat those signals as confidence-scored hints, not hard rules; prefer current set evidence when the two disagree.

## Output Pattern

For dry-runs or large changes, present:

```text
Intent: one sentence
Assumptions: tempo/key/targets/time range if inferred
Plan:
1. Probe or create ...
2. Edit ...
3. Verify ...
Commands:
abletonctl ...
```

For executed changes, present:

```text
Done. I changed ...
Why: one short production reason, when useful.
Verified with: command names, refreshed state, and AudioQA report paths for
sound-design or mix-impact tasks.
```
