"""Drum Rack pad command mixins for the Codex_AI Ableton bridge."""


class DrumPadCommandMixin(object):
    def _drum_pad_load(self, payload):
        track = self._drum_pad_track(payload)
        rack = self._resolve_drum_rack(payload, track)
        pad = self._resolve_drum_pad(rack, payload.get("pad"))
        item = self._resolve_browser_item(payload.get("item"))
        if not self._safe_get(item, "is_loadable", False):
            raise ValueError("Browser item is not loadable: %s" % self._safe_get(item, "name", payload.get("item")))

        before = self._drum_pad_info(pad)
        if before["chain_count"] and not payload.get("clear", False):
            raise ValueError(
                "Pad %s already has %s chain(s); use --clear to replace it"
                % (before.get("note"), before["chain_count"])
            )
        if payload.get("clear", False) and before["chain_count"]:
            self._clear_drum_pad(pad)

        self._select_drum_pad_target(track, rack, pad)
        self.application().browser.load_item(item)
        after = self._drum_pad_info(pad)
        if after["chain_count"] <= 0:
            raise ValueError("Browser item loaded, but pad %s did not report any chains" % after.get("note"))

        return {
            "track": self._track_info(track, self._track_index(track), self._track_kind(track)),
            "rack": self._device_info(rack, self._device_index(rack)),
            "item": self._browser_item_info(item),
            "pad": {"before": before, "after": after},
            "done": True,
        }

    def _drum_pad_track(self, payload):
        if payload.get("track") is not None:
            return self._resolve_track(payload.get("track"))
        rack = self._resolve_lom_path(payload.get("device_path"))
        return self._track_for_container(self._device_container(rack))

    def _resolve_drum_rack(self, payload, track):
        if payload.get("device_path"):
            rack = self._resolve_lom_path(payload.get("device_path"))
        else:
            rack = self._resolve_device(track, payload.get("device") or "Drum Rack")
        if not self._is_drum_rack_device(rack):
            raise ValueError("Device is not a Drum Rack: %s" % self._safe_get(rack, "name", ""))
        return rack

    def _is_drum_rack_device(self, device):
        pads = self._safe_get(device, "drum_pads")
        return self._is_indexable_vector(pads)

    def _resolve_drum_pad(self, rack, note):
        if note is None:
            raise ValueError("pad note is required")
        requested = int(note)
        for pad in list(self._safe_get(rack, "drum_pads", [])):
            if int(self._safe_get(pad, "note", -1)) == requested:
                return pad
        raise ValueError("Drum Rack has no pad for note %s" % requested)

    def _clear_drum_pad(self, pad):
        if not hasattr(pad, "delete_all_chains"):
            raise ValueError("DrumPad does not expose delete_all_chains")
        pad.delete_all_chains()

    def _select_drum_pad_target(self, track, rack, pad):
        try:
            self.song().view.selected_track = track
        except Exception:
            pass
        try:
            track.view.selected_device = rack
        except Exception:
            pass
        rack_view = self._safe_get(rack, "view")
        if rack_view is not None:
            try:
                rack_view.selected_drum_pad = pad
            except Exception:
                pass
        try:
            self.application().view.show_view("Detail")
            self.application().view.show_view("Detail/DeviceChain")
        except Exception:
            pass

    def _drum_pad_info(self, pad):
        chains = list(self._safe_get(pad, "chains", []))
        return {
            "name": self._safe_get(pad, "name"),
            "note": self._safe_get(pad, "note"),
            "mute": self._safe_get(pad, "mute"),
            "solo": self._safe_get(pad, "solo"),
            "chain_count": len(chains),
            "chains": [self._drum_pad_chain_info(chain, index) for index, chain in enumerate(chains)],
        }

    def _drum_pad_chain_info(self, chain, index):
        return {
            "index": index,
            "name": self._safe_get(chain, "name"),
            "device_count": len(self._safe_get(chain, "devices", [])),
            "devices": self._container_device_infos(chain) if hasattr(chain, "devices") else [],
        }
