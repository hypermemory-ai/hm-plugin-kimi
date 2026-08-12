# Repository guidance

This repository publishes two OpenAI plugins through one marketplace. Keep the
plugins independently installable and do not introduce dependencies between
their manifests.

## Invariants

- Marketplace name: `hypermemory-ai`
- Plugin IDs and folders: `hypermemory`, `hypercolab`
- OpenAI surfaces only; do not add formats or instructions for unrelated agent
  ecosystems.
- Keep `.codex-plugin/plugin.json` as the required manifest entry point.
- Keep MCP credentials out of source. Use OAuth or local credential storage.
- Preserve explicit hook trust and safe degraded behavior.
- Keep HyperMemory recall on the main agent and persistence/token reporting on
  one awaited memory-writer sub-agent.
- Keep HyperColab join/sync/claims on the main agent. Delegated coordination
  writers may record progress but must not bypass ownership conflicts.

## Validation

Run before committing:

```bash
ruff check plugins packages tests scripts
pytest -q
python scripts/build_plugin_archives.py
```

When Codex's authoring skills are installed, validate both plugin roots and both
skills with their bundled validators.
