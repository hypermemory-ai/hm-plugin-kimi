from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "hypermemory"
LISTENER = PLUGIN / "scripts" / "codex_token_listener.py"
HOOK = PLUGIN / "scripts" / "hypermemory_hook.py"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_rollout(
    path: Path,
    *,
    physical_id: str,
    logical_id: str,
    total: int,
    input_tokens: int,
    output_tokens: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "timestamp": "2026-08-12T10:00:00Z",
            "type": "session_meta",
            "payload": {"id": physical_id, "session_id": logical_id, "source": "test"},
        },
        {"type": "event_msg", "payload": {"type": "message", "content": "must not be parsed"}},
        {
            "timestamp": "2026-08-12T10:01:00Z",
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "model": "gpt-test",
                    "total_token_usage": {
                        "input_tokens": input_tokens,
                        "cached_input_tokens": max(0, input_tokens - 5),
                        "cache_write_input_tokens": 0,
                        "output_tokens": output_tokens,
                        "reasoning_output_tokens": 3,
                        "total_tokens": total,
                    },
                },
            },
        },
    ]
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def test_plugin_is_chatgpt_and_codex_only() -> None:
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "hypermemory"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert "hooks" not in manifest  # default hooks/hooks.json is auto-discovered
    assert (PLUGIN / "hooks" / "hooks.json").is_file()
    assert (PLUGIN / "agents" / "memory-writer.md").is_file()


def test_public_marketplace_is_self_contained() -> None:
    marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())
    assert marketplace["name"] == "hypermemory-ai"
    assert marketplace["plugins"] == [
        {
            "name": "hypermemory",
            "source": {"source": "local", "path": "./plugins/hypermemory"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Memory & Knowledge",
        },
        {
            "name": "hypercolab",
            "source": {"source": "local", "path": "./plugins/hypercolab"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        },
    ]


def test_mcp_uses_rust_stage_oauth_endpoint() -> None:
    config = json.loads((PLUGIN / ".mcp.json").read_text())
    assert config == {
        "mcpServers": {
            "hypermemory": {"type": "http", "url": "https://stage.hypermemory.io/mcp"}
        }
    }


def test_stop_hook_requires_one_subagent_and_guards_recursion(tmp_path: Path) -> None:
    env = {**os.environ, "PLUGIN_ROOT": str(PLUGIN), "PLUGIN_DATA": str(tmp_path)}
    base = {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "transcript_path": None,
        "model": "gpt-test",
        "hook_event_name": "Stop",
    }
    first = subprocess.run(
        [sys.executable, str(HOOK), "stop"],
        input=json.dumps({**base, "stop_hook_active": False}),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    output = json.loads(first.stdout)
    assert output["decision"] == "block"
    assert "exactly one memory-writer sub-agent" in output["reason"]
    assert list((tmp_path / "jobs").glob("turn-*.json"))

    second = subprocess.run(
        [sys.executable, str(HOOK), "stop"],
        input=json.dumps({**base, "stop_hook_active": True}),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    assert json.loads(second.stdout) == {"continue": True}


def test_listener_aggregates_parent_and_subagent_then_acks(tmp_path: Path, capsys) -> None:
    logical = "logical-session"
    parent = tmp_path / ".codex" / "sessions" / "rollout-parent.jsonl"
    child = tmp_path / ".codex" / "sessions" / "rollout-child.jsonl"
    _write_rollout(parent, physical_id="parent", logical_id=logical, total=110, input_tokens=90, output_tokens=20)

    state_file = tmp_path / "plugin-data" / "token-state.json"
    baseline_job = tmp_path / "baseline.json"
    baseline_job.write_text(
        json.dumps(
            {
                "version": 1,
                "session_id": logical,
                "transcript_path": str(parent),
                "state_file": str(state_file),
            }
        ),
        encoding="utf-8",
    )
    listener = _module(LISTENER, "hypermemory_token_listener_test")
    old_codex_home = os.environ.get("CODEX_HOME")
    os.environ["CODEX_HOME"] = str(tmp_path / ".codex")
    try:
        assert listener.baseline(baseline_job) == 0
        capsys.readouterr()

        _write_rollout(parent, physical_id="parent", logical_id=logical, total=150, input_tokens=125, output_tokens=25)
        _write_rollout(child, physical_id="child", logical_id=logical, total=60, input_tokens=45, output_tokens=15)
        job_path = tmp_path / "turn.json"
        job_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "session_id": logical,
                    "turn_id": "turn-1",
                    "transcript_path": str(parent),
                    "model": "gpt-test",
                    "state_file": str(state_file),
                }
            ),
            encoding="utf-8",
        )
        assert listener.inspect(job_path, 0) == 0
        inspected = json.loads(capsys.readouterr().out)
        report = inspected["hm_tokens_payload"]
        assert inspected["exact_available"] is True
        assert report["measurement_quality"] == "client_exact"
        assert report["total_tokens"] == 100
        assert report["input_tokens"] == 80
        assert report["output_tokens"] == 20

        assert listener.ack(job_path) == 0
        capsys.readouterr()
        state = json.loads(state_file.read_text())
        assert state["sessions"][logical]["turn_sequence"] == 1
        assert len(state["sessions"][logical]["rollouts"]) == 2
    finally:
        if old_codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = old_codex_home


def test_baseline_does_not_discard_unreported_resume_tail(tmp_path: Path, capsys) -> None:
    logical = "resume-session"
    rollout = tmp_path / ".codex" / "sessions" / "rollout-resume.jsonl"
    _write_rollout(rollout, physical_id="parent", logical_id=logical, total=30, input_tokens=20, output_tokens=10)
    state_file = tmp_path / "plugin-data" / "token-state.json"
    job = tmp_path / "baseline.json"
    job.write_text(
        json.dumps(
            {
                "version": 1,
                "session_id": logical,
                "transcript_path": str(rollout),
                "state_file": str(state_file),
            }
        ),
        encoding="utf-8",
    )
    listener = _module(LISTENER, "hypermemory_token_listener_resume_test")
    old_codex_home = os.environ.get("CODEX_HOME")
    os.environ["CODEX_HOME"] = str(tmp_path / ".codex")
    try:
        assert listener.baseline(job) == 0
        capsys.readouterr()
        _write_rollout(rollout, physical_id="parent", logical_id=logical, total=50, input_tokens=35, output_tokens=15)
        assert listener.baseline(job) == 0
        resumed = json.loads(capsys.readouterr().out)
        assert resumed["baselined"] is False

        turn_job = tmp_path / "turn.json"
        turn_job.write_text(
            json.dumps(
                {
                    "version": 1,
                    "session_id": logical,
                    "turn_id": "turn-after-resume",
                    "transcript_path": str(rollout),
                    "model": "gpt-test",
                    "state_file": str(state_file),
                }
            ),
            encoding="utf-8",
        )
        assert listener.inspect(turn_job, 0) == 0
        inspected = json.loads(capsys.readouterr().out)
        assert inspected["hm_tokens_payload"]["total_tokens"] == 20
    finally:
        if old_codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = old_codex_home
