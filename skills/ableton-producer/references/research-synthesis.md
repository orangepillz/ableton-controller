# Research Synthesis

Use this file when the user asks for inspiration from Tipper, G Jones, Chris Lake, experimental bass, tech house, bass movement, resampling, groove, or arrangement flow. The goal is original synthesis: translate observed principles into the user's own project, not imitation.

## Non-Imitation Rule

- Do not recreate identifiable melodies, bass patches, drops, arrangements, or signature transitions from any named artist.
- Use references as abstract production constraints: density, movement, restraint, contrast, sound-system translation, and arrangement logic.
- Prefer current set evidence and the user's taste over artist-name defaults.
- If the user asks for "like Tipper/G Jones/Chris Lake," translate that into a neutral production target and say what you are borrowing at the principle level.

## Source Notes

- [TPi: One-Source Productions on Tipper & Friends audio](https://www.tpimagazine.com/one-source-productions-delivers-unprecedented-audio-for-tipper-friends/) describes Tipper performances as highly detailed, clean in the low end, spatially dynamic, and dependent on system-aware presentation.
- [Optimal Breaks: Tipper profile](https://www.optimalbreaks.com/en/artists/tipper) frames Tipper through technical breaks, elastic low end, intricate edits, and immersive sequencing.
- [EDM.com: G Jones interview](https://edm.com/interviews/g-jones-interview/) describes a process of finding riffs, recording long synth takes with live parameter movement, then chopping the best material into arrangements.
- [MusicRadar: Chris Lake interview](https://www.musicradar.com/news/chris-lake-interview) emphasizes sketching many small ideas, saving clips, reusing strong kick/bass combinations, and staying centered on personal taste.
- [EDM.com: Chris Lake on taking risks](https://edm.com/interviews/chris-lake-interview-2026-protect-culture-taking-risks/) emphasizes stepping back from pressure, following emotion first, and resisting formulaic output.
- [Ableton: Bass Shapes](https://www.ableton.com/de/blog/vespers-tutorial-bass-shapes/) highlights layered effect shaping for memorable bass.
- [Ableton: Sub Bass, Chords and FX](https://www.ableton.com/en/blog/step-by-step-guide-for-sub-bass-chords-and-fx/) highlights layering synth instances, sub anchoring, pitch glides, reverb, racks, and glitch FX.
- [Ableton Live 12 Routing and I/O](https://www.ableton.com/en/manual/routing-and-i-o/) documents Resampling as routing the Main output into an audio track, then recording it into clip slots.
- [MusicRadar: Ableton Auto Filter movement](https://www.musicradar.com/tutorials/music-production-tutorials/6-ways-to-bring-your-tracks-to-life-with-ableton-lives-revamped-auto-filter) shows filter modes, envelope following, LFO movement, and sidechain-driven bass motion.
- [MusicRadar: Creative distortion in Ableton Live](https://www.musicradar.com/music-tech/5-creative-ways-to-use-distortion-in-ableton-live-from-punchier-drums-to-dub-techno-delays) describes rhythmic distortion movement with Roar, Saturator weight, and modulation-driven character.
- [BassGorilla: Resampling in Ableton Live](https://bassgorilla.com/resampling-in-ableton-live-tutorial/) frames resampling as printing a synth/effects chain back into audio for fresh editing.
- [Isotonik Studios: From a Single Sine Wave to Usable Basslines](https://isotonikstudios.com/from-a-single-sine-wave-to-usable-basslines/) describes a modern bass workflow using modulation, distortion, resampling, slicing, and one-shot extraction.
- [Ableton Live Audio Effect Reference](https://www.ableton.com/en/live-manual/11/live-audio-effect-reference/) documents device behavior useful for distortion, Beat Repeat, filtering, and resampling-style pitch/time effects.

## Synthesis Heuristics

### Tipper-Inspired Principles

Translate to: sculptural rhythm, clean low end, spatial detail, and careful restraint.

- Treat rhythm as contour, not only grid. Use holes, shuffled edits, and short artifacts to make a phrase feel carved.
- Separate sub foundation from mid/high sound-design motion. If the sub moves too much, keep the mid layer expressive and the low layer simple.
- Build system-aware contrast: dry transient detail, intentional reverb tails, and panning moves that do not smear mono impact.
- Prefer fewer high-quality gestures over constant activity. A single warped fill, reverse tail, or stereo flick can carry more weight than dense decoration.
- Verify low-end plans through kick/sub reads, mono-safe utility, and conservative bus processing rather than master loudness.

CLI planning moves:

```sh
abletonctl session-snapshot --track "Sub" --track "Mid Bass" --device-tree-depth 4
abletonctl workflow-macro render kick-sub-separation --kick-track Kick --track Sub --start 0 --length 8
abletonctl workflow-macro render bass-movement --track "Mid Bass" --slot 0
```

### G Jones-Inspired Principles

Translate to: exploratory sound generation, decisive editing, narrative transitions, and emotional contrast.

- Separate writing from polish. Capture a strong riff, gesture, or live parameter pass before perfecting the mix.
- Record long automation or performance passes, then chop the strongest moments into a structured phrase.
- Use transitions as musical story logic: decide whether the space between sections should breathe, tense up, hard-cut, or resolve.
- Let rough, unusual sounds survive if the musical idea is strong. Engineering can refine a real idea later.
- Use fewer plugin assumptions and more parameter movement, resampling, chopping, and arrangement edits.

CLI planning moves:

```sh
abletonctl session-snapshot --track "Bass Print" --track "FX" --device-tree-depth 5
abletonctl clip-copy --source-track "Bass Print" --source-arrangement-start 32 --dest-track "Bass Print" --dest-start 48 --length 4
abletonctl clip-split --track "Bass Print" --arrangement-start 48 --time 50
```

### Chris Lake-Inspired Principles

Translate to: functional groove, kick/bass economy, fast sketch capture, and human taste over option overload.

- Start from a body-moving loop: kick, bass, core drum groove, and one memorable hook or texture.
- Save small ideas instead of overworking one session. Reuse proven kick/bass combinations when they fit the new track.
- Make bass translate on small speakers with controlled harmonic content, but protect low-end detail from excessive saturation.
- Use automation as a moment highlighter. Distortion, noise, or filter movement should make selected hits speak, not flatten the whole loop.
- If the track works as kick, bass, drums, and a few vocal or texture moments, resist adding layers that blur the groove.

CLI planning moves:

```sh
abletonctl workflow-macro render drum-punch-bus --track "Drum Bus"
abletonctl workflow-macro render kick-sub-separation --kick-track Kick --track Bass --start 0 --length 8
abletonctl set-track --track "FX Texture" --volume 0.45
```

### Bass Movement And Resampling Workflow

Translate to: controlled chaos, commitment, and editable audio.

- Start with a stable source. A simple sustained note or sparse MIDI phrase makes movement easier to hear than a crowded riff.
- Create motion in the mid layer first: filter cutoff, vowel/formant motion, distortion amount, resonant notches, Roar/noise accents, or LFO/envelope-followed modulation.
- Keep the sub layer separate or conservative while the mid layer mutates. Print movement only after kick/sub timing still works.
- Resample when the movement becomes more interesting than the patch. Printing turns live modulation into audio that can be split, reversed, warped, faded, and arranged.
- Record long passes, then curate. The goal is not to use every second; it is to create a pool of usable fills, growls, impacts, and one-shots.
- After printing, cut for function: downbeat impact, response phrase, pre-drop tease, fill, or texture bed. Do not leave a full chaotic pass running under the whole section.
- Validate translation: check mono low end, transient timing, gain before print, and whether saturation erased low-frequency detail.

CLI planning moves:

```sh
abletonctl workflow-macro render bass-resampling-pass --track "Mid Bass" --start 64 --length 8 --print-track "Bass Resample Print"
abletonctl clip-split --track "Bass Resample Print" --arrangement-start 64 --time 66
abletonctl clip-warp --track "Bass Resample Print" --arrangement-start 64 --warping true --warp-mode beats
```

## Intent Mappings

- "Make it more Tipper-ish": make it more sculptural, spacious, low-end-clean, and rhythmically detailed. Ask only if tempo/section is unknown.
- "Give it G Jones energy": capture or generate a bold riff/gesture, then chop and arrange it with contrast before deep mix work.
- "Make it hit like Chris Lake": prioritize kick/bass coexistence, minimal but sticky groove, controlled mid harmonics, and mix translation.
- "More psychedelic bass": add evolving mid-layer automation and spatial ear candy while keeping the sub stable.
- "Make a resampling pass": automate one strong movement target, create a print track, route to Resampling, arm it, and ask before recording.
- "Turn this bass into fills": print or use an existing audio pass, split the best gestures, then place only functional moments around transitions.
- "More club-effective": simplify the arrangement around kick, bass, drums, and one hook; verify headroom and low-end conflict.
- "More narrative": make section transitions intentional: breath, tension, hard cut, or resolution.

## Planning Defaults

When the user gives an artist-inspired request without detailed targets:

1. Run `session-snapshot`.
2. Use `copilot-intent` and read `profile_hints.artist_inspiration` for neutral translation, focus axes, and recommended commands.
3. Infer the target from selected track and memory signals before asking.
4. Choose one primary musical axis: low-end clarity, movement, groove, transition, or space.
5. Render a relevant `workflow-macro` when available.
6. Add only one or two custom gestures beyond the macro.
7. Verify with refreshed clip/device/automation state.

Do not ask broad questions like "what kind of Tipper/G Jones/Chris Lake vibe?" unless the set context cannot identify tempo, section, or target material.
