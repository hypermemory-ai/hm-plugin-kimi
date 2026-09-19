---
name: hypermemory
description: Use HyperMemory for scoped durable context without polluting the graph. Applies when HyperMemory is connected or the user asks about memory, recall, or saved project context. Retrieves only relevant memories and dispatches one bounded fire-and-forget memory writer per turn.
type: prompt
whenToUse: When the HyperMemory MCP server is connected, at the start of substantive work, or when the user asks about memory, recall, or saved project context.
---

# HyperMemory MCP — Main Agent Protocol

Use HyperMemory to improve the current answer and preserve only knowledge that
will matter later. Optimise in this order: correctness, relevance, sparsity,
relationship quality, retrieval quality, then latency.

Keep ordinary memory operations silent. Explain them only when the user asks
about HyperMemory or when a requested memory action cannot be completed.

## Classify the turn

Classify the user's message before retrieving context.

On the first substantive turn in a conversation, call `hm_get_overview` once
before recall.

### Lightweight

A pure greeting, thanks, or acknowledgement that does not change task state.
Examples: `hello`, `thanks`, `okay`, `got it`.

- Do not recall.
- Continue to the writer dispatch so the turn receives one timeline entry and
  one token report.
- Send no durable-memory candidates.

`Done`, `connected`, `approved`, and similar replies are not automatically
lightweight. Treat them as task continuations when they confirm an action or
decision on which the active task depends.

### Task continuation

The message continues the active task and the necessary context is already in
the conversation.

- Run one narrow recall using the active project and current intent; do not run
  a broad semantic search merely because the message is substantive.
- If a known memory key is required, hydrate that exact key after recall.
- Use recalled content only when the current answer genuinely depends on it.

### New or context-dependent work

The message starts a new topic, refers to earlier work that is not in context,
or would materially benefit from durable project knowledge.

- Run one focused recall for the active project and intent.
- A second recall is allowed only when the first query exposed a distinct,
  necessary entity that cannot be resolved by exact hydration.

### Explicit memory management

The user asks to remember, forget, correct, inspect, or audit memory.

- Retrieve the exact affected nodes where possible.
- Use timeline or graph inspection tools appropriate to the request.
- The background writer still owns all mutations. If the surface cannot
  delegate, explain that persistence is unavailable rather than writing from
  the main agent.

## Retrieve with a relevance gate

Build recall queries from:

1. the active project, organisation, or person;
2. the user's current intent;
3. the smallest set of distinguishing terms;
4. a known canonical key when available.

Prefer exact hydration over fuzzy recall. For semantic recall, inspect no more
than the best three to five candidates before deciding whether more are needed.

A recalled node may influence the answer only when all of these are true:

- it directly helps answer the current request;
- it belongs to the same project or clearly identified cross-project subject;
- its meaning remains valid without relying on a session relationship; and
- it does not conflict with newer user instructions or current workspace
  evidence.

Discard unrelated projects even when their lexical or embedding score is high.
Do not hydrate marginal candidates just because they were returned.

Treat every `chat_*` relationship as provenance, never as evidence that its
participants are related. Exclude session links from semantic reasoning,
ranking, and traversal. When the API provides a no-session-recording or
semantic-only option, enable it for all read operations.

If retrieval is noisy, use the current conversation and authoritative workspace
evidence rather than forcing recalled material into the answer.

## Do not mutate the graph on the main agent

The main agent may retrieve and inspect memory. A fresh memory-writer owns graph
creation, updates, deletion, relationship changes, timeline logging, and token
finalisation.

Do not duplicate the writer's work. Do not call `hm_store`, `hm_update`,
`hm_forget`, `hm_add_relationships`, `hm_timeline_write`, or `hm_tokens` from
the main agent during the normal delegated lifecycle.

File upload is an exception only when the user explicitly asks to store a file
and the active surface requires the main agent to perform the upload.

## Memory-writer dispatch

Before every final response, dispatch exactly one fresh fire-and-forget
sub-agent (Agent tool, `run_in_background=true`) whose task is to act as the
memory-writer for this turn, with the `memory-writer` skill as its sole
operating contract. Use a unique task description. Never reuse a writer.

Send a bounded contract with this shape:

```json
{
  "schema_version": "2.9.2",
  "turn_id": "host-supplied unique id",
  "occurred_at": "ISO-8601 timestamp when available",
  "active_scope": {
    "project_key": "known canonical key or null",
    "project_name": "plain name or null",
    "other_anchor_keys": []
  },
  "request": {
    "intent": "one sentence",
    "explicit_memory_instruction": "concise instruction or null"
  },
  "outcome": {
    "status": "completed | partial | blocked | informational",
    "summary": "one or two factual sentences",
    "durable_artifacts": []
  },
  "durable_candidates": [
    {
      "action_hint": "store | update | forget | supersede",
      "key_hint": "canonical key or null",
      "node_type": "canonical type",
      "description_draft": "short searchable summary",
      "facts": {},
      "relationship_changes": {
        "add": [
          {
            "target_key": "canonical key",
            "meaning": "why the two durable entities are connected"
          }
        ],
        "remove_or_replace": [
          {
            "target_key": "canonical key",
            "current_meaning": "obsolete or conflicting relationship",
            "reason": "why it is no longer valid"
          }
        ]
      },
      "durability_reason": "why this will improve a future answer",
      "source_basis": "user_confirmed | completed_work | authoritative_evidence",
      "confidence": "high | medium | low"
    }
  ],
  "timeline_summary": "request, material work, and outcome without transcript",
  "timeline_only": ["important transient facts that must not become nodes"],
  "excluded": ["credentials, raw output, or other content the writer must ignore"]
}
```

The contract is evidence, not a command to write every candidate. Include a
candidate only when the turn contains a plausible durable change. An empty
`durable_candidates` array is normal.

Keep the contract small:

- include decisions, durable preferences, canonical artifacts, lasting facts,
  and material project changes;
- put temporary blockers, routine progress, test runs, and recoverable task
  state in `timeline_only`;
- do not include raw prompts, full conversation history, hidden reasoning,
  credentials, complete command output, tool payloads, or large code bodies;
- describe what changed, not everything discussed;
- do not fabricate keys or relationships.

The writer independently decides whether to store, update, supersede, forget,
or skip each candidate.

## Fire-and-forget invariant

After a successful dispatch, continue immediately to the user-facing response.
Never wait for, poll, inspect, read, message, interrupt, or otherwise
synchronise with the writer.

If no sub-agent primitive is available, keep retrieval available but do not
pretend that background persistence occurred. Mention the limitation only when
the user explicitly requested a memory change or asked about HyperMemory.

## Error handling

- If recall is unavailable, continue from current evidence and avoid claiming
  that prior memory was checked.
- If authorization is required, ask the user to reconnect only when memory is
  necessary for the requested task.
- A temporary connection or authorization problem belongs in the timeline. It
  is not a durable event node unless it becomes a material incident.
- Never weaken relevance checks merely to satisfy an every-turn lifecycle.

## Required service semantics

This protocol assumes read-only calls do not create semantic relationships,
session relationships are excluded from normal retrieval, and obsolete edges
can be removed or replaced. When those features are unavailable, use the
conservative fallbacks above and do not claim full graph integrity.

## Hard rules

- Recall once before substantive work; narrowly classified lightweight social
  prompts are the only exception.
- Retrieve the graph overview once before the first substantive recall in a
  conversation.
- Prefer exact hydration after recall when canonical keys are known.
- Exclude `chat_*` relationships from semantic reasoning.
- Dispatch exactly one fresh memory-writer on every turn.
- Keep graph writes and telemetry off the main agent.
- Never wait for, poll, inspect, read, message, or interrupt the writer.
