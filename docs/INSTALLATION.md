# Installation

This repository is the HyperMemory Kimi Code plugin. The plugin root is the
repository root, with the manifest at `kimi.plugin.json`, so it installs
directly from GitHub.

## Prerequisites

- A current Kimi Code CLI (TUI session)
- A HyperMemory account

## 1. Install

In a Kimi Code session, run one of:

```text
/plugins install https://github.com/hypermemory-ai/hm-plugin-kimi.git
```

```text
/plugins install https://github.com/hypermemory-ai/hm-plugin-kimi/tree/main
```

Or from a local checkout:

```text
/plugins install /path/to/hm-plugin-kimi
```

The installer copies the plugin to
`$KIMI_CODE_HOME/plugins/managed/hypermemory/`; later edits to the source
checkout require a reinstall.

## 2. Authorize the MCP server

The plugin declares the hosted MCP inline:

```text
https://stage.hypermemory.io/mcp
```

Complete OAuth once:

```text
/mcp-config login hypermemory
```

No API key is stored in the plugin package. The server handles
authorization-code flow, PKCE, refresh tokens, and dynamic client
registration.

## 3. Activate

Plugin changes apply after `/reload` or in new sessions. Run `/reload` or
start a new session (`/new`) so the MCP server, bundled skills, and hooks
load.

## 4. Verify

```text
/plugins list
/plugins info hypermemory
/mcp
```

Useful first prompt:

```text
What do you remember about this project?
```

## Updates

Reinstall to pick up a new version, then reload:

```text
/plugins install https://github.com/hypermemory-ai/hm-plugin-kimi.git
/reload
```

## Removal

```text
/plugins remove hypermemory
```

Removing the plugin only deletes the installation record; the managed copy
and original source files remain on disk. It does not delete data already
stored in HyperMemory.

## MCP server toggles

The MCP server can be disabled and re-enabled without removing the plugin:

```text
/plugins mcp disable hypermemory hypermemory
/plugins mcp enable hypermemory hypermemory
/reload
```

## Troubleshooting

### MCP tools are missing

Confirm the plugin is installed and enabled with `/plugins list`, then run
`/reload` or start a new session. Check `/plugins info hypermemory` for
diagnostics.

### Hooks do not run

Check `/plugins info hypermemory` diagnostics for broken manifest fields or
unsafe paths. Plugin hooks are active only while the plugin is enabled and
fire when their matching lifecycle event occurs. All hook failures fail open
and never block your turn.

### OAuth did not open

Run `/mcp-config login hypermemory` and complete the browser flow. Confirm the
installed MCP URL is `https://stage.hypermemory.io/mcp`.

### The plugin changed but the session uses old behavior

Run `/plugins reload`, then `/reload` or start a new session. Local
installations run from the managed copy, so source edits require a reinstall.
