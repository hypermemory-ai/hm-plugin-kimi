# HyperMemory plugin for ChatGPT and Codex

This universal plugin bundles a ChatGPT/Codex main-agent skill, a parent-only
memory-writer skill with a strict quality gate, the OAuth-protected HyperMemory
MCP server, and Codex lifecycle enforcement. The writer has separate
token-reporting branches for ChatGPT and Codex.

## Behavior

- Main agent: project-scoped recall for substantive prompts, exact hydration
  when keys are known, and a relevance gate that rejects unrelated projects and
  session-only relationships. Narrow standalone greetings and acknowledgements
  skip retrieval.
- Memory-writer sub-agent: a fresh, turn-unique worker created without parent
  conversation history applies a durability gate, performs only justified graph
  changes, validates every changed node, writes one timeline entry, and reports
  tokens once. The parent never waits for, polls, messages, or reads the worker.
- Codex: trusted hooks enforce the lifecycle and read exact cumulative token
  counters from the active rollout JSONL using a two-phase inspect/ack helper.
- ChatGPT: reports an uncertainty-labelled workload estimate because consumer
  ChatGPT does not expose a stable local exact-usage file to plugins.

The token listener parses only `token_count` records. It does not return or
upload prompts, model responses, tool arguments, or tool results.

Cached reads are reported separately and never included in the fresh-token
total. Stable rollout identities prevent archived transcripts from being
counted twice, and an implausible fresh-token spike is rejected before it can
reach `hm_tokens`.

Codex cannot observe tokens produced after the final tool call of a turn. The
listener carries that exact tail into the next successful report. If a session
never receives another turn, its final tail remains unreported; the plugin does
not falsely label a guess as client-exact.

## Install from the public Git marketplace

Install directly from GitHub:

```bash
codex plugin marketplace add hypermemory-ai/hm-plugins-openai
codex plugin add hypermemory@hypermemory-ai
```

Restart the ChatGPT desktop app or start a new Codex session. Complete the
OAuth sign-in when prompted. In Codex CLI, open `/hooks`, review the bundled
hook definition, and trust it; Codex does not run non-managed plugin hooks until
the user explicitly trusts their current hash.

ChatGPT web local testing requires registering
`https://stage.hypermemory.io/mcp` in developer mode. A public directory
submission should use the **With MCP** flow and submit this MCP server directly;
it does not require a checked-in `.app.json`.

## Validate

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/hypermemory
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/hypermemory/skills/hypermemory
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/hypermemory/skills/memory-writer
pytest -q tests/test_hypermemory_plugin.py
```
