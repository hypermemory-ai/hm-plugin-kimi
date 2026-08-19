from __future__ import annotations

import json
import time

from hypercolab_cli import config, hooks
from hypercolab_cli.config import operations_have_live_cached_leases, remember_check, remember_repository


def _configure_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(config, "QUEUE_FILE", tmp_path / "timeline-queue.jsonl")
    monkeypatch.setattr(hooks, "QUEUE_FILE", tmp_path / "timeline-queue.jsonl")


def test_live_cached_lease_is_honored_only_until_expiry(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    remote = "git@github.com:example-org/example.git"
    operation = {"path": "src/auth/token.py", "operation": "modify"}
    remember_repository(remote, project={"project_id": "p1"}, session={"session_id": "s1"})
    remember_check(
        remote,
        [operation],
        {
            "decisions": [
                {
                    **operation,
                    "decision": "allow",
                    "claim_id": "c1",
                    "lease_expires_at": time.time() + 60,
                }
            ]
        },
    )

    assert operations_have_live_cached_leases(remote, [operation])
    assert not operations_have_live_cached_leases(remote, [{"path": "src/billing/invoice.py", "operation": "modify"}])


def test_git_queue_retries_and_removes_delivered_events(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    queued = {
        "git": {
            "root": str(tmp_path),
            "remote": "git@github.com:example-org/example.git",
            "branch": "colab",
            "worktree": str(tmp_path),
        },
        "kind": "git.post_commit",
        "summary": "Git post commit on colab",
        "source": "git",
        "paths": ["src/app.py"],
        "commit_refs": ["abc"],
        "metadata": {"branch": "colab"},
    }
    hooks.queue_event(queued)

    class _Client:
        def __init__(self):
            self.events = []

        def log_activity(self, **event):
            self.events.append(event)

    client = _Client()
    assert hooks.flush_queued_events(client) == 1
    assert len(client.events) == 1
    assert json.loads(json.dumps(client.events[0]["git"].to_dict()))["branch"] == "colab"
    assert hooks.QUEUE_FILE.read_text(encoding="utf-8") == ""
