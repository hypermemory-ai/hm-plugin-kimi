# HyperMemory plugin for Kimi Code

This Kimi Code plugin bundles a main-agent skill, a parent-only memory-writer
skill with a strict quality gate, the `memory-writer` custom agent, the
OAuth-protected HyperMemory MCP server, and always-on lifecycle hooks.

## Behavior

- Main agent: project-scoped recall for substantive prompts, exact hydration
  when keys are known, and a relevance gate that rejects unrelated projects and
  session-only relationships. Narrow standalone greetings and acknowledgements
  skip retrieval.
- Memory-writer sub-agent: a fresh, turn-unique worker created without parent
  conversation history applies a durability gate, performs only justified graph
  changes, validates every changed node, writes one timeline entry, and reports
  tokens once. The parent never waits for, polls, messages, or reads the
  worker.
- Lifecycle hooks inject concise recall and fire-and-forget dispatch
  instructions on `SessionStart` and `UserPromptSubmit`. If local lifecycle
  preparation fails, the hook reports the problem and fails open so it cannot
  block the user's chat.
- Tokens: Kimi Code does not expose local exact-usage counters to plugins, so
  the writer submits one honest `self_estimated` report per turn. Uncertainty
  and cost fields are omitted unless defensibly known; the plugin never labels
  an estimate as client-exact.

The manifest's `systemPromptPath` (`SYSTEM.md`) contributes the always-on
recall-and-delegate instructions to the agent's system prompt while the plugin
is enabled.

## Install

From a checkout of this repository, in a Kimi Code session:

```text
/plugins install ./plugins/hypermemory
/reload
```

The plugin declares the hosted MCP inline:

```text
https://stage.hypermemory.io/mcp
```

Complete OAuth with `/mcp-config login hypermemory` when prompted. No API key
is stored in the plugin package.

## Validate

```bash
pytest -q tests/test_hypermemory_plugin.py
```
