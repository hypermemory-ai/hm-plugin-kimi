"""Shared HTTP client used by direct CLI commands, hooks, and MCP tools."""

from __future__ import annotations

import json
from typing import Any, Self

import httpx

from .auth import refresh
from .config import Config, load_config, remember_check, remember_repository, repository_state
from .git import GitContext, discover_git_context


class HypercolabError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 0, detail: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class HypercolabClient:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or load_config()
        self.http = httpx.Client(base_url=f"{self.config.api_url}/api/colab", timeout=30)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Authorization": f"Bearer {self.config.auth_token}"}
        try:
            response = self.http.request(method, path, headers=headers, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise HypercolabError("Hypercolab service is unavailable") from exc
        if response.status_code == 401 and refresh(self.config):
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
            response = self.http.request(method, path, headers=headers, **kwargs)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if response.status_code >= 400:
            detail = data.get("detail", data) if isinstance(data, dict) else data
            raise HypercolabError(str(detail), status_code=response.status_code, detail=detail)
        return data

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._request("POST", path, json=body)

    def join(
        self,
        *,
        git: GitContext | None = None,
        goal: str | None = None,
        agent_name: str = "coding-agent",
        client_name: str = "cli",
    ) -> dict[str, Any]:
        git = git or discover_git_context()
        result = self.post(
            "/join",
            {
                "repository_remote": git.remote,
                "agent_name": agent_name,
                "client_name": client_name,
                "branch": git.branch,
                "worktree": git.worktree,
                "goal": goal,
            },
        )
        remember_repository(git.remote, project=result["project"], session=result["session"])
        return result

    def ensure_session(self, git: GitContext | None = None, *, client_name: str = "cli") -> tuple[GitContext, dict]:
        git = git or discover_git_context()
        state = repository_state(git.remote)
        if state and state.get("session", {}).get("session_id"):
            return git, state
        joined = self.join(git=git, client_name=client_name)
        return git, {"project": joined["project"], "session": joined["session"]}

    def sync(self, *, git: GitContext | None = None, client_name: str = "cli") -> dict[str, Any]:
        _, state = self.ensure_session(git, client_name=client_name)
        return self.get(f"/sync/{state['session']['session_id']}")

    def claim(self, paths: list[str], task: str = "", *, git: GitContext | None = None) -> dict[str, Any]:
        _, state = self.ensure_session(git)
        return self.post(
            "/claim",
            {"session_id": state["session"]["session_id"], "paths": paths, "task": task, "ttl_seconds": 600},
        )

    def check(
        self,
        operations: list[dict[str, Any]],
        *,
        git: GitContext | None = None,
        auto_claim: bool = True,
        client_name: str = "cli",
    ) -> dict[str, Any]:
        git, state = self.ensure_session(git, client_name=client_name)
        result = self.post(
            "/check",
            {"session_id": state["session"]["session_id"], "operations": operations, "auto_claim": auto_claim},
        )
        remember_check(git.remote, operations, result)
        return result

    def update(
        self,
        summary: str,
        *,
        status: str = "working",
        rationale_summary: str | None = None,
        paths: list[str] | None = None,
        claim_id: str | None = None,
        git: GitContext | None = None,
    ) -> dict[str, Any]:
        _, state = self.ensure_session(git)
        return self.post(
            "/update",
            {
                "session_id": state["session"]["session_id"],
                "claim_id": claim_id,
                "status": status,
                "summary": summary,
                "rationale_summary": rationale_summary,
                "paths": paths or [],
            },
        )

    def finish(
        self,
        summary: str,
        *,
        outcome: str = "completed",
        changed_files: list[str] | None = None,
        commit_refs: list[str] | None = None,
        tests: list[str] | None = None,
        claim_id: str | None = None,
        git: GitContext | None = None,
    ) -> dict[str, Any]:
        _, state = self.ensure_session(git)
        return self.post(
            "/finish",
            {
                "session_id": state["session"]["session_id"],
                "claim_id": claim_id,
                "outcome": outcome,
                "summary": summary,
                "changed_files": changed_files or [],
                "commit_refs": commit_refs or [],
                "tests": tests or [],
            },
        )

    def log_activity(
        self,
        *,
        kind: str,
        summary: str,
        source: str = "cli",
        rationale_summary: str | None = None,
        paths: list[str] | None = None,
        commit_refs: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        git: GitContext | None = None,
    ) -> dict[str, Any]:
        git, state = self.ensure_session(git)
        return self.post(
            f"/projects/{state['project']['project_id']}/activity",
            {
                "session_id": state["session"]["session_id"],
                "source": source,
                "kind": kind,
                "summary": summary,
                "rationale_summary": rationale_summary,
                "branch": git.branch,
                "worktree": git.worktree,
                "paths": paths or [],
                "commit_refs": commit_refs or [],
                "metadata": metadata or {},
            },
        )

    def timeline(self, *, query: str | None = None, limit: int = 100, git: GitContext | None = None):
        _, state = self.ensure_session(git)
        return self.post(
            f"/projects/{state['project']['project_id']}/timeline",
            {"query": query, "limit": limit, "offset": 0},
        )

    def graph_search(self, query: str, *, limit: int = 25, git: GitContext | None = None):
        _, state = self.ensure_session(git)
        return self.post(f"/projects/{state['project']['project_id']}/graph/search", {"query": query, "limit": limit})


def compact_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)
