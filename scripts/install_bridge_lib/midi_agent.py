"""CoreMIDI virtual-port LaunchAgent installation."""

import argparse
import os
import plistlib
import shutil
import subprocess
from pathlib import Path

from .config import MIDI_AGENT_LABEL

def install_midi_agent(args: argparse.Namespace) -> None:
    binary = Path(args.binary).expanduser().resolve()
    if not binary.exists():
        raise SystemExit(
            f"Binary not found: {binary}. "
            "Compile it with: swiftc -module-cache-path .build/ModuleCache "
            "scripts/codex_midi_ports.swift -o codex-midi-ports"
        )

    agent_dir = Path(args.agent_dir).expanduser()
    launch_agents = Path(args.launch_agents).expanduser()
    agent_dir.mkdir(parents=True, exist_ok=True)
    launch_agents.mkdir(parents=True, exist_ok=True)

    target = agent_dir / "codex-midi-ports"
    shutil.copy2(binary, target)
    target.chmod(0o755)

    plist_path = launch_agents / f"{MIDI_AGENT_LABEL}.plist"
    plist = {
        "Label": MIDI_AGENT_LABEL,
        "ProgramArguments": [str(target), args.source_name, args.destination_name],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(agent_dir / "midi-ports.out.log"),
        "StandardErrorPath": str(agent_dir / "midi-ports.err.log"),
        "WorkingDirectory": str(agent_dir),
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=False)

    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(plist_path)], check=False, capture_output=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(plist_path)], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{MIDI_AGENT_LABEL}"], check=False)
    print(f"Installed and started {MIDI_AGENT_LABEL}")
    print(f"Binary: {target}")
    print(f"Plist: {plist_path}")


def uninstall_midi_agent(args: argparse.Namespace) -> None:
    plist_path = Path(args.launch_agents).expanduser() / f"{MIDI_AGENT_LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(plist_path)], check=False, capture_output=True)
    if plist_path.exists():
        plist_path.unlink()
    print(f"Uninstalled {MIDI_AGENT_LABEL}")
