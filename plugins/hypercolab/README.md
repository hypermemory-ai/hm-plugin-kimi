# HyperColab for Kimi Code

HyperColab coordinates developers and coding agents around the Git repository
they are actually working in. It combines a project graph, chronological
development timeline, active ownership, path claims, and file-level collision
protection.

## Included

- `kimi.plugin.json` declares the local `hypercolab mcp` stdio shim inline,
  the coordination skill, the coordination-writer agent, and lifecycle hooks.
- `skills/hypercolab/` defines join, sync, claim, update, and finish behavior.
- Hooks load project context, check write ownership, and record structured
  development activity while the plugin is enabled.
- `scripts/hypercolab_hook.py` provides a safe launcher when the CLI is absent.
- `agents/coordination-writer.md` defines the bounded timeline-writer role.

## Install

```bash
pipx install "git+https://github.com/hypermemory-ai/hm-plugin-kimi.git#subdirectory=packages/hypercolab-cli"
hypercolab login
```

Then in a Kimi Code session:

```text
/plugins install ./plugins/hypercolab
/reload
```

Start a new task inside a Git repository enrolled in HyperColab. HyperMemory's
personal memory MCP remains a separate plugin and can be installed alongside
HyperColab.

## Data boundary

HyperColab sends structured summaries, affected paths, commit identifiers,
claims, and visible rationale to the project service. It does not send raw
source, raw diffs, transcripts, complete shell output, or hidden reasoning by
default.
