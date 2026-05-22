"""Parser setup for browser_lom commands."""

def add_browser_lom_commands(sub):
    lom_get = sub.add_parser("lom-get", help="Read a Live Object Model path.")
    lom_get.add_argument("path")

    lom_set = sub.add_parser("lom-set", help="Set a Live Object Model property.")
    lom_set.add_argument("path")
    lom_set.add_argument("value")
    lom_set.add_argument("--json", action="store_true", help="Parse value as JSON.")

    lom_call = sub.add_parser("lom-call", help="Call a Live Object Model method.")
    lom_call.add_argument("path")
    lom_call.add_argument("--args", default="[]", help="JSON array of positional arguments.")
    lom_call.add_argument("--kwargs", default="{}", help="JSON object of keyword arguments.")

    lom_inspect = sub.add_parser("lom-inspect", help="Inspect attributes and methods at a Live Object Model path.")
    lom_inspect.add_argument("path")

    show_view = sub.add_parser("show-view", help="Show a Live view, e.g. Browser, Session, Arranger, Detail/Clip.")
    show_view.add_argument("view")

    hide_view = sub.add_parser("hide-view", help="Hide a Live view.")
    hide_view.add_argument("view")

    focus_view = sub.add_parser("focus-view", help="Focus a Live view.")
    focus_view.add_argument("view")

    sub.add_parser("toggle-browse", help="Toggle Live browser browse mode.")

    sub.add_parser("browser-roots", help="List available browser roots.")

    browser_children = sub.add_parser("browser-children", help="List browser children by path, e.g. 'audio_effects/EQ Eight'.")
    browser_children.add_argument("item")

    browser_tree = sub.add_parser("browser-tree", help="Read a recursive Live browser tree.")
    browser_tree.add_argument("item", nargs="?", help="Optional root/path, e.g. instruments or 'audio_effects/EQ Eight'. Defaults to all roots.")
    browser_tree.add_argument("--depth", type=int, default=2, help="How many child levels to read.")
    browser_tree.add_argument("--max-items", type=int, default=500, help="Stop after this many browser items.")

    browser_search = sub.add_parser("browser-search", help="Search Live browser items by name/source/path/URI.")
    browser_search.add_argument("query")
    browser_search.add_argument("--item", help="Optional root/path to search under. Defaults to all roots.")
    browser_search.add_argument("--depth", type=int, default=6, help="How many child levels to search.")
    browser_search.add_argument("--max-results", type=int, default=100)
    browser_search.add_argument("--max-items", type=int, default=5000, help="Stop after scanning this many browser items.")

    browser_load = sub.add_parser("browser-load", help="Load a browser item into Live by path.")
    browser_load.add_argument("item")

    browser_preview = sub.add_parser("browser-preview", help="Preview a browser item by path.")
    browser_preview.add_argument("item")

    sub.add_parser("browser-stop-preview", help="Stop browser preview playback.")
