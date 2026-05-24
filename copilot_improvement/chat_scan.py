"""Historical chat evidence collection from text exports and Codex sessions."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .chat_workflow_patterns import chat_workflow_patterns


CHAT_SUFFIXES = {".md", ".txt", ".json", ".jsonl"}
CHAT_TERMS = (
    "drop",
    "bass",
    "sub",
    "kick",
    "snare",
    "hats",
    "sidechain",
    "automation",
    "fakeout",
    "transition",
    "movement",
    "humanize",
    "groove",
    "resample",
    "riser",
    "rise",
    "swell",
    "inhale",
    "build",
    "buildup",
    "uplifter",
    "mix",
    "master",
    "loudness",
    "limiter",
    "synth",
    "drum",
    "drum rack",
    "loop",
    "stutter",
    "glitch",
    "glitchy",
    "cut out",
    "zap",
    "perc",
    "tipper",
    "g jones",
    "chris lake",
)
REFINEMENT_RULES = (
    ("correction-instead-of", ("instead of",)),
    ("correction-actually", ("actually",)),
    ("negative-revision-not-quite", ("not quite", "not right")),
    ("increase-intensity-more", ("more",)),
    ("reduce-intensity-less", ("less",)),
    ("pad-mapping-correction", ("one pad", "own pad", "same pad", "different pads")),
)
CODEX_THREAD_HINTS = (
    "ableton",
    "producer",
    "beat",
    "drum",
    "rack",
    "bass",
    "synth",
    "glitch",
    "loop",
    "mix",
)
ABLETONCTL_COMMAND_RE = re.compile(r"(?:\bpython3\s+)?(?:\S*/)?abletonctl(?:\.py)?\s+([a-z0-9-]+)")


def scan_chats(roots: tuple[Path, ...], limit: int = 50) -> dict[str, Any]:
    existing = _existing_roots(roots)
    files = _chat_files(existing, limit)
    codex_files = _codex_session_files(roots, limit)
    seen = {str(path) for path in files}
    files.extend(path for path in codex_files if str(path) not in seen)
    files = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    return {
        "roots": [str(root) for root in roots],
        "existing_roots": [str(root) for root in existing],
        "files_seen": len(files),
        "chats": [_chat_counts(path, roots) for path in files],
    }


def _existing_roots(roots: tuple[Path, ...]) -> list[Path]:
    return [root for root in roots if root.exists()]


def _chat_files(roots: list[Path], limit: int) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        paths.extend(path for path in root.rglob("*") if _is_chat_file(path))
    paths = [path for path in paths if ".git" not in path.parts]
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def _is_chat_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in CHAT_SUFFIXES


def _chat_counts(path: Path, roots: tuple[Path, ...]) -> dict[str, Any]:
    if _looks_like_codex_session(path):
        text, metadata = _codex_session_text(path)
        user_text = str(metadata.pop("_user_text", ""))
        if not _is_relevant_codex_session(metadata, text, roots):
            text = ""
            user_text = ""
    else:
        text = _read_text(path)
        metadata = {}
        user_text = text
    lowered = text.lower()
    terms = {term: _term_count(lowered, term) for term in CHAT_TERMS if _term_count(lowered, term)}
    commands = Counter(ABLETONCTL_COMMAND_RE.findall(text))
    refinements = _refinement_counts(user_text or text)
    workflows = chat_workflow_patterns(terms)
    corrections = sum(refinements.values())
    return {
        "path": str(path),
        "kind": "codex-session" if metadata else path.suffix.lower(),
        "thread_id": metadata.get("id"),
        "thread_name": metadata.get("thread_name"),
        "cwd": metadata.get("cwd"),
        "terms": terms,
        "commands": dict(commands.most_common(20)),
        "correction_markers": corrections,
        "refinements": dict(refinements.most_common(20)),
        "workflows": workflows,
    }


def _read_text(path: Path, max_chars: int = 500_000) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def _codex_session_files(roots: tuple[Path, ...], limit: int) -> list[Path]:
    homes = _candidate_homes(roots)
    candidates: list[Path] = []
    for home in homes:
        codex = home / ".codex"
        sessions = codex / "sessions"
        if not sessions.exists():
            continue
        index_ids = _relevant_session_ids(codex / "session_index.jsonl")
        files = [path for path in sessions.rglob("*.jsonl") if path.is_file()]
        recent = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[: max(limit * 8, 80)]
        for path in recent:
            text, metadata = _codex_session_text(path, max_messages=12)
            indexed = any(session_id in path.name for session_id in index_ids)
            if _is_relevant_codex_session(metadata, text, roots, indexed):
                candidates.append(path)
    return sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def _candidate_homes(roots: tuple[Path, ...]) -> list[Path]:
    homes: set[Path] = set()
    for root in roots:
        expanded = root.expanduser()
        parts = expanded.parts
        if ".codex" in parts:
            homes.add(Path(*parts[: parts.index(".codex")]))
        if "Documents" in parts:
            homes.add(Path(*parts[: parts.index("Documents")]))
    return sorted(homes)


def _relevant_session_ids(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    ids: set[str] = set()
    for line in index_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = str(item.get("thread_name", ""))
        if _relevance_score(name) > 0:
            ids.add(str(item.get("id")))
    return ids


def _looks_like_codex_session(path: Path) -> bool:
    return path.suffix.lower() == ".jsonl" and "rollout-" in path.name


def _codex_session_text(path: Path, max_messages: int = 120) -> tuple[str, dict[str, Any]]:
    messages: list[str] = []
    user_messages: list[str] = []
    metadata: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "session_meta":
            payload = item.get("payload", {})
            metadata = {
                "id": payload.get("id"),
                "cwd": payload.get("cwd"),
                "thread_name": payload.get("thread_name"),
            }
            continue
        payload = item.get("payload", {})
        if item.get("type") != "response_item" or payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = _message_text(payload.get("content", []))
        if text:
            messages.append(text)
            if role == "user":
                user_messages.append(text)
        if len(messages) >= max_messages:
            break
    metadata["_user_text"] = "\n".join(user_messages)
    return "\n".join(messages), metadata


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") if item.get("type") in {"input_text", "output_text", "text"} else None
        if text:
            parts.append(str(text))
    return "\n".join(parts)


def _is_relevant_codex_session(metadata: dict[str, Any], text: str, roots: tuple[Path, ...], indexed: bool = False) -> bool:
    cwd = str(metadata.get("cwd") or "")
    if cwd and any(cwd.startswith(str(root.expanduser())) for root in roots):
        return True
    if not any(root.expanduser().name == ".codex" for root in roots):
        return False
    name = str(metadata.get("thread_name") or "")
    return indexed or _relevance_score(name) > 0 or _relevance_score(text) >= 2


def _relevance_score(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in CODEX_THREAD_HINTS if _term_count(lowered, term))


def _term_count(lowered_text: str, term: str) -> int:
    pattern = r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(term.lower())
    return len(re.findall(pattern, lowered_text))


def _refinement_counts(text: str) -> Counter[str]:
    lowered = text.lower()
    refinements: Counter[str] = Counter()
    for label, terms in REFINEMENT_RULES:
        count = sum(_term_count(lowered, term) for term in terms)
        if count:
            refinements[label] = count
    return refinements
