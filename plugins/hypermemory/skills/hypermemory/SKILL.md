---
name: hypermemory
description: >-
  Use HyperMemory as mandatory durable memory in every ChatGPT and Codex chat,
  task, session, and turn whenever the HyperMemory MCP tools are available.
  Recall context before responding, then delegate graph writes, updates,
  timeline logging, and token reporting to a memory-writer sub-agent. Apply to
  every prompt, including short, conversational, planning, coding, blocked,
  and no-change turns.
---

# HyperMemory

Keep recall on the main agent because it informs the answer. Keep persistence
and telemetry off the main agent by delegating finalization to one sub-agent.
Routine memory operations are silent.

All HyperMemory coordination is internal. Never mention recall, memory-writer
delegation, finalization, timeline logging, or token telemetry in commentary or
the final response unless the user explicitly asks about HyperMemory operation.
Do not relay the memory-writer's operational status to the user.

## Start and recall

On the first response in a conversation:

1. Call `hm_get_overview`.
2. Call `hm_recall` with terms from the user's request.
3. Hydrate exact relevant keys with `hm_get_nodes` when full details or
   relationships are needed.

On every later user turn, call `hm_recall` before substantive work. Use recalled
information naturally and never re-ask for facts already in memory.

## Delegate finalization

Before the final response, spawn exactly one fresh memory-writer sub-agent with
`fork_turns="none"` and wait for it. Use a unique task name derived from the
current turn id. Never reuse a memory-writer from an earlier turn and never fork
the conversation history into it: either behavior repeatedly charges the full
parent context during the writer's tool continuations. Pass only a concise,
bounded summary of the user's request, material actions, decisions, corrections,
durable facts, and relevant project or component keys. The main agent must not
call `hm_store`, `hm_update`, `hm_forget`, `hm_timeline_write`, or `hm_tokens`
when delegation is available.

When a `UserPromptSubmit` hook supplies a token-listener job path, pass that
path and its listener path to the memory-writer. Finalize before returning the
user-facing answer; do not rely on a blocking `Stop` hook.

Use the bounded role contract in
[references/memory-writer-agent.md](references/memory-writer-agent.md) when
constructing the delegated task.

Tell the memory-writer sub-agent to:

1. Call `hm_recall` before any write.
2. Use `hm_store` for new durable knowledge and `hm_update` for changed
   knowledge. Avoid duplicates and trivial or transient facts.
3. Give every new node at least one specific relationship.
4. Call `hm_timeline_write` exactly once with a concise turn record.
5. Call `hm_tokens` exactly once.

When operating as the memory-writer sub-agent, execute these finalization steps
directly and do not spawn another sub-agent. This rule prevents recursive
delegation.

If the host cannot spawn sub-agents, perform persistence directly as an
explicit degraded fallback so memory is not silently lost. Mention degraded
mode only when the user asks about memory operation.

## Codex token reporting

When a Codex lifecycle hook supplies a token-listener job path, the
memory-writer sub-agent must:

1. Run `codex_token_listener.py inspect --job <path>`.
2. Submit the returned `hm_tokens_payload` exactly once through MCP.
3. Run `codex_token_listener.py ack --job <path>` only after the MCP call
   succeeds.

The listener reads only `session_meta` and `token_count` records from the
logical Codex session's parent and sub-agent rollout JSONL files. It never
returns or uploads prompts, responses, tool arguments, or tool results. It
reports cumulative-counter deltas as `client_exact`. Tokens written after
inspection roll into the next successful delta rather than being discarded.
Cached input is emitted only as `cache_tokens`, not as fresh input or total
usage. If the listener rejects an implausible fresh-token spike, treat exact
telemetry as unavailable and follow the bounded self-estimated fallback.

If exact local telemetry is unavailable, submit one honest `self_estimated`
report with uncertainty and no invented cost. Use the listener's
`fallback_turn_sequence` and do not run `ack` because no exact claim exists.

No in-turn observer can count tokens generated after its last tool call. The
listener therefore preserves the unreported tail and includes it in the next
successful Codex delta. A session with no later turn can retain a final tail;
never mislabel an estimate as exact to hide this host limitation.

## ChatGPT token reporting

Consumer ChatGPT does not expose a stable, client-exact per-turn usage file to
plugins. The memory-writer sub-agent must estimate the complete workload across
model invocations, including hidden context and tool continuations. Use
`measurement_quality: self_estimated`, normally
`uncertainty_percentage: 40`, an honest `estimation_bias` (prefer `high` for
tool-heavy turns), and `cost_quality: unavailable`. Never claim
provider-actual usage or cost.

## Canonical segments

Estimate activity segments based on the actual work performed on the turn. Use
the substantive activity as the largest segment (e.g. `coding`, `planning`,
`research`, `writing`), with `context` and `memory` as smaller shares reflecting
system prompt overhead and HyperMemory tool calls respectively. All weights must
total exactly 100. Example for a coding turn:

```json
[
  {"category": "coding", "weight": 80},
  {"category": "context", "weight": 15},
  {"category": "memory", "weight": 5}
]
```

Read [references/protocol.md](references/protocol.md) when storing nodes,
creating relationships, ingesting dense text, or cleaning graph orphans.
