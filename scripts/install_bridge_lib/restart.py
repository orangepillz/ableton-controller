"""Restart-and-activate workflow orchestration."""

import argparse
import subprocess

from .automation import discard_unsaved_dialog, request_live_quit
from .bridge_api import cleanup_unsaved_project, live_set_file_path, save_live_set
from .filesystem import activate, install
from .recovery import force_discard_unsaved_project, wait_for_live_to_quit

def restart_activate(args: argparse.Namespace) -> None:
    install(args)
    live_set_path = live_set_file_path(args)
    if live_set_path:
        print(f"Live set has a saved path; saving before quit: {live_set_path}")
        try:
            save_live_set(args)
        except RuntimeError as error:
            raise SystemExit(f"Could not save the existing Live set, so Live was not quit: {error}")
    elif live_set_path == "":
        print("Live set has no saved path.")
        cleanup_unsaved_project(args)
        if args.unsaved_action == "stop":
            raise SystemExit(
                "Refusing to restart an unsaved Live set. Save the set first, "
                "or rerun with --unsaved-action force-discard-recovery to force quit "
                "and quarantine Live's recovery trigger files."
            )
        if args.unsaved_action == "force-discard-recovery":
            force_discard_unsaved_project(args)
            activate(args)
            print(f"Reopening {args.app_name}...")
            subprocess.run(["open", "-a", args.app_name], check=True)
            print("Live reopened. Wait for startup, then run: python3 abletonctl.py ping")
            return
    else:
        raise SystemExit("Could not determine whether the Live set has a saved path, so Live was not quit.")

    print(f"Requesting quit for {args.app_name}...")
    request_live_quit(args)
    if live_set_path == "" and args.unsaved_action == "discard":
        discard_unsaved_dialog(args)
    if not wait_for_live_to_quit(args.process_pattern, args.quit_timeout):
        raise SystemExit("Live did not quit normally; refusing to force quit because it would trigger recovery on next launch.")
    activate(args)
    print(f"Reopening {args.app_name}...")
    subprocess.run(["open", "-a", args.app_name], check=True)
    print("Live reopened. Wait for startup, then run: python3 abletonctl.py ping")
