# Context And Safety

## Session Snapshot

Maintain this state mentally across an operation and refresh it after edits:

- Transport: tempo, time signature, playing/stopped state, selected track.
- Structure: track names, indices, kinds, returns, master, scenes, relevant clip slots.
- Template hierarchy: top-level groups, nested drum groups, each target track's `is_grouped` and `group_track.name` when creating or moving material.
- Musical metadata: requested or inferred key, scale, genre, section labels, bar range.
- Track roles: kick, snare/clap, hats, percussion, sub, mid bass, lead, pad, vocal, FX, buses, returns, master.
- Sidechain state: `SC In` LFO Tool, `SC Trigger` MIDI trigger, and source-group output routing into `SC In`.
- Device state: top-level devices, rack paths from `device-tree`, stock control names, current parameter values.
- Clip refs: session `--track` plus `--slot`, arrangement `--track` plus `--arrangement-start` or `--arrangement-index`, or a LOM `--path`.
- Pending risk: destructive commands, bulk scope, UI automation, uncertain targets, user approval.

## Minimum Probes

Start most workflows with:

```sh
abletonctl session-snapshot
```

For narrower debugging or when you need separate outputs, use:

```sh
abletonctl ping
abletonctl status
abletonctl tracks
abletonctl selected --devices
```

Then probe the target domain:

```sh
abletonctl devices --track "Bass"
abletonctl device-tree --track "Bass" --depth 5
abletonctl clips --track "Bass"
abletonctl midi-get-notes --track "Bass" --slot 0 --start 0 --end 4
abletonctl stock-controls --device "Auto Filter"
abletonctl params --track "Bass" --device "Auto Filter"
abletonctl devices --track "SC In"
```

## Targeting Rules

- Prefer exact names for newly created tracks and clips.
- Prefer indices only after reading `tracks`, `clips`, or `device-tree`.
- If a name is ambiguous, stop and resolve it with indices instead of guessing.
- Before adding or duplicating a regular track, choose one of the template top-level groups: `SC`, `Drums`, `Sub`, `Synths`, `Vox`, or `FX`.
- Use `SC` only for sidechain infrastructure. Normal musical material belongs in `Drums`, `Sub`, `Synths`, `Vox`, or `FX`.
- Reuse existing tracks or starter tracks inside those groups before creating a new track.
- If creating a track, use `create-track --index` to place it inside the selected group and verify the result with `lom-get 'song.tracks[N].group_track.name'`.
- Ask before creating a top-level track, a new top-level group, a broad bus/return structure, or any track outside the template groups.
- For nested rack devices, use `device-tree` paths and then `--device-path`.
- For arrangement edits, be explicit about bars/beats. At 4/4, bar 17 starts at beat 64.

## Dry-Run Plan JSON

Use this shape with `scripts/ableton_plan.py` when the plan should be previewed or audited:

```json
{
  "summary": "Make the drop hit harder by tightening kick/sub space and adding controlled mid-bass movement.",
  "assumptions": ["Drop starts at beat 64", "Bass track is named Bass"],
  "commands": [
    {
      "why": "Read current set state before editing.",
      "args": ["status"]
    },
    {
      "why": "Inspect the bass chain before adding movement.",
      "args": ["device-tree", "--track", "Bass", "--depth", "5"]
    }
  ]
}
```

Run dry:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json
```

Run after approval:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json --execute
```

For approved destructive execution:

```sh
python3 skills/ableton-producer/scripts/ableton_plan.py plan.json --execute --allow-destructive
```

## Risk Classes

Small reversible changes:
- Add a track inside an approved template group, create a new clip, add a device, set a single parameter, set tempo, create a scene, add notes to an empty new clip.

Plan first:
- Creating a new subgroup inside a template group, multi-track routing, bus setup, sidechain setup, bulk send changes, arrangement section edits, long MIDI rewrites, rack construction, resampling preparation.

Require approval:
- New top-level regular tracks or groups outside `SC`, `Drums`, `Sub`, `Synths`, `Vox`, or `FX`.
- New return tracks or global mix buses.
- Changes to `SC In`, `SC Trigger`, LFO Tool, sidechain trigger MIDI, or group output routing into/out of `SC In`.
- `delete-track`, `delete-scene`, `device-delete`, `clip-delete`.
- `midi-clear-notes`, `midi-replace-notes`, broad `midi-remove-notes`.
- `clip-automation-clear`, `clip-stock-automation-clear`, `clip-envelope-clear`.
- `clip-create-midi --replace`, `clip-create-audio --replace`.
- `save`, export menu actions, `clip-audio-set --reverse`, focus-dependent UI automation, unfamiliar `lom-set` or `lom-call`.

## Recovery

If a command fails:

1. Read the error and do not blindly retry.
2. Re-probe the likely stale object: `tracks`, `devices`, `device-tree`, `clips`, or `params`.
3. If a name is ambiguous, rerun with the exact index/path from probe output.
4. If a stock control fails, run `stock-controls --device ... --control ...` and use the returned alias.
5. If a clip slot already has a clip, either choose a free slot or ask before using `--replace`.
6. If a local macOS command fails, mention Accessibility or focus requirements and switch to a bridge/LOM command when possible.
7. If the edit partially succeeded, refresh touched state and explain the clean continuation path.

Use `abletonctl undo` only when the last command clearly caused the unwanted edit and undo will not erase user work performed after it.
