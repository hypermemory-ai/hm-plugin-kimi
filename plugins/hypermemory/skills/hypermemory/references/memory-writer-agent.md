# Memory-writer role reference

Invoke the parent-only skill at `../../memory-writer/SKILL.md`. That skill loads
the canonical detailed role packaged at `../../../agents/memory-writer.md`.
Do not copy the parent conversation history.

In Codex, create a fresh turn-unique task with `collaboration.spawn_agent` and
`fork_turns="none"`. Supply only the concise turn summary, the complete role
contract, and any listener/job paths emitted by the lifecycle hook. After the
spawn succeeds, return immediately without waiting, polling, inspecting,
reading, messaging, or reusing the writer.
