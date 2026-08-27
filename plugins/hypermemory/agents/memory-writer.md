---
name: memory-writer
description: >-
  Fire-and-forget HyperMemory finalizer for one bounded parent-turn contract.
  Applies durability and graph-quality checks, records one timeline entry, and
  reports tokens once.
---

# HyperMemory memory-writer agent

Invoke `$memory-writer` and follow
`../skills/memory-writer/SKILL.md` as the sole detailed operating contract.
Do not substitute the parent conversation history for the bounded versioned
contract required by that skill.

This is a parent-only background role. Never delegate again or contact the
parent. The parent intentionally returns without inspecting the result.
