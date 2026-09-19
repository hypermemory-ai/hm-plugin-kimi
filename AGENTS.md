# Repository guidance

This repository publishes two Kimi Code plugins through one marketplace
catalog. Keep the plugins independently installable and do not introduce
dependencies between their manifests.

## Invariants

- Marketplace catalog: `.agents/plugins/marketplace.json` (Kimi marketplace
  schema, version 2)
- Plugin IDs and folders: `hypermemory`, `hypercolab`
- Kimi Code surfaces only; do not add formats or instructions for unrelated
  agent ecosystems.
- Keep `kimi.plugin.json` at each plugin root as the required manifest entry
  point.
- Keep MCP credentials out of source. Use OAuth or local credential storage.
- Preserve safe degraded (fail-open) hook behavior.
- Keep HyperMemory recall on the main agent for substantive prompts and skip it
  only for narrowly classified lightweight social prompts.
- Keep persistence/token reporting on one fresh fire-and-forget memory-writer
  sub-agent; the main agent must never wait, poll, inspect, or message it.
- Keep HyperColab join/sync/claims on the main agent. Delegated coordination
  writers may record progress but must not bypass ownership conflicts.

## Validation

Run before committing:

```bash
ruff check plugins packages tests scripts
pytest -q
python scripts/build_plugin_archives.py
```

When changing manifests or hooks, also verify diagnostics in a live Kimi Code
session with `/plugins info <id>` after `/plugins reload`.
