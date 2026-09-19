# Marketplace maintenance

## Catalog identity

The marketplace file lives at `.agents/plugins/marketplace.json`. Its ordered
plugin list is:

1. `hypermemory`
2. `hypercolab`

Each entry needs an `id`, a `displayName`, and a `source` (a local path, zip
URL, or GitHub URL):

```json
{
  "version": "2",
  "plugins": [
    {
      "id": "hypermemory",
      "displayName": "HyperMemory",
      "source": "./plugins/hypermemory"
    }
  ]
}
```

A catalog is browsed with `/plugins marketplace <path-or-url>` (or the
`KIMI_CODE_PLUGIN_MARKETPLACE_URL` environment variable). Browsing the catalog
is separate from installing a plugin.

## Plugin package contract

Each plugin root contains:

```text
kimi.plugin.json
assets/
agents/
skills/<skill>/SKILL.md
skills/<skill>/references/
```

The manifest declares `skills`, `agents`, inline `mcpServers`, and a `hooks`
array directly. HyperMemory also includes its lifecycle bridge under
`scripts/` and a `SYSTEM.md` contributing system-prompt instructions.
HyperColab includes a graceful hook launcher, while its complete CLI and stdio
MCP shim live under `packages/hypercolab-cli/` for `pipx` installation.

## Manifest rules

- `name` is the plugin id and must match `[a-z0-9][a-z0-9_-]{0,63}`.
- `skills` and `agents` are `./` paths within the plugin root.
- MCP servers are declared inline; stdio `command` may be a PATH command or a
  `./` path inside the plugin root.
- Hook commands run from the plugin root, so `./scripts/...` paths resolve
  there.
- `systemPrompt`/`systemPromptPath` content is limited to 32 KB per field and
  64 KB across all enabled plugins.

## Versions and cache behavior

Use semantic versions in each `kimi.plugin.json`. Increment only the plugin
that changed. After publishing a Git change, reinstall the plugin and run
`/reload`; local installations are copied to
`$KIMI_CODE_HOME/plugins/managed/<id>/`, so editing the original source
directory has no effect.

## Archives

Marketplace installation consumes the plugin directories referenced by the
catalog; checked-in archives are not required. For review or release
automation, build deterministic ZIPs locally:

```bash
python scripts/build_plugin_archives.py
```

The command writes one archive per plugin under `dist/`. Generated archives are
ignored by Git so the repository remains source-first and avoids stale binary
packages.
