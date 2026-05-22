# Architecture

This repository is split around the two runtime surfaces for the Ableton controller:

- `abletonctl.py` is a compatibility wrapper. The implementation lives in `ableton_controller/`.
- `remote_scripts/Codex_AI/bridge.py` is the Ableton Remote Script entrypoint. The Live command implementation is composed from focused mixins beside it.
- `scripts/install_bridge.py` is a compatibility wrapper. Installer support code lives in `scripts/install_bridge_lib/`.

## CLI Package

`ableton_controller/` owns the local command-line app.

- `config.py` contains defaults, command sets, key maps, and stable constants.
- `arg_types.py` contains argparse value coercion and validation.
- `parser*.py` modules define command families only; they do not build bridge payloads.
- `payload*.py` modules convert parsed namespaces into bridge JSON payloads.
- `transport.py` owns the JSON socket protocol and connection errors.
- `local_automation.py` owns macOS `osascript` keyboard/menu actions.
- `local_commands.py` coordinates local-only commands, including stock registry commands that may call the bridge.
- `stock_cli.py` owns CLI-specific stock-device registry presentation and control resolution.
- `main.py` wires parser, local command dispatch, payload construction, transport, and output.

Parser modules should not import transport or local automation. Payload modules should not perform I/O. Transport should know nothing about individual Ableton commands.

## Ableton Remote Script

`remote_scripts/Codex_AI/bridge.py` keeps Ableton's expected `CodexBridge` entrypoint and socket server lifecycle. Command behavior is organized by Live domain:

- `dispatch.py` maps JSON command names to bridge methods.
- `device_commands.py`, `clip_commands.py`, `clip_warp_commands.py`, `automation_commands.py`, `browser_commands.py`, `track_commands.py`, and `midi_commands.py` implement command handlers.
- `clip_refs.py`, `automation_helpers.py`, `warp_markers.py`, `midi_helpers.py`, `lom_resolver.py`, `resolvers.py`, `serialization.py`, and `utilities.py` hold reusable Live Object Model helpers.
- `live_api.py` centralizes optional `Live` module access for code that needs Ableton API classes.

Command handlers may orchestrate Live actions, but shared lookup, serialization, MIDI note, clip reference, automation, and warp marker behavior belongs in helper mixins.

## Installer

`scripts/install_bridge_lib/` owns install and restart workflows:

- `filesystem.py` installs the Remote Script and patches Live preferences.
- `bridge_core.py` performs raw bridge requests; `bridge_api.py` contains higher-level bridge operations.
- `automation.py` owns macOS quit/dialog automation.
- `recovery.py` owns unsaved-set recovery quarantine behavior.
- `midi_agent.py` owns LaunchAgent install/uninstall.
- `restart.py` orchestrates the restart-and-activate workflow.
- `parser.py` and `main.py` wire the script entrypoint.

## Size And Ownership

Python code files should stay under roughly 300 lines whenever practical. Files approaching 500 lines need a clear reason in review. Large generated data and long-form documentation are exempt, but generated artifacts should be named and documented as such.

When adding functionality, prefer extending the closest existing domain module. Create a new module only when it creates a clearer ownership boundary or prevents a file from becoming a mixed-purpose module.
