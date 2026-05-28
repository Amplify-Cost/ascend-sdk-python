"""
SDK-261 — governance violations return a decision instead of raising,
plus backend-vocabulary `result.status` and `result.raw_status`.

Locks in the contracts on ascend/client.py and ascend/models.py:

  CONTRACT 1 — HTTP 403 with a body whose `detail.error` mentions
               'governance' or 'violation' returns
               AuthorizationDecision(decision=DENIED) instead of
               raising AuthorizationError. Detection is on the error
               STRING, not just the status code, so misclassified 403s
               (real auth failures) keep their exception path.

  CONTRACT 2 — The returned decision carries:
               - decision == Decision.DENIED
               - reason populated from detail['detail'] / detail['error']
               - metadata['governance_violation'] == True
               - metadata['correlation_id'] == backend correlation id
               - metadata['raw_status'] == 'denied'
               - metadata['mcp_server_name'] / metadata['model_id']
                 preserved when present (SDK-251 routing fields).

  CONTRACT 3 — Non-governance 403 (no 'governance' / 'violation' in
               detail) still raises AuthorizationError so callers don't
               silently treat a real auth failure as a denied decision.

  CONTRACT 4 — AuthorizationError(message=...) is constructed with a
               readable string, not a Python dict repr — even when the
               backend returns a nested `detail` object.

  CONTRACT 5 — `result.status` returns the CWG / backend vocabulary:
                 PENDING → 'pending_approval'
                 ALLOWED → 'approved'
                 DENIED  → 'denied'
               Always derived from `decision`, never from
               `metadata["status"]` (F5 regression contract from
               SDK-260 still holds).

  CONTRACT 6 — `result.raw_status` exposes the wire status string
               unchanged (e.g. 'auto_approved', 'executed', 'escalated',
               'requires_modification'), and falls back to `.status`
               when the platform did not send a `status` field.

  CONTRACT 7 — Version is 2.6.1 across __init__, constants, and
               pyproject.toml (sentinel sanity check).

The 403 handler lives in `_request`; we exercise it through a
fake-request layer rather than re-implementing the dispatch.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import ascend
from ascend import FailMode
from ascend.client import AscendClient
from ascend.exceptions import AuthorizationError
from ascend.models import AuthorizationDecision, Decision


# ---------------------------------------------------------------------------
# Fake-response helper — `requests.Response`-shaped enough for `_request`.
# ---------------------------------------------------------------------------


def _fake_response(status_code: int, body):
    """Build a stand-in for `requests.Response` covering the surface
    `_request` actually touches: `.status_code`, `.json()`, `.text`,
    `.headers`. The real `requests` library is not invoked."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    resp.json.return_value = body
    resp.text = json.dumps(body) if not isinstance(body, str) else body
    return resp


def _client():
    """Construct a client without touching the network. FailMode.OPEN
    keeps the constructor from blocking on health-check probes."""
    return AscendClient(
        api_key="owkai_test_key_AAAAAAAAAAAAAAAA",
        api_url="https://test.local",
        agent_id="test-agent",
        fail_mode=FailMode.OPEN,
    )


def _drive_403(client, body):
    """Patch the underlying `requests.Session` so the next `_request`
    call sees our fake 403 response, then invoke `_request`. The 403
    handler runs end-to-end. SDK-262 changed `_request`'s contract to
    always return a dict on non-exception paths, so this helper wraps
    the dict in `from_dict()` to mirror what every production caller
    (`evaluate_action`, `get_action_status`, etc.) does immediately
    after `_request`. Net result: the test still observes the final
    caller-facing `AuthorizationDecision`."""
    client._session = MagicMock()
    client._session.request.return_value = _fake_response(403, body)
    out = client._request("POST", "/test", data={})
    if isinstance(out, dict):
        return AuthorizationDecision.from_dict(out)
    return out


# ---------------------------------------------------------------------------
# CONTRACT 1 + 2 — governance 403 returns DENIED decision with metadata
# ---------------------------------------------------------------------------


class TestContract1And2GovernanceReturnsDecision:
    def test_mcp_governance_returns_decision(self):
        body = {
            "detail": {
                "error": "MCP server governance violation",
                "detail": "MCP server is not registered. Register via "
                          "POST /mcp-servers before submitting governed "
                          "actions.",
                "mcp_server_name": "unregistered-server-xyz",
                "correlation_id": "action_20260429_015457_68ba629f",
            }
        }
        result = _drive_403(_client(), body)

        assert isinstance(result, AuthorizationDecision)
        assert result.decision == Decision.DENIED
        assert "not registered" in (result.reason or "").lower()
        assert result.metadata.get("governance_violation") is True
        assert result.metadata.get("correlation_id") == \
            "action_20260429_015457_68ba629f"
        assert result.metadata.get("mcp_server_name") == \
            "unregistered-server-xyz"
        assert result.metadata.get("raw_status") == "denied"

    def test_model_governance_returns_decision(self):
        body = {
            "detail": {
                "error": "Model governance violation",
                "detail": "Model is not registered in the organization "
                          "model registry. Register via Model Registry "
                          "before using in governed actions.",
                "model_id": "gpt-4-production",
                "correlation_id": "action_20260429_015457_517b81b1",
            }
        }
        result = _drive_403(_client(), body)

        assert isinstance(result, AuthorizationDecision)
        assert result.decision == Decision.DENIED
        assert "not registered" in (result.reason or "").lower()
        assert result.metadata.get("governance_violation") is True
        assert result.metadata.get("model_id") == "gpt-4-production"
        assert result.metadata.get("correlation_id") == \
            "action_20260429_015457_517b81b1"

    def test_governance_does_not_raise(self):
        """The whole point: callers stop wrapping in try/except for
        expected denial outcomes."""
        body = {
            "detail": {
                "error": "Generic governance violation",
                "detail": "Something governance",
                "correlation_id": "test-corr-1",
            }
        }
        # Should NOT raise.
        result = _drive_403(_client(), body)
        assert result.decision == Decision.DENIED

    def test_status_property_on_governance_decision_is_denied(self):
        body = {
            "detail": {
                "error": "MCP server governance violation",
                "detail": "Unregistered",
                "mcp_server_name": "x",
                "correlation_id": "c",
            }
        }
        result = _drive_403(_client(), body)
        assert result.status == "denied"


# ---------------------------------------------------------------------------
# CONTRACT 3 — non-governance 403 still raises
# ---------------------------------------------------------------------------


class TestContract3NonGovernance403StillRaises:
    def test_plain_403_string_detail_raises(self):
        body = {"detail": "Forbidden"}
        with pytest.raises(AuthorizationError) as exc_info:
            _drive_403(_client(), body)
        assert "Forbidden" in str(exc_info.value)

    def test_403_with_dict_detail_no_governance_keyword_raises(self):
        body = {
            "detail": {
                "error": "Permission denied",
                "detail": "API key not authorised for this tenant",
            }
        }
        with pytest.raises(AuthorizationError) as exc_info:
            _drive_403(_client(), body)
        # The message should be the readable inner detail string,
        # not the raw dict.
        assert "API key not authorised" in str(exc_info.value)
        assert "{" not in str(exc_info.value), (
            "AuthorizationError stringified to dict repr — "
            "SDK-261 contract: must extract a readable string."
        )

    def test_403_with_empty_body_raises(self):
        body = {}
        with pytest.raises(AuthorizationError):
            _drive_403(_client(), body)


# ---------------------------------------------------------------------------
# CONTRACT 4 — message is readable string, never dict repr
# ---------------------------------------------------------------------------


class TestContract4ReadableErrorMessage:
    def test_message_extracted_from_nested_detail(self):
        body = {
            "detail": {
                "error": "Auth failure",
                "detail": "JWT signature mismatch",
            }
        }
        with pytest.raises(AuthorizationError) as exc_info:
            _drive_403(_client(), body)
        msg = str(exc_info.value)
        assert "JWT signature mismatch" in msg
        # Must not contain the dict repr braces.
        assert "{'error':" not in msg


# ---------------------------------------------------------------------------
# CONTRACT 5 — status property returns backend vocabulary
# ---------------------------------------------------------------------------


class TestContract5StatusBackendVocabulary:
    def test_pending_returns_pending_approval(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.PENDING)
        assert ad.status == "pending_approval"

    def test_allowed_returns_approved(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.ALLOWED)
        assert ad.status == "approved"

    def test_denied_returns_denied(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.DENIED)
        assert ad.status == "denied"

    def test_status_is_string(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.PENDING)
        assert type(ad.status) is str

    def test_cwg_pending_approval_check_passes(self):
        """The exact assertion the CWG test plan runs."""
        ad = AuthorizationDecision(action_id="x", decision=Decision.PENDING)
        assert ad.status == "pending_approval"

    def test_status_property_ignores_metadata_post_261(self):
        """SDK-260 F5 regression contract still holds under the new
        vocabulary: `.status` is derived from `.decision`, never from
        `metadata["status"]`."""
        ad = AuthorizationDecision(
            action_id="x",
            decision=Decision.ALLOWED,
            metadata={"status": "denied"},  # adversarial
        )
        assert ad.status == "approved"
        # Metadata access still returns the dict's value — both paths
        # coexist, they just don't share state.
        assert ad.metadata.get("status") == "denied"


# ---------------------------------------------------------------------------
# CONTRACT 6 — raw_status property
# ---------------------------------------------------------------------------


class TestContract6RawStatus:
    def test_raw_status_property_present(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.PENDING)
        assert hasattr(ad, "raw_status")

    def test_raw_status_falls_back_to_status_when_absent(self):
        ad = AuthorizationDecision(action_id="x", decision=Decision.PENDING)
        # No raw_status in metadata → fall back to the normalised value.
        assert ad.raw_status == "pending_approval"

    def test_raw_status_surfaces_auto_approved(self):
        """The platform sometimes returns 'auto_approved' which the
        v2.0 enum collapses to ALLOWED. raw_status must surface the
        original wire string."""
        wire = {
            "decision": "approved",   # mapped to ALLOWED by from_dict
            "status": "auto_approved",
            "action_id": "1",
        }
        ad = AuthorizationDecision.from_dict(wire)
        assert ad.decision == Decision.ALLOWED
        assert ad.status == "approved"
        assert ad.raw_status == "auto_approved"

    def test_raw_status_surfaces_executed(self):
        wire = {"decision": "approved", "status": "executed", "action_id": "1"}
        ad = AuthorizationDecision.from_dict(wire)
        assert ad.raw_status == "executed"

    def test_raw_status_surfaces_escalated(self):
        wire = {"decision": "pending", "status": "escalated", "action_id": "1"}
        ad = AuthorizationDecision.from_dict(wire)
        assert ad.raw_status == "escalated"

    def test_raw_status_surfaces_pending_approval(self):
        wire = {"status": "pending_approval", "action_id": "1"}
        ad = AuthorizationDecision.from_dict(wire)
        assert ad.decision == Decision.PENDING  # collapsed
        assert ad.status == "pending_approval"  # via .status mapping
        # raw_status from metadata reflects the wire value (same here).
        assert ad.raw_status == "pending_approval"

    def test_raw_status_does_not_clobber_caller_metadata(self):
        """If a caller pre-seeds metadata['raw_status'], from_dict
        should not overwrite it (setdefault contract)."""
        wire = {
            "status": "executed",
            "action_id": "1",
            "metadata": {"raw_status": "caller_supplied"},
        }
        ad = AuthorizationDecision.from_dict(wire)
        assert ad.raw_status == "caller_supplied"


# ---------------------------------------------------------------------------
# CONTRACT 7 — version sanity
# ---------------------------------------------------------------------------


class TestContract7Version:
    def test_version_is_2_6_2(self):
        # SDK-262 bumped 2.6.1 → 2.6.2 (BUG-02-04/05 + kill-switch
        # fail-secure + Decision enum expansion).
        assert ascend.__version__ == "2.7.0"

    def test_constants_version_matches(self):
        from ascend.constants import SDK_VERSION
        assert SDK_VERSION == "2.7.0"
