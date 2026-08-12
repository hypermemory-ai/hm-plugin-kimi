# Marketplace maintenance

## Catalog identity

The marketplace file lives at `.agents/plugins/marketplace.json` and has the
stable identifier `hypermemory-ai`. Its ordered plugin list is:

1. `hypermemory`
2. `hypercolab`

Install identifiers follow `<plugin>@<marketplace>`:

```text
hypermemory@hypermemory-ai
hypercolab@hypermemory-ai
```

The catalog entries use `source: local` because Codex first checks out the Git
marketplace and then resolves each `./plugins/...` path inside that snapshot.
Registering the repository is separate from installing a plugin.

## Required entry fields

Every catalog entry includes:

- `name`, matching the plugin folder and manifest name
- a repository-relative source path
- `policy.installation`
- `policy.authentication`
- `category`

Both plugins are `AVAILABLE` and authenticate on installation. Do not add
product gating unless there is an explicit release requirement for it.

## Plugin package contract

Each plugin root contains:

```text
.codex-plugin/plugin.json
.mcp.json
assets/
hooks/hooks.json
skills/<skill>/SKILL.md
skills/<skill>/agents/openai.yaml
skills/<skill>/references/
```

HyperMemory also includes its token listener and lifecycle bridge under
`scripts/`. HyperColab includes a graceful hook launcher, while its complete CLI
and stdio MCP shim live under `packages/hypercolab-cli/` for `pipx`
installation.

## Versions and cache behavior

Use semantic versions in each `.codex-plugin/plugin.json`. Increment only the
plugin that changed. After publishing a Git change:

```bash
codex plugin marketplace upgrade hypermemory-ai
codex plugin add <plugin>@hypermemory-ai
```

Start a new task to load the updated package. Changed hook definitions require
new trust approval.

## Archives and `.plugin` files

Codex marketplace installation consumes the plugin directories referenced by
the catalog; it does not require checked-in `.plugin` archives. OpenAI's public
submission workflow uses the plugin manifest, MCP details, and skill uploads;
skills-only upload artifacts are ZIP files.

For review or release automation, build deterministic ZIPs locally:

```bash
python scripts/build_plugin_archives.py
```

The command writes one archive per plugin under `dist/`. Generated archives are
ignored by Git so the repository remains source-first and avoids stale binary
packages.

## Public Plugins Directory

This Git marketplace supports Codex installation, development, and private or
team distribution. To offer one-click installation to normal ChatGPT and Codex
users, submit each plugin separately through OpenAI's universal Plugins
Directory.

HyperMemory should use the **With MCP** flow with its hosted MCP URL and final
skill bundle. HyperColab needs a publication plan that preserves repository
identity while satisfying the target surface's MCP transport requirements.
