#!/usr/bin/env python3
"""Silent Kimi Code lifecycle bridge for mandatory HyperMemory behavior.

The hook classifies lightweight prompts and injects concise context before
model work. It never blocks Stop, creates continuation prompts, or reads
conversation content beyond the submitted prompt text. Failures fail open so a
local hook error can never block the user's turn.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

LIGHTWEIGHT_MAX_CHARS = 80
LIGHTWEIGHT_PHRASES = frozenset({"got it", "hello", "hey", "hi", "howdy", "ok", "okay", "thank you", "thanks"})


def _prompt_text(payload: dict[str, Any]) -> str:
    prompt = payload.get("prompt")
    return prompt if isinstance(prompt, str) else ""


def _normalize_prompt(text: str) -> str:
    text = text.casefold().replace("’", "'")
    return " ".join(re.sub(r"[^\w\s']+", " ", text).split())


def _is_lightweight_prompt(text: str) -> bool:
    return bool(text) and len(text) <= LIGHTWEIGHT_MAX_CHARS and _normalize_prompt(text) in LIGHTWEIGHT_PHRASES


def _read_input() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid hook JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise TypeError("hook input must be a JSON object")
    return value


def _writer_task_name(payload: dict[str, Any]) -> str:
    """Return a unique fire-and-forget task name for this turn."""
    turn = str(payload.get("turn_id") or payload.get("prompt_id") or "")
    if not turn:
        turn = f"{payload.get('session_id') or 'session'}-{os.getpid()}"
    safe = "".join(char if char.isalnum() or char in "-_" else "_" for char in turn)[:120]
    return f"memory_writer_{safe}"


def _context(text: str) -> None:
    print(text)


def _fail_open(exc: Exception) -> int:
    """Keep the user's turn available when local lifecycle preparation fails."""
    print(f"HyperMemory hook degraded: {type(exc).__name__}: {exc}", file=sys.stderr)
    _context(
        "HyperMemory lifecycle preparation was unavailable for this event. "
        "Continue the user's request without blocking the turn. Apply the "
        "HyperMemory skill directly if it is available, and do not claim that "
        "local lifecycle preparation succeeded."
    )
    return 0


def session_start(payload: dict[str, Any]) -> int:
    del payload
    _context(
        "HyperMemory is active. Follow the HyperMemory skill and each turn's "
        "prompt classification. Do not recall solely because the session started. "
        "Memory-writers are fire-and-forget: dispatch once, never wait or poll."
    )
    return 0


def user_prompt(payload: dict[str, Any]) -> int:
    writer_task = _writer_task_name(payload)
    lightweight = _is_lightweight_prompt(_prompt_text(payload))
    recall_instruction = (
        "mode=lightweight; skip hm_get_overview and hm_recall on the main agent."
        if lightweight
        else "mode=substantive; call hm_recall before substantive work and call "
        "hm_get_overview first if it has not run in this conversation."
    )
    _context(
        f"HyperMemory turn: {recall_instruction}\n"
        "Apply the HyperMemory skill. Keep graph writes and telemetry "
        "off the main agent. "
        "Before the final response, dispatch exactly one fresh memory-writer "
        f"sub-agent (task name {writer_task}) with run_in_background=true and a "
        "bounded turn contract; the sub-agent loads the memory-writer skill as "
        "its sole operating contract.\n"
        "Fire-and-forget: after dispatch succeeds, do not wait, poll, inspect, "
        "read, message, or otherwise synchronize with the writer; return the "
        "final response immediately."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=("session-start", "user-prompt"))
    args = parser.parse_args()
    try:
        payload = _read_input()
        if args.event == "session-start":
            return session_start(payload)
        return user_prompt(payload)
    except Exception as exc:
        return _fail_open(exc)


if __name__ == "__main__":
    raise SystemExit(main())
