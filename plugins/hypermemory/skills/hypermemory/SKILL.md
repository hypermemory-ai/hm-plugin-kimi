---
name: hypermemory
version: 0.6.8
description: >-
  Persistent memory graph for AI agents via HyperMemory MCP tools. Recall
  context, store facts and relationships, enforce hyperedge policy, and
  maintain graph hygiene on every message. Use when user-hypermemory MCP is
  connected or the user mentions HyperMemory, hm_store, hm_recall, or memory.
  Skip main-agent retrieval only for hook-classified lightweight social
  messages, and dispatch end-of-turn persistence through a fire-and-forget
  memory-writer sub-agent.
enforcement: mandatory
trigger: every_turn
---

# HyperMemory MCP — Agent Protocol

You have the `user-hypermemory` MCP server. Use its tools every message according
to the main-agent and memory-writer roles below.

## Every conversation

**First substantive message (before responding):**

1. `hm_get_overview`
2. `hm_recall` with keywords from the user's message

**Every substantive message (silently, before responding):**

1. Main agent → `hm_recall` with keywords from the user's message.
2. Use recalled context naturally in the response.

When the lifecycle hook classifies a message as `lightweight`, skip
`hm_get_overview` and `hm_recall` on the main agent. Classification must be
narrow and deterministic: after trimming whitespace and punctuation, the prompt
must be at most 80 characters and consist solely of a standalone greeting or
acknowledgement such as `hey`, `hello`, `hi`, `howdy`, `thanks`, `thank you`,
`okay`, `ok`, or `got it`. A short task, question, entity, file, code fragment,
number, or decision remains substantive. If classification is absent or
uncertain, treat the message as substantive.

**Every message (silently, before the final response):**

1. Spawn exactly one fresh memory-writer sub-agent with `fork_turns="none"` and
   a turn-unique task name.
2. Pass only a concise bounded summary plus any token-listener job supplied by
   the lifecycle hook.
3. Tell the writer to call `hm_recall`, then use `hm_store`, `hm_update`, or
   `hm_forget` as appropriate; write exactly one `hm_timeline_write` entry; and
   call `hm_tokens` exactly once. Every new node needs a specific relationship.
4. Fire and forget: after the spawn succeeds, return the user-facing response
   immediately. Never call `wait_agent`, poll, inspect, read, message, or
   otherwise synchronize with the writer.

The writer performs graph persistence and token finalization. The main agent
must not duplicate those writes when sub-agent dispatch is available.

Never ask permission to save. Never announce that you saved.

---

## Tool reference

| Tool | Use when |
|------|----------|
| `hm_get_overview` | Start of conversation — graph stats |
| `hm_recall` | Search memory; always before store |
| `hm_get_nodes` | Hydrate known exact keys with full node details |
| `hm_store` | New node + optional relationships |
| `hm_update` | Correct or expand existing node |
| `hm_forget` | Delete node (cascades edges) |
| `hm_find_related` | Traverse graph from a seed node |
| `hm_add_relationships` | Connect existing nodes; fix orphans |
| `hm_get_relationships` | *(REST/CLI only — not MCP)* |
| `hm_get_chat_context` | Reload nodes from current chat session |
| `hm_list_orphans` | After every `hm_ingest` |
| `hm_ingest` | Dense multi-entity text (creates orphans) |
| `hm_upload_file` | User explicitly asks to store a file (Pro+) |
| `hm_list_files` | Query uploaded files |
| `hm_timeline_write` | Diary line not captured as a node |
| `hm_tokens` | End-of-turn token/cost report with weighted activity segments |
| `hm_timeline` | Temporal lookup (not auto-loaded) |
| `hm_skill` | Retrieve or update current HyperMemory agent skills |

For `hm_tokens`, report `cost_usd` with a separate `cost_quality`:
`provider_actual`, `price_calculated`, `self_estimated`, or `unavailable`.
Only use `provider_actual` for a provider-billed amount.
For OpenRouter, submit client-visible token fields and weighted segments.
HyperMemory treats them as provisional attribution and reconciles them with
management analytics for the OpenRouter key mapped to the user. Never invent
provider-actual values. Claude Desktop uses `self_estimated`, includes
uncertainty, and does not report API-equivalent dollar cost.
When multiple AI accounts are configured, include the matching `ai_account_id`
in `hm_tokens`. Without it, HyperMemory auto-assigns only when exactly one
active account matches `ai_tool`; ambiguous reports remain unassigned but still
count in the user's aggregate totals.
Each segment category may appear only once per report. Merge activities that
share a category into one segment and combine their weights before calling
`hm_tokens`; all resulting weights must total exactly 100.
Estimate segmentation separately from token counting. Exact token counters do
not make activity attribution exact.

Allowed categories are `reasoning`, `memory`, `context`,
`doc_processing`, `automation`, `personal`, `chatting`, `research`,
`design`, `calculations`, `coding`, `planning`, `productivity`,
`writing`, and `unmatched`.

Classify the work actually performed:

- Make the substantive activity the largest share. For software implementation,
  debugging, testing, code review, repository inspection, deployment, and
  technical configuration, use `coding` as the primary category.
- Use `planning` when the deliverable is a plan rather than implementation,
  `research` for material source gathering, and the other substantive
  categories only when that work actually occurred.
- Use `memory` only for HyperMemory recall, graph persistence, timeline, and
  token-finalization overhead. Use `context` only for reading conversation,
  retrieved files, instructions, and tool results.
- Never use `memory` or `context` as catch-all substitutes for the turn's
  real work. If classification is genuinely unavailable, use
  `unmatched: 100` explicitly.
- Omit zero-weight categories, keep categories unique, and verify that weights
  total 100. Do not use the removed `mem_ingest` or `mem_retrieve`
  categories.
`estimation_bias` is exactly `low`, `neutral`, or `high`. Token and cost
provenance are independent: exact tokens may use `cost_quality: self_estimated`
for an estimated USD amount. If validation rejects
a report, correct the named field once and never repeat an unchanged payload.

**Naming traps:** There is no `hm_related` or `hm_relate`. Use `hm_find_related` to traverse, `hm_add_relationships` to create edges.

**Recall vs hydrate:** Use `hm_recall` to search for candidate nodes. Use
`hm_get_nodes(keys=[...])` when you already know exact keys and need full,
untruncated descriptions, data, assets, duplicate records, and relationships.

**Skill updates:** If asked to install or update HyperMemory instructions, call
`hm_skill` with `action="get"` and the best variant for the agent. Preserve the
returned skill verbatim as the baseline, including all YAML frontmatter, and
apply local behavioral amendments as a minimal diff.

---

## Node types

```
user person organization component event decision concept artifact
project technology preference fact skill
```

`node_type` is one canonical ontology class, not a free-form label. Do not
invent new types or ontology classes in agent output. If unsure, omit
`node_type` or choose the closest canonical class; the server resolves invalid
or missing input internally before persistence.

**Key format:** `{type}_{name}` — e.g. `decision_jwt_auth`, `person_alice`, `tech_redis`

**Singleton:** `user_profile` — primary user; keep updated.

---

## Style Contract

Use `node_type="preference"` for prescriptive communication and visual-language
memories that should guide future agent output.

Style nodes are not transcripts. Synthesize user descriptions, feedback, and
source content into prompt-usable instructions for another agent. Keep short
source quotes only when they are valuable as examples.

**Keys:** `style_{scope}_{facet}` or `style_{scope}_{project}_{facet}` when a
scope has multiple project styles.

**Data envelope convention:**

```json
{
  "facet": "voice | tone | lexicon | format | visual | photography | persona",
  "scope": "brand/project/audience this governs",
  "project": "optional project discriminator within the scope",
  "strength": "mandatory | preferred | situational",
  "intent": "one-line purpose",
  "rules": ["operational do-rules"],
  "avoid": ["explicit anti-patterns"],
  "examples": [{"do": "...", "dont": "..."}],
  "tokens": {}
}
```

`facet`, `scope`, and `strength` are required by convention. `project`,
`intent`, `rules`, `avoid`, `examples`, and `tokens` are optional.

Always include an `applies_to` edge to `project_*`, `org_*`, or `user_profile`.
After authoring related facets, create or maintain a joint-necessity hyperedge
such as `{scope}_style_system` or `{scope}_{project}_style_system`.

Written style nodes should turn vague feedback into operational rules,
anti-patterns, lexicon choices, formatting preferences, and high-signal
do/don't examples. Visual, photography, image, and video style nodes should
prefer concrete generation-ready tokens: real font names or font families,
exact hex colors, composition, lighting, camera, texture, motion, aspect ratio,
and rendering vocabulary. Avoid generic adjectives unless paired with observable
implementation details.

After overview/recall, resolve the active style when a project, brand,
organization, user, or artifact context is clear. Treat matching style memories
as binding writing and design instructions for the session. If no active context
is clear, do not pin a style contract.

---

## Relationships

Always include at least one relationship on `hm_store`. Orphan nodes (zero edges) are a hygiene failure.

Describe **why** nodes connect — not bare verbs.

```json
{"relationships": [{"to_key": "tech_qdrant", "relationship": "search pipeline depends on Qdrant for hybrid vector retrieval"}]}
```

### Binary edge spec

```json
{"from_key": "person_alice", "to_key": "project_foo", "relationship": "Alice leads the platform migration", "description": "optional"}
```

Omit `from_key` on `hm_store` — defaults to the stored node's key. Use `to_key` or `target_key`.

### Hyperedge spec (3+ participants)

```json
{
  "relationships": [{
    "participant_keys": ["project_hypermemory", "tech_surrealdb", "tech_qdrant", "tech_redis"],
    "relationship": "platform_component_assembly",
    "description": "These four components ship as one deployable platform unit; removing any one breaks the production stack definition"
  }]
}
```

---

## Hyperedge policy (enforced server-side)

Hyperedges mean **joint necessity** — removing any participant changes the meaning.

| Participants | Rule |
|--------------|------|
| **2** | Auto-downgraded to binary edge — never stored as hyperedge |
| **3** | Allowed only with **80+ char** `description` explaining joint necessity |
| **4–5** | Specific `relationship` label (≥10 chars, not generic) |
| **6–9** | Pass if label is specific |
| **10+** | Encouraged for true assembly/cluster facts |
| **Any** | Generic labels rejected: `relates_to`, `connected`, `associated`, `linked`, `related`, `related_to` |
| **`chat_*`** | **Reserved** — system creates session hyperedges; agents must never use |

**Removal test:** If the group still makes sense after removing one node, use binary edges instead.

**5+ nodes in one joint fact:** one hyperedge with all `participant_keys` — not a mesh of pairs or overlapping triads.

---

## Graph hygiene

`hm_ingest` creates nodes but often skips edges. **After every ingest:**

1. `hm_list_orphans` (limit 20)
2. Enriched orphans → `hm_add_relationships`
3. Noise / empty orphans → `hm_forget`
4. Re-check: `hm_list_orphans` (limit 1) — target zero

Never chain multiple ingests without orphan cleanup between them.

---

## Session hyperedges

The server auto-groups nodes touched in a chat after **5+ tool calls** (`hm_recall`, `hm_store`, `hm_find_related`, `hm_add_relationships`, `hm_ingest`).

- Resume a session: `hm_get_chat_context` (optional `session_id`)
- Do not create `chat_*` relationships yourself

---

## Files (Pro+)

- `hm_upload_file` — only when user explicitly asks (`filename`, `content_base64`)
- `hm_list_files` — query stored files

---

## Timeline (optional)

Not loaded automatically. Use when temporal context matters:

- `hm_timeline_write(summary)` — explicit diary entry
- `hm_timeline(period="24h")` — recent activity
- `hm_timeline(node_key="tech_redis")` — history for one node

Periods: `1h`, `3h`, `6h`, `12h`, `24h`, `7d`, `14d`, `30d`, `90d`, `1y`

---

## Store / skip

**Store:** decisions + rationale, preferences, people/roles, projects, architecture, bugs/fixes, deployments, important facts.

**Skip:** trivial acks, duplicates (update instead), conversation mechanics.

---

## Hard rules

- `hm_get_overview` + `hm_recall` before first substantive response
- `hm_recall` before every `hm_store`
- Use a canonical `node_type` when confident; omit rather than invent one
- Always include `relationships` on store
- Never skip fire-and-forget memory-writer dispatch on any message
- Never wait for, poll, or inspect the memory-writer after dispatch
- Never use `chat_*` relationship names
