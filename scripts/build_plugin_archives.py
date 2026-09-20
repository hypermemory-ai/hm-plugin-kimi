#!/usr/bin/env python3
"""Build a deterministic HyperMemory Kimi Code plugin review archive."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store", ".venv", ".git", ".github", ".pytest_cache", ".ruff_cache", "dist"}


def _files() -> list[Path]:
    return sorted(
        file
        for file in ROOT.rglob("*")
        if file.is_file()
        and not any(part in EXCLUDED_PARTS for part in file.relative_to(ROOT).parts)
        and file.suffix != ".pyc"
    )


def build() -> Path:
    manifest = json.loads((ROOT / "kimi.plugin.json").read_text(encoding="utf-8"))
    version = str(manifest["version"])
    DIST.mkdir(parents=True, exist_ok=True)
    destination = DIST / f"hypermemory-{version}.zip"
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for file in _files():
            relative = file.relative_to(ROOT).as_posix()
            info = ZipInfo(relative, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if file.stat().st_mode & 0o111 else 0o644) << 16
            archive.writestr(info, file.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    return destination


if __name__ == "__main__":
    print(build().relative_to(ROOT))
