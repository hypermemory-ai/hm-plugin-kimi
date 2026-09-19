from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
MANIFEST_NAME = "kimi.plugin.json"


def test_marketplace_entries_resolve_to_complete_plugins() -> None:
    catalog = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    assert catalog["version"] == "2"
    assert [entry["id"] for entry in catalog["plugins"]] == ["hypermemory", "hypercolab"]

    for entry in catalog["plugins"]:
        relative = entry["source"].removeprefix("./")
        plugin = ROOT / relative
        manifest = json.loads((plugin / MANIFEST_NAME).read_text(encoding="utf-8"))
        assert plugin.name == entry["id"] == manifest["name"]
        assert isinstance(manifest["mcpServers"], dict) and manifest["mcpServers"]
        assert (plugin / "skills" / entry["id"] / "SKILL.md").is_file()
        if entry["id"] == "hypermemory":
            assert (plugin / "skills" / "memory-writer" / "SKILL.md").is_file()
        assert (plugin / "agents").is_dir()
        for hook in manifest.get("hooks", []):
            assert hook["command"].startswith(("python3 ", "node "))
            assert not hook["command"].startswith("/")


def test_plugin_ids_match_kimi_naming_rules() -> None:
    import re

    for plugin_name in ("hypermemory", "hypercolab"):
        manifest = json.loads((ROOT / "plugins" / plugin_name / MANIFEST_NAME).read_text(encoding="utf-8"))
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", manifest["name"])


def test_brand_assets_are_valid_square_pngs() -> None:
    for plugin_name in ("hypermemory", "hypercolab"):
        plugin = ROOT / "plugins" / plugin_name
        manifest = json.loads((plugin / MANIFEST_NAME).read_text(encoding="utf-8"))
        for field in ("composerIcon", "logo"):
            path = plugin / manifest["interface"][field].removeprefix("./")
            data = path.read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert data[12:16] == b"IHDR"
            assert struct.unpack(">II", data[16:24]) == (256, 256)
