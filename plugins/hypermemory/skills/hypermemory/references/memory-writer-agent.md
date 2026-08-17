# Memory-writer agent contract

The parent agent dispatches exactly one bounded finalization task before
returning the user-facing response. It must create a fresh task with
`fork_turns="none"` and a turn-unique name. Once the spawn succeeds, the parent
must continue immediately without waiting, polling, reading the result, or
sending follow-ups. It must not reuse an earlier writer or copy the parent
conversation history. The delegated agent must not delegate again.

The parent supplies a concise turn summary, relevant project or component keys,
the host name, model, session identifier, and token-listener job paths when
Codex exposes them.

The memory-writer agent then:

1. Recalls related nodes before changing the graph.
2. Stores only durable new knowledge and updates existing nodes instead of
   duplicating them.
3. Gives every new node at least one specific relationship.
4. Writes exactly one concise timeline entry.
5. Reports tokens exactly once, using the Codex listener payload when available
   and an uncertainty-labelled estimate otherwise.
6. Acknowledges a Codex listener claim only after the MCP accepted the report.

It never stores credentials, hidden reasoning, raw transcripts, full tool
output, or large code bodies. It may return a short operational status for
diagnostics, but the parent intentionally does not wait for or consume it.
