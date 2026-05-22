"""BrowserCommand mixins for the Codex_AI Ableton bridge."""

import re


class BrowserCommandMixin(object):
    def _view_command(self, payload):
        action = str(payload.get("action", "show"))
        view = payload.get("view")
        app_view = self.application().view
        if action == "toggle-browse":
            app_view.toggle_browse()
            return {"browse_mode": app_view.browse_mode}
        if not view:
            raise ValueError("view is required")
        if action == "show":
            app_view.show_view(str(view))
            return {"view": view, "visible": app_view.is_view_visible(str(view))}
        if action == "hide":
            app_view.hide_view(str(view))
            return {"view": view, "visible": app_view.is_view_visible(str(view))}
        if action == "focus":
            app_view.focus_view(str(view))
            return {"focused_document_view": app_view.focused_document_view}
        if action == "zoom":
            app_view.zoom_view(int(payload.get("direction", 0)), str(view), bool(payload.get("alt", False)))
            return {"view": view, "done": True}
        if action == "scroll":
            app_view.scroll_view(int(payload.get("direction", 0)), str(view), bool(payload.get("alt", False)))
            return {"view": view, "done": True}
        raise ValueError("Unknown view action: %r" % action)

    def _browser_roots(self):
        roots = []
        for name in self._browser_root_names():
            roots.append({"path": name, "item": self._browser_item_info(getattr(self.application().browser, name))})
        return {"roots": roots}

    def _browser_children(self, payload):
        item = self._resolve_browser_item(payload.get("item"))
        children = self._browser_item_children(item)
        return {
            "item": self._browser_item_info(item),
            "children": [{"path": self._browser_child_path(payload.get("item"), child), "item": self._browser_item_info(child)} for child in children],
        }

    def _browser_tree(self, payload):
        depth = max(0, int(payload.get("depth", 2)))
        max_items = max(1, int(payload.get("max_items", 500)))
        state = {"seen": 0, "truncated": False}
        identifier = payload.get("item")
        if identifier:
            item = self._resolve_browser_item(identifier)
            root = self._browser_tree_node(item, str(identifier).strip(), depth, state, max_items)
            roots = [root]
        else:
            roots = []
            for name in self._browser_root_names():
                if state["seen"] >= max_items:
                    state["truncated"] = True
                    break
                item = getattr(self.application().browser, name)
                roots.append(self._browser_tree_node(item, name, depth, state, max_items))
        return {
            "roots": roots,
            "depth": depth,
            "items_seen": state["seen"],
            "max_items": max_items,
            "truncated": state["truncated"],
        }

    def _browser_tree_node(self, item, path, depth, state, max_items):
        state["seen"] += 1
        node = {"path": path, "item": self._browser_item_info(item)}
        if depth <= 0 or state["seen"] >= max_items:
            if depth > 0 and self._browser_children_count(item) > 0:
                state["truncated"] = True
            return node
        children = []
        for child in self._browser_item_children(item):
            if state["seen"] >= max_items:
                state["truncated"] = True
                break
            child_path = self._browser_child_path(path, child)
            children.append(self._browser_tree_node(child, child_path, depth - 1, state, max_items))
        if children:
            node["children"] = children
        return node

    def _browser_search(self, payload):
        query = payload.get("query")
        needle = self._normalize_name(query or "")
        if not needle:
            raise ValueError("query is required")
        depth = max(0, int(payload.get("depth", 6)))
        max_results = max(1, int(payload.get("max_results", 100)))
        max_items = max(1, int(payload.get("max_items", 5000)))
        state = {"seen": 0, "truncated": False, "results": []}
        identifier = payload.get("item")
        if identifier:
            item = self._resolve_browser_item(identifier)
            self._browser_search_node(item, str(identifier).strip(), needle, depth, state, max_results, max_items)
        else:
            for name in self._browser_root_names():
                if state["seen"] >= max_items or len(state["results"]) >= max_results:
                    state["truncated"] = True
                    break
                item = getattr(self.application().browser, name)
                self._browser_search_node(item, name, needle, depth, state, max_results, max_items)
        return {
            "query": query,
            "results": state["results"],
            "result_count": len(state["results"]),
            "items_seen": state["seen"],
            "max_items": max_items,
            "max_results": max_results,
            "depth": depth,
            "truncated": state["truncated"],
        }

    def _browser_search_node(self, item, path, needle, depth, state, max_results, max_items):
        if state["seen"] >= max_items or len(state["results"]) >= max_results:
            state["truncated"] = True
            return
        state["seen"] += 1
        haystack = self._normalize_name("%s %s %s %s" % (
            self._safe_get(item, "name", ""),
            self._safe_get(item, "source", ""),
            self._safe_get(item, "uri", ""),
            path,
        ))
        if needle in haystack:
            state["results"].append({"path": path, "item": self._browser_item_info(item)})
            if len(state["results"]) >= max_results:
                state["truncated"] = True
                return
        if depth <= 0:
            return
        for child in self._browser_item_children(item):
            self._browser_search_node(child, self._browser_child_path(path, child), needle, depth - 1, state, max_results, max_items)
            if state["seen"] >= max_items or len(state["results"]) >= max_results:
                state["truncated"] = True
                break

    def _browser_item_action(self, payload, action):
        item = self._resolve_browser_item(payload.get("item"))
        browser = self.application().browser
        if action == "load":
            browser.load_item(item)
        elif action == "preview":
            browser.preview_item(item)
        else:
            raise ValueError("Unknown browser action: %r" % action)
        return {"action": action, "item": self._browser_item_info(item), "done": True}

    def _resolve_stock_device_item(self, payload):
        path = payload.get("path")
        if path:
            return self._resolve_browser_item(path)
        name = payload.get("name")
        if not name:
            raise ValueError("name or path is required")
        roots = [payload.get("root")] if payload.get("root") else ["audio_effects", "midi_effects", "instruments"]
        matches = []
        for root_name in roots:
            root = getattr(self.application().browser, root_name)
            self._find_stock_device_items(root, root_name, name, matches, 0, 7, 6000)
        exact = [item for item in matches if self._normalize_name(self._safe_get(item, "name", "")) == self._normalize_name(name)]
        choices = exact or matches
        if len(choices) == 1:
            return choices[0]
        if choices:
            raise ValueError("Ambiguous stock device %r: %s" % (name, [self._safe_get(item, "name", "") for item in choices[:12]]))
        raise ValueError("No stock device named %r" % name)

    def _find_stock_device_items(self, item, path, name, matches, depth, max_depth, max_items):
        if len(matches) >= 20 or depth > max_depth or max_items <= 0:
            return max_items
        max_items -= 1
        normalized = self._normalize_name(name)
        item_name = self._safe_get(item, "name", "")
        if (
            normalized in self._normalize_name(item_name)
            and self._safe_get(item, "is_loadable", False)
            and self._safe_get(item, "is_device", False)
            and self._safe_get(item, "source", "") == "Built-in"
        ):
            matches.append(item)
        for child in self._browser_item_children(item):
            if max_items <= 0 or len(matches) >= 20:
                break
            child_path = self._browser_child_path(path, child)
            max_items = self._find_stock_device_items(child, child_path, name, matches, depth + 1, max_depth, max_items)
        return max_items

    def _browser_root_names(self):
        return [
            "sounds",
            "drums",
            "instruments",
            "audio_effects",
            "midi_effects",
            "max_for_live",
            "plugins",
            "clips",
            "samples",
            "packs",
            "user_library",
            "current_project",
        ]

    def _resolve_browser_item(self, identifier):
        if not identifier:
            raise ValueError("Browser item path is required")
        text = str(identifier).strip()
        if text.startswith("application.browser."):
            item = self._resolve_lom_path(text)
            if not hasattr(item, "is_loadable") and not hasattr(item, "children"):
                raise ValueError("Path did not resolve to a browser item: %r" % text)
            return item

        parts = [part.strip() for part in re.split(r"\s*/\s*|\s*>\s*", text) if part.strip()]
        if not parts:
            raise ValueError("Browser item path is required")

        browser = self.application().browser
        root = None
        normalized = self._normalize_name(parts[0])
        for name in self._browser_root_names():
            item = getattr(browser, name)
            if normalized in (self._normalize_name(name), self._normalize_name(item.name)):
                root = item
                break
        if root is None:
            raise ValueError("Unknown browser root: %r" % parts[0])

        item = root
        for part in parts[1:]:
            item = self._find_named_child(item, part)
        return item

    def _find_named_child(self, item, name):
        normalized = self._normalize_name(name)
        exact = [
            child
            for child in self._browser_item_children(item)
            if normalized == self._normalize_name(getattr(child, "name", ""))
        ]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise ValueError("Ambiguous browser item %r: %s" % (name, [child.name for child in exact]))
        matches = [
            child
            for child in self._browser_item_children(item)
            if normalized in self._normalize_name(getattr(child, "name", ""))
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Ambiguous browser item %r: %s" % (name, [child.name for child in matches]))
        raise ValueError("No child named %r under %s" % (name, item.name))

    def _browser_child_path(self, parent_identifier, child):
        if not parent_identifier:
            return child.name
        return "%s/%s" % (str(parent_identifier).rstrip("/"), child.name)

    def _browser_item_children(self, item):
        try:
            children = item.children
        except Exception:
            return []
        if self._is_indexable_vector(children):
            return list(children)
        return []

    def _browser_children_count(self, item):
        try:
            return len(item.children)
        except Exception:
            return 0

    def _browser_item_info(self, item):
        return {
            "name": self._safe_get(item, "name"),
            "uri": self._safe_get(item, "uri"),
            "source": self._safe_get(item, "source"),
            "is_device": self._safe_get(item, "is_device"),
            "is_folder": self._safe_get(item, "is_folder"),
            "is_loadable": self._safe_get(item, "is_loadable"),
            "is_selected": self._safe_get(item, "is_selected"),
            "children_count": self._browser_children_count(item),
        }
