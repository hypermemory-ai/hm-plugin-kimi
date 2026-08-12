#!/usr/bin/env python3
"""Codex lifecycle bridge for mandatory HyperMemory behavior.

The hook injects recall instructions and turns end-of-turn persistence into a
bounded sub-agent job. It does not call the MCP server or read conversation
content from the transcript.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _read_input() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid hook JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise TypeError("hook input must be a JSON object")
    return value


def _plugin_root() -> Path:
    configured = os.environ.get("PLUGIN_ROOT")
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[1]


def _plugin_data() -> Path:
    configured = os.environ.get("PLUGIN_DATA")
    path = (
        Path(configured).resolve()
        if configured
        else Path(tempfile.gettempdir()) / "hypermemory-plugin-data"
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_id(value: object, fallback: str) -> str:
    text = str(value or fallback)
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in text)[:160]


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _context(event: str, text: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": text,
                }
            }
        )
    )


def session_start(payload: dict[str, Any]) -> int:
    session_id = _safe_id(payload.get("session_id"), "unknown-session")
    state_file = _plugin_data() / "token-state.json"
    baseline = {
        "version": 1,
        "session_id": session_id,
        "transcript_path": payload.get("transcript_path"),
        "state_file": str(state_file),
    }
    baseline_path = _plugin_data() / "jobs" / f"baseline-{session_id}.json"
    _atomic_json(baseline_path, baseline)

    # Baseline synchronously so installation never uploads historical usage.
    listener = _plugin_root() / "scripts" / "codex_token_listener.py"
    if listener.exists():
        import subprocess

        subprocess.run(
            [sys.executable, str(listener), "baseline", "--job", str(baseline_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

    _context(
        "SessionStart",
        "HyperMemory is mandatory for this session. Before the first response, "
        "call hm_get_overview and hm_recall. On every turn recall on the main "
        "agent, then delegate store/update/forget, one timeline entry, and one "
        "token report to a memory-writer sub-agent before returning the final response.",
    )
    return 0


def user_prompt(_: dict[str, Any]) -> int:
    _context(
        "UserPromptSubmit",
        "For this turn, silently call HyperMemory hm_recall before substantive "
        "work. Keep graph writes, hm_timeline_write, and hm_tokens off the main "
        "agent: a memory-writer sub-agent must perform them during finalization.",
    )
    return 0


def stop(payload: dict[str, Any]) -> int:
    if bool(payload.get("stop_hook_active")):
        print(json.dumps({"continue": True}))
        return 0

    session_id = _safe_id(payload.get("session_id"), "unknown-session")
    turn_id = _safe_id(payload.get("turn_id"), "unknown-turn")
    data_dir = _plugin_data()
    job_path = data_dir / "jobs" / f"turn-{session_id}-{turn_id}.json"
    job = {
        "version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "session_id": str(payload.get("session_id") or session_id),
        "turn_id": str(payload.get("turn_id") or turn_id),
        "transcript_path": payload.get("transcript_path"),
        "model": str(payload.get("model") or "unknown"),
        "state_file": str(data_dir / "token-state.json"),
    }
    _atomic_json(job_path, job)

    listener = _plugin_root() / "scripts" / "codex_token_listener.py"
    reason = (
        "Mandatory HyperMemory finalization before showing the response. Spawn "
        "exactly one memory-writer sub-agent and wait for it. Do not perform "
        "graph writes or token reporting on the main agent. Give the sub-agent "
        "a concise summary of this turn. It must recall first; store or update "
        "durable knowledge with specific relationships; write exactly one "
        "hm_timeline_write entry; run the local token listener; call hm_tokens "
        "exactly once; and acknowledge the listener only after hm_tokens "
        "succeeds. Pass these exact local paths:\n"
        f"listener={listener}\njob={job_path}\n"
        "Listener sequence: python3 <listener> inspect --job <job>; call MCP "
        "hm_tokens with hm_tokens_payload from stdout; then python3 <listener> "
        "ack --job <job>. If exact inspection is unavailable, the sub-agent "
        "must send one honest self_estimated report instead."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=("session-start", "user-prompt", "stop"))
    args = parser.parse_args()
    try:
        payload = _read_input()
        if args.event == "session-start":
            return session_start(payload)
        if args.event == "user-prompt":
            return user_prompt(payload)
        return stop(payload)
    except (OSError, RuntimeError, TypeError) as exc:
        print(f"HyperMemory hook error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
