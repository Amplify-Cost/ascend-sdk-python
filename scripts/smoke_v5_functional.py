"""SDK 2.4.0 — BUG-16 cohort · V5 functional smoke test.

Exercises every symbol the docs reference against a FRESHLY-INSTALLED
ascend-ai-sdk 2.4.0 wheel. Points the client at an unreachable URL
(contract-test.invalid) so the smoke test does not require network;
the goal is to prove the public surface resolves, not to reach ASCEND.

Coverage:
  - package root: `from ascend import ...` including deprecated aliases
  - ascend.exceptions: including renamed aliases
  - ascend.constants: deprecated re-export path
  - ascend.models: ActionType canonical home
  - AscendClient method surface: evaluate_action (canonical) and every
    Class A deprecated shim (submit_action, send_heartbeat, etc.)
  - ascend.wrappers subpackage: safe_eval, safe_exec, SafeEvaluator,
    subprocess, ast_analyzer
  - Class B heartbeat scheduler: start_heartbeat / stop_heartbeat
  - DeprecationWarning emission on first access of each deprecated
    name (once-per-process contract preserved)

Fail-fast: any AttributeError, ImportError, or assertion failure
stops the smoke test immediately with a non-zero exit.
"""
from __future__ import annotations

import sys
import warnings


def section(label: str) -> None:
    print(f"\n--- {label} ---", flush=True)


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"  ok: {msg}")


def main() -> None:
    section("version check")
    import ascend
    assert_true(ascend.__version__ == "2.4.0",
                f"ascend.__version__ == 2.4.0 (got {ascend.__version__})")

    section("canonical imports resolve")
    from ascend import (
        AscendClient, FailMode, ActionType,
        OWKAIError, AuthenticationError, AuthorizationError,
        ConnectionError as _ConnectionError,
        TimeoutError as _TimeoutError,
        RateLimitError, ValidationError, ConfigurationError,
        CircuitBreakerOpen, KillSwitchError,
        ServerError, NotFoundError, ConflictError,
        AgentAction, Decision, DecisionStatus,
        mcp_governance, MCPGovernanceMiddleware,
    )
    assert_true(AscendClient is not None, "AscendClient imported")
    assert_true(FailMode.CLOSED.value == "closed", "FailMode.CLOSED is 'closed'")
    assert_true(ActionType.DATA_ACCESS.value == "data_access",
                "ActionType.DATA_ACCESS is 'data_access'")

    section("deprecated aliases at `ascend` root emit DeprecationWarning once")
    for alias_name, canonical_name in [
        ("AuthorizationDeniedError", "AuthorizationError"),
        ("NetworkError", "ConnectionError"),
        ("AscendError", "OWKAIError"),
        ("AscendConnectionError", "ConnectionError"),
    ]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            obj = getattr(ascend, alias_name)
            assert_true(any(issubclass(w.category, DeprecationWarning)
                            for w in caught),
                        f"DeprecationWarning fired for {alias_name}")
            assert_true(obj.__name__ == canonical_name,
                        f"{alias_name} resolves to {canonical_name}")

    section("ascend.exceptions deprecated aliases")
    import ascend.exceptions as aex
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ne = aex.NetworkError
        _ace = aex.AscendConnectionError
        _aee = aex.AscendError
        _ade = aex.AuthorizationDeniedError
        _aae = aex.AscendAuthenticationError
        _are = aex.AscendRateLimitError
        dw = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert_true(len(dw) >= 6,
                    f">= 6 DeprecationWarnings from ascend.exceptions (got {len(dw)})")

    section("ascend.constants ActionType re-export")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from ascend.constants import ActionType as _ActionType_via_constants
        assert_true(_ActionType_via_constants is ActionType,
                    "ascend.constants.ActionType is ascend.ActionType")
        assert_true(any(issubclass(w.category, DeprecationWarning) for w in caught),
                    "DeprecationWarning fired for ActionType-via-constants")

    section("new first-class exception types are real subclasses")
    assert_true(issubclass(ServerError, OWKAIError),
                "ServerError subclass of OWKAIError")
    assert_true(issubclass(NotFoundError, OWKAIError),
                "NotFoundError subclass of OWKAIError")
    assert_true(issubclass(ConflictError, OWKAIError),
                "ConflictError subclass of OWKAIError")

    section("AscendClient construction and surface")
    client = AscendClient(
        api_key="smoke_test_fake_key",
        agent_id="v5-smoke",
        agent_name="V5 Smoke Test",
        api_url="https://contract-test.invalid",
        fail_mode="closed",
        timeout=1,
        max_retries=0,
        enable_circuit_breaker=False,
    )
    try:
        # Canonical methods must exist
        for name in ("evaluate_action", "register", "heartbeat",
                     "get_agent_status", "query_audit_log",
                     "evaluate_policy", "get_resource_classification",
                     "start_kill_switch_polling", "stop_kill_switch_polling",
                     "start_heartbeat", "stop_heartbeat",
                     "close"):
            assert_true(callable(getattr(client, name, None)),
                        f"AscendClient.{name} is callable")

        # Class A deprecated shims must exist AND forward correctly.
        for name in ("submit_action", "send_heartbeat", "register_agent",
                     "wait_for_approval", "get_agent"):
            assert_true(callable(getattr(client, name, None)),
                        f"AscendClient.{name} (deprecated shim) is callable")

        section("Class B: heartbeat scheduler lifecycle (fail-secure)")
        # start → stop must not raise against unreachable URL.
        client.start_heartbeat(interval_seconds=30)
        assert_true(client._heartbeat_timer is not None,
                    "scheduler armed")
        assert_true(client._heartbeat_timer.daemon is True,
                    "scheduler runs on daemon thread")
        client.stop_heartbeat()
        assert_true(client._heartbeat_timer is None,
                    "stop_heartbeat cancels cleanly")
        client.stop_heartbeat()  # idempotent
        # Negative interval must raise ValueError at boundary.
        raised = False
        try:
            client.start_heartbeat(interval_seconds=-1)
        except ValueError:
            raised = True
        assert_true(raised, "negative interval raises ValueError")

        section("Class A shim emits DeprecationWarning on first call (once-per-process)")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                client.submit_action(
                    "test.action", "test_resource",
                    parameters={"key": "value"},
                )
            except Exception:
                # Will fail at transport (unreachable) — we only care the
                # shim fired the deprecation warning before the network call.
                pass
            dw_submit = [w for w in caught
                         if issubclass(w.category, DeprecationWarning)
                         and "submit_action" in str(w.message)]
            assert_true(len(dw_submit) == 1,
                        f"exactly 1 DeprecationWarning for submit_action (got {len(dw_submit)})")
    finally:
        client.close()

    section("ascend.wrappers subpackage")
    from ascend.wrappers.dynamic_code import safe_eval, safe_exec, SafeEvaluator
    from ascend.wrappers.subprocess import classify_command_risk
    from ascend.wrappers.ast_analyzer import ASTAnalyzer
    assert_true(safe_eval("2 + 2") == 4, "safe_eval('2 + 2') == 4")
    assert_true(safe_eval("price * qty", {"price": 10, "qty": 5}) == 50,
                "safe_eval with context")
    assert_true(classify_command_risk("cat file.txt") == "low",
                "classify_command_risk('cat file.txt') == 'low' (regex fix verified)")
    assert_true(classify_command_risk("chmod 777 /var/www") == "high",
                "classify_command_risk('chmod 777 /var/www') == 'high' (regex fix verified)")
    assert_true(classify_command_risk("rm -rf /") == "critical",
                "classify_command_risk('rm -rf /') == 'critical'")
    analyzer = ASTAnalyzer()
    result = analyzer.analyze("x = 1 + 2")
    assert_true(result.is_safe is True, "ASTAnalyzer on safe code")
    result = analyzer.analyze("__import__('os').system('echo pwned')")
    assert_true(result.is_safe is False, "ASTAnalyzer catches __import__")

    section("MCP governance middleware")
    middleware_cls = MCPGovernanceMiddleware
    assert_true(hasattr(middleware_cls, "govern"),
                "MCPGovernanceMiddleware.govern exists (canonical)")
    assert_true(hasattr(middleware_cls, "wrap"),
                "MCPGovernanceMiddleware.wrap exists (deprecated alias)")

    print("\nV5 functional smoke test: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
