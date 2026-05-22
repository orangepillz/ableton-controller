import json
import queue
import re
import socket
import threading
import traceback

from _Framework.ControlSurface import ControlSurface

try:
    import Live
except Exception:
    Live = None


HOST = "127.0.0.1"
PORT = 37337


class _Request(object):
    def __init__(self, payload):
        self.payload = payload
        self.event = threading.Event()
        self.response = None


class CodexBridge(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._requests = queue.Queue()
        self._stop_event = threading.Event()
        self._server_socket = None
        self._server_thread = threading.Thread(target=self._serve, name="CodexBridgeServer")
        self._server_thread.daemon = True
        self._server_thread.start()
        self.schedule_message(1, self._poll)
        self.log_message("Codex_AI bridge starting on %s:%s" % (HOST, PORT))

    def disconnect(self):
        self._stop_event.set()
        server_socket = self._server_socket
        if server_socket is not None:
            try:
                server_socket.close()
            except Exception:
                pass
        ControlSurface.disconnect(self)

    def _serve(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen(8)
            server_socket.settimeout(0.25)
            self._server_socket = server_socket
        except Exception:
            self._server_socket = None
            return

        while not self._stop_event.is_set():
            try:
                client, _address = server_socket.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            thread = threading.Thread(target=self._handle_client, args=(client,))
            thread.daemon = True
            thread.start()

    def _handle_client(self, client):
        try:
            client.settimeout(8.0)
            raw = self._read_request(client)
            payload = json.loads(raw.decode("utf-8"))
            request = _Request(payload)
            self._requests.put(request)
            if not request.event.wait(7.5):
                response = {"ok": False, "error": "Timed out waiting for Live thread"}
            else:
                response = request.response
            client.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
        except Exception as error:
            response = {"ok": False, "error": str(error)}
            try:
                client.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
            except Exception:
                pass
        try:
            client.close()
        except Exception:
            pass

    def _read_request(self, client):
        chunks = []
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        raw = b"".join(chunks).strip()
        if not raw:
            raise ValueError("Empty request")
        return raw

    def _poll(self):
        processed = 0
        while processed < 50:
            try:
                request = self._requests.get_nowait()
            except queue.Empty:
                break
            try:
                request.response = {"ok": True, "result": self._dispatch(request.payload)}
            except Exception:
                request.response = {
                    "ok": False,
                    "error": traceback.format_exc(),
                }
            request.event.set()
            processed += 1
        if not self._stop_event.is_set():
            self.schedule_message(1, self._poll)

    def _dispatch(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("Request must be a JSON object")
        command = payload.get("command")
        if command == "ping":
            return {"bridge": "Codex_AI", "status": "ok"}
        if command == "status":
            return self._status()
        if command == "tracks":
            return {"tracks": [self._track_info(track, index) for index, track in enumerate(self.song().tracks)],
                    "returns": [self._track_info(track, index, "return") for index, track in enumerate(self.song().return_tracks)],
                    "master": self._track_info(self.song().master_track, 0, "master")}
        if command == "selected":
            return self._selected(payload.get("devices", False))
        if command == "select_track":
            track = self._resolve_track(payload.get("track"))
            self.song().view.selected_track = track
            return self._track_info(track, self._track_index(track), self._track_kind(track))
        if command == "devices":
            track = self._resolve_track(payload.get("track"))
            return {"track": track.name, "devices": self._device_infos(track)}
        if command == "params":
            track = self._resolve_track(payload.get("track"))
            device = self._resolve_device(track, payload.get("device"))
            return {"track": track.name, "device": device.name, "parameters": self._parameter_infos(device)}
        if command == "set_track":
            return self._set_track(payload)
        if command == "set_send":
            return self._set_send(payload)
        if command == "set_param":
            return self._set_param(payload)
        if command == "lom_get":
            return self._serialize(self._resolve_lom_path(payload.get("path")))
        if command == "lom_set":
            return self._lom_set(payload)
        if command == "lom_call":
            return self._lom_call(payload)
        if command == "lom_inspect":
            return self._lom_inspect(payload)
        if command == "view":
            return self._view_command(payload)
        if command == "browser_roots":
            return self._browser_roots()
        if command == "browser_children":
            return self._browser_children(payload)
        if command == "browser_tree":
            return self._browser_tree(payload)
        if command == "browser_search":
            return self._browser_search(payload)
        if command == "browser_load":
            return self._browser_item_action(payload, "load")
        if command == "browser_preview":
            return self._browser_item_action(payload, "preview")
        if command == "browser_stop_preview":
            self.application().browser.stop_preview()
            return {"done": True}
        if command == "create_track":
            return self._create_track(payload)
        if command == "delete_track":
            track = self._resolve_track(payload.get("track"))
            index = self._track_index(track)
            name = self._safe_get(track, "name")
            if self._track_kind(track) == "return":
                self.song().delete_return_track(index)
            elif self._track_kind(track) == "master":
                raise ValueError("Cannot delete the master track")
            else:
                self.song().delete_track(index)
            return {"deleted_index": index, "deleted_track": name, "done": True}
        if command == "duplicate_track":
            track = self._resolve_track(payload.get("track"))
            if self._track_kind(track) != "track":
                raise ValueError("Only regular tracks can be duplicated")
            self.song().duplicate_track(self._track_index(track))
            return {"source": track.name, "done": True}
        if command == "create_scene":
            return self._create_scene(payload)
        if command == "delete_scene":
            index = int(payload.get("scene"))
            self.song().delete_scene(index)
            return {"deleted_scene": index, "done": True}
        if command == "duplicate_scene":
            index = int(payload.get("scene"))
            self.song().duplicate_scene(index)
            return {"source_scene": index, "done": True}
        if command == "fire_scene":
            scene = self._resolve_scene(payload.get("scene"))
            scene.fire()
            return {"scene": self._scene_info(scene, self._scene_index(scene)), "done": True}
        if command == "set_routing":
            return self._set_routing(payload)
        if command == "midi_get_notes":
            return self._midi_get_notes(payload)
        if command == "midi_add_notes":
            return self._midi_add_notes(payload)
        if command == "midi_replace_notes":
            return self._midi_replace_notes(payload)
        if command == "midi_update_notes":
            return self._midi_update_notes(payload)
        if command == "midi_remove_notes":
            return self._midi_remove_notes(payload)
        if command == "midi_clear_notes":
            return self._midi_clear_notes(payload)
        if command == "midi_transform_notes":
            return self._midi_transform_notes(payload)
        if command == "midi_duplicate_region":
            return self._midi_duplicate_region(payload)
        if command == "clips":
            return self._clips(payload)
        if command == "clip_create_midi":
            return self._clip_create_midi(payload)
        if command == "clip_set":
            return self._clip_set(payload)
        if command == "clip_delete":
            return self._clip_delete(payload)
        if command == "clip_copy":
            return self._clip_copy_or_move(payload, False)
        if command == "clip_move":
            return self._clip_copy_or_move(payload, True)
        if command == "clip_split":
            return self._clip_split(payload)
        if command == "clip_slots":
            return self._clip_slots(payload)
        if command == "fire_clip":
            return self._fire_clip(payload)
        if command == "stop_track_clips":
            track = self._resolve_track(payload.get("track"))
            track.stop_all_clips()
            return {"track": track.name, "done": True}
        if command == "tempo":
            if "value" in payload:
                self.song().tempo = float(payload["value"])
            return {"tempo": self.song().tempo}
        if command == "play":
            self.song().start_playing()
            return {"is_playing": self.song().is_playing}
        if command == "stop":
            self.song().stop_playing()
            return {"is_playing": self.song().is_playing}
        if command == "continue":
            self.song().continue_playing()
            return {"is_playing": self.song().is_playing}
        if command == "undo":
            self.song().undo()
            return {"done": True}
        if command == "redo":
            self.song().redo()
            return {"done": True}
        raise ValueError("Unknown command: %r" % (command,))

    def _lom_set(self, payload):
        path = payload.get("path")
        value = payload.get("value")
        target_path, attribute = self._split_lom_attribute(path)
        target = self._resolve_lom_path(target_path)
        current = getattr(target, attribute)
        coerced = self._coerce_like(value, current)
        setattr(target, attribute, coerced)
        return {"path": path, "value": self._serialize(getattr(target, attribute))}

    def _lom_call(self, payload):
        method = self._resolve_lom_path(payload.get("path"))
        if not callable(method):
            raise ValueError("LOM path is not callable: %r" % (payload.get("path"),))
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if not isinstance(args, list):
            raise ValueError("args must be a list")
        if not isinstance(kwargs, dict):
            raise ValueError("kwargs must be an object")
        return self._serialize(method(*args, **kwargs))

    def _lom_inspect(self, payload):
        obj = self._resolve_lom_path(payload.get("path"))
        attrs = []
        methods = []
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                value = getattr(obj, name)
            except Exception:
                continue
            if callable(value):
                methods.append(name)
            else:
                attrs.append({"name": name, "summary": self._summary(value)})
        return {
            "path": payload.get("path"),
            "type": type(obj).__name__,
            "summary": self._summary(obj),
            "attributes": attrs,
            "methods": methods,
        }

    def _clip_slots(self, payload):
        track = self._resolve_track(payload.get("track"))
        slots = []
        for index, slot in enumerate(track.clip_slots):
            info = {
                "index": index,
                "has_clip": slot.has_clip,
                "is_playing": slot.is_playing,
                "is_recording": slot.is_recording,
                "will_record_on_start": slot.will_record_on_start,
            }
            if slot.has_clip:
                info["clip"] = self._clip_info(slot.clip)
            slots.append(info)
        return {"track": track.name, "clip_slots": slots}

    def _fire_clip(self, payload):
        track = self._resolve_track(payload.get("track"))
        slot_index = int(payload.get("slot", 0))
        slot = self._resolve_clip_slot(track, slot_index)
        slot.fire()
        return {"track": track.name, "slot": slot_index, "done": True}

    def _clips(self, payload):
        track = self._resolve_track(payload.get("track"))
        arrangement = []
        for index, clip in enumerate(track.arrangement_clips):
            arrangement.append({"index": index, "clip": self._clip_info(clip)})
        slots = []
        for index, slot in enumerate(track.clip_slots):
            info = {
                "index": index,
                "has_clip": slot.has_clip,
                "is_playing": slot.is_playing,
                "is_recording": slot.is_recording,
                "will_record_on_start": slot.will_record_on_start,
            }
            if slot.has_clip:
                info["clip"] = self._clip_info(slot.clip)
            slots.append(info)
        return {"track": track.name, "arrangement_clips": arrangement, "clip_slots": slots}

    def _clip_create_midi(self, payload):
        track = self._resolve_track(payload.get("track"))
        self._ensure_midi_track(track)
        name = payload.get("name")
        color = payload.get("color")
        color_index = payload.get("color_index")
        if "slot" in payload:
            slot_index = int(payload.get("slot"))
            slot = self._resolve_clip_slot(track, slot_index)
            if slot.has_clip:
                if payload.get("replace", False):
                    slot.delete_clip()
                else:
                    raise ValueError("Clip slot %s on %s already has a clip" % (slot_index, track.name))
            length = self._clip_length_from_payload(payload, None)
            slot.create_clip(length)
            clip = slot.clip
            location = {"kind": "session", "track": track.name, "slot": slot_index}
        else:
            start, length = self._arrangement_range_from_payload(payload, 0.0, 4.0)
            clip = track.create_midi_clip(start, length)
            if clip is None:
                clip = self._find_arrangement_clip(track, start, length)
            location = {"kind": "arrangement", "track": track.name, "start": start, "length": length}
        self._set_optional_clip_property(clip, "name", name)
        self._set_optional_clip_property(clip, "color", color)
        self._set_optional_clip_property(clip, "color_index", color_index)
        try:
            self.song().view.selected_track = track
            self.song().view.detail_clip = clip
        except Exception:
            pass
        return {"location": location, "clip": self._clip_info(clip)}

    def _clip_set(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        changed = {}
        for key, attr in (
            ("name", "name"),
            ("color", "color"),
            ("color_index", "color_index"),
            ("muted", "muted"),
            ("looping", "looping"),
            ("launch_mode", "launch_mode"),
            ("launch_quantization", "launch_quantization"),
            ("legato", "legato"),
            ("velocity_amount", "velocity_amount"),
            ("signature_numerator", "signature_numerator"),
            ("signature_denominator", "signature_denominator"),
            ("position", "position"),
            ("loop_start", "loop_start"),
            ("loop_end", "loop_end"),
            ("start_marker", "start_marker"),
            ("end_marker", "end_marker"),
        ):
            if key in payload:
                setattr(clip, attr, payload[key])
                changed[attr] = self._safe_get(clip, attr)
        return {"location": self._clip_ref_info(ref), "changed": changed, "clip": self._clip_info(clip)}

    def _clip_delete(self, payload):
        ref = self._resolve_clip_ref(payload)
        info = self._clip_info(ref["clip"])
        location = self._clip_ref_info(ref)
        self._delete_clip_ref(ref)
        return {"location": location, "deleted_clip": info, "done": True}

    def _clip_copy_or_move(self, payload, move):
        source = self._resolve_clip_ref(payload, "source")
        source_clip = source["clip"]
        if not self._safe_get(source_clip, "is_midi_clip", False):
            raise ValueError("Only MIDI clip copy/move is implemented")
        source_info = self._clip_ref_info(source)
        target = self._create_midi_clip_destination(payload, source)
        self._copy_midi_clip_contents(source_clip, target["clip"])
        if move:
            self._delete_clip_ref(source)
        return {
            "source": source_info,
            "target": self._clip_ref_info(target),
            "clip": self._clip_info(target["clip"]),
            "moved": move,
            "done": True,
        }

    def _clip_split(self, payload):
        ref = self._resolve_clip_ref(payload)
        clip = ref["clip"]
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Only MIDI clips can be split by this command")
        if not self._safe_get(clip, "is_arrangement_clip", False):
            raise ValueError("clip-split currently supports Arrangement clips; copy Session clips to slots first")
        track = ref.get("track")
        if track is None:
            raise ValueError("Could not resolve Arrangement clip track")
        split_time = float(payload.get("time"))
        relative = bool(payload.get("relative", False))
        clip_start = float(self._safe_get(clip, "start_time", 0.0))
        clip_length = float(self._safe_get(clip, "length", 0.0))
        split_offset = split_time if relative else split_time - clip_start
        if split_offset <= 0.0 or split_offset >= clip_length:
            raise ValueError("Split time must be inside the clip range")
        original_info = self._clip_info(clip)
        original_name = self._safe_get(clip, "name", "")
        source_info = self._clip_ref_info(ref)
        notes = self._midi_note_dicts(clip)
        left_notes, right_notes = self._split_note_dicts(notes, split_offset)
        self._delete_clip_ref(ref)
        left = track.create_midi_clip(clip_start, split_offset)
        if left is None:
            left = self._find_arrangement_clip(track, clip_start, split_offset)
        right_start = clip_start + split_offset
        right_length = clip_length - split_offset
        right = track.create_midi_clip(right_start, right_length)
        if right is None:
            right = self._find_arrangement_clip(track, right_start, right_length)
        self._apply_clip_look(original_info, left, original_name)
        self._apply_clip_look(original_info, right, (original_name + " Split").strip())
        self._add_note_dicts(left, left_notes)
        self._add_note_dicts(right, right_notes)
        return {
            "source": source_info,
            "split_time": split_time,
            "split_offset": split_offset,
            "left": self._clip_info(left),
            "right": self._clip_info(right),
            "done": True,
        }

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

    def _create_track(self, payload):
        kind = str(payload.get("type", "midi")).lower()
        index = payload.get("index")
        args = [] if index is None else [int(index)]
        if kind == "audio":
            track = self.song().create_audio_track(*args)
        elif kind == "midi":
            track = self.song().create_midi_track(*args)
        elif kind == "return":
            track = self.song().create_return_track(*args)
        else:
            raise ValueError("Track type must be audio, midi, or return")
        if payload.get("name"):
            track.name = str(payload.get("name"))
        return self._track_info(track, self._track_index(track), self._track_kind(track))

    def _create_scene(self, payload):
        index = payload.get("index")
        scene = self.song().create_scene() if index is None else self.song().create_scene(int(index))
        if payload.get("name"):
            scene.name = str(payload.get("name"))
        return self._scene_info(scene, self._scene_index(scene))

    def _set_routing(self, payload):
        track = self._resolve_track(payload.get("track"))
        direction = str(payload.get("direction", "input")).lower()
        if direction not in ("input", "output"):
            raise ValueError("direction must be input or output")
        result = {"track": track.name, "direction": direction}
        route_type = payload.get("type")
        route_channel = payload.get("channel")
        if route_type is not None:
            setattr(track, "%s_routing_type" % direction, self._match_routing(getattr(track, "available_%s_routing_types" % direction), route_type))
            result["type"] = self._safe_get(track, "current_%s_routing" % direction)
        if route_channel is not None:
            setattr(track, "%s_routing_channel" % direction, self._match_routing(getattr(track, "available_%s_routing_channels" % direction), route_channel))
            result["channel"] = self._safe_get(track, "current_%s_sub_routing" % direction)
        return result

    def _match_routing(self, values, requested):
        normalized = self._normalize_name(requested)
        matches = [value for value in list(values) if normalized in self._normalize_name(self._routing_name(value))]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Ambiguous routing %r: %s" % (requested, [self._routing_name(value) for value in matches]))
        raise ValueError("No routing option named %r. Available: %s" % (requested, [self._routing_name(value) for value in list(values)]))

    def _routing_name(self, value):
        for name in ("display_name", "name", "identifier"):
            found = self._safe_get(value, name)
            if found:
                return found
        return str(value)

    def _midi_get_notes(self, payload):
        clip = self._resolve_clip(payload)
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")
        if self._has_note_region(payload):
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
            notes = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)
        else:
            try:
                notes = clip.get_all_notes_extended()
            except TypeError:
                notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
        return {"clip": self._clip_info(clip), "notes": self._serialize(notes)}

    def _midi_add_notes(self, payload):
        if Live is None:
            raise ValueError("Live module is not available")
        clip = self._resolve_clip(payload)
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")
        notes = payload.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("notes must be a list")
        self._add_note_dicts(clip, notes)
        return self._midi_get_notes(payload)

    def _midi_replace_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        notes = payload.get("notes", [])
        if not isinstance(notes, list):
            raise ValueError("notes must be a list")
        self._remove_notes_region(clip, 0, 128, 0.0, max(float(self._safe_get(clip, "length", 0.0)), 1576800.0))
        self._add_note_dicts(clip, notes)
        return self._midi_get_notes(payload)

    def _midi_update_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        updates = payload.get("notes", [])
        if not isinstance(updates, list):
            raise ValueError("notes must be a list")
        existing = {}
        for note in self._midi_note_dicts(clip):
            note_id = note.get("note_id")
            if note_id is not None:
                existing[int(note_id)] = note
        modified = []
        for update in updates:
            if not isinstance(update, dict) or "note_id" not in update:
                raise ValueError("Each update note must include note_id")
            note_id = int(update["note_id"])
            if note_id not in existing:
                raise ValueError("No note with note_id %s" % note_id)
            data = dict(existing[note_id])
            data.update(update)
            modified.append(data)
        if modified:
            self._replace_notes_by_id(clip, modified)
        return self._midi_get_notes(payload)

    def _midi_remove_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        ids = payload.get("note_ids")
        if ids:
            clip.remove_notes_by_id(tuple(int(note_id) for note_id in ids))
        else:
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
            self._remove_notes_region(clip, from_pitch, pitch_span, from_time, time_span)
        return self._midi_get_notes(payload)

    def _midi_clear_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        if self._has_note_region(payload):
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(payload, clip)
        else:
            from_pitch, pitch_span, from_time, time_span = (0, 128, 0.0, max(float(self._safe_get(clip, "length", 0.0)), 1576800.0))
        self._remove_notes_region(clip, from_pitch, pitch_span, from_time, time_span)
        return self._midi_get_notes(payload)

    def _midi_transform_notes(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        notes = self._midi_note_dicts(clip, payload if self._has_note_region(payload) else None)
        modified = []
        transpose = int(payload.get("transpose", 0))
        time_delta = float(payload.get("time_delta", 0.0))
        duration_scale = float(payload.get("duration_scale", 1.0))
        duration_delta = float(payload.get("duration_delta", 0.0))
        velocity_scale = float(payload.get("velocity_scale", 1.0))
        velocity_delta = float(payload.get("velocity_delta", 0.0))
        for note in notes:
            data = dict(note)
            data["pitch"] = self._clamp_int(int(data.get("pitch", 0)) + transpose, 0, 127)
            data["start_time"] = max(0.0, float(data.get("start_time", 0.0)) + time_delta)
            data["duration"] = max(0.0001, float(data.get("duration", 0.0)) * duration_scale + duration_delta)
            data["velocity"] = self._clamp_float(float(data.get("velocity", 100.0)) * velocity_scale + velocity_delta, 0.0, 127.0)
            if "probability" in payload:
                data["probability"] = self._clamp_float(float(payload["probability"]), 0.0, 1.0)
            if "velocity_deviation" in payload:
                data["velocity_deviation"] = self._clamp_float(float(payload["velocity_deviation"]), -127.0, 127.0)
            if "release_velocity" in payload:
                data["release_velocity"] = self._clamp_float(float(payload["release_velocity"]), 0.0, 127.0)
            if "mute" in payload:
                data["mute"] = bool(payload["mute"])
            modified.append(data)
        if modified:
            self._replace_notes_by_id(clip, modified)
        return self._midi_get_notes(payload)

    def _midi_duplicate_region(self, payload):
        clip = self._resolve_clip(payload)
        self._ensure_midi_clip(clip)
        region_start = float(payload.get("start", 0.0))
        if "length" in payload:
            region_length = float(payload.get("length"))
        elif "end" in payload:
            region_length = float(payload.get("end")) - region_start
        else:
            raise ValueError("midi-duplicate-region needs --length or --end")
        destination_time = float(payload.get("destination_time"))
        pitch = int(payload.get("pitch", -1))
        transposition = int(payload.get("transpose", 0))
        try:
            clip.duplicate_region(region_start, region_length, destination_time, pitch, transposition)
        except TypeError:
            if pitch != -1 or transposition != 0:
                clip.duplicate_region(region_start, region_length, destination_time, pitch, transposition)
            else:
                clip.duplicate_region(region_start, region_length, destination_time)
        result_payload = dict(payload)
        for key in ("start", "end", "length", "pitch_min", "pitch_max"):
            result_payload.pop(key, None)
        return self._midi_get_notes(result_payload)

    def _midi_note_spec(self, note, include_note_id=False):
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object")
        data = {
            "pitch": int(note["pitch"]),
            "start_time": float(note.get("start_time", note.get("start", 0.0))),
            "duration": float(note.get("duration", 1.0)),
            "velocity": float(note.get("velocity", 100.0)),
            "mute": bool(note.get("mute", False)),
            "probability": float(note.get("probability", 1.0)),
            "velocity_deviation": float(note.get("velocity_deviation", 0.0)),
            "release_velocity": float(note.get("release_velocity", 64.0)),
        }
        if include_note_id and "note_id" in note:
            data["note_id"] = int(note["note_id"])
        spec_class = Live.Clip.MidiNoteSpecification
        try:
            return spec_class(**data)
        except TypeError:
            spec = spec_class()
            for key, value in data.items():
                setattr(spec, key, value)
            return spec

    def _resolve_clip(self, payload):
        return self._resolve_clip_ref(payload)["clip"]

    def _ensure_midi_track(self, track):
        if not self._safe_get(track, "has_midi_input", False):
            raise ValueError("Track %s is not a MIDI track" % track.name)

    def _ensure_midi_clip(self, clip):
        if not self._safe_get(clip, "is_midi_clip", False):
            raise ValueError("Clip is not a MIDI clip")

    def _resolve_clip_slot(self, track, slot_index):
        slots = list(track.clip_slots)
        if slot_index < 0 or slot_index >= len(slots):
            raise ValueError("Clip slot index out of range: %s" % slot_index)
        return slots[slot_index]

    def _resolve_clip_ref(self, payload, prefix=""):
        path = self._prefixed(payload, prefix, "path")
        if path:
            clip = self._resolve_lom_path(path)
            if not hasattr(clip, "is_audio_clip") and not hasattr(clip, "is_midi_clip"):
                raise ValueError("Path did not resolve to a clip")
            return self._clip_ref_from_clip(clip)

        track = self._resolve_track(self._prefixed(payload, prefix, "track"))
        arrangement_index = self._prefixed(payload, prefix, "arrangement_index", None)
        if arrangement_index is not None:
            clips = list(track.arrangement_clips)
            index = int(arrangement_index)
            if index < 0 or index >= len(clips):
                raise ValueError("Arrangement clip index out of range: %s" % index)
            return {"kind": "arrangement", "track": track, "arrangement_index": index, "clip": clips[index]}

        arrangement_start = self._prefixed(payload, prefix, "arrangement_start", None)
        if arrangement_start is not None:
            clip = self._find_arrangement_clip_at(track, float(arrangement_start))
            return self._clip_ref_from_clip(clip)

        slot_index = int(self._prefixed(payload, prefix, "slot", 0))
        slot = self._resolve_clip_slot(track, slot_index)
        if not slot.has_clip:
            raise ValueError("Clip slot %s on %s has no clip" % (slot_index, track.name))
        return {"kind": "session", "track": track, "slot": slot, "slot_index": slot_index, "clip": slot.clip}

    def _clip_ref_from_clip(self, clip):
        ref = {"kind": "path", "clip": clip}
        try:
            if self._safe_get(clip, "is_session_clip", False):
                slot = clip.canonical_parent
                track = slot.canonical_parent
                ref.update({"kind": "session", "track": track, "slot": slot, "slot_index": self._slot_index(track, slot)})
            elif self._safe_get(clip, "is_arrangement_clip", False):
                track = clip.canonical_parent
                ref.update({"kind": "arrangement", "track": track, "arrangement_index": self._arrangement_clip_index(track, clip)})
        except Exception:
            pass
        return ref

    def _delete_clip_ref(self, ref):
        if ref.get("kind") == "session" and ref.get("slot") is not None:
            ref["slot"].delete_clip()
            return
        track = ref.get("track")
        if track is None:
            track = ref["clip"].canonical_parent
        track.delete_clip(ref["clip"])

    def _clip_ref_info(self, ref):
        info = {"kind": ref.get("kind")}
        track = ref.get("track")
        if track is not None:
            info["track"] = track.name
            info["track_index"] = self._track_index(track)
        if "slot_index" in ref:
            info["slot"] = ref["slot_index"]
        if "arrangement_index" in ref:
            info["arrangement_index"] = ref["arrangement_index"]
        clip = ref.get("clip")
        if clip is not None:
            if self._safe_get(clip, "is_arrangement_clip", False):
                info["start_time"] = self._safe_get(clip, "start_time")
                info["end_time"] = self._safe_get(clip, "end_time")
            info["clip"] = self._clip_info(clip)
        return info

    def _prefixed(self, payload, prefix, key, default=None):
        if prefix:
            return payload.get("%s_%s" % (prefix, key), default)
        return payload.get(key, default)

    def _clip_length_from_payload(self, payload, fallback):
        if payload.get("from_loop", False):
            return float(self.song().loop_length)
        if "length" in payload:
            return float(payload.get("length"))
        if "end" in payload:
            start = float(payload.get("start", 0.0))
            return float(payload.get("end")) - start
        if fallback is not None:
            return float(fallback)
        return 4.0

    def _arrangement_range_from_payload(self, payload, fallback_start, fallback_length):
        if payload.get("from_loop", False):
            start = float(self.song().loop_start)
            length = float(self.song().loop_length)
        else:
            start = float(payload.get("start", fallback_start))
            length = self._clip_length_from_payload(payload, fallback_length)
        if "end" in payload:
            end = float(payload.get("end"))
            length = end - start
        if length <= 0.0:
            raise ValueError("Clip length must be greater than 0")
        return start, length

    def _create_midi_clip_destination(self, payload, source_ref):
        source_clip = source_ref["clip"]
        source_track = source_ref.get("track")
        target_track = self._resolve_track(payload.get("dest_track", source_track.name if source_track is not None else None))
        self._ensure_midi_track(target_track)
        length = self._clip_length_from_payload(payload, self._safe_get(source_clip, "length", 4.0))
        dest_slot = payload.get("dest_slot")
        if dest_slot is not None:
            slot_index = int(dest_slot)
            slot = self._resolve_clip_slot(target_track, slot_index)
            if slot.has_clip:
                if payload.get("replace", False):
                    slot.delete_clip()
                else:
                    raise ValueError("Destination clip slot %s on %s already has a clip" % (slot_index, target_track.name))
            slot.create_clip(length)
            return {"kind": "session", "track": target_track, "slot": slot, "slot_index": slot_index, "clip": slot.clip}

        if payload.get("dest_from_loop", False):
            start = float(self.song().loop_start)
        elif "dest_start" in payload:
            start = float(payload.get("dest_start"))
        elif "start" in payload:
            start = float(payload.get("start"))
        else:
            start = float(self._safe_get(source_clip, "start_time", 0.0))
        if "dest_end" in payload:
            length = float(payload.get("dest_end")) - start
        if length <= 0.0:
            raise ValueError("Destination clip length must be greater than 0")
        clip = target_track.create_midi_clip(start, length)
        if clip is None:
            clip = self._find_arrangement_clip(target_track, start, length)
        return self._clip_ref_from_clip(clip)

    def _find_arrangement_clip(self, track, start, length):
        target_end = start + length
        for clip in track.arrangement_clips:
            clip_start = float(self._safe_get(clip, "start_time", -1.0))
            clip_end = float(self._safe_get(clip, "end_time", -1.0))
            if abs(clip_start - start) < 0.0001 and abs(clip_end - target_end) < 0.0001:
                return clip
        raise ValueError("Could not find newly-created Arrangement clip")

    def _find_arrangement_clip_at(self, track, start):
        matches = []
        for clip in track.arrangement_clips:
            clip_start = float(self._safe_get(clip, "start_time", -1.0))
            clip_end = float(self._safe_get(clip, "end_time", -1.0))
            if abs(clip_start - start) < 0.0001 or (clip_start <= start < clip_end):
                matches.append(clip)
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Arrangement time %s matches multiple clips" % start)
        raise ValueError("No Arrangement clip at %s on %s" % (start, track.name))

    def _slot_index(self, track, slot):
        for index, candidate in enumerate(track.clip_slots):
            if candidate == slot:
                return index
        return -1

    def _arrangement_clip_index(self, track, clip):
        for index, candidate in enumerate(track.arrangement_clips):
            if candidate == clip:
                return index
        return -1

    def _copy_midi_clip_contents(self, source, target):
        self._apply_clip_look(self._clip_info(source), target, self._safe_get(source, "name", ""))
        self._add_note_dicts(target, self._midi_note_dicts(source))

    def _apply_clip_look(self, info, clip, name):
        self._set_optional_clip_property(clip, "name", name)
        self._set_optional_clip_property(clip, "color", info.get("color"))
        self._set_optional_clip_property(clip, "color_index", info.get("color_index"))
        self._set_optional_clip_property(clip, "muted", info.get("muted"))
        self._set_optional_clip_property(clip, "looping", info.get("looping"))
        self._set_optional_clip_property(clip, "signature_numerator", info.get("signature_numerator"))
        self._set_optional_clip_property(clip, "signature_denominator", info.get("signature_denominator"))

    def _set_optional_clip_property(self, clip, attr, value):
        if value is None:
            return
        try:
            setattr(clip, attr, value)
        except Exception:
            pass

    def _add_note_dicts(self, clip, notes):
        if not notes:
            return
        clip.add_new_notes(tuple(self._midi_note_spec(note) for note in notes))

    def _replace_notes_by_id(self, clip, notes):
        ids = [int(note["note_id"]) for note in notes if "note_id" in note]
        if ids:
            clip.remove_notes_by_id(tuple(ids))
        self._add_note_dicts(clip, notes)

    def _midi_note_dicts(self, clip, region_payload=None):
        self._ensure_midi_clip(clip)
        if region_payload is not None:
            from_pitch, pitch_span, from_time, time_span = self._midi_region_args(region_payload, clip)
            notes = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)
        else:
            try:
                notes = clip.get_all_notes_extended()
            except TypeError:
                notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
        serialized = self._serialize(notes)
        if isinstance(serialized, dict) and "items" in serialized:
            return serialized["items"]
        if isinstance(serialized, list):
            return serialized
        return []

    def _remove_notes_region(self, clip, from_pitch, pitch_span, from_time, time_span):
        try:
            clip.remove_notes_extended(int(from_pitch), int(pitch_span), float(from_time), float(time_span))
        except TypeError:
            clip.remove_notes(float(from_time), int(from_pitch), float(time_span), int(pitch_span))

    def _midi_region_args(self, payload, clip):
        from_pitch = self._clamp_int(int(payload.get("pitch_min", 0)), 0, 127)
        pitch_max = self._clamp_int(int(payload.get("pitch_max", 127)), from_pitch, 127)
        pitch_span = pitch_max - from_pitch + 1
        from_time = max(0.0, float(payload.get("start", 0.0)))
        if "end" in payload:
            time_span = float(payload.get("end")) - from_time
        elif "length" in payload:
            time_span = float(payload.get("length"))
        else:
            time_span = max(float(self._safe_get(clip, "length", 0.0)) - from_time, 0.0)
        if time_span < 0.0:
            raise ValueError("MIDI note region end must be after start")
        return from_pitch, pitch_span, from_time, time_span

    def _has_note_region(self, payload):
        return any(key in payload for key in ("start", "end", "length", "pitch_min", "pitch_max"))

    def _split_note_dicts(self, notes, split_offset):
        left = []
        right = []
        for note in notes:
            start = float(note.get("start_time", 0.0))
            duration = float(note.get("duration", 0.0))
            end = start + duration
            if start < split_offset:
                left_duration = min(end, split_offset) - start
                if left_duration > 0.0001:
                    data = dict(note)
                    data["duration"] = left_duration
                    left.append(data)
            if end > split_offset:
                right_start = max(start, split_offset) - split_offset
                right_duration = end - max(start, split_offset)
                if right_duration > 0.0001:
                    data = dict(note)
                    data["start_time"] = right_start
                    data["duration"] = right_duration
                    right.append(data)
        return left, right

    def _clamp_int(self, value, minimum, maximum):
        return max(minimum, min(maximum, int(value)))

    def _clamp_float(self, value, minimum, maximum):
        return max(minimum, min(maximum, float(value)))

    def _status(self):
        song = self.song()
        return {
            "tempo": song.tempo,
            "is_playing": song.is_playing,
            "selected_track": song.view.selected_track.name,
            "track_count": len(song.tracks),
            "return_count": len(song.return_tracks),
            "tracks": [self._track_info(track, index) for index, track in enumerate(song.tracks)],
        }

    def _selected(self, include_devices):
        track = self.song().view.selected_track
        info = self._track_info(track, self._track_index(track), self._track_kind(track))
        if include_devices:
            info["devices"] = self._device_infos(track)
        return info

    def _set_track(self, payload):
        track = self._resolve_track(payload.get("track"))
        mixer = track.mixer_device
        changed = {}
        if "volume" in payload:
            self._set_parameter(mixer.volume, value=float(payload["volume"]))
            changed["volume"] = self._parameter_info(mixer.volume)
        if "pan" in payload:
            self._set_parameter(mixer.panning, value=float(payload["pan"]))
            changed["pan"] = self._parameter_info(mixer.panning)
        for name in ("mute", "solo", "arm"):
            if name in payload:
                try:
                    setattr(track, name, bool(payload[name]))
                    changed[name] = getattr(track, name)
                except Exception as error:
                    raise ValueError("Track %s does not support %s: %s" % (track.name, name, error))
        return {"track": track.name, "changed": changed}

    def _set_send(self, payload):
        track = self._resolve_track(payload.get("track"))
        send = payload.get("send")
        sends = list(track.mixer_device.sends)
        if isinstance(send, int):
            index = send
        else:
            normalized = self._normalize_name(str(send))
            index = None
            for candidate_index, parameter in enumerate(sends):
                if normalized in (self._normalize_name(parameter.name), str(candidate_index)):
                    index = candidate_index
                    break
            if index is None and len(str(send)) == 1:
                possible = ord(str(send).upper()) - ord("A")
                if 0 <= possible < len(sends):
                    index = possible
        if index is None or index < 0 or index >= len(sends):
            raise ValueError("Unknown send %r on track %s" % (send, track.name))
        parameter = sends[index]
        self._set_parameter(parameter, value=float(payload["value"]))
        return {"track": track.name, "send": index, "parameter": self._parameter_info(parameter)}

    def _set_param(self, payload):
        track = self._resolve_track(payload.get("track"))
        device = self._resolve_device(track, payload.get("device"))
        parameter = self._resolve_parameter(device, payload.get("param"))
        if "normalized" in payload:
            self._set_parameter(parameter, normalized=float(payload["normalized"]))
        elif "delta" in payload:
            self._set_parameter(parameter, value=parameter.value + float(payload["delta"]))
        elif "value" in payload:
            self._set_parameter(parameter, value=float(payload["value"]))
        else:
            raise ValueError("set_param requires value, normalized, or delta")
        return {
            "track": track.name,
            "device": device.name,
            "parameter": self._parameter_info(parameter),
        }

    def _set_parameter(self, parameter, value=None, normalized=None):
        if normalized is not None:
            normalized = max(0.0, min(1.0, normalized))
            value = parameter.min + (parameter.max - parameter.min) * normalized
        value = max(parameter.min, min(parameter.max, value))
        parameter.value = value

    def _resolve_lom_path(self, path):
        if path is None or path == "" or path == "song":
            return self.song()
        if isinstance(path, list):
            parts = path
        else:
            text = str(path).strip()
            if text in ("song", "live_set"):
                return self.song()
            if text == "application":
                return self.application()
            parts = text.split(".")

        if not parts:
            return self.song()

        first = parts[0]
        if first in ("song", "live_set"):
            obj = self.song()
            parts = parts[1:]
        elif first == "application":
            obj = self.application()
            parts = parts[1:]
        else:
            obj = self.song()

        for part in parts:
            obj = self._resolve_lom_part(obj, part)
        return obj

    def _resolve_lom_part(self, obj, part):
        if isinstance(part, dict):
            obj = getattr(obj, part["attr"]) if "attr" in part else obj
            if "index" in part:
                obj = obj[int(part["index"])]
            return obj
        text = str(part)
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(.+)\])?$", text)
        if not match:
            raise ValueError("Invalid LOM path segment: %r" % text)
        attr, index = match.groups()
        obj = getattr(obj, attr)
        if index is None:
            return obj
        key = index.strip().strip("\"'")
        if key == "selected":
            return self.song().view.selected_track
        try:
            return obj[int(key)]
        except ValueError:
            normalized = self._normalize_name(key)
            matches = [item for item in obj if normalized in self._normalize_name(getattr(item, "name", ""))]
            if len(matches) == 1:
                return matches[0]
            if matches:
                raise ValueError("Ambiguous collection lookup %r: %s" % (key, [getattr(item, "name", "") for item in matches]))
            raise ValueError("No collection item named %r" % key)

    def _split_lom_attribute(self, path):
        if not path:
            raise ValueError("path is required")
        if isinstance(path, list):
            return path[:-1], path[-1]
        text = str(path)
        if "." not in text:
            raise ValueError("set path must include an attribute, e.g. song.tempo")
        target, attribute = text.rsplit(".", 1)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", attribute):
            raise ValueError("Invalid set attribute: %r" % attribute)
        return target, attribute

    def _coerce_like(self, value, current):
        if isinstance(current, bool):
            return bool(value)
        if isinstance(current, int) and not isinstance(current, bool):
            return int(value)
        if isinstance(current, float):
            return float(value)
        return value

    def _resolve_track(self, identifier):
        song = self.song()
        if identifier is None:
            return song.view.selected_track
        if isinstance(identifier, int):
            tracks = list(song.tracks)
            if 0 <= identifier < len(tracks):
                return tracks[identifier]
            raise ValueError("Track index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        if lowered == "selected":
            return song.view.selected_track
        if lowered == "master":
            return song.master_track
        if lowered.startswith("return:"):
            return self._resolve_return_track(text.split(":", 1)[1])
        for track in list(song.tracks) + list(song.return_tracks) + [song.master_track]:
            if track.name.lower() == lowered:
                return track
        normalized = self._normalize_name(text)
        matches = [
            track
            for track in list(song.tracks) + list(song.return_tracks) + [song.master_track]
            if normalized in self._normalize_name(track.name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Track %r is ambiguous: %s" % (identifier, [track.name for track in matches]))
        raise ValueError("Unknown track: %r" % (identifier,))

    def _resolve_return_track(self, identifier):
        returns = list(self.song().return_tracks)
        text = str(identifier).strip()
        if text.isdigit():
            index = int(text)
            if 0 <= index < len(returns):
                return returns[index]
        if len(text) == 1 and text.isalpha():
            index = ord(text.upper()) - ord("A")
            if 0 <= index < len(returns):
                return returns[index]
        lowered = text.lower()
        for track in returns:
            if track.name.lower() == lowered:
                return track
        raise ValueError("Unknown return track: %r" % identifier)

    def _resolve_device(self, track, identifier):
        devices = list(track.devices)
        if isinstance(identifier, int):
            if 0 <= identifier < len(devices):
                return devices[identifier]
            raise ValueError("Device index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        for device in devices:
            if device.name.lower() == lowered or device.class_name.lower() == lowered:
                return device
        normalized = self._normalize_name(text)
        matches = [
            device
            for device in devices
            if normalized in self._normalize_name(device.name)
            or normalized in self._normalize_name(device.class_name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Device %r is ambiguous: %s" % (identifier, [device.name for device in matches]))
        raise ValueError("Unknown device %r on track %s" % (identifier, track.name))

    def _resolve_parameter(self, device, identifier):
        parameters = list(device.parameters)
        if isinstance(identifier, int):
            if 0 <= identifier < len(parameters):
                return parameters[identifier]
            raise ValueError("Parameter index out of range: %s" % identifier)
        text = str(identifier).strip()
        lowered = text.lower()
        for parameter in parameters:
            if parameter.name.lower() == lowered:
                return parameter
        normalized = self._normalize_name(text)
        matches = [
            parameter
            for parameter in parameters
            if normalized in self._normalize_name(parameter.name)
        ]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Parameter %r is ambiguous: %s" % (identifier, [parameter.name for parameter in matches]))
        raise ValueError("Unknown parameter %r on device %s" % (identifier, device.name))

    def _track_info(self, track, index, kind="track"):
        mixer = track.mixer_device
        info = {
            "kind": kind,
            "index": index,
            "name": track.name,
            "volume": self._parameter_info(mixer.volume),
            "pan": self._parameter_info(mixer.panning),
            "mute": self._safe_get(track, "mute"),
            "solo": self._safe_get(track, "solo"),
            "arm": self._safe_get(track, "arm"),
            "device_count": len(track.devices),
            "send_count": len(mixer.sends),
        }
        return info

    def _device_infos(self, track):
        return [self._device_info(device, index) for index, device in enumerate(track.devices)]

    def _device_info(self, device, index):
        return {
            "index": index,
            "name": device.name,
            "class_name": device.class_name,
            "can_have_chains": getattr(device, "can_have_chains", False),
            "parameter_count": len(device.parameters),
        }

    def _clip_info(self, clip):
        return {
            "name": clip.name,
            "color": self._safe_get(clip, "color"),
            "color_index": self._safe_get(clip, "color_index"),
            "is_audio_clip": self._safe_get(clip, "is_audio_clip"),
            "is_midi_clip": self._safe_get(clip, "is_midi_clip"),
            "is_session_clip": self._safe_get(clip, "is_session_clip"),
            "is_arrangement_clip": self._safe_get(clip, "is_arrangement_clip"),
            "length": self._safe_get(clip, "length"),
            "start_time": self._safe_get(clip, "start_time"),
            "end_time": self._safe_get(clip, "end_time"),
            "looping": self._safe_get(clip, "looping"),
            "loop_start": self._safe_get(clip, "loop_start"),
            "loop_end": self._safe_get(clip, "loop_end"),
            "start_marker": self._safe_get(clip, "start_marker"),
            "end_marker": self._safe_get(clip, "end_marker"),
            "muted": self._safe_get(clip, "muted"),
            "launch_mode": self._safe_get(clip, "launch_mode"),
            "launch_quantization": self._safe_get(clip, "launch_quantization"),
            "legato": self._safe_get(clip, "legato"),
            "signature_numerator": self._safe_get(clip, "signature_numerator"),
            "signature_denominator": self._safe_get(clip, "signature_denominator"),
            "velocity_amount": self._safe_get(clip, "velocity_amount"),
            "gain": self._safe_get(clip, "gain"),
            "pitch_coarse": self._safe_get(clip, "pitch_coarse"),
            "pitch_fine": self._safe_get(clip, "pitch_fine"),
            "warping": self._safe_get(clip, "warping"),
        }

    def _scene_info(self, scene, index):
        return {
            "index": index,
            "name": scene.name,
            "color": self._safe_get(scene, "color"),
            "color_index": self._safe_get(scene, "color_index"),
            "is_empty": self._safe_get(scene, "is_empty"),
            "is_triggered": self._safe_get(scene, "is_triggered"),
            "tempo": self._safe_get(scene, "tempo"),
            "tempo_enabled": self._safe_get(scene, "tempo_enabled"),
            "time_signature_enabled": self._safe_get(scene, "time_signature_enabled"),
            "time_signature_numerator": self._safe_get(scene, "time_signature_numerator"),
            "time_signature_denominator": self._safe_get(scene, "time_signature_denominator"),
        }

    def _parameter_infos(self, device):
        return [self._parameter_info(parameter, index) for index, parameter in enumerate(device.parameters)]

    def _parameter_info(self, parameter, index=None):
        try:
            display_value = parameter.str_for_value(parameter.value)
        except Exception:
            display_value = str(parameter.value)
        info = {
            "name": parameter.name,
            "value": parameter.value,
            "min": parameter.min,
            "max": parameter.max,
            "display_value": display_value,
            "is_enabled": getattr(parameter, "is_enabled", True),
            "is_quantized": getattr(parameter, "is_quantized", False),
        }
        if index is not None:
            info["index"] = index
        return info

    def _serialize(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, dict):
            return {str(key): self._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize(item) for item in list(value)[:512]]
        if self._is_indexable_vector(value):
            length = len(value)
            return {
                "type": type(value).__name__,
                "length": length,
                "items": [self._serialize(value[index]) for index in range(min(length, 512))],
                "truncated": length > 512,
            }
        if hasattr(value, "min") and hasattr(value, "max") and hasattr(value, "value"):
            return self._parameter_info(value)
        if hasattr(value, "clip_slots") and hasattr(value, "mixer_device"):
            return self._track_info(value, self._track_index(value), self._track_kind(value))
        if hasattr(value, "parameters") and hasattr(value, "class_name"):
            return self._device_info(value, -1)
        if hasattr(value, "is_audio_clip") or hasattr(value, "is_midi_clip"):
            return self._clip_info(value)
        if hasattr(value, "is_loadable") and hasattr(value, "children"):
            return {"type": type(value).__name__, "item": self._browser_item_info(value)}
        if hasattr(value, "pitch") and hasattr(value, "start_time"):
            return self._note_info(value)
        return {"type": type(value).__name__, "summary": self._summary(value)}

    def _note_info(self, note):
        keys = (
            "note_id",
            "pitch",
            "start_time",
            "duration",
            "velocity",
            "velocity_deviation",
            "release_velocity",
            "probability",
            "mute",
        )
        return {key: self._safe_get(note, key) for key in keys if self._safe_get(note, key) is not None}

    def _summary(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return {"type": type(value).__name__, "length": len(value)}
        if self._is_indexable_vector(value):
            return {"type": type(value).__name__, "length": len(value)}
        name = self._safe_get(value, "name")
        class_name = self._safe_get(value, "class_name")
        summary = {"type": type(value).__name__}
        if name is not None:
            summary["name"] = name
        if class_name is not None:
            summary["class_name"] = class_name
        return summary

    def _track_index(self, track):
        for index, candidate in enumerate(self.song().tracks):
            if candidate == track:
                return index
        for index, candidate in enumerate(self.song().return_tracks):
            if candidate == track:
                return index
        return 0

    def _track_kind(self, track):
        if track == self.song().master_track:
            return "master"
        if track in list(self.song().return_tracks):
            return "return"
        return "track"

    def _resolve_scene(self, identifier):
        scenes = list(self.song().scenes)
        if isinstance(identifier, int):
            if 0 <= identifier < len(scenes):
                return scenes[identifier]
            raise ValueError("Scene index out of range: %s" % identifier)
        text = str(identifier).strip()
        if text.isdigit():
            return self._resolve_scene(int(text))
        normalized = self._normalize_name(text)
        matches = [scene for scene in scenes if normalized in self._normalize_name(scene.name)]
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError("Scene %r is ambiguous: %s" % (identifier, [scene.name for scene in matches]))
        raise ValueError("Unknown scene: %r" % identifier)

    def _scene_index(self, scene):
        for index, candidate in enumerate(self.song().scenes):
            if candidate == scene:
                return index
        return 0

    def _normalize_name(self, value):
        return "".join(character.lower() for character in str(value) if character.isalnum())

    def _safe_get(self, obj, name, default=None):
        try:
            return getattr(obj, name)
        except Exception:
            return default

    def _is_indexable_vector(self, value):
        if isinstance(value, (bytes, str)):
            return False
        return hasattr(value, "__len__") and hasattr(value, "__getitem__")
