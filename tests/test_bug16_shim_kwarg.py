"""BUG-16-SHIM-KWARG regression — AscendClient.submit_action kwarg syntax.

SDK 2.4.0 shipped the submit_action → evaluate_action forwarding shim
(BUG-16 cohort) that worked for positional calls but raised TypeError
"got multiple values for keyword argument 'action_type'" on kwarg
syntax. Alan's Section 6.2 test plan uses kwarg syntax, blocking his
Wave 1 re-run.

This module pins:
  (1) positional calls still work and still emit DeprecationWarning,
  (2) kwarg calls forward correctly to evaluate_action (the 2.4.2 fix),
  (3) mixed-conflicting calls raise a TypeError attributed to
      submit_action() identifying the ambiguity (not the silent
      wins-latest behavior, and not the opaque collision from deep
      inside evaluate_action).
"""
from __future__ import annotations

import warnings
from unittest.mock import patch

import pytest

from ascend import AscendClient


def _stub_request(*args, **kwargs):
    return {
        "action_id": "t-stub",
        "decision": "allowed",
        "status": "allowed",
        "reason": "stub",
        "risk_score": 0,
        "ascend_version_hash": "stub",
    }


def _client() -> AscendClient:
    return AscendClient(
        api_key="stub-key",
        api_url="http://localhost:1/",
        agent_id="bug16-shim-kwarg-test",
    )


def test_submit_action_positional_still_works():
    c = _client()
    with patch.object(c, "_request", side_effect=_stub_request), \
         patch.object(c, "evaluate_action", wraps=c.evaluate_action) as ev, \
         warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        c.submit_action("database.read", "reports_db")

    assert any(
        issubclass(wi.category, DeprecationWarning) and "submit_action" in str(wi.message)
        for wi in w
    ), "positional submit_action must emit DeprecationWarning"
    assert ev.call_args.kwargs.get("action_type") == "database.read"
    assert ev.call_args.kwargs.get("resource") == "reports_db"


def test_submit_action_kwarg_syntax_works():
    """BUG-16-SHIM-KWARG fix — the call that raised in 2.4.1."""
    c = _client()
    with patch.object(c, "_request", side_effect=_stub_request), \
         patch.object(c, "evaluate_action", wraps=c.evaluate_action) as ev:
        c.submit_action(action_type="database.read", resource="reports_db")

    assert ev.call_args.kwargs.get("action_type") == "database.read"
    assert ev.call_args.kwargs.get("resource") == "reports_db"


def test_submit_action_mixed_conflicting_raises():
    c = _client()
    with pytest.raises(TypeError) as excinfo:
        c.submit_action(
            "database.read",
            action_type="database.write",
            resource="reports_db",
        )
    message = str(excinfo.value)
    assert "action_type" in message
    assert "positionally" in message.lower() or "keyword" in message.lower(), (
        f"TypeError must identify ambiguity between positional and kwarg, got: {message!r}"
    )
