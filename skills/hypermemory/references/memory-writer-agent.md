# Memory-writer role reference

Invoke the parent-only skill at `../../memory-writer/SKILL.md`. It is the sole
detailed writer contract and includes durability, relationship, validation,
timeline, and token-reporting rules. Do not copy the parent conversation
history.

In Kimi Code, dispatch a fresh turn-unique sub-agent with the Agent tool and
`run_in_background=true`. Supply the versioned bounded contract as the task
description. After dispatch, return immediately without waiting, polling,
inspecting, reading, messaging, interrupting, or reusing the writer.
