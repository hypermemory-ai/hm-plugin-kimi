"""Coding-client guard hook and non-blocking Git timeline hooks."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from .client import HypercolabClient, HypercolabError
from .config import QUEUE_FILE, operations_have_live_cached_leases
from .git import GitContext, changed_paths, current_commit, discover_git_context

MANAGED_START = "# >>> hypercolab managed hook >>>"
MANAGED_END = "# <<< hypercolab managed hook <<<"
GIT_HOOKS = ("post-commit", "post-checkout", "post-merge", "post-rewrite", "pre-push")
READ_ONLY_COMMANDS = re.compile(
    r"^\s*(git\s+(status|diff|log|show|branch|remote|rev-parse)|"
    r"(rg|grep|find|ls|pwd|sed\s+-n|head|tail|cat|wc|which|type)\b)"
)
WRITE_COMMANDS = re.compile(
    r"\b(rm|mv|cp|mkdir|touch|install|truncate|tee|sed\s+-i|git\s+(add|commit|merge|rebase))\b|>>?|\|\s*tee\b"
)
GIT_PUSH = re.compile(r"(?:^|[;&|]\s*)git\s+(?:-[^\s]+\s+)*push\b")


def _hook_block(reason: str, event_name: str = "PreToolUse") -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _extract_file_paths(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "path", "target_file"):
        if tool_input.get(key):
            return [{"path": tool_input[key], "operation": "modify"}]
    if tool == "apply_patch":
        command = str(tool_input.get("command") or tool_input.get("patch") or "")
        paths = re.findall(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", command, re.MULTILINE)
        return [{"path": path, "operation": "modify"} for path in paths]
    return []


def _command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    return str(tool_input.get("command") or tool_input.get("cmd") or payload.get("command") or "")


def evaluate_client_hook(payload: dict[str, Any]) -> dict[str, Any]:
    """Return cross-client hook JSON. Empty dict means allow."""

    event = payload.get("hook_event_name", "")
    if event in {"SessionStart", "sessionStart"}:
        try:
            with HypercolabClient() as client:
                brief = client.sync(client_name="plugin")
            return {
                "hookSpecificOutput": {
                    "hookEventName": payload.get("hook_event_name", "SessionStart"),
                    "additionalContext": "Hypercolab coordination brief:\n" + json.dumps(brief, default=str),
                }
            }
        except (HypercolabError, RuntimeError):
            # Unregistered repositories are intentionally unaffected.
            return {}

    if event in {"PostToolUse", "afterFileEdit", "afterShellExecution"}:
        try:
            operations = _extract_file_paths(payload)
            tool = payload.get("tool_name") or payload.get("tool") or "tool"
            paths = [operation["path"] for operation in operations]
            command = _command(payload)
            response = payload.get("tool_response") or payload.get("tool_output") or {}
            exit_code = response.get("exit_code") if isinstance(response, dict) else None
            kind = "git.push_completed" if GIT_PUSH.search(command) else "tool.completed"
            summary = (
                "Git push completed"
                if kind == "git.push_completed" and exit_code in {None, 0}
                else "Git push failed"
                if kind == "git.push_completed"
                else f"Agent completed {tool}"
            )
            with HypercolabClient() as client:
                client.log_activity(
                    kind=kind,
                    summary=summary,
                    source="plugin",
                    paths=paths,
                    metadata={"tool": tool, "path_count": len(paths), "exit_code": exit_code},
                )
        except (HypercolabError, RuntimeError):
            pass
        return {}

    if event in {"Stop", "SessionEnd", "sessionEnd"}:
        try:
            with HypercolabClient() as client:
                client.log_activity(
                    kind="session.stopped",
                    summary="Agent session stopped",
                    source="plugin",
                    metadata={"hook_event": event},
                )
        except (HypercolabError, RuntimeError):
            pass
        return {}

    if event not in {"PreToolUse", "beforeFileEdit", "beforeShellExecution"}:
        return {}
    operations = _extract_file_paths(payload)
    command = _command(payload)
    if not operations and command:
        if GIT_PUSH.search(command):
            try:
                with HypercolabClient() as client:
                    client.log_activity(
                        kind="git.push_attempted",
                        summary="Git push attempted",
                        source="plugin",
                        metadata={"tool": payload.get("tool_name") or payload.get("tool") or "shell"},
                    )
            except (HypercolabError, RuntimeError):
                pass
            return {}
        if READ_ONLY_COMMANDS.search(command) and not WRITE_COMMANDS.search(command):
            return {}
        if WRITE_COMMANDS.search(command):
            return _hook_block(
                "Hypercolab cannot safely infer every path written by this shell command. "
                "Claim the intended files first or use a file-edit tool."
            )
        return {}
    if not operations:
        return {}
    try:
        git = discover_git_context(payload.get("cwd") or None)
        relative: list[dict[str, Any]] = []
        root = Path(git.root).resolve()
        for operation in operations:
            path = Path(operation["path"])
            if path.is_absolute():
                try:
                    path = path.resolve().relative_to(root)
                except ValueError:
                    return _hook_block("Hypercolab blocks writes outside the coordinated repository")
            relative.append({**operation, "path": path.as_posix()})
        with HypercolabClient() as client:
            result = client.check(relative, git=git, auto_claim=True, client_name="plugin")
        if not result.get("allowed", False):
            blocked = [item for item in result.get("decisions", []) if item.get("decision") == "block"]
            return _hook_block("Hypercolab claim conflict: " + json.dumps(blocked, default=str))
        return {}
    except HypercolabError as exc:
        if exc.status_code == 404:
            return {}
        if exc.status_code == 0 and operations_have_live_cached_leases(git.remote, relative):
            return {}
        return _hook_block(str(exc))
    except RuntimeError:
        return {}


def run_client_hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        payload = {}
    output = evaluate_client_hook(payload)
    if output:
        print(json.dumps(output))
    return 0


def install_git_hooks(root: str | Path | None = None) -> list[str]:
    git = discover_git_context(root)
    git_dir_text = subprocess.run(
        ["git", "-C", git.root, "rev-parse", "--git-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()
    git_dir = Path(git.root, git_dir_text) if not Path(git_dir_text).is_absolute() else Path(git_dir_text)
    hook_dir = git_dir / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    installed = []
    for hook_name in GIT_HOOKS:
        path = hook_dir / hook_name
        existing = path.read_text(encoding="utf-8") if path.exists() else "#!/bin/sh\n"
        if MANAGED_START in existing:
            continue
        block = (
            f"\n{MANAGED_START}\nhypercolab git-event {shlex.quote(hook_name)} >/dev/null 2>&1 || true\n{MANAGED_END}\n"
        )
        path.write_text(existing.rstrip() + block, encoding="utf-8")
        path.chmod(path.stat().st_mode | 0o111)
        installed.append(str(path))
    return installed


def uninstall_git_hooks(root: str | Path | None = None) -> list[str]:
    git = discover_git_context(root)
    git_dir_text = subprocess.run(
        ["git", "-C", git.root, "rev-parse", "--git-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()
    git_dir = Path(git.root, git_dir_text) if not Path(git_dir_text).is_absolute() else Path(git_dir_text)
    changed = []
    for hook_name in GIT_HOOKS:
        path = git_dir / "hooks" / hook_name
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        updated = re.sub(
            rf"\n?{re.escape(MANAGED_START)}.*?{re.escape(MANAGED_END)}\n?", "\n", content, flags=re.DOTALL
        )
        if updated != content:
            path.write_text(updated, encoding="utf-8")
            changed.append(str(path))
    return changed


def queue_event(event: dict[str, Any]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")


def flush_queued_events(client: HypercolabClient) -> int:
    """Retry queued Git events, retaining only entries that still fail."""

    if not QUEUE_FILE.exists():
        return 0
    try:
        entries = [json.loads(line) for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError):
        return 0
    remaining: list[dict[str, Any]] = []
    sent = 0
    for entry in entries:
        original = dict(entry)
        try:
            git_data = entry.get("git")
            event = {key: value for key, value in entry.items() if key != "git"}
            git = GitContext(**git_data)
            client.log_activity(git=git, **event)
            sent += 1
        except (HypercolabError, RuntimeError, TypeError):
            remaining.append(original)
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text("".join(json.dumps(entry, default=str) + "\n" for entry in remaining), encoding="utf-8")
    return sent


def record_git_event(kind: str) -> bool:
    git = discover_git_context()
    commit = current_commit(git.root)
    paths = changed_paths(git.root)
    event = {
        "kind": f"git.{kind.replace('-', '_')}",
        "summary": f"Git {kind.replace('-', ' ')} on {git.branch}",
        "source": "git",
        "paths": paths,
        "commit_refs": [commit] if commit else [],
        "metadata": {"branch": git.branch},
    }
    try:
        with HypercolabClient() as client:
            flush_queued_events(client)
            client.log_activity(git=git, **event)
        return True
    except (HypercolabError, RuntimeError):
        queue_event({"git": git.to_dict(), **event})
        return False
