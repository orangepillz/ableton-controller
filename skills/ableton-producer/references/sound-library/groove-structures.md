# Groove, Editing, And Arrangement Moves

Use this file when the request is about feel, timing, fills, density, or
arrangement trickery rather than a single device patch. Default target group is
usually `Drums`, but some moves apply to `Synths`, `Vox`, or `FX`.

## Core Groove Commands

Read before editing:

```sh
abletonctl clips --track "Drums"
abletonctl midi-get-notes --track "Drums" --slot 0 --start 0 --end 8
```

Humanize hats/percussion:

```sh
abletonctl midi-transform-notes --track "Hats" --slot 0 --start 0 --end 8 --pitch-min 42 --pitch-max 46 --velocity-deviation 8 --probability 0.94
```

Duplicate a response:

```sh
abletonctl midi-duplicate-region --track "Bass" --slot 0 --start 0 --length 2 --destination-time 2 --transpose 7
```

## Percussive Fills

Rapid-fire rhythmic embellishments. See `drums-breaks.md` for drum sound
choices; use this when the main question is where the fill goes.

Placement rules:
- Bar 4 or 8 endings get the most obvious fills.
- Tiny microfills can answer vocals or bass gaps every 1 or 2 bars.
- Leave a short breath before a heavy downbeat unless the style demands a smear.

## Shuffles / Ghost Hats

Quiet syncopated percussion adding groove and swing.

CLI moves:
- Add low-velocity hats between main hats.
- Shift selected offbeats slightly late with `midi-update-notes` after reading
  note IDs.
- In tech house, keep the main offbeat hat steady and let ghost hats move.

## Ghost Notes

Very quiet in-between snare, kick, or percussion hits adding groove and realism.

CLI moves:
- Velocities around 30 to 70, short durations.
- Avoid ghosting the main downbeat unless a lurching feel is intended.
- Use probability for subtle variation.

## Shuffle / Swing

Deliberately off-grid timing giving a drunken or funky feel.

CLI moves:
- For new notes, write later offbeat start times manually.
- For existing notes, read note IDs and update selected starts.
- Preserve kick/snare anchors unless the whole groove should sag.

## Microtiming Push/Pull

Tiny timing offsets that create human groove tension.

CLI moves:
- Push percussion slightly early for urgency.
- Pull hats/shakers slightly late for funk.
- Keep bass and kick relationship tight unless the looseness is intentional.

## Syncopation

Accents landing in unexpected rhythmic pockets.

CLI moves:
- Place bass, rim, vocal chop, or percussion hits on e, a, or offbeat positions.
- Use velocity accents to reveal the syncopation.
- Works especially well in tech house bass and glitch hop drums.

## Polyrhythms

Multiple rhythmic divisions layered simultaneously.

CLI moves:
- Layer 3-over-4 or 5-over-4 percussion against a steady kick/snare grid.
- Use short muted percussion so the pattern intrigues rather than clutters.
- Keep one anchor element simple.

## Tuplet Fills

Triplet, quintuplet, or septuplet-style fills against straight rhythms.

CLI moves:
- Approximate tuplets with carefully placed MIDI starts, or use a rendered audio
  fill source when exact tuplets are not ergonomic through CLI.
- Use sparingly before transitions or as a bass answer.
- Verify note timing with `midi-get-notes`.

## Microfills

Tiny 1/16 or 1/32 edits between beats that keep tracks evolving.

CLI moves:
- Add one or two clicks, zaps, hats, or drum hits in a gap.
- Keep velocity low unless it is a transition.
- Pan slightly or add short delay so the detail does not fight the main groove.

## Call-and-Response Drumming

Rhythmic phrases answering each other.

CLI moves:
- Put a "call" on a strong beat and a lighter "response" later in the bar.
- Use different timbres: snare to tom, click to zap, rim to foley.
- Avoid constant answers; leave some bars unanswered for contrast.

## Question/Answer Fills

Alternating rhythmic motifs between bars.

CLI moves:
- Bar 1 asks with a short fill; bar 2 answers with a variation or register
  change.
- Duplicate and transpose/shift the region, then edit velocities.
- Works for drums and bass alike.

## Stop-Time Edits

Sudden pauses or rhythmic cutouts.

CLI moves:
- Mute, split, or leave empty notes for 1/8 to 1 bar.
- Use a tiny vocal chop or zap in the silence if the pause needs personality.
- Any deletion or clearing of existing material needs approval.

## Fake Drops

Drum tension implies a drop before pulling away.

CLI moves:
- Build riser, snare rush, or fill to the expected downbeat.
- Remove or delay the first kick/sub hit, add silence or a small ear-candy hit.
- Bring the true impact back 1/2 to 1 bar later.

## Stutter Edits

Tiny repeated fragments creating rhythmic glitches.

CLI moves:
- For MIDI, write repeated notes or duplicate a small region.
- For audio, split/copy a short fragment.
- For device flavor, automate Beat Repeat/Redux only during the stutter.

## Retriggers

Rapidly repeated hits from one source sound.

CLI moves:
- Repeated MIDI notes are more deterministic than relying on a device.
- Use velocity ramps for snare and hat retriggers.
- Keep duration short to avoid flams unless desired.

## Ratchets

Burst-fire drum subdivisions common in trap and glitch.

CLI moves:
- Use 1/32 or 1/64 hats, snares, or zaps in short groups.
- Alternate velocity and pan to avoid machine-gun flatness.
- Best placed before a barline or as a bass call response.

## Broken Beat Grooves

Non-linear rhythms avoiding standard four-on-the-floor structure.

CLI moves:
- Keep a strong snare or clap anchor while moving kicks and percussion around it.
- Use ghost notes and syncopated bass to imply the pulse.
- Works well for glitch hop, deep dub, and experimental bass.

## IDM Programming

Extremely intricate non-repeating drum sequencing.

CLI moves:
- Build in short 1 or 2 bar cells, then duplicate and mutate.
- Vary velocity, probability, timbre, and timing in each copy.
- Keep a simple sub or pad anchor so the listener has orientation.

## Boom-Bap Influence

Hip-hop inspired kick/snare pocketing.

CLI moves:
- Strong kick/snare sample choices, swung hats, and ghost snares.
- Use break fragments and lower tempo ranges for glitch hop/trip-hop.
- Avoid over-quantizing; the pocket is the point.

## Trip-Hop Grooves

Slower smoky swung rhythms.

CLI moves:
- Use lower tempos, dusty breaks, quiet ghost notes, and roomy percussion.
- Add vinyl/noise texture only if it supports the song.
- Keep bass simple and warm.

## Funk Pocket Drumming

Groove-first syncopated rhythmic feel.

CLI moves:
- Accentuate offbeats, ghost snares, and shaker waves.
- Use question/answer between percussion and bass.
- Let some hits arrive late for feel.

## Humanized Velocity

Different hit strengths for realism and groove.

CLI moves:
- Use `midi-transform-notes --velocity-deviation` for existing hats/percussion.
- Main kick/snare anchors should change less than ghost notes.
- Velocity should create phrasing, not randomness for its own sake.

## Dynamic Accenting

Constantly changing rhythmic emphasis.

CLI moves:
- Emphasize different 1/16 positions across repeated bars.
- Vary bass and percussion velocities together for call/response.
- Tech house benefits from subtle velocity-to-filter bass accents.

## Percussive Ear Candy

Tiny one-shot details hidden in the stereo field.

CLI moves:
- Use clicks, zaps, foley, vocal crumbs, or rim taps.
- Keep them low volume and rhythmically placed.
- Pan or delay them so they are discovered on repeat listens.

## Stereo Percussion Movement

Drum elements panning dynamically around the mix.

CLI moves:
- Use static pan with `set-track` for separate percussion tracks.
- For moving one-shots, automate device/rack pan if exposed, or use track-level
  moves over a safe range.
- Keep kick, snare, sub, and lead vocal centered.

## Calligraphic Editing

Extremely detailed micro-editing where nearly every transient is shaped.

CLI moves:
- Work from duplicates or newly created clips.
- Split/copy small regions, then verify after each group of edits.
- Use this for high-detail experimental sections, not every part of a track.

## Breathing Grooves

Rhythms intentionally leaving negative space.

CLI moves:
- Remove or avoid notes before major bass hits and snares.
- Use rests as an arrangement device.
- This is core to Detox/Tipper-adjacent detail: the small sounds need silence
  around them to be audible.

## Elastic Timing

Groove subtly stretching or compressing over time.

CLI moves:
- For MIDI, update selected note starts gradually across a phrase.
- For audio breaks, add/move warp markers rather than forcing every transient to
  the grid.
- Use carefully; too much elasticity weakens club impact.
