"""macOS keyboard and menu automation used by local CLI commands."""

import json
import subprocess

from .config import KEY_CODES, MODIFIER_NAMES

def run_hotkey(app: str, combo: str, activation_delay: float) -> None:
    action = applescript_key_action(combo)
    run_applescript(
        [
            'tell application %s to activate' % applescript_string(app),
            "delay %.3f" % max(0.0, activation_delay),
            "tell application \"System Events\"",
            "  %s" % action,
            "end tell",
        ]
    )


def run_menu_search(app: str, query: str, activation_delay: float, search_delay: float) -> None:
    run_applescript(
        [
            'tell application %s to activate' % applescript_string(app),
            "delay %.3f" % max(0.0, activation_delay),
            "tell application \"System Events\"",
            "  keystroke \"/\" using {command down, shift down}",
            "  delay 0.150",
            "  keystroke %s" % applescript_string(query),
            "  delay %.3f" % max(0.0, search_delay),
            "  key code 125",
            "  delay 0.050",
            "  key code 36",
            "end tell",
        ]
    )


def applescript_key_action(combo: str) -> str:
    key, modifiers = parse_combo(combo)
    suffix = ""
    if modifiers:
        suffix = " using {%s}" % ", ".join(modifiers)
    key_name = key.lower()
    if key_name in KEY_CODES:
        return "key code %d%s" % (KEY_CODES[key_name], suffix)
    if len(key) == 1:
        return "keystroke %s%s" % (applescript_string(key), suffix)
    raise SystemExit("Unknown key %r. Use a single character, a function key, arrows, tab, return, escape, space, delete, home/end, or pageup/pagedown." % key)


def parse_combo(combo: str) -> tuple[str, list[str]]:
    parts = [part.strip().lower() for part in combo.split("+") if part.strip()]
    if not parts:
        raise SystemExit("Empty key combo.")
    key = parts[-1]
    modifiers = []
    for part in parts[:-1]:
        modifier = MODIFIER_NAMES.get(part)
        if modifier is None:
            raise SystemExit("Unknown modifier %r in combo %r." % (part, combo))
        if modifier not in modifiers:
            modifiers.append(modifier)
    return key, modifiers


def applescript_string(value: str) -> str:
    return json.dumps(value)


def run_applescript(lines: list[str]) -> None:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown osascript failure"
        raise SystemExit(
            "macOS keyboard/menu automation failed: %s\n"
            "Grant Accessibility permission to the terminal/Codex app if macOS blocks System Events." % detail
        )
