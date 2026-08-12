"""Git repository context used for safe project resolution and audit events."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class GitContext:
    root: str
    remote: str
    branch: str
    worktree: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _git(*args: str, cwd: str | Path | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "Not inside a Git repository")
    return result.stdout.strip()


def discover_git_context(cwd: str | Path | None = None) -> GitContext:
    root = _git("rev-parse", "--show-toplevel", cwd=cwd)
    remote = _git("remote", "get-url", "origin", cwd=root, check=False)
    if not remote:
        remotes = _git("remote", cwd=root, check=False).splitlines()
        if len(remotes) == 1:
            remote = _git("remote", "get-url", remotes[0], cwd=root)
    if not remote:
        raise RuntimeError("The repository has no resolvable Git remote")
    branch = _git("branch", "--show-current", cwd=root, check=False) or "detached"
    worktree = _git("rev-parse", "--show-toplevel", cwd=root)
    return GitContext(root=root, remote=remote, branch=branch, worktree=worktree)


def changed_paths(cwd: str | Path | None = None, revision: str = "HEAD") -> list[str]:
    output = _git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", revision, cwd=cwd, check=False)
    return [line for line in output.splitlines() if line]


def current_commit(cwd: str | Path | None = None) -> str:
    return _git("rev-parse", "HEAD", cwd=cwd, check=False)
