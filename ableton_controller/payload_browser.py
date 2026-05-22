"""Payload builders for browser commands."""

def build_browser_payload(args):
    command = args.command
    if command == "browser-roots":
        return {"command": "browser_roots"}
    if command == "browser-children":
        return {"command": "browser_children", "item": args.item}
    if command == "browser-tree":
        payload = {"command": "browser_tree", "depth": args.depth, "max_items": args.max_items}
        if args.item:
            payload["item"] = args.item
        return payload
    if command == "browser-search":
        payload = {
            "command": "browser_search",
            "query": args.query,
            "depth": args.depth,
            "max_results": args.max_results,
            "max_items": args.max_items,
        }
        if args.item:
            payload["item"] = args.item
        return payload
    if command == "browser-load":
        return {"command": "browser_load", "item": args.item}
    if command == "browser-preview":
        return {"command": "browser_preview", "item": args.item}
    if command == "browser-stop-preview":
        return {"command": "browser_stop_preview"}
    return None
