from __future__ import annotations

import subprocess
from pathlib import Path

from hypercolab_cli.git import changed_paths, discover_git_context


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_discover_git_context(tmp_path: Path):
    _run(tmp_path, "init")
    _run(tmp_path, "remote", "add", "origin", "git@github.com:RunStack-AI/example.git")
    context = discover_git_context(tmp_path)
    assert context.root == str(tmp_path)
    assert context.remote == "git@github.com:RunStack-AI/example.git"


def test_changed_paths_from_commit(tmp_path: Path):
    _run(tmp_path, "init")
    _run(tmp_path, "config", "user.email", "test@example.com")
    _run(tmp_path, "config", "user.name", "Test")
    (tmp_path / "hello.txt").write_text("hello\n", encoding="utf-8")
    _run(tmp_path, "add", "hello.txt")
    _run(tmp_path, "commit", "-m", "initial")
    assert changed_paths(tmp_path) == ["hello.txt"]
