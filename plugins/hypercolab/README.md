# HyperColab for ChatGPT and Codex

HyperColab coordinates developers and coding agents around the Git repository
they are actually working in. It combines a project graph, chronological
development timeline, active ownership, path claims, and file-level collision
protection.

## Included

- `.mcp.json` registers the local `hypercolab mcp` stdio shim.
- `skills/hypercolab/` defines join, sync, claim, update, and finish behavior.
- `hooks/hooks.json` loads project context, checks write ownership, and records
  structured development activity after explicit Codex trust.
- `scripts/hypercolab_hook.py` provides a safe launcher when the CLI is absent.
- `agents/coordination-writer.md` defines the bounded timeline-writer role used
  by the skill.

## Install

```bash
pipx install "git+https://github.com/hypermemory-ai/hm-plugins-openai.git#subdirectory=packages/hypercolab-cli"
hypercolab login
codex plugin marketplace add hypermemory-ai/hm-plugins-openai
codex plugin add hypercolab@hypermemory-ai
```

Start a new task and review the plugin hooks with `/hooks`. HyperMemory's
personal memory MCP remains a separate plugin and can be installed alongside
HyperColab.

## Data boundary

HyperColab sends structured summaries, affected paths, commit identifiers,
claims, and visible rationale to the project service. It does not send raw
source, raw diffs, transcripts, complete shell output, or hidden reasoning by
default.
