"""Output formatting helpers."""

import json
from typing import Any

def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))
