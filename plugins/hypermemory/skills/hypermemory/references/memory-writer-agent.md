# Memory-writer role reference

Invoke the parent-only skill at `../../memory-writer/SKILL.md`. It is the sole
detailed writer contract and includes durability, relationship, validation,
timeline, and token-reporting rules. Do not copy the parent conversation
history.

In Codex, create a fresh turn-unique task with `collaboration.spawn_agent` and
`fork_turns="none"`. Supply the versioned bounded contract and any listener/job
paths emitted by the lifecycle hook. After dispatch, return immediately without
waiting, polling, inspecting, reading, messaging, interrupting, or reusing the
writer.
