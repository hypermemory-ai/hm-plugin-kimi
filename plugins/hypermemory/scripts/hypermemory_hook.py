#!/usr/bin/env python3
"""Silent Codex lifecycle bridge for mandatory HyperMemory behavior.

The hook classifies lightweight prompts, prepares token-listener jobs before
model work, and injects concise hidden developer context. It never blocks Stop,
creates continuation prompts, or reads conversation content from the transcript.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LIGHTWEIGHT_MAX_CHARS = 80
LIGHTWEIGHT_PHRASES = frozenset({"got it", "hello", "hey", "hi", "howdy", "ok", "okay", "thank you", "thanks"})


def _prompt_text(payload):
    prompt = payload.get("prompt")
    return prompt if isinstance(prompt, str) else ""


def _normalize_prompt(text):
    text = text.casefold().replace("’", "'")
    return " ".join(re.sub(r"[^\w\s']+", " ", text).split())


def _is_lightweight_prompt(text):
    return bool(text) and len(text) <= LIGHTWEIGHT_MAX_CHARS and _normalize_prompt(text) in LIGHTWEIGHT_PHRASES


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


def _agent_task_name(turn_id: object) -> str:
    """Return a unique collaboration task name accepted by Codex."""
    safe_turn = _safe_id(turn_id, "unknown-turn").replace("-", "_")
    return f"memory_writer_{safe_turn}"[:160]


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


def _fail_open(event: str, exc: Exception) -> int:
    """Keep the user's turn available when local lifecycle preparation fails."""
    print(f"HyperMemory hook degraded: {type(exc).__name__}: {exc}", file=sys.stderr)
    hook_event = "SessionStart" if event == "session-start" else "UserPromptSubmit"
    _context(
        hook_event,
        "HyperMemory lifecycle preparation was unavailable for this event. "
        "Continue the user's request without blocking the turn. Apply the "
        "HyperMemory skill directly if it is available, and do not claim that "
        "local lifecycle or token preparation succeeded.",
    )
    return 0


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
        "HyperMemory is active. Follow the HyperMemory skill and each turn's "
        "prompt classification. Do not recall solely because the session started. "
        "Memory-writers are fire-and-forget: dispatch once, never wait or poll.",
    )
    return 0


def _turn_job(payload: dict[str, Any]) -> tuple[Path, Path]:
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
    return _plugin_root() / "scripts" / "codex_token_listener.py", job_path


def user_prompt(payload: dict[str, Any]) -> int:
    listener, job_path = _turn_job(payload)
    writer_task = _agent_task_name(payload.get("turn_id"))
    lightweight = _is_lightweight_prompt(_prompt_text(payload))
    recall_instruction = (
        "mode=lightweight; skip hm_get_overview and hm_recall on the main agent."
        if lightweight
        else "mode=substantive; call hm_recall before substantive work and call "
        "hm_get_overview first if it has not run in this conversation."
    )
    _context(
        "UserPromptSubmit",
        f"HyperMemory turn: {recall_instruction}\n"
        "Apply the HyperMemory skill. Keep graph writes and telemetry "
        "off the main agent. "
        "Before the final response, spawn exactly one fresh memory-writer with "
        f"task_name={writer_task}, fork_turns=\"none\", a bounded turn summary, "
        "and explicit use of the $memory-writer skill. Pass:\n"
        f"listener={listener}\njob={job_path}\n"
        "Fire-and-forget: after spawn succeeds, do not wait, poll, inspect, read, "
        "message, or otherwise synchronize with the writer; return the final "
        "response immediately.",
    )
    return 0


def stop(payload: dict[str, Any]) -> int:
    # Kept as a backwards-compatible no-op for already-running sessions whose
    # hook registry still references the old Stop command. Never emit a block
    # reason: Codex turns one into a visible synthetic user continuation.
    del payload
    print(json.dumps({"continue": True}))
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
    except Exception as exc:
        return _fail_open(args.event, exc)


if __name__ == "__main__":
    raise SystemExit(main())
