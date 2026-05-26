"""DeviceCommand mixins for the Codex_AI Ableton bridge."""


class DeviceCommandMixin(object):
    def _device_tree(self, payload):
        track = self._resolve_track(payload.get("track"))
        depth = max(0, int(payload.get("depth", 4)))
        path = self._track_path(track)
        return {"track": self._track_info(track, self._track_index(track), self._track_kind(track)), "path": path, "devices": self._device_tree_devices(track, path, depth)}

    def _device_add_stock(self, payload):
        container = self._resolve_container_ref(payload, "target")
        item = self._resolve_stock_device_item(payload)
        if not payload.get("allow_presets", False):
            if not self._safe_get(item, "is_device", False):
                raise ValueError("Browser item is not a stock device. Use --allow-presets to load presets: %s" % self._safe_get(item, "name", ""))
            if self._safe_get(item, "source", "") != "Built-in":
                raise ValueError("Browser item is not a built-in Live device: %s" % self._safe_get(item, "name", ""))

        return self._load_device_item_to_container(container, item, payload.get("target_index", None))

    def _load_device_item_to_container(self, container, item, target_index):
        owner_track = self._track_for_container(container)
        owner_order = list(owner_track.devices)
        container_order = owner_order if container == owner_track else list(container.devices)
        owner_before = self._device_identity_set(owner_track)
        container_before = self._device_identity_set(container)
        try:
            self.song().view.selected_track = owner_track
        except Exception:
            pass

        if hasattr(container, "insert_device"):
            name = self._safe_get(item, "name", "")
            args = [str(name)] if target_index is None else [str(name), int(target_index)]
            try:
                container.insert_device(*args)
                device = self._new_or_last_device(container, container_before)
                return {
                    "item": self._browser_item_info(item),
                    "target": self._container_info(container),
                    "device": self._device_info(device, self._device_index(device)),
                    "devices": self._container_device_infos(container),
                    "done": True,
                }
            except Exception:
                pass

        self.application().browser.load_item(item)
        device = self._new_or_last_device(owner_track, owner_before)
        if container == owner_track:
            inserted_index = len(container_order) if target_index is None else int(target_index)
            desired_order = [candidate for candidate in container_order if candidate != device]
            desired_order.insert(max(0, min(inserted_index, len(desired_order))), device)
            self._reorder_container_devices(container, desired_order)
            inserted_index = self._device_index(device, container)
            device = self._device_at(container, inserted_index)
        else:
            inserted_index = len(container.devices) if target_index is None else int(target_index)
            inserted_index = self.song().move_device(device, container, inserted_index)
            self._reorder_container_devices(owner_track, owner_order)
            device = self._device_at(container, inserted_index)
        return {
            "item": self._browser_item_info(item),
            "target": self._container_info(container),
            "device": self._device_info(device, self._device_index(device)),
            "devices": self._container_device_infos(container),
            "done": True,
        }

    def _device_move(self, payload):
        device = self._resolve_device_ref(payload, "source")
        target = self._resolve_container_ref(payload, "target")
        requested_index = int(payload.get("target_index"))
        inserted_index = self.song().move_device(device, target, requested_index)
        moved = self._device_at(target, inserted_index)
        return {
            "target": self._container_info(target),
            "requested_index": requested_index,
            "inserted_index": inserted_index,
            "device": self._device_info(moved, inserted_index),
            "devices": self._container_device_infos(target),
            "done": True,
        }

    def _device_delete(self, payload):
        ref = self._resolve_device_ref_info(payload)
        container = ref["container"]
        index = ref["index"]
        info = self._device_info(ref["device"], index)
        container.delete_device(index)
        return {"container": self._container_info(container), "deleted_device": info, "devices": self._container_device_infos(container), "done": True}
