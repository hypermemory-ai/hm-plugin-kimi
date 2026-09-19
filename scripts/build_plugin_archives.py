#!/usr/bin/env python3
"""Build deterministic Kimi Code plugin review archives from marketplace sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
DIST = ROOT / "dist"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store"}


def _files(plugin: Path) -> list[Path]:
    return sorted(
        file
        for file in plugin.rglob("*")
        if file.is_file()
        and not any(part in EXCLUDED_PARTS for part in file.relative_to(plugin).parts)
        and file.suffix != ".pyc"
    )


def build(plugin_name: str) -> Path:
    plugin = PLUGINS / plugin_name
    manifest_path = plugin / "kimi.plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != plugin_name:
        raise ValueError(f"manifest name mismatch for {plugin_name}")
    version = str(manifest["version"])
    DIST.mkdir(parents=True, exist_ok=True)
    destination = DIST / f"{plugin_name}-{version}.zip"
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for file in _files(plugin):
            relative = file.relative_to(plugin).as_posix()
            info = ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if file.stat().st_mode & 0o111 else 0o644) << 16
            archive.writestr(info, file.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugins", nargs="*", default=["hypermemory", "hypercolab"])
    args = parser.parse_args()
    for plugin_name in args.plugins:
        print(build(plugin_name).relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
