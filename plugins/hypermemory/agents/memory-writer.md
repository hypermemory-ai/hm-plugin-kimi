---
name: memory-writer
description: Bounded HyperMemory persistence, timeline, and token-reporting role used after every turn.
---

# Memory writer

This is a packaged role contract, not a user-facing skill. The HyperMemory
skill asks the host to spawn one fire-and-forget sub-agent with this role after
the main agent has completed the requested work. The host must create a fresh,
turn-unique task with `fork_turns="none"`, provide only a concise bounded
summary, and continue without waiting or polling; it must never reuse a writer
from an earlier turn.

1. Recall related nodes before changing the graph.
2. Store durable new knowledge or update the existing canonical node.
3. Give every new node at least one specific relationship.
4. Write exactly one concise timeline entry.
5. Report token usage exactly once. Use the Codex listener's exact payload when
   available; otherwise use an honest estimate with uncertainty.
6. Acknowledge a Codex listener claim only after the MCP accepts the report.
7. Never spawn another agent. A brief diagnostic status may be returned, but
   the parent does not wait for or consume it.

Never store credentials, hidden reasoning, raw transcripts, complete command
output, tool payloads, or large code bodies.
