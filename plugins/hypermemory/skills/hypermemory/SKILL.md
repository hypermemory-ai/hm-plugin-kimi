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

## Start and recall

On the first response in a conversation:

1. Call `hm_get_overview`.
2. Call `hm_recall` with terms from the user's request.
3. Hydrate exact relevant keys with `hm_get_nodes` when full details or
   relationships are needed.

On every later user turn, call `hm_recall` before substantive work. Use recalled
information naturally and never re-ask for facts already in memory.

## Delegate finalization

Before the final response, spawn exactly one memory-writer sub-agent and wait
for it. Pass a concise summary of the user's request, material actions,
decisions, corrections, durable facts, and relevant project or component keys.
The main agent must not call `hm_store`, `hm_update`, `hm_forget`,
`hm_timeline_write`, or `hm_tokens` when delegation is available.

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

Use exactly these activity segments because the Rust MCP canonicalizes them:

```json
[
  {"category": "memory", "weight": 10},
  {"category": "context", "weight": 90}
]
```

Read [references/protocol.md](references/protocol.md) when storing nodes,
creating relationships, ingesting dense text, or cleaning graph orphans.
