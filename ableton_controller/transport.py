"""JSON socket transport for the Ableton bridge."""

import json
import socket
from typing import Any

def send(payload: dict[str, Any], host: str, port: int, timeout: float) -> dict[str, Any]:
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(data)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
    except OSError as exc:
        raise SystemExit(
            f"Could not connect to Ableton bridge at {host}:{port}: {exc}\n"
            "Is the Codex_AI control surface loaded in Live?"
        )

    raw = b"".join(chunks).strip()
    if not raw:
        raise SystemExit("Ableton bridge returned an empty response.")
    try:
        response = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise SystemExit(f"Ableton bridge returned invalid JSON: {exc}: {raw!r}")
    if not response.get("ok", False):
        message = response.get("error") or response
        raise SystemExit(f"Ableton bridge error: {message}")
    return response
