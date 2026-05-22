# Repository Standards

## Maintainability

- Keep code files small and focused. Aim for under 300 lines; treat 500 lines as a hard warning threshold unless the file is generated or has a documented reason.
- Do not create god files. Split parser setup, payload construction, transport, domain logic, integrations, and presentation/output into separate modules.
- Components and functions should have one primary responsibility. Prefer cohesive modules over broad utility buckets.
- Extract duplicated logic when it has real behavior or policy. Avoid one-line wrappers and abstractions that only rename an existing call.
- Keep business/domain logic out of command entrypoints and UI/CLI wiring. Entry wrappers should delegate quickly.
- Isolate MIDI, Ableton Live Object Model, socket, macOS automation, and filesystem side effects behind clear modules.
- Keep dependency direction intentional: parsers should not perform I/O, payload builders should not call transports, and transports should not know individual command families.
- Use strong typing for public helpers and payload/data boundaries where Python's standard typing keeps the code clearer.
- Remove dead code, stale experiments, and unused imports as part of nearby refactors.
- Prefer direct, descriptive names that match the folder/module responsibility.

## Quality Gates

- Preserve existing command names, flags, defaults, payload shapes, and bridge responses unless a change is explicitly requested.
- Add or update focused tests when extracting logic or changing command behavior.
- Run `python3 -m compileall -q ...` and `python3 -m unittest discover -s tests` before handing off code changes.
- Generated data and caches should remain out of source edits unless the task explicitly changes them.
