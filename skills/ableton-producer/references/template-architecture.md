# Template Architecture

The open set is the starting template for new projects. Preserve this
architecture unless the user explicitly approves changing it.

## Current Hierarchy

Top-level groups:

- `SC`: protected sidechain infrastructure.
  Existing children: `SC In`, `SC Trigger`.
  `SC In` hosts the LFO Tool volume envelope; `SC Trigger` is the MIDI trigger
  track that drives that envelope. Music groups that should duck are routed into
  `SC In`, so verify output routing before changing this path.
- `Drums`: drum machines, drum racks, samples, percussion, and drum subgroups.
  Existing children: `5-Maschine 2`, `TR8S`, `Kicks`, `Snares`, `Cymbols`, `Percs`.
- `Sub`: mono low-end instruments and sub/808 layers.
  Existing child: `28-Operator`.
- `Synths`: leads, pads, chords, arps, mid-bass synths, melodic instruments.
  Existing child: `30-Audio`.
- `Vox`: vocal recordings, chops, throws, spoken samples.
  Existing child: `32-Audio`.
- `FX`: risers, impacts, noise, transitions, ear candy, global print tracks when no source group is obvious.
  Existing child: `34-MIDI`.

Nested drum groups:

- `TR8S`: `BD`, `SD`, `LT`, `MT`, `HT`, `RS`, `HC`, `CH`, `OH`, `CC`, `RC`.
- `Kicks`: `19-Simpler`, `20-Audio`.
- `Snares`: `22-Simpler`.
- `Cymbols`: `24-Audio`. Preserve the template spelling.
- `Percs`: `26-Audio`.

Returns:

- `A-Reverb`
- `B-Delay`

Master:

- `Main`

## Placement Policy

- Prefer existing tracks and groups. Rename, populate, or process an existing empty/starter track when that satisfies the request more cleanly than adding a new track.
- Never create a new regular track at the top level unless the user explicitly approves that structural change.
- Never create a new group outside the known top-level groups without approval. If a new subgroup is musically useful, place it inside the correct top-level group and preview the plan first.
- New return tracks affect the global mix architecture. Ask before creating returns or broad bus/routing structures.
- Duplicating a track is allowed only when the duplicate remains inside the same intended group; verify the duplicate's group after creation.
- Treat `SC In`, `SC Trigger`, and routes into `SC In` as protected sidechain
  infrastructure. Do not repurpose these tracks for creative material, and ask
  before changing the LFO Tool, trigger MIDI, or group output routing.

## Role Mapping

- Sidechain/control: `SC`, using `SC In` for the ducked audio path and
  `SC Trigger` for the MIDI envelope trigger. Do not add normal musical parts
  here.
- Drum machine and full drum racks: `Drums`; use `TR8S` only for the existing TR-8S-style lanes.
- Kicks: `Drums` -> `Kicks` when using kick sample/instrument tracks; existing `BD` when editing the TR-8S kick lane.
- Snares and claps: `Drums` -> `Snares` for sample/instrument tracks; existing `SD` when editing the TR-8S snare lane.
- Hats/cymbals: `Drums` -> `Cymbols` for sample/instrument tracks; existing `CH`, `OH`, or `HC` when editing TR-8S hat lanes.
- Percussion, toms, rims, claps, rides: `Drums` -> `Percs` unless the request clearly targets an existing TR-8S lane.
- Sub bass, 808, pure sine/triangle low end: `Sub`.
- Mid-bass, leads, pads, plucks, chords, arps, melodic synths: `Synths`.
- Vocal recordings, chops, throws, adlibs: `Vox`.
- Risers, sweeps, downlifters, impacts, atmospheres, noise, transition one-shots: `FX`.
- Resampling/print tracks: place inside the source's group when printing a specific source; use `FX` only for global transition/ear-candy prints or when the source is intentionally mixed.

## Safe Creation Workflow

1. Run `abletonctl session-snapshot` or `abletonctl tracks`.
   For sidechain-sensitive work, also inspect `SC In`, `SC Trigger`, and the
   current output routing of the relevant source groups.
2. If placement matters, inspect group metadata:

```sh
abletonctl lom-get 'song.tracks[N].is_foldable'
abletonctl lom-get 'song.tracks[N].is_grouped'
abletonctl lom-get 'song.tracks[N].group_track.name'
```

3. Choose the target group from the role mapping and prefer an existing child track.
4. If a new track is needed, create it with `--index` inside the target group.
   The safest insertion point is usually before an existing child of the target
   group; inserting at the end of a group is allowed only when the current
   hierarchy makes that boundary unambiguous.
5. Immediately verify the created track:

```sh
abletonctl tracks
abletonctl lom-get 'song.tracks[N].group_track.name'
```

6. If the new track is not in the intended group, stop. Use `abletonctl undo` only if the failed placement was the last change and undo will not erase user work; otherwise ask how to proceed.

When the insertion index is uncertain, present a dry-run plan with the target
group and intended index instead of guessing.
