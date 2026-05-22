"""macOS automation and Live dialog helpers for restart activation."""

import argparse
import subprocess
import time

from .bridge_core import bridge_request

def request_live_quit(args: argparse.Namespace) -> None:
    try:
        quit_result = subprocess.run(
            ["osascript", "-e", f'tell application "{args.app_name}" to quit'],
            check=False,
            timeout=args.quit_request_timeout,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        print("Timed out while requesting normal quit; checking Live dialogs.")
        return
    if quit_result.returncode != 0:
        detail = quit_result.stderr.strip() or quit_result.stdout.strip() or "unknown osascript error"
        print(f"Normal quit request returned an error; checking Live dialogs: {detail}")


def discard_unsaved_dialog(args: argparse.Namespace) -> None:
    if args.unsaved_dialog_button is None:
        message = current_dialog_message(args)
        count = current_dialog_button_count(args)
        raise SystemExit(
            "Unsaved discard requested, but --unsaved-dialog-button was not provided. "
            "Live dialog button count: %s. Message: %r" % (count, message)
        )
    if not wait_for_live_dialog(args, args.dialog_timeout):
        print("No Live dialog appeared after quit request; continuing to wait for normal quit.")
        return
    count = current_dialog_button_count(args)
    index = int(args.unsaved_dialog_button)
    if index < 0 or index >= count:
        raise SystemExit("Dialog button index %s is outside the current button count %s." % (index, count))
    bridge_request(
        {"command": "lom_call", "path": "application.press_current_dialog_button", "args": [index]},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    )


def wait_for_live_dialog(args: argparse.Namespace, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if current_dialog_button_count(args) > 0:
            return True
        time.sleep(0.25)
    return False


def current_dialog_message(args: argparse.Namespace) -> str:
    return bridge_request(
        {"command": "lom_get", "path": "application.current_dialog_message"},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    )


def current_dialog_button_count(args: argparse.Namespace) -> int:
    return int(bridge_request(
        {"command": "lom_get", "path": "application.current_dialog_button_count"},
        args.bridge_host,
        args.bridge_port,
        args.bridge_timeout,
    ))


def run_applescript(lines: list[str], timeout: float) -> None:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("osascript timed out")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown osascript failure"
        raise RuntimeError(detail)
