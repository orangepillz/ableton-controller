"""Configuration for recurring copilot improvement runs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


STATE_DIR_ENV = "ABLETON_COPILOT_STATE_DIR"
PROJECT_ROOTS_ENV = "ABLETON_PROJECT_ROOTS"
CHAT_ROOTS_ENV = "ABLETON_CHAT_ROOTS"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _split_roots(value: str | None) -> list[Path]:
    if not value:
        return []
    return [Path(item).expanduser() for item in value.split(os.pathsep) if item.strip()]


def default_project_roots(home: Path) -> list[Path]:
    return [
        home / "Music" / "Ableton",
        home / "Documents" / "codex_ableton",
    ]


def default_chat_roots(home: Path) -> list[Path]:
    return [home / "Documents" / "ableton-chats"]


@dataclass(frozen=True)
class ImprovementConfig:
    repo_root: Path
    state_dir: Path
    project_roots: tuple[Path, ...]
    chat_roots: tuple[Path, ...]


def load_config() -> ImprovementConfig:
    root = repo_root()
    home = Path.home()
    state_dir = Path(os.environ.get(STATE_DIR_ENV, root / ".ableton-copilot")).expanduser()
    project_roots = _split_roots(os.environ.get(PROJECT_ROOTS_ENV)) or default_project_roots(home)
    chat_roots = _split_roots(os.environ.get(CHAT_ROOTS_ENV)) or default_chat_roots(home)
    return ImprovementConfig(
        repo_root=root,
        state_dir=state_dir,
        project_roots=tuple(project_roots),
        chat_roots=tuple(chat_roots),
    )

