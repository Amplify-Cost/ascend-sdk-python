"""SEC-REL-001: network-isolated mock transport for executable doc blocks.

Installs the mock by monkey-patching `requests.Session.send` before the SDK
is imported. DNS resolution is hard-blocked at the socket level so any
accidental non-mocked path fails loud.

Canned-response policy: return a minimally valid AuthorizationDecision
shape for every POST /api/v1/actions/submit. Other endpoints return an
empty-but-schema-safe response.
"""
from __future__ import annotations

import contextlib
import json
import socket
import os
from typing import Any, Dict

_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "contract-test.invalid"}

_SESSION_BACKUP: Dict[str, Any] = {}
_SOCKET_BACKUP: Dict[str, Any] = {}


def _canned_response_for(url: str, method: str) -> Dict[str, Any]:
    if "/actions/submit" in url or url.endswith("/actions"):
        return {
            "action_id": "contract-test-action-1",
            "decision": "allowed",
            "risk_score": 10,
            "risk_level": "low",
            "reason": "contract-test mock response",
            "execution_allowed": True,
        }
    if "/register" in url:
        return {"status": "registered", "agent_id": "contract-test-agent"}
    if "/health" in url or "/status" in url:
        return {"status": "ok", "version": "contract-test"}
    return {"status": "ok"}


class _FakeResponse:
    def __init__(self, url: str, method: str):
        self.status_code = 200
        self._body = _canned_response_for(url, method)
        self.url = url
        self.headers = {"content-type": "application/json"}
        self.text = json.dumps(self._body)
        self.content = self.text.encode()

    def json(self) -> Dict[str, Any]:
        return self._body

    def raise_for_status(self) -> None:
        return None


def _fake_send(self, request, **kwargs):
    return _FakeResponse(request.url, request.method)


def _blocked_getaddrinfo(host, *args, **kwargs):
    if host in _ALLOWED_HOSTS or (isinstance(host, str) and (host.startswith("127.") or host == "::1")):
        return _SOCKET_BACKUP["getaddrinfo"](host, *args, **kwargs)
    raise OSError(
        f"SEC-REL-001: outbound network blocked in contract-test sandbox (host={host!r})"
    )


@contextlib.contextmanager
def network_sandbox():
    """Patch requests.Session.send and socket.getaddrinfo for the block of code."""
    try:
        import requests
    except ImportError:
        requests = None  # type: ignore

    _SOCKET_BACKUP["getaddrinfo"] = socket.getaddrinfo
    socket.getaddrinfo = _blocked_getaddrinfo  # type: ignore

    if requests is not None:
        _SESSION_BACKUP["send"] = requests.Session.send
        requests.Session.send = _fake_send  # type: ignore

    prior_env = {}
    for k, v in {
        "ASCEND_API_KEY": "fake_contract_test_key_do_not_use",
        "ASCEND_API_URL": "https://contract-test.invalid",
        "ASCEND_AGENT_ID": "contract-test-agent",
        "OWKAI_API_KEY": "fake_contract_test_key_do_not_use",
        "OWKAI_API_URL": "https://contract-test.invalid",
    }.items():
        prior_env[k] = os.environ.get(k)
        os.environ[k] = v

    try:
        yield
    finally:
        socket.getaddrinfo = _SOCKET_BACKUP["getaddrinfo"]  # type: ignore
        if requests is not None and "send" in _SESSION_BACKUP:
            requests.Session.send = _SESSION_BACKUP["send"]  # type: ignore
        for k, v in prior_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
