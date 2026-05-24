# Ableton Copilot Self-Improvement

This repo includes a recurring improvement framework for the Ableton producer copilot. The framework is intentionally modular: the local script gathers evidence and writes reviewable artifacts, while the scheduled Codex automation uses those artifacts to make focused source or skill improvements.

## Run Cycle

Use:

```sh
python3 scripts/copilot_improvement.py run --validate
```

Each run:

- indexes the current `abletonctl.py` command surface
- checks producer plan validation drift against the parser
- scans configured Ableton project roots for `.als`, `.alp`, `.adg`, `.adv`, and `.alc` material
- extracts historical set signals for track types, names, device usage, device-chain signatures, routing targets, arrangement markers/scenes, locator timing anchors, arrangement shape from clip timing, semantic clip roles and phase signatures from arrangement clip names, and automation features
- scans configured chat roots and relevant local Codex session logs for communication patterns, iterative refinement markers, and recurring workflow language
- updates `.ableton-copilot/memory.json` with confidence-scored signals
- derives confidence-scored intent mappings and writes `.ableton-copilot/personal-workflow-profile.md`
- syncs the workflow macro registry into memory with confidence, tags, linked intents, and supporting signal ids
- audits coverage against the long-running goal and records proven/partial/missing evidence
- writes `.ableton-copilot/runs/<run-id>/reasoning-log.json`
- writes `.ableton-copilot/runs/<run-id>/improvement-report.md`
- appends `.ableton-copilot/CHANGELOG.md`
- backs up prior memory for rollback

The `.ableton-copilot/` directory is ignored by git because it is runtime memory, not source. The profile is the quickest planning read: it turns raw project/chat evidence into likely intent mappings, recommended command families, follow-up predictions, and an inventory of reusable workflow macros.

For command planning, the learned mappings are also available through the local
CLI:

```sh
abletonctl copilot-intent "make a glitchy zap transition into the synth"
```

This read-only command returns matched recognition terms, evidence-backed
triggers, planning bias, likely follow-ups, recommended command families, and
compact profile hints from learned target aliases, arrangement phase, role,
device-chain, routing, automation, and chat refinement evidence, including
numbered locator timing anchors when historical sets use marker-style section
labels.
The profile also renders derived section-label proposals separately from
historically learned labels so future runs can act on timing anchors without
mistaking generated names for source evidence.
Those derived labels are also persisted as `project.arrangement-label-proposal`
signals with separate confidence, making it clear when a section name is a
reviewable proposal rather than a historical locator label.
It also renders iterative refinement patterns, such as correction phrases or
pad-mapping corrections, so plans can adapt likely follow-up behavior without
asking the user to repeat context.
Target aliases turn recurring project names such as `BD`, `SD`, `SC Trigger`,
`TR8S`, `A-Reverb`, and `B-Delay` into confidence-scored planning hints for
kick, snare, sidechain, drum, and return-track references.

## Scheduler

The Codex app automation should run every 6 hours with this workspace as its cwd. Its first action should be:

```sh
python3 scripts/copilot_improvement.py run --validate
```

Then it should inspect `.ableton-copilot/latest-report.md`, choose one meaningful open improvement, implement it, and rerun:

```sh
python3 -m compileall -q ableton_controller copilot_improvement remote_scripts scripts tests
python3 -m unittest discover -s tests
python3 scripts/copilot_size_gate.py
python3 scripts/copilot_improvement.py run --validate \
  --note "Implemented <specific change>" \
  --why "<evidence-backed reason>" \
  --impact "<expected musical or workflow improvement>"
```

Every scheduled run should leave an explicit report describing what changed, why, expected impact, validation performed, and current goal coverage. If no source change is justified, the run should improve memory, backlog quality, goal coverage, or research synthesis rather than making cosmetic churn.

## Configurable Evidence Roots

Defaults:

- Ableton projects: `~/Music/Ableton`, `~/Documents/codex_ableton`
- Chat history: `~/Documents/ableton-chats`, plus relevant local Codex JSONL sessions discovered from `~/.codex/session_index.jsonl` and `~/.codex/sessions`
- Memory/log state: `<repo>/.ableton-copilot`

Override with path-separated environment variables:

```sh
ABLETON_PROJECT_ROOTS="/path/to/projects:/another/root" \
ABLETON_CHAT_ROOTS="/path/to/chats" \
ABLETON_COPILOT_STATE_DIR="/path/to/state" \
python3 scripts/copilot_improvement.py run
```

## Rollback And Recovery

Memory rollback:

```sh
python3 scripts/copilot_improvement.py rollback --run-id <run-id>
```

Source rollback should use git inspection and targeted restoration for only the files changed by the scheduled run. The run report records the branch, short commit, dirty status, and memory backup path.

## Quality Gates

The recurring job must preserve command names, flags, defaults, payload shapes, and bridge responses unless the chosen improvement explicitly changes them. It should prefer high-signal improvements:

- missing CLI capability that unlocks a repeated workflow
- command-planning determinism or validation
- personalized intent mapping backed by project or chat evidence
- sound-design, arrangement, or mixing heuristics that produce better command sequences
- focused refactors that reduce real duplication or keep files below the repo size standard

Avoid broad rewrites, naming-only changes, and abstractions that hide the concrete Ableton command plan.
