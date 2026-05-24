"""Derived target-role aliases from personalized project memory."""

from __future__ import annotations

import re
from typing import Any


ROLE_RULES = (
    ("kick", ("bd", "kick", "kicks")),
    ("snare", ("sd", "snare", "sanre")),
    ("hats", ("ch", "hat", "hats", "hh", "closed hat", "open hat")),
    ("sidechain", ("sc", "sc trigger", "sc in", "sidechain")),
    ("drums", ("drums", "tr8s", "maschine", "codex drums")),
    ("sub-bass", ("sub", "808", "basic organ bass")),
    ("reverb-return", ("a reverb", "reverb")),
    ("delay-return", ("b delay", "delay")),
)


def target_aliases(memory: dict[str, Any]) -> list[dict[str, Any]]:
    name_signals = [signal for signal in memory.get("signals", []) if signal.get("category") == "project.name"]
    aliases = []
    for role, terms in ROLE_RULES:
        matches = [signal for signal in name_signals if _matches_role(str(signal.get("label", "")), terms)]
        if not matches:
            continue
        ranked = sorted(matches, key=lambda signal: (-float(signal.get("confidence", 0)), -int(signal.get("evidence_count", 0)), str(signal.get("label", ""))))[:5]
        names = [str(signal.get("label", "")) for signal in ranked]
        aliases.append(
            {
                "role": role,
                "aliases": names,
                "label": f"{role}: {', '.join(names)}",
                "confidence": _alias_confidence(ranked),
                "evidence_signal_ids": [str(signal.get("id", "")) for signal in ranked],
            }
        )
    return sorted(aliases, key=lambda item: (-float(item["confidence"]), item["role"]))


def target_alias_hint(alias: dict[str, Any], matched: list[str] | None = None) -> dict[str, Any]:
    names = ", ".join(alias.get("aliases", [])[:4])
    role = str(alias.get("role", "target"))
    return {
        "id": f"target-alias.{role}",
        "label": alias.get("label", ""),
        "role": role,
        "aliases": list(alias.get("aliases", [])[:5]),
        "matched_terms": matched or [],
        "confidence": alias.get("confidence", 0),
        "evidence_count": len(alias.get("evidence_signal_ids", [])),
        "hint": f"Personal target alias for {role}: prefer {names} when current-set inspection agrees.",
    }


def target_alias_probe_command(aliases: list[dict[str, Any]], *, depth: int = 3) -> str | None:
    tracks: list[str] = []
    seen = set()
    for alias in aliases:
        for name in alias.get("aliases", [])[:1]:
            track = str(name).strip()
            if track and track not in seen:
                seen.add(track)
                tracks.append(track)
    if not tracks:
        return None
    flags = " ".join(f'--track "{track}"' for track in tracks[:3])
    return f"session-snapshot {flags} --device-tree-depth {depth}"


def _matches_role(label: str, terms: tuple[str, ...]) -> bool:
    normalized = _normalize(label)
    compact = normalized.replace(" ", "")
    for term in terms:
        normalized_term = _normalize(term)
        if len(normalized_term) <= 2:
            if normalized == normalized_term:
                return True
            continue
        if normalized_term in normalized or normalized_term.replace(" ", "") in compact:
            return True
    return False


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _alias_confidence(signals: list[dict[str, Any]]) -> float:
    if not signals:
        return 0.0
    best = max(float(signal.get("confidence", 0.2)) for signal in signals)
    evidence_bonus = min(0.12, 0.02 * (len(signals) - 1))
    return round(min(0.95, best + evidence_bonus), 3)
