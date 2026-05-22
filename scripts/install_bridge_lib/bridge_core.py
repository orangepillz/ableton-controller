"""Low-level JSON bridge request helper."""

import json
import socket

def bridge_request(payload: dict, host: str, port: int, timeout: float):
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(data)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    if not chunks:
        raise RuntimeError("empty bridge response")
    response = json.loads(b"".join(chunks).decode("utf-8"))
    if not response.get("ok", False):
        raise RuntimeError(response.get("error", "unknown bridge error"))
    return response.get("result")
