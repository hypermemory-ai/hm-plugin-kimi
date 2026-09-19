# Installation

This repository is a custom Kimi Code marketplace catalog named
`hypermemory-ai`. Pointing Kimi Code at it makes the catalog available; it does
not install either plugin.

## Prerequisites

- A current Kimi Code CLI (TUI session)
- A HyperMemory account
- Python 3.10 or newer and `pipx` for the HyperColab local shim

## 1. Add the marketplace

From a checkout of this repository, run inside a Kimi Code session:

```text
/plugins marketplace ./.agents/plugins/marketplace.json
```

A hosted JSON URL works the same way. You can also set
`KIMI_CODE_PLUGIN_MARKETPLACE_URL` to the JSON location to override the
default catalog.

The catalog exposes two plugin IDs: `hypermemory` and `hypercolab`.

## 2. Install HyperMemory

```text
/plugins install ./plugins/hypermemory
```

Or select it in the plugin manager (`/plugins`, Custom tab) after adding the
marketplace. The plugin connects to:

```text
https://stage.hypermemory.io/mcp
```

The MCP server is enabled by default after installation. If OAuth is required,
complete it with:

```text
/mcp-config login hypermemory
```

No API key is stored in the plugin package. The server handles
authorization-code flow, PKCE, refresh tokens, and dynamic client
registration.

Run `/reload` or start a new session (`/new`) so the MCP server, bundled
skills, and hooks are loaded.

## 3. Install HyperColab

HyperColab resolves the current Git root, remote, branch, and worktree locally.
Install its CLI and stdio MCP shim before installing the plugin:

```bash
pipx install "git+https://github.com/hypermemory-ai/hm-plugins-openai.git#subdirectory=packages/hypercolab-cli"
hypercolab login
hypercolab doctor
```

Then install the plugin:

```text
/plugins install ./plugins/hypercolab
```

Inside a repository enrolled in HyperColab, optionally install the non-blocking
Git activity hooks:

```bash
hypercolab hooks install
```

Run `/reload` or start a new session afterward. Repositories that are not
registered with HyperColab remain unaffected.

## 4. Verify

```text
/plugins list
/plugins info hypermemory
/plugins info hypercolab
/mcp
```

```bash
hypercolab status
```

Useful first prompts:

- `What do you remember about this project?`
- `Join this HyperColab project and show active work.`
- `Claim the files needed for this task before editing.`

## Updates

Reinstall the desired package from the refreshed source and run `/reload`:

```text
/plugins install ./plugins/hypermemory
/plugins install ./plugins/hypercolab
```

```bash
pipx upgrade hypercolab
```

Local installations are copied to
`$KIMI_CODE_HOME/plugins/managed/<id>/`; editing the original source
directory after installation has no effect, so a reinstall is required to pick
up changes.

## Removal

```text
/plugins remove hypermemory
/plugins remove hypercolab
```

Removing a plugin only deletes the installation record; the managed copy and
original source files remain on disk. Remove local HyperColab Git hooks before
uninstalling the CLI if you installed them:

```bash
hypercolab hooks uninstall
pipx uninstall hypercolab
```

Removing the plugins does not delete data already stored in HyperMemory or
HyperColab.

## MCP server toggles

Each plugin's MCP servers can be disabled and re-enabled without removing the
plugin:

```text
/plugins mcp disable hypermemory hypermemory
/plugins mcp enable hypermemory hypermemory
/plugins mcp disable hypercolab hypercolab
/plugins mcp enable hypercolab hypercolab
```

Run `/reload` after toggling so the change takes effect.

## Troubleshooting

### MCP tools are missing

Confirm the plugin is installed and enabled with `/plugins list`, then run
`/reload` or start a new session. For HyperColab, also confirm `hypercolab` is
on `PATH` with `hypercolab doctor`.

### Hooks do not run

Check `/plugins info <id>` diagnostics for broken manifest fields or unsafe
paths. Plugin hooks are active only while the plugin is enabled and fire on
their matching lifecycle events.

### OAuth did not open

For HyperMemory, run `/mcp-config login hypermemory` and complete the browser
flow. For HyperColab, run `hypercolab login` directly in a terminal.

### A HyperColab write is blocked

Run `hypercolab sync` to inspect current ownership. Coordinate a handoff or wait
for the conflicting lease instead of bypassing a live claim.

### The plugin changed but the session uses old behavior

Run `/plugins reload`, then `/reload` or start a new session. In-flight
requests keep their existing system prompt; prompt contributions converge on
the next rebuild.
