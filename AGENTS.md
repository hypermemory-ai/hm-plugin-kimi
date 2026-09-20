# Repository guidance

This repository IS the HyperMemory Kimi Code plugin: the plugin root is the
repository root and the manifest is `kimi.plugin.json` at the top level, so
`/plugins install <github-url>` works directly.

## Invariants

- Plugin id: `hypermemory`; manifest at repo-root `kimi.plugin.json`.
- Kimi Code surfaces only; do not add formats or instructions for unrelated
  agent ecosystems.
- Keep MCP credentials out of source. OAuth only; Kimi Code stores tokens.
- Preserve safe degraded (fail-open) hook behavior.
- Keep HyperMemory recall on the main agent for substantive prompts and skip it
  only for narrowly classified lightweight social prompts.
- Keep persistence/token reporting on one fresh fire-and-forget memory-writer
  sub-agent; the main agent must never wait, poll, inspect, or message it.
- GitHub installs must keep the manifest at the repository root; do not move
  the plugin into a subdirectory.

## Validation

Run before committing:

```bash
ruff check scripts tests
pytest -q
python scripts/build_plugin_archives.py
```

When changing manifests or hooks, also verify `/plugins info hypermemory`
diagnostics in a live Kimi Code session after `/plugins reload`.
