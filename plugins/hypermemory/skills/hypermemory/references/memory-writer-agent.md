# Memory-writer agent contract

The parent agent delegates exactly one bounded finalization task and waits for
it before returning the user-facing response. The delegated agent must not
delegate again.

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
output, or large code bodies. Its return value is a short operational status
for the parent agent.
