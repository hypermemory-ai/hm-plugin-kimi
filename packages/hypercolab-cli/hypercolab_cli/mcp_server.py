"""Local stdio MCP shim. All tools share the same Hypercolab client methods."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import HypercolabClient

mcp = FastMCP(
    "Hypercolab",
    instructions=(
        "Join and sync before planning. Claim intended paths before editing. "
        "Publish progress, rationale summaries, blockers, and completions to the project timeline."
    ),
)


def _call(method: str, *args: Any, **kwargs: Any) -> Any:
    with HypercolabClient() as client:
        return getattr(client, method)(*args, **kwargs)


@mcp.tool()
def colab_join(goal: str = "", agent_name: str = "coding-agent", client_name: str = "mcp") -> dict[str, Any]:
    """Join the Hypercolab project associated with the current Git repository."""

    return _call("join", goal=goal or None, agent_name=agent_name, client_name=client_name)


@mcp.tool()
def colab_sync() -> dict[str, Any]:
    """Get active work, ownership, recent timeline, and touch/do-not-touch guidance."""

    return _call("sync", client_name="mcp")


@mcp.tool()
def colab_claim(paths: list[str], task: str = "") -> dict[str, Any]:
    """Atomically claim repository-relative files or directories."""

    return _call("claim", paths, task)


@mcp.tool()
def colab_check(operations: list[dict[str, Any]], auto_claim: bool = True) -> dict[str, Any]:
    """Check create/modify/rename/delete operations immediately before editing."""

    return _call("check", operations, auto_claim=auto_claim, client_name="mcp")


@mcp.tool()
def colab_update(
    summary: str,
    status: str = "working",
    rationale_summary: str = "",
    paths: list[str] | None = None,
    claim_id: str = "",
) -> dict[str, Any]:
    """Publish meaningful progress and renew an active claim."""

    return _call(
        "update",
        summary,
        status=status,
        rationale_summary=rationale_summary or None,
        paths=paths or [],
        claim_id=claim_id or None,
    )


@mcp.tool()
def colab_finish(
    summary: str,
    outcome: str = "completed",
    changed_files: list[str] | None = None,
    commit_refs: list[str] | None = None,
    tests: list[str] | None = None,
    claim_id: str = "",
) -> dict[str, Any]:
    """Complete, release, abandon, or hand off work and release its claim."""

    return _call(
        "finish",
        summary,
        outcome=outcome,
        changed_files=changed_files or [],
        commit_refs=commit_refs or [],
        tests=tests or [],
        claim_id=claim_id or None,
    )


@mcp.tool()
def colab_log_activity(
    kind: str,
    summary: str,
    rationale_summary: str = "",
    paths: list[str] | None = None,
    commit_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Append a structured, project-scoped development timeline event."""

    return _call(
        "log_activity",
        kind=kind,
        summary=summary,
        source="plugin",
        rationale_summary=rationale_summary or None,
        paths=paths or [],
        commit_refs=commit_refs or [],
    )


@mcp.tool()
def colab_timeline(query: str = "", limit: int = 100) -> dict[str, Any]:
    """Search or read the current project's chronological development record."""

    return _call("timeline", query=query or None, limit=limit)


@mcp.tool()
def colab_graph_search(query: str, limit: int = 25) -> dict[str, Any]:
    """Search durable project knowledge in the project-scoped HyperMemory graph."""

    return _call("graph_search", query, limit=limit)


def run() -> None:
    mcp.run(transport="stdio")
