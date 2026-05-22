"""Paths and constants for Ableton bridge installation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_NAME = "Codex_AI"
SOURCE = PROJECT_ROOT / "remote_scripts" / SCRIPT_NAME
DEFAULT_USER_LIBRARY = Path.home() / "Music" / "Ableton" / "User Library"
DEFAULT_PREFS_ROOT = Path.home() / "Library" / "Preferences" / "Ableton"
DEFAULT_AGENT_DIR = Path.home() / "Library" / "Application Support" / "CodexAbleton"
DEFAULT_LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
MIDI_AGENT_LABEL = "com.codex.ableton-midi-ports"
RECOVERY_TRIGGER_NAMES = ("CrashRecoveryInfo.cfg", "BaseFiles", "Undo")
