# Contributing

Thank you for improving the HyperMemory AI OpenAI plugins.

## Development setup

```bash
git clone https://github.com/hypermemory-ai/hm-plugins-openai.git
cd hm-plugins-openai
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

Also run the Codex plugin and skill validators listed in the root README when
available.

## Release checklist

1. Increment the changed plugin's semantic version.
2. Confirm marketplace name, plugin ID, folder name, and manifest name match.
3. Validate every referenced asset, skill, hook, and MCP path.
4. Review hook commands for safe failure behavior and explicit trust.
5. Confirm no credentials, tokens, test accounts, or private endpoints entered
   the package.
6. Build fresh review ZIPs and test installation in a new Codex task.
7. Document user-visible changes.
