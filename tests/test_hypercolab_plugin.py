from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "hypercolab"
HOOK = PLUGIN / "scripts" / "hypercolab_hook.py"


def test_hypercolab_plugin_registers_local_shim_and_agent() -> None:
    manifest = json.loads((PLUGIN / "kimi.plugin.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "hypercolab"
    assert manifest["mcpServers"] == {"hypercolab": {"command": "hypercolab", "args": ["mcp"]}}
    assert (PLUGIN / "agents" / "coordination-writer.md").is_file()
    hooks_by_event = {hook["event"]: hook for hook in manifest["hooks"]}
    assert set(hooks_by_event) == {"SessionStart", "PreToolUse", "PostToolUse", "Stop"}
    assert hooks_by_event["PreToolUse"]["matcher"] == "Bash|Edit|Write"
    assert all(
        "scripts/hypercolab_hook.py" in hook["command"]
        for hook in manifest["hooks"]
    )


def test_hook_launcher_explains_missing_cli_without_blocking(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        text=True,
        capture_output=True,
        check=True,
        env={"PATH": str(tmp_path)},
    )
    output = json.loads(completed.stdout)
    assert "CLI/MCP shim is missing" in output["hookSpecificOutput"]["additionalContext"]
    assert "lifecycle coordination is inactive" in completed.stderr
