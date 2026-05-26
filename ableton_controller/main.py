"""abletonctl application entrypoint."""

from .config import LOCAL_COMMANDS
from .local_commands import run_local_command
from .output import print_json
from .parser import build_parser
from .payloads import command_payload
from .transport import send


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in LOCAL_COMMANDS:
            print_json(run_local_command(args))
            return 0
        payload = command_payload(args)
        request_timeout = getattr(args, "request_timeout", None)
        timeout = max(args.timeout, float(request_timeout) + 5.0) if request_timeout is not None else args.timeout
        response = send(payload, args.host, args.port, timeout)
        print_json(response.get("result", response))
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc))
    return 0
