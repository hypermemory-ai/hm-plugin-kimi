"""OAuth 2.1 PKCE authentication for Hypercolab."""

from __future__ import annotations

import base64
import hashlib
import http.server
import secrets
import urllib.parse
import webbrowser
from typing import Any

import httpx

from .config import Config, load_config, save_config


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class _Callback(http.server.BaseHTTPRequestHandler):
    code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _Callback.code = params.get("code", [None])[0]
        _Callback.error = params.get("error_description", params.get("error", [None]))[0]
        self.send_response(200 if _Callback.code else 400)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        message = (
            "Authenticated. You can close this tab." if _Callback.code else f"Authentication failed: {_Callback.error}"
        )
        self.wfile.write(
            f"<html><body style='font-family:system-ui;padding:40px'><h2>{message}</h2></body></html>".encode()
        )

    def log_message(self, _format: str, *args: Any) -> None:
        return


def login() -> Config:
    config = load_config(require_auth=False)
    verifier, challenge = _pkce()
    server = http.server.HTTPServer(("127.0.0.1", 0), _Callback)
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}"
    registration = httpx.post(
        f"{config.api_url}/register",
        json={
            "client_name": "Hypercolab CLI",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
        timeout=15,
    )
    registration.raise_for_status()
    client_id = registration.json()["client_id"]
    auth_url = (
        f"{config.api_url}/authorize?response_type=code&client_id={urllib.parse.quote(client_id)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}&code_challenge={challenge}"
        "&code_challenge_method=S256&scope=memory:read+memory:write+memory:admin"
    )
    print(f"Open this URL to authenticate:\n{auth_url}")
    webbrowser.open(auth_url)
    _Callback.code = None
    _Callback.error = None
    server.timeout = 120
    while _Callback.code is None and _Callback.error is None:
        server.handle_request()
    server.server_close()
    if not _Callback.code:
        raise RuntimeError(_Callback.error or "No authorization code received")
    response = httpx.post(
        f"{config.api_url}/token",
        json={
            "grant_type": "authorization_code",
            "code": _Callback.code,
            "code_verifier": verifier,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
        },
        timeout=15,
    )
    response.raise_for_status()
    tokens = response.json()
    config.access_token = tokens["access_token"]
    config.refresh_token = tokens.get("refresh_token", "")
    config.client_id = client_id
    save_config(config)
    return config


def refresh(config: Config) -> bool:
    if not config.refresh_token or not config.client_id:
        return False
    response = httpx.post(
        f"{config.api_url}/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": config.refresh_token,
            "client_id": config.client_id,
        },
        timeout=15,
    )
    if response.status_code >= 400:
        return False
    tokens = response.json()
    config.access_token = tokens.get("access_token", "")
    config.refresh_token = tokens.get("refresh_token", config.refresh_token)
    save_config(config)
    return bool(config.access_token)
