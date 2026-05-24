"""Long-term memory storage for copilot improvement evidence."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    lowered = value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return cleaned or "item"


def default_memory() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "runs": [],
        "signals": [],
        "workflow_macros": [],
        "intent_mappings": [],
        "backlog": [],
    }


def load_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_memory()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("runs", [])
    data.setdefault("signals", [])
    data.setdefault("workflow_macros", [])
    data.setdefault("intent_mappings", [])
    data.setdefault("backlog", [])
    return data


def save_memory(memory: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    memory["updated_at"] = utc_now()
    path.write_text(json.dumps(memory, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup_memory(memory_path: Path, backup_dir: Path, run_id: str) -> Path | None:
    if not memory_path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"memory-{run_id}.json"
    shutil.copy2(memory_path, backup_path)
    return backup_path


def restore_memory(backup_path: Path, memory_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(f"backup not found: {backup_path}")
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, memory_path)


def confidence_after(current: float, evidence_weight: float) -> float:
    return round(max(0.05, min(0.95, current + evidence_weight)), 3)


def _find_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    return next((item for item in items if item.get("id") == item_id), None)


def upsert_signal(
    memory: dict[str, Any],
    *,
    category: str,
    label: str,
    evidence: str,
    source: str,
    confidence_delta: float = 0.04,
) -> dict[str, Any]:
    item_id = f"{category}.{slugify(label)}"
    signals = memory.setdefault("signals", [])
    signal = _find_by_id(signals, item_id)
    if signal is None:
        signal = {
            "id": item_id,
            "category": category,
            "label": label,
            "confidence": 0.2,
            "evidence_count": 0,
            "evidence": [],
            "first_seen": utc_now(),
            "last_seen": utc_now(),
        }
        signals.append(signal)

    evidence_items = signal.setdefault("evidence", [])
    is_duplicate = any(item.get("source") == source and item.get("detail") == evidence for item in evidence_items)
    if not is_duplicate:
        signal["confidence"] = confidence_after(float(signal.get("confidence", 0.2)), confidence_delta)
        signal["evidence_count"] = int(signal.get("evidence_count", 0)) + 1
        entry = {"source": source, "detail": evidence, "seen_at": utc_now()}
        evidence_items.append(entry)
    del evidence_items[:-8]
    signal["last_seen"] = utc_now()
    return {**signal, "changed": not is_duplicate}


def upsert_backlog(
    memory: dict[str, Any],
    *,
    item_id: str,
    title: str,
    why: str,
    expected_impact: str,
    priority: int,
    evidence: str,
) -> dict[str, Any]:
    backlog = memory.setdefault("backlog", [])
    item = _find_by_id(backlog, item_id)
    created = item is None
    if item is None:
        item = {
            "id": item_id,
            "title": title,
            "why": why,
            "expected_impact": expected_impact,
            "priority": priority,
            "status": "open",
            "evidence": [],
            "created_at": utc_now(),
            "last_seen": utc_now(),
        }
        backlog.append(item)
    else:
        changed_fields = (
            item.get("title") != title
            or item.get("why") != why
            or item.get("expected_impact") != expected_impact
            or item.get("priority") != priority
        )
        item.update({"title": title, "why": why, "expected_impact": expected_impact, "priority": priority})
        item["last_seen"] = utc_now()
    evidence_items = item.setdefault("evidence", [])
    new_evidence = evidence not in evidence_items
    if evidence not in evidence_items:
        evidence_items.append(evidence)
    del evidence_items[:-8]
    return {**item, "changed": created or new_evidence or (not created and changed_fields)}


def set_backlog_status(memory: dict[str, Any], item_id: str, status: str, evidence: str) -> dict[str, Any] | None:
    item = _find_by_id(memory.setdefault("backlog", []), item_id)
    if item is None:
        return None
    changed = item.get("status") != status
    item["status"] = status
    item["last_seen"] = utc_now()
    evidence_items = item.setdefault("evidence", [])
    if evidence not in evidence_items:
        evidence_items.append(evidence)
        changed = True
    del evidence_items[:-8]
    return {**item, "changed": changed}


def record_run(memory: dict[str, Any], run: dict[str, Any]) -> None:
    runs = memory.setdefault("runs", [])
    runs.append(run)
    del runs[:-50]
