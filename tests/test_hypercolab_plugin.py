from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "hypercolab"
HOOK = PLUGIN / "scripts" / "hypercolab_hook.py"


def test_hypercolab_plugin_registers_local_shim_and_agent() -> None:
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "hypercolab"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert mcp == {"mcpServers": {"hypercolab": {"command": "hypercolab", "args": ["mcp"]}}}
    assert (PLUGIN / "agents" / "coordination-writer.md").is_file()
    assert "exec_command" in hooks["hooks"]["PreToolUse"][0]["matcher"]
    assert all(
        "${PLUGIN_ROOT}/scripts/hypercolab_hook.py" in handler["command"]
        for event in hooks["hooks"].values()
        for group in event
        for handler in group["hooks"]
    )


def test_hook_launcher_explains_missing_cli_without_blocking(tmp_path: Path) -> None:
    env = {**os.environ, "PATH": str(tmp_path)}
    completed = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    output = json.loads(completed.stdout)
    assert "CLI/MCP shim is missing" in output["hookSpecificOutput"]["additionalContext"]
    assert "lifecycle coordination is inactive" in completed.stderr
