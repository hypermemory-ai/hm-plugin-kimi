#!/usr/bin/env python3
"""Bridge Kimi Code lifecycle events to the installed HyperColab CLI.

The plugin keeps the MCP shim and hook implementation in one CLI package. This
launcher makes hook behavior graceful when the CLI has not been installed yet:
session start explains the missing prerequisite, while write operations remain
unblocked rather than making an unconfigured repository unusable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _payload(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw or b"{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _binary() -> str | None:
    configured = os.environ.get("HYPERCOLAB_BIN")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return str(candidate)
    return shutil.which("hypercolab")


def _missing_cli_context(payload: dict[str, Any]) -> None:
    event = str(payload.get("hook_event_name") or "")
    if event != "SessionStart":
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        "HyperColab is installed, but its local CLI/MCP shim is missing. "
                        "Install the bundled package from this marketplace repository, run "
                        "`hypercolab login`, and start a new task before relying on project "
                        "claims or timeline coordination."
                    ),
                }
            }
        )
    )


def main() -> int:
    raw = sys.stdin.buffer.read()
    binary = _binary()
    if binary is None:
        _missing_cli_context(_payload(raw))
        print("HyperColab CLI not found; lifecycle coordination is inactive.", file=sys.stderr)
        return 0
    completed = subprocess.run([binary, "hook"], input=raw, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
