"""Payload builders for raw commands."""

import json

def build_raw_payload(args):
    command = args.command
    if command == "raw":
        try:
            payload = json.loads(args.json_payload)
        except ValueError as exc:
            raise SystemExit(f"Invalid JSON payload: {exc}")
        if not isinstance(payload, dict):
            raise SystemExit("Raw payload must be a JSON object.")
        return payload
    return None
