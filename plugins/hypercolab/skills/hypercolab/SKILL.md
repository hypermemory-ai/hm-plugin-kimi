---
name: hypercolab
description: Coordinate work in a Hypercolab-enabled Git repository. Join and sync before planning, claim paths before edits, respect other agents' ownership, and record meaningful project activity.
---

# Hypercolab

Use this skill whenever the current Git repository resolves to a Hypercolab project.

1. Call `colab_join` at the start of a coding session, then read the returned brief.
2. Call `colab_sync` before accepting or decomposing work.
3. Call `colab_claim` for planned directories or file sets. File edits may auto-claim a free file through the hook.
4. Treat `do_not_touch` paths as blocked. Coordinate or request a handoff instead of bypassing a conflict.
5. Call `colab_update` when the plan, rationale, scope, status, or blocker changes.
6. Use `colab_log_activity` for architectural choices, rejected alternatives, discoveries, test results, or release activity.
7. Call `colab_finish` before stopping completed, released, abandoned, or handed-off work.

For work where timeline maintenance would distract the implementation agent,
delegate one bounded coordination writer and wait for it. Follow
[references/coordination-agent.md](references/coordination-agent.md). Keep
`colab_join`, `colab_sync`, and path claims on the main agent because their
results directly affect planning and write safety.

Never put hidden reasoning, secrets, raw source contents, or full command output in timeline summaries.

If the `hypercolab` executable is missing, tell the developer to install the
bundled CLI/MCP shim from the marketplace repository and run `hypercolab login`.
Repositories that are not registered with HyperColab remain unaffected.
