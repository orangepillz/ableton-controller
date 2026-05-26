import json
import queue
import socket
import threading
import traceback

from _Framework.ControlSurface import ControlSurface

try:
    from .automation_commands import AutomationCommandMixin
    from .automation_helpers import AutomationHelperMixin
    from .browser_commands import BrowserCommandMixin
    from .clip_commands import ClipCommandMixin
    from .clip_automation_commands import ClipAutomationCommandMixin
    from .clip_envelope_commands import ClipEnvelopeCommandMixin
    from .clip_refs import ClipReferenceMixin
    from .clip_warp_commands import ClipWarpCommandMixin
    from .device_commands import DeviceCommandMixin
    from .dispatch import CommandDispatcherMixin
    from .drum_pad_commands import DrumPadCommandMixin
    from .lom_commands import LomCommandMixin
    from .lom_resolver import LomResolverMixin
    from .midi_commands import MidiCommandMixin
    from .midi_helpers import MidiHelperMixin
    from .resolvers import ResolverMixin
    from .serum_commands import SerumCommandMixin
    from .serialization import SerializationMixin
    from .track_commands import TrackCommandMixin
    from .utilities import UtilityMixin
    from .warp_markers import WarpMarkerMixin
except ImportError:
    from automation_commands import AutomationCommandMixin
    from automation_helpers import AutomationHelperMixin
    from browser_commands import BrowserCommandMixin
    from clip_commands import ClipCommandMixin
    from clip_automation_commands import ClipAutomationCommandMixin
    from clip_envelope_commands import ClipEnvelopeCommandMixin
    from clip_refs import ClipReferenceMixin
    from clip_warp_commands import ClipWarpCommandMixin
    from device_commands import DeviceCommandMixin
    from dispatch import CommandDispatcherMixin
    from drum_pad_commands import DrumPadCommandMixin
    from lom_commands import LomCommandMixin
    from lom_resolver import LomResolverMixin
    from midi_commands import MidiCommandMixin
    from midi_helpers import MidiHelperMixin
    from resolvers import ResolverMixin
    from serum_commands import SerumCommandMixin
    from serialization import SerializationMixin
    from track_commands import TrackCommandMixin
    from utilities import UtilityMixin
    from warp_markers import WarpMarkerMixin


HOST = "127.0.0.1"
PORT = 37337


class _Request(object):
    def __init__(self, payload):
        self.payload = payload
        self.event = threading.Event()
        self.response = None


class CodexBridge(
    CommandDispatcherMixin,
    LomCommandMixin,
    DeviceCommandMixin,
    SerumCommandMixin,
    DrumPadCommandMixin,
    ClipCommandMixin,
    ClipEnvelopeCommandMixin,
    ClipWarpCommandMixin,
    ClipAutomationCommandMixin,
    AutomationCommandMixin,
    BrowserCommandMixin,
    TrackCommandMixin,
    MidiCommandMixin,
    ClipReferenceMixin,
    AutomationHelperMixin,
    WarpMarkerMixin,
    MidiHelperMixin,
    LomResolverMixin,
    ResolverMixin,
    SerializationMixin,
    UtilityMixin,
    ControlSurface,
):
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
