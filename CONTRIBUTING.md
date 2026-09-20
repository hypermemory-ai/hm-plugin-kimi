# Contributing

Thank you for improving the HyperMemory Kimi Code plugin.

## Development setup

```bash
git clone https://github.com/hypermemory-ai/hm-plugin-kimi.git
cd hm-plugin-kimi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ruff pytest
```

## Quality checks

```bash
ruff check scripts tests
pytest -q
python scripts/build_plugin_archives.py
```

Then sanity-check in a live session: `/plugins install ./plugins/hypermemory`
(local path works), `/plugins info hypermemory`, `/plugins reload`, and confirm
the diagnostics are clean.

## Release checklist

1. Increment the semantic version in `kimi.plugin.json`.
2. Validate every referenced skill, agent, hook, and MCP declaration.
3. Review hook commands for safe failure behavior (fail-open) and plugin-root
   relative paths.
4. Confirm no credentials, tokens, test accounts, or private endpoints entered
   the package.
5. Build a fresh review ZIP and test installation in a new Kimi Code session.
6. Document user-visible changes.
