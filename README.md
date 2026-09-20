# HyperMemory plugin for Kimi Code

This repository **is** the HyperMemory Kimi Code plugin: the plugin root is the
repository root, with the manifest at `kimi.plugin.json`, so it installs
directly from its GitHub URL.

HyperMemory adds durable, relationship-aware memory to Kimi Code. It recalls
the right context before a response, then delegates memory writes, timeline
entries, and token telemetry to one fire-and-forget memory-writer sub-agent
after the work is done.

## Install

In a Kimi Code session:

```text
/plugins install https://github.com/hypermemory-ai/hm-plugin-kimi.git
```

Or from a local checkout:

```text
/plugins install /path/to/hm-plugin-kimi
```

Then run `/reload` or start a new session (`/new`), and authorize the hosted
MCP server once:

```text
/mcp-config login hypermemory
```

The plugin connects to `https://stage.hypermemory.io/mcp` (OAuth
authorization-code flow with PKCE; no API key is stored in the plugin).

## What's included

| Component | Path | Responsibility |
| --- | --- | --- |
| Plugin manifest | `kimi.plugin.json` | Identity, skills, agent, hooks, and inline MCP declaration |
| Main-agent skill | `skills/hypermemory/` | Recall protocol and fire-and-forget writer dispatch |
| Memory-writer skill | `skills/memory-writer/` | Parent-only finalization workflow; model invocation disabled |
| Memory-writer agent | `agents/memory-writer.md` | Delegatable sub-agent: MCP tools only, no further delegation |
| Plugin instructions | `SYSTEM.md` | Always-on recall/delegate rules via `systemPromptPath` |
| Lifecycle hooks | manifest `hooks` array | Inject prompt classification and dispatch instructions, fail open |
| Hook bridge | `scripts/hypermemory_hook.py` | Classifies lightweight prompts and emits concise context |

## How a turn works

1. **Classify** — bare greetings/thanks skip retrieval; everything else is
   substantive.
2. **Recall** — before substantive work, the main agent calls `hm_get_overview`
   (once per conversation) and one focused `hm_recall`, hydrating exact keys
   when known.
3. **Work** — the main agent answers using recalled context plus current
   workspace evidence.
4. **Delegate** — before the final response, it dispatches exactly one fresh
   memory-writer sub-agent in the background with a bounded turn contract
   (durable candidates, timeline-only facts, exclusions).
5. **Respond** — the user-facing answer returns immediately; the main agent
   never waits for, polls, or messages the writer.

The writer applies a durability gate, performs only justified graph mutations,
validates every changed node, writes exactly one timeline entry, and submits
one honest `self_estimated` token report (Kimi Code exposes no local
exact-usage counters to plugins, so estimates are never labeled client-exact).

## Validate and build

```bash
ruff check scripts tests
pytest -q
python scripts/build_plugin_archives.py
```

## Repository layout

```text
kimi.plugin.json               # Plugin manifest (plugin root = repo root)
SYSTEM.md                      # System-prompt contribution
agents/memory-writer.md        # Fire-and-forget writer agent
skills/hypermemory/            # Main-agent recall protocol
skills/memory-writer/          # Writer operating contract + node-type reference
scripts/hypermemory_hook.py    # Lifecycle hook bridge
scripts/build_plugin_archives.py
tests/test_hypermemory_plugin.py
docs/INSTALLATION.md
```

## Security and credentials

No access token, refresh token, client secret, or API key belongs in this
repository. MCP credentials are held by Kimi Code. Hook failures fail open and
never block the user's turn. Report vulnerabilities privately per
[SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
