"""CommandDispatcher mixins for the Codex_AI Ableton bridge."""


class CommandDispatcherMixin(object):
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
        if command == "device_tree":
            return self._device_tree(payload)
        if command == "device_add_stock":
            return self._device_add_stock(payload)
        if command == "device_move":
            return self._device_move(payload)
        if command == "device_delete":
            return self._device_delete(payload)
        if command == "drum_pad_load":
            return self._drum_pad_load(payload)
        if command == "params":
            device = self._resolve_device_ref(payload)
            return {"device": self._device_info(device, self._device_index(device)), "parameters": self._parameter_infos(device)}
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
        if command == "locators":
            return self._locators()
        if command == "set_locator":
            return self._set_locator(payload)
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
        if command == "clip_create_audio":
            return self._clip_create_audio(payload)
        if command == "clip_set":
            return self._clip_set(payload)
        if command == "clip_warp":
            return self._clip_warp(payload)
        if command == "clip_warp_marker_add":
            return self._clip_warp_marker_add(payload)
        if command == "clip_warp_marker_move":
            return self._clip_warp_marker_move(payload)
        if command == "clip_warp_marker_remove":
            return self._clip_warp_marker_remove(payload)
        if command == "clip_automation_get":
            return self._clip_automation_get(payload)
        if command == "clip_automation_set":
            return self._clip_automation_set(payload)
        if command == "clip_automation_clear":
            return self._clip_automation_clear(payload)
        if command == "arrangement_automation_get":
            return self._arrangement_automation_get(payload)
        if command == "arrangement_automation_set":
            return self._arrangement_automation_set(payload)
        if command == "arrangement_automation_set_many":
            return self._arrangement_automation_set_many(payload)
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
