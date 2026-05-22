import json
import queue
import re
import socket
import threading
import traceback

from _Framework.ControlSurface import ControlSurface


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
        slots = list(track.clip_slots)
        if slot_index < 0 or slot_index >= len(slots):
            raise ValueError("Clip slot index out of range: %s" % slot_index)
        slots[slot_index].fire()
        return {"track": track.name, "slot": slot_index, "done": True}

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
            "is_audio_clip": self._safe_get(clip, "is_audio_clip"),
            "is_midi_clip": self._safe_get(clip, "is_midi_clip"),
            "looping": self._safe_get(clip, "looping"),
            "loop_start": self._safe_get(clip, "loop_start"),
            "loop_end": self._safe_get(clip, "loop_end"),
            "start_marker": self._safe_get(clip, "start_marker"),
            "end_marker": self._safe_get(clip, "end_marker"),
            "gain": self._safe_get(clip, "gain"),
            "pitch_coarse": self._safe_get(clip, "pitch_coarse"),
            "pitch_fine": self._safe_get(clip, "pitch_fine"),
            "warping": self._safe_get(clip, "warping"),
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
        if isinstance(value, (list, tuple)):
            return [self._serialize(item) for item in list(value)[:512]]
        if hasattr(value, "min") and hasattr(value, "max") and hasattr(value, "value"):
            return self._parameter_info(value)
        if hasattr(value, "clip_slots") and hasattr(value, "mixer_device"):
            return self._track_info(value, self._track_index(value), self._track_kind(value))
        if hasattr(value, "parameters") and hasattr(value, "class_name"):
            return self._device_info(value, -1)
        if hasattr(value, "is_audio_clip") or hasattr(value, "is_midi_clip"):
            return self._clip_info(value)
        return {"type": type(value).__name__, "summary": self._summary(value)}

    def _summary(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
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

    def _normalize_name(self, value):
        return "".join(character.lower() for character in str(value) if character.isalnum())

    def _safe_get(self, obj, name, default=None):
        try:
            return getattr(obj, name)
        except Exception:
            return default
