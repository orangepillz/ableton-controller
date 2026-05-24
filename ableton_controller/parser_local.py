"""Parser setup for local commands."""

from pathlib import Path

from .arg_types import json_arg, track_value
from .arrangement_automation import CURVE_PRESETS
from .parser_args import add_app_arg

def add_local_commands(sub):
    intent = sub.add_parser("copilot-intent", help="Match a natural-language request against personalized copilot memory.")
    intent.add_argument("query", help="Natural-language production request to match.")
    intent.add_argument("--memory", type=Path, help="Path to .ableton-copilot/memory.json.")
    intent.add_argument("--limit", type=int, default=5, help="Maximum matches to return.")
    intent.add_argument("--min-score", type=float, default=0.15, help="Minimum match score to include.")
    intent.add_argument("--include-inactive", action="store_true", help="Include inactive mappings from memory.")

    macro = sub.add_parser("workflow-macro", help="List or render reusable producer workflow plan templates.")
    macro.add_argument("action", choices=("list", "render"), nargs="?", default="list")
    macro.add_argument("macro", nargs="?", help="Macro name for the render action.")
    macro.add_argument("--memory", type=Path, help="Path to .ableton-copilot/memory.json for personalized macros.")
    macro.add_argument("--track", type=track_value, help="Primary target track for the rendered macro.")
    macro.add_argument("--slot", type=int, default=0, help="Session clip slot used by clip-based macros.")
    macro.add_argument("--start", type=float, default=0.0, help="Start beat for range-based macros.")
    macro.add_argument("--end", type=float, help="End beat for range-based macros.")
    macro.add_argument("--length", type=float, default=8.0, help="Clip or beat-range length.")
    macro.add_argument("--name", help="Clip name used by generation macros.")
    macro.add_argument("--print-track", default="Bass Resample Print", type=track_value, help="Audio track name/index for resampling macros.")
    macro.add_argument("--secondary-track", default="Perc Glitch Rack", type=track_value, help="Second track for two-layer workflow macros.")
    macro.add_argument("--synth-track", default="Synth", type=track_value, help="Synth target for transition-oriented macros.")
    macro.add_argument("--zap-query", default="zap", help="Browser search query for zap-style samples.")
    macro.add_argument("--perc-query", default="perc", help="Browser search query for percussion samples.")
    macro.add_argument("--kick-track", default="Kick", type=track_value)
    macro.add_argument("--sub-track", default="Sub", type=track_value)
    macro.add_argument("--scene-index", type=int, help="Scene insertion index for arrangement scaffold macros.")

    file_get = sub.add_parser("arrangement-automation-file-get", help="Read a saved .als Arrangement automation lane including curve controls.")
    file_get.add_argument("--set-file", required=True, type=Path, help="Path to the saved .als file.")
    file_get.add_argument("--track", required=True, type=track_value)
    file_get.add_argument("--arrangement-start", required=True, type=float)
    file_get.add_argument("--device", required=True)
    file_get.add_argument("--param", required=True)

    file_set = sub.add_parser("arrangement-automation-file-set", help="Write saved .als Arrangement breakpoint events with Ableton curve controls.")
    file_set.add_argument("--set-file", required=True, type=Path, help="Path to the saved .als file.")
    file_set.add_argument("--track", required=True, type=track_value)
    file_set.add_argument("--arrangement-start", required=True, type=float)
    file_set.add_argument("--clip-name", help="Optional clip name disambiguator for the Arrangement start.")
    file_set.add_argument("--device", required=True)
    file_set.add_argument("--param", required=True)
    file_set.add_argument("--duration", type=float, help="Automation duration in clip beats.")
    file_start = file_set.add_mutually_exclusive_group()
    file_start.add_argument("--from-normalized", type=float, help="Starting 0..1 normalized value.")
    file_start.add_argument("--from-value", type=float, help="Starting raw parameter value.")
    file_end = file_set.add_mutually_exclusive_group()
    file_end.add_argument("--to-normalized", type=float, help="Ending 0..1 normalized value.")
    file_end.add_argument("--to-value", type=float, help="Ending raw parameter value.")
    file_set.add_argument("--events", type=json_arg, help="JSON list of breakpoint {time,value|normalized,curve_coefficients?} objects.")
    file_set.add_argument("--curve", choices=CURVE_PRESETS, help="Write two breakpoint events with this curve between them.")
    file_set.add_argument("--curve-coefficients", type=json_arg, help="Bezier control object {x1,y1,x2,y2} for the first generated breakpoint.")
    file_set.add_argument("--no-preserve-boundaries", dest="preserve_boundaries", action="store_false", help="Do not insert same-time restore events at the clip boundaries.")
    file_set.add_argument("--backup", dest="backup", action="store_true", default=True, help="Write a sibling .bak before changing the .als file.")
    file_set.add_argument("--no-backup", dest="backup", action="store_false", help="Do not write a sibling .bak file.")
    file_set.add_argument("--dry-run", action="store_true", help="Resolve and preview the write without modifying the .als file.")

    hotkey = sub.add_parser("hotkey", help="Send any keyboard shortcut to Ableton, e.g. cmd+s or shift+tab.")
    add_app_arg(hotkey)
    hotkey.add_argument("combo", help="Key combo using + separators, e.g. cmd+option+b, cmd+shift+r, f11, tab.")

    key_sequence = sub.add_parser("key-sequence", help="Send multiple key combos in order.")
    add_app_arg(key_sequence)
    key_sequence.add_argument("combos", nargs="+", help="One or more combos accepted by `hotkey`.")
    key_sequence.add_argument("--between", type=float, default=0.1, help="Delay between combos, in seconds.")

    type_text = sub.add_parser("type-text", help="Type text into Ableton's focused field.")
    add_app_arg(type_text)
    type_text.add_argument("text")

    menu_search = sub.add_parser("menu-search", help="Use macOS menu search to run a Live menu command by name.")
    add_app_arg(menu_search)
    menu_search.add_argument("query", help="Menu command to search, e.g. Export Audio/Video.")
    menu_search.add_argument("--search-delay", type=float, default=0.35, help="Delay after typing the menu query.")

    save = sub.add_parser("save", help="Save the current Live set via Cmd+S.")
    add_app_arg(save)
