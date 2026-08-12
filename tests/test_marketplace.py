from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


def test_marketplace_entries_resolve_to_complete_plugins() -> None:
    catalog = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    assert catalog["name"] == "hypermemory-ai"
    assert [entry["name"] for entry in catalog["plugins"]] == ["hypermemory", "hypercolab"]

    for entry in catalog["plugins"]:
        relative = entry["source"]["path"].removeprefix("./")
        plugin = ROOT / relative
        manifest = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        assert plugin.name == entry["name"] == manifest["name"]
        assert manifest["repository"] == "https://github.com/hypermemory-ai/hm-plugins-openai"
        assert (plugin / manifest["mcpServers"].removeprefix("./")).is_file()
        assert (plugin / "hooks" / "hooks.json").is_file()
        assert (plugin / "skills" / entry["name"] / "SKILL.md").is_file()
        assert (plugin / "agents").is_dir()
        assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}


def test_brand_assets_are_valid_square_pngs() -> None:
    for plugin_name in ("hypermemory", "hypercolab"):
        plugin = ROOT / "plugins" / plugin_name
        manifest = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        for field in ("composerIcon", "logo"):
            path = plugin / manifest["interface"][field].removeprefix("./")
            data = path.read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert data[12:16] == b"IHDR"
            assert struct.unpack(">II", data[16:24]) == (256, 256)
