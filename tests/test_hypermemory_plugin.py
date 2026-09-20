from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "kimi.plugin.json"
HOOK = ROOT / "scripts" / "hypermemory_hook.py"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_at_plugin_root_declares_kimi_layout() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["name"] == "hypermemory"
    assert manifest["version"] == "2.9.2"
    assert manifest["skills"] == "./skills/"
    assert manifest["agents"] == "./agents/"
    assert manifest["mcpServers"]["hypermemory"]["url"] == "https://stage.hypermemory.io/mcp"
    assert manifest["systemPromptPath"] == "./SYSTEM.md"
    assert (ROOT / "SYSTEM.md").is_file()
    assert (ROOT / "skills" / "hypermemory" / "SKILL.md").is_file()
    assert (ROOT / "skills" / "memory-writer" / "SKILL.md").is_file()
    assert (ROOT / "skills" / "memory-writer" / "references" / "node-types.md").is_file()
    assert (ROOT / "agents" / "memory-writer.md").is_file()
    events = [hook["event"] for hook in manifest["hooks"]]
    assert events == ["SessionStart", "UserPromptSubmit"]
    for hook in manifest["hooks"]:
        assert hook["command"].startswith("python3 ./scripts/")
        assert "timeout" in hook


def test_skills_use_kimi_frontmatter() -> None:
    main_skill = (ROOT / "skills" / "hypermemory" / "SKILL.md").read_text()
    front = main_skill.split("---", 2)[1]
    assert "name: hypermemory" in front
    assert "whenToUse:" in front
    assert "version:" not in front
    assert "# HyperMemory MCP — Main Agent Protocol" in main_skill
    assert "## Memory-writer dispatch" in main_skill
    assert '"schema_version": "2.9.2"' in main_skill
    assert "run_in_background=true" in main_skill
    assert "fork_turns" not in main_skill
    assert "token_listener" not in main_skill

    writer = (ROOT / "skills" / "memory-writer" / "SKILL.md").read_text()
    writer_front = writer.split("---", 2)[1]
    assert "name: memory-writer" in writer_front
    assert "disableModelInvocation: true" in writer_front
    assert "## Durability gate" in writer
    assert "## Post-write quality gate" in writer
    assert "## Token reporting" in writer
    assert "Accept `schema_version: 2.9.2`" in writer
    assert "self_estimated" in writer
    assert "listener" not in writer

    writer_agent = (ROOT / "agents" / "memory-writer.md").read_text()
    assert "memory-writer skill" in writer_agent
    assert "sole detailed operating contract" in writer_agent
    assert "mcp__hypermemory__*" in writer_agent


def test_user_prompt_prepares_fire_and_forget_dispatch() -> None:
    payload = {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "prompt": "Fix CI",
        "hook_event_name": "UserPromptSubmit",
    }
    completed = subprocess.run(
        [sys.executable, str(HOOK), "user-prompt"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env={"KIMI_PLUGIN_ROOT": str(ROOT), "PATH": ""},
    )
    context = completed.stdout
    assert "mode=substantive" in context
    assert "exactly one fresh memory-writer" in context
    assert "run_in_background=true" in context
    assert "memory_writer_turn-1" in context
    assert "Fire-and-forget" in context
    assert "do not wait" in context


def test_lightweight_prompt_classifier_is_narrow() -> None:
    hook = _module(HOOK, "hypermemory_hook_classifier_test")
    for prompt in ("hey", "Hey!", " thank you ", "okay."):
        assert hook._is_lightweight_prompt(prompt)
    for prompt in ("Fix CI", "Redis?", "hey, can you fix CI?", "x" * 81):
        assert not hook._is_lightweight_prompt(prompt)
    assert hook._prompt_text({"prompt": {"text": "hey"}}) == ""
    assert hook._prompt_text({"prompt": ["hey"]}) == ""

    payload = {
        "session_id": "session-1",
        "turn_id": "turn-lightweight",
        "prompt": "hey",
        "hook_event_name": "UserPromptSubmit",
    }
    completed = subprocess.run(
        [sys.executable, str(HOOK), "user-prompt"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env={"KIMI_PLUGIN_ROOT": str(ROOT), "PATH": ""},
    )
    assert "mode=lightweight" in completed.stdout
    assert "skip hm_get_overview and hm_recall" in completed.stdout


def test_hook_failures_degrade_without_blocking_the_chat() -> None:
    for event in ("session-start", "user-prompt"):
        failed = subprocess.run(
            [sys.executable, str(HOOK), event],
            input="not-json",
            text=True,
            capture_output=True,
            check=True,
            env={"KIMI_PLUGIN_ROOT": str(ROOT), "PATH": ""},
        )
        assert "without blocking the turn" in failed.stdout
        assert "do not claim" in failed.stdout
        assert "HyperMemory hook degraded" in failed.stderr
