# Contributing

Thank you for improving the HyperMemory AI Kimi Code plugins.

## Development setup

```bash
git clone https://github.com/hypermemory-ai/hm-plugin-kimi.git
cd hm-plugin-kimi
python -m pip install -e "packages/hypercolab-cli[dev]"
```

Create a focused branch, change only the plugin or shared catalog behavior in
scope, and include tests for lifecycle or manifest changes.

## Quality checks

```bash
ruff check plugins packages tests scripts
pytest -q
python scripts/build_plugin_archives.py
```

Then sanity-check both plugins in a live session: `/plugins install
./plugins/hypermemory`, `/plugins info hypermemory`, `/plugins reload`, and
confirm the diagnostics are clean.

## Release checklist

1. Increment the changed plugin's semantic version in `kimi.plugin.json`.
2. Confirm the plugin id, folder name, and marketplace entry id match.
3. Validate every referenced asset, skill, agent, hook, and MCP declaration.
4. Review hook commands for safe failure behavior (fail-open) and plugin-root
   relative paths.
5. Confirm no credentials, tokens, test accounts, or private endpoints entered
   the package.
6. Build fresh review ZIPs and test installation in a new Kimi Code session.
7. Document user-visible changes.
