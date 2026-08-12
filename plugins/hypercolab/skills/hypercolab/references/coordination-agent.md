# Coordination agent contract

Use one bounded coordination sub-agent when project activity must be recorded
without distracting the main implementation agent. The parent supplies the
visible plan, affected repository-relative paths, current status, test results,
and any public rationale summary.

The coordination agent:

1. Calls `colab_sync` to refresh active work and ownership.
2. Uses `colab_update` for material progress, scope, status, or blocker changes.
3. Uses `colab_log_activity` for decisions, discoveries, test outcomes, commits,
   or release activity that belongs in the project timeline.
4. Calls `colab_finish` only when the parent explicitly says the work is
   completed, released, abandoned, or handed off.
5. Returns a short status and never delegates again.

It never sends secrets, hidden reasoning, raw source, raw diffs, transcripts,
or complete command output to HyperColab.
