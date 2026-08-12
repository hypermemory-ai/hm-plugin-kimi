"""Local Hypercolab configuration, credentials and repository session state."""

from __future__ import annotations

import json
import logging
import os
import posixpath
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://api.hypermemory.io"
CONFIG_DIR = Path(os.environ.get("HYPERCOLAB_CONFIG_DIR", Path.home() / ".config" / "hypercolab"))
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE = CONFIG_DIR / "state.json"
QUEUE_FILE = CONFIG_DIR / "timeline-queue.jsonl"
KEYRING_SERVICE = "io.hypermemory.hypercolab"


@dataclass(slots=True)
class Config:
    api_url: str = DEFAULT_API_URL
    access_token: str = ""
    refresh_token: str = ""
    client_id: str = ""

    @property
    def auth_token(self) -> str:
        return os.environ.get("HYPERCOLAB_API_TOKEN") or os.environ.get("HYPERMEMORY_API_KEY") or self.access_token


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_DIR.chmod(0o700)
    except OSError:
        pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("config_read_failed: %s", exc)
        return {}


def _keyring_get(name: str) -> str:
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, name) or ""
    except Exception as exc:  # noqa: BLE001 - keyring backends raise platform-specific errors
        logger.debug("keyring_read_failed: %s", exc)
        return ""


def _keyring_set(name: str, value: str) -> None:
    try:
        import keyring

        if value:
            keyring.set_password(KEYRING_SERVICE, name, value)
        else:
            keyring.delete_password(KEYRING_SERVICE, name)
    except Exception as exc:  # noqa: BLE001 - keyring backends raise platform-specific errors
        logger.debug("keyring_write_failed: %s", exc)


def load_config(*, require_auth: bool = True) -> Config:
    data = _read_json(CONFIG_FILE)
    config = Config(
        api_url=(os.environ.get("HYPERCOLAB_API_URL") or data.get("api_url") or DEFAULT_API_URL).rstrip("/"),
        access_token=_keyring_get("access_token") or data.get("access_token", ""),
        refresh_token=_keyring_get("refresh_token") or data.get("refresh_token", ""),
        client_id=data.get("client_id", ""),
    )
    if require_auth and not config.auth_token:
        raise RuntimeError("Not authenticated. Run `hypercolab login` or set HYPERCOLAB_API_TOKEN.")
    return config


def save_config(config: Config) -> None:
    _ensure_dir()
    _keyring_set("access_token", config.access_token)
    _keyring_set("refresh_token", config.refresh_token)
    data = {"api_url": config.api_url, "client_id": config.client_id}
    # Keyring-less/headless installations need a restricted fallback.
    if config.access_token and not _keyring_get("access_token"):
        data["access_token"] = config.access_token
        data["refresh_token"] = config.refresh_token
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def clear_credentials() -> None:
    current = load_config(require_auth=False)
    current.access_token = ""
    current.refresh_token = ""
    current.client_id = ""
    save_config(current)


def load_state() -> dict[str, Any]:
    return _read_json(STATE_FILE)


def save_state(state: dict[str, Any]) -> None:
    _ensure_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    try:
        STATE_FILE.chmod(0o600)
    except OSError:
        pass


def remember_repository(remote: str, *, project: dict[str, Any], session: dict[str, Any]) -> None:
    state = load_state()
    state.setdefault("repositories", {})[remote] = {"project": project, "session": session}
    save_state(state)


def repository_state(remote: str) -> dict[str, Any] | None:
    return load_state().get("repositories", {}).get(remote)


def remember_check(remote: str, operations: list[dict[str, Any]], result: dict[str, Any]) -> None:
    """Cache only server-approved, leased write scopes for brief outages."""

    state = load_state()
    repository = state.setdefault("repositories", {}).setdefault(remote, {})
    leases = repository.setdefault("leases", {})
    for operation, decision in zip(operations, result.get("decisions", []), strict=False):
        expires_at = decision.get("lease_expires_at")
        if decision.get("decision") != "allow" or not decision.get("claim_id") or not expires_at:
            continue
        leases[_normalized_path(operation["path"])] = {
            "claim_id": decision["claim_id"],
            "lease_expires_at": float(expires_at),
        }
    repository["leases"] = {
        path: lease for path, lease in leases.items() if float(lease.get("lease_expires_at", 0)) > time.time()
    }
    save_state(state)


def operations_have_live_cached_leases(remote: str, operations: list[dict[str, Any]]) -> bool:
    repository = repository_state(remote) or {}
    now = time.time()
    leases = {
        path: lease
        for path, lease in repository.get("leases", {}).items()
        if float(lease.get("lease_expires_at", 0)) > now
    }
    if not leases:
        return False
    for operation in operations:
        if operation.get("operation") == "read":
            continue
        targets = [_normalized_path(operation["path"])]
        if operation.get("destination"):
            targets.append(_normalized_path(operation["destination"]))
        if not all(any(_paths_overlap(target, scope) for scope in leases) for target in targets):
            return False
    return True


def _normalized_path(path: str) -> str:
    value = posixpath.normpath(str(path).replace("\\", "/").removeprefix("./"))
    return value.rstrip("/")


def _paths_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def config_dict(config: Config) -> dict[str, Any]:
    data = asdict(config)
    data["access_token"] = "***" if config.access_token else ""
    data["refresh_token"] = "***" if config.refresh_token else ""
    return data
