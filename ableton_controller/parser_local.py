"""Parser setup for local commands."""

from .parser_args import add_app_arg

def add_local_commands(sub):
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
