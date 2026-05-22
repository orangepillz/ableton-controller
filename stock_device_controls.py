"""Helpers for Ableton stock-device control registry lookup."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY_PATH = ROOT / "data" / "stock_device_controls.live12.json"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return slug or "control"


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path else DEFAULT_REGISTRY_PATH
    try:
        with registry_path.open("r", encoding="utf-8") as handle:
            registry = json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Stock device registry not found at %s. Run "
            "`python3 scripts/generate_stock_device_controls.py --output %s` with Live open."
            % (registry_path, DEFAULT_REGISTRY_PATH)
        ) from exc
    if not isinstance(registry, dict) or not isinstance(registry.get("devices"), list):
        raise ValueError("Stock device registry is invalid: %s" % registry_path)
    return registry


def registry_summary(registry: dict[str, Any]) -> dict[str, Any]:
    roots: dict[str, int] = {}
    parameter_count = 0
    for device in registry.get("devices", []):
        root = str(device.get("root", ""))
        roots[root] = roots.get(root, 0) + 1
        parameter_count += len(device.get("controls", []))
    return {
        "schema_version": registry.get("schema_version"),
        "generated_at": registry.get("generated_at"),
        "live_version": registry.get("live_version"),
        "device_count": len(registry.get("devices", [])),
        "parameter_count": parameter_count,
        "roots": roots,
        "failure_count": len(registry.get("failures", [])),
    }


def iter_devices(registry: dict[str, Any], root: str | None = None) -> list[dict[str, Any]]:
    devices = list(registry.get("devices", []))
    if root:
        devices = [device for device in devices if device.get("root") == root]
    return devices


def find_device(registry: dict[str, Any], identifier: Any, root: str | None = None) -> dict[str, Any]:
    text = str(identifier or "").strip()
    if not text:
        raise ValueError("Stock device identifier is required")
    devices = iter_devices(registry, root)
    exact = [device for device in devices if _device_exact(device, text)]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError("Ambiguous stock device %r: %s" % (text, _device_names(exact)))
    needle = normalize(text)
    matches = [device for device in devices if needle in _device_search_text(device)]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError("Ambiguous stock device %r: %s" % (text, _device_names(matches)))
    raise ValueError("Unknown stock device %r" % text)


def find_control(device: dict[str, Any], identifier: Any) -> dict[str, Any]:
    controls = list(device.get("controls", []))
    if isinstance(identifier, int):
        for control in controls:
            if control.get("index") == identifier:
                return control
        raise ValueError("Parameter index out of range for %s: %s" % (device.get("name"), identifier))

    text = str(identifier or "").strip()
    if text.isdigit():
        return find_control(device, int(text))
    if not text:
        raise ValueError("Control identifier is required")

    exact = [control for control in controls if _control_exact(control, text)]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError("Ambiguous control %r on %s: %s" % (text, device.get("name"), _control_names(exact)))

    needle = normalize(text)
    matches = [control for control in controls if needle in _control_search_text(control)]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError("Ambiguous control %r on %s: %s" % (text, device.get("name"), _control_names(matches)))
    raise ValueError("Unknown control %r on stock device %s" % (text, device.get("name")))


def verify_registry(registry: dict[str, Any]) -> dict[str, Any]:
    devices = registry.get("devices", [])
    missing_controls = [
        {"path": device.get("path"), "name": device.get("name")}
        for device in devices
        if not device.get("controls")
    ]
    duplicate_devices = _duplicates(device.get("path") for device in devices)
    duplicate_controls = []
    for device in devices:
        slugs = [control.get("slug") for control in device.get("controls", [])]
        duplicates = _duplicates(slugs)
        if duplicates:
            duplicate_controls.append({"path": device.get("path"), "duplicates": duplicates})
    return {
        "summary": registry_summary(registry),
        "ok": not registry.get("failures") and not missing_controls and not duplicate_devices and not duplicate_controls,
        "failures": registry.get("failures", []),
        "missing_controls": missing_controls,
        "duplicate_devices": duplicate_devices,
        "duplicate_controls": duplicate_controls,
    }


def control_parameter_name(control: dict[str, Any]) -> str:
    parameter = control.get("parameter", {})
    return str(parameter.get("name") or control.get("name"))


def _device_exact(device: dict[str, Any], text: str) -> bool:
    candidates = [
        device.get("name"),
        device.get("path"),
        device.get("slug"),
        device.get("class_name"),
        device.get("loaded_name"),
    ]
    normalized = normalize(text)
    return any(str(candidate).strip().lower() == text.lower() or normalize(candidate) == normalized for candidate in candidates if candidate)


def _device_search_text(device: dict[str, Any]) -> str:
    fields = [
        device.get("name"),
        device.get("path"),
        device.get("slug"),
        device.get("root"),
        device.get("class_name"),
        device.get("loaded_name"),
    ]
    return normalize(" ".join(str(field) for field in fields if field))


def _device_names(devices: list[dict[str, Any]]) -> list[str]:
    return [str(device.get("path") or device.get("name")) for device in devices[:20]]


def _control_exact(control: dict[str, Any], text: str) -> bool:
    parameter = control.get("parameter", {})
    aliases = list(control.get("aliases", [])) + [
        control.get("name"),
        control.get("slug"),
        parameter.get("name"),
        parameter.get("original_name"),
        str(control.get("index")),
    ]
    normalized = normalize(text)
    return any(str(alias).strip().lower() == text.lower() or normalize(alias) == normalized for alias in aliases if alias is not None)


def _control_search_text(control: dict[str, Any]) -> str:
    parameter = control.get("parameter", {})
    fields = list(control.get("aliases", [])) + [
        control.get("name"),
        control.get("slug"),
        parameter.get("name"),
        parameter.get("original_name"),
        control.get("index"),
    ]
    return normalize(" ".join(str(field) for field in fields if field is not None))


def _control_names(controls: list[dict[str, Any]]) -> list[str]:
    return ["%s:%s" % (control.get("index"), control.get("name")) for control in controls[:20]]


def _duplicates(values: Any) -> list[Any]:
    seen = set()
    duplicates = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates
