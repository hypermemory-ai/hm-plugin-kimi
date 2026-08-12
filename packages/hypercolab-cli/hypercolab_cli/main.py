"""Hypercolab command-line interface."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from . import __version__
from .auth import login as oauth_login
from .client import HypercolabClient, HypercolabError
from .config import clear_credentials, config_dict, load_config, repository_state
from .git import current_commit, discover_git_context
from .hooks import install_git_hooks, record_git_event, run_client_hook, uninstall_git_hooks
from .mcp_server import run as run_mcp

app = typer.Typer(help="Coordinate developers and AI coding agents with project-scoped HyperMemory.")
timeline_app = typer.Typer(help="Read or append project timeline events.")
graph_app = typer.Typer(help="Search the project-scoped HyperMemory graph.")
hooks_app = typer.Typer(help="Install or remove non-blocking Git activity hooks.")
app.add_typer(timeline_app, name="timeline")
app.add_typer(graph_app, name="graph")
app.add_typer(hooks_app, name="hooks")
console = Console(stderr=True)


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def _run(callable_, *args: Any, **kwargs: Any) -> None:
    try:
        with HypercolabClient() as client:
            _print(callable_(client, *args, **kwargs))
    except (HypercolabError, RuntimeError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show the installed version."),
) -> None:
    if version:
        print(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
def login() -> None:
    """Authenticate through HyperMemory OAuth."""

    try:
        config = oauth_login()
        console.print(f"[green]Authenticated[/green] with {config.api_url}")
    except Exception as exc:
        console.print(f"[red]Authentication failed:[/red] {exc}")
        raise typer.Exit(1) from exc


@app.command()
def logout() -> None:
    """Remove local Hypercolab credentials."""

    clear_credentials()
    console.print("Logged out.")


@app.command()
def status() -> None:
    """Show authentication, repository, project, and session status."""

    try:
        config = load_config(require_auth=False)
        git = discover_git_context()
        _print({"config": config_dict(config), "git": git.to_dict(), "state": repository_state(git.remote)})
    except RuntimeError as exc:
        _print({"config": config_dict(load_config(require_auth=False)), "repository": None, "warning": str(exc)})


@app.command()
def doctor() -> None:
    """Check prerequisites without modifying the repository."""

    config = load_config(require_auth=False)
    checks: dict[str, Any] = {
        "hypercolab": __version__,
        "git": shutil.which("git") or False,
        "authenticated": bool(config.auth_token),
        "api_url": config.api_url,
    }
    try:
        checks["repository"] = discover_git_context().to_dict()
    except RuntimeError as exc:
        checks["repository"] = False
        checks["repository_error"] = str(exc)
    _print(checks)
    if not all((checks["git"], checks["authenticated"])):
        raise typer.Exit(1)


@app.command()
def setup(
    client: str = typer.Option("codex", help="OpenAI coding client to configure (codex)."),
) -> None:
    """Configure project-scoped MCP files and install Git timeline hooks."""

    git = discover_git_context()
    if client != "codex":
        raise typer.BadParameter(f"Unknown client: {client}")
    written = []
    root_path = Path(git.root)
    path = root_path / ".codex" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "[mcp_servers.hypercolab]"
    if marker not in existing:
        block = '\n[mcp_servers.hypercolab]\ncommand = "hypercolab"\nargs = ["mcp"]\n'
        path.write_text(existing.rstrip() + block, encoding="utf-8")
    written.append(str(path))
    hooks = install_git_hooks(git.root)
    _print({"configured": written, "git_hooks": hooks})


@app.command()
def join(
    goal: str = typer.Option("", help="Current work goal."),
    agent_name: str = typer.Option("coding-agent"),
    client_name: str = typer.Option("cli"),
) -> None:
    """Join the project associated with the current Git remote."""

    _run(lambda client: client.join(goal=goal or None, agent_name=agent_name, client_name=client_name))


@app.command()
def sync() -> None:
    """Get current work ownership, recent timeline, and path guidance."""

    _run(lambda client: client.sync())


@app.command()
def who() -> None:
    """List active developers and agents."""

    _run(lambda client: {"active_sessions": client.sync().get("active_sessions", [])})


@app.command()
def claim(paths: list[str], task: str = typer.Option("", help="Task or intended outcome.")) -> None:
    """Atomically claim files or directories."""

    _run(lambda client: client.claim(paths, task))


@app.command()
def check(
    paths: list[str],
    operation: str = typer.Option("modify", help="read, create, modify, rename, or delete"),
    auto_claim: bool = typer.Option(True),
) -> None:
    """Check paths immediately before an operation."""

    _run(lambda client: client.check([{"path": path, "operation": operation} for path in paths], auto_claim=auto_claim))


@app.command()
def update(
    summary: str,
    status: str = typer.Option("working"),
    rationale: str = typer.Option(""),
    paths: list[str] = typer.Option(None),
    claim_id: str = typer.Option(""),
) -> None:
    """Publish progress and visible rationale to the project timeline."""

    _run(
        lambda client: client.update(
            summary,
            status=status,
            rationale_summary=rationale or None,
            paths=paths or [],
            claim_id=claim_id or None,
        )
    )


@app.command()
def finish(
    summary: str,
    outcome: str = typer.Option("completed"),
    changed_files: list[str] = typer.Option(None),
    commit: list[str] = typer.Option(None),
    test: list[str] = typer.Option(None),
    claim_id: str = typer.Option(""),
) -> None:
    """Finish, abandon, release, or hand off coordinated work."""

    _run(
        lambda client: client.finish(
            summary,
            outcome=outcome,
            changed_files=changed_files or [],
            commit_refs=commit or [],
            tests=test or [],
            claim_id=claim_id or None,
        )
    )


@app.command()
def release(claim_id: str, summary: str = typer.Option("Released work scope")) -> None:
    """Release a claim without marking the task complete."""

    _run(lambda client: client.finish(summary, outcome="released", claim_id=claim_id))


@timeline_app.callback(invoke_without_command=True)
def timeline_read(ctx: typer.Context, query: str = typer.Option(""), limit: int = typer.Option(100)) -> None:
    """Read or search the project timeline."""

    if ctx.invoked_subcommand is None:
        _run(lambda client: client.timeline(query=query or None, limit=limit))


@timeline_app.command("add")
def timeline_add(
    summary: str,
    kind: str = typer.Option("note.added"),
    rationale: str = typer.Option(""),
    paths: list[str] = typer.Option(None),
) -> None:
    """Append an explicit structured project event."""

    _run(
        lambda client: client.log_activity(
            kind=kind,
            summary=summary,
            rationale_summary=rationale or None,
            paths=paths or [],
        )
    )


@graph_app.command("search")
def graph_search(query: str, limit: int = typer.Option(25)) -> None:
    """Search durable project graph knowledge."""

    _run(lambda client: client.graph_search(query, limit=limit))


@hooks_app.command("install")
def hooks_install() -> None:
    _print({"installed": install_git_hooks()})


@hooks_app.command("uninstall")
def hooks_uninstall() -> None:
    _print({"removed": uninstall_git_hooks()})


@app.command()
def mcp() -> None:
    """Run the local Hypercolab MCP server over stdio."""

    run_mcp()


@app.command(hidden=True)
def hook() -> None:
    raise typer.Exit(run_client_hook())


@app.command("git-event", hidden=True)
def git_event(kind: str) -> None:
    raise typer.Exit(0 if record_git_event(kind) else 1)


@app.command(hidden=True)
def commit() -> None:
    """Print the current commit; useful for hook diagnostics."""

    print(current_commit())


def main() -> None:
    try:
        app()
    except BrokenPipeError:
        sys.stdout.close()


if __name__ == "__main__":
    main()
