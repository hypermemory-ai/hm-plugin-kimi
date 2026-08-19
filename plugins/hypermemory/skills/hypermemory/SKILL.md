---
name: hypermemory
description: >-
  Persistent memory graph for ChatGPT and Codex via HyperMemory MCP. Recall
  context on every substantive message and dispatch one fire-and-forget
  memory-writer sub-agent for graph persistence, timeline logging, and token
  finalization. Use whenever the HyperMemory MCP is connected or the user
  mentions HyperMemory, memory, recall, or durable project context.
---

# HyperMemory MCP — Main Agent Protocol

Use the `user-hypermemory` MCP server every turn according to this protocol.
Keep the lifecycle invisible in normal user-facing responses.

## Recall

On the first substantive message in a conversation:

1. Call `hm_get_overview`.
2. Call `hm_recall` with keywords from the user's message.

On every later substantive message, call `hm_recall` before substantive work
and use the recalled context naturally.

When the lifecycle hook classifies a message as `lightweight`, skip overview
and recall. Classification is deliberately narrow: after trimming whitespace
and punctuation, the prompt must be at most 80 characters and consist solely
of a greeting or acknowledgement (`hey`, `hello`, `hi`, `howdy`, `thanks`,
`thank you`, `okay`, `ok`, or `got it`). Short tasks, questions, entities,
paths, code, numbers, and decisions remain substantive. If classification is
missing or uncertain, treat the message as substantive.

## Memory-writer dispatch

Before every final response:

1. Spawn exactly one fresh memory-writer sub-agent with the host's sub-agent
   primitive. In Codex, use `collaboration.spawn_agent` with
   `fork_turns="none"`. Use the turn-unique task name supplied by the lifecycle
   hook; when no hook exists, generate a fresh `memory_writer_<unique-turn-id>`
   name. Never reuse a writer.
2. Tell the sub-agent to invoke `$memory-writer`. Pass only a concise bounded
   turn summary and any token-listener/job paths supplied by the hook. Do not
   copy the parent conversation history or rely on an unresolved file path as
   the contract.
3. Require the writer to recall before changing the graph; store, update, or
   forget only durable knowledge; give every new node a specific relationship;
   write exactly one timeline entry; and report tokens exactly once. When a
   Codex listener job exists, require inspect, one `hm_tokens` submission, and
   acknowledgement only after MCP acceptance.
4. After the spawn succeeds, return the user-facing response immediately.
   Never wait, poll, inspect, read, message, or otherwise synchronize with the
   writer.

The writer owns graph persistence and token finalization. The main agent must
not duplicate those writes. `$memory-writer` is the parent-only writer skill;
its canonical detailed role is packaged at `agents/memory-writer.md`.

If the current surface has no sub-agent primitive, degrade safely: keep recall
available, do not perform delegated graph writes on the main agent, and state
that persistence is unavailable on this surface. Do not simulate background
completion or claim that the turn was stored.

Never ask permission to save and never announce memory operations.

## Main-agent tool reference

| Tool | Use when |
| --- | --- |
| `hm_get_overview` | Start of the first substantive turn |
| `hm_recall` | Search memory before substantive work |
| `hm_get_nodes` | Hydrate known exact keys with full details |
| `hm_find_related` | Traverse relationships from a known node |
| `hm_get_chat_context` | Reload nodes from a known chat session |
| `hm_timeline` | Retrieve temporal context when history matters |
| `hm_upload_file` | The user explicitly asks to store a file |
| `hm_list_files` | Query previously uploaded files |
| `hm_tabular` | Inspect a processed spreadsheet or tabular file |
| `hm_skill` | Retrieve or update HyperMemory agent instructions |

There is no `hm_related` or `hm_relate`; use `hm_find_related` for traversal.
Use `hm_get_nodes(keys=[...])` when exact keys are already known.

When updating HyperMemory instructions with `hm_skill`, preserve the returned
skill verbatim as the baseline and apply local amendments as a minimal diff.

## Hard rules

- Call `hm_get_overview` and `hm_recall` before the first substantive response.
- Call `hm_recall` before every later substantive response.
- Dispatch exactly one fresh memory-writer on every message.
- Keep graph writes and telemetry off the main agent.
- Never wait for, poll, inspect, read, or message the dispatched writer.
- Never create `chat_*` relationship names; they are system-reserved.
