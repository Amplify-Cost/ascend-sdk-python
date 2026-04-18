"""
Smoke test: AscendClient surface is consistent with SDK 2.2.0.

Replaces the prior 1.0.0-era test file (which targeted the retired
ActionResult API). For 2.2.0 this file focuses on:
  - AscendClient importable and has expected methods
  - evaluate_mcp_action present (FEAT-008)
  - Public API symbols stable
"""
from ascend.client import AscendClient
import ascend


def test_client_importable():
    assert AscendClient is not None


def test_client_has_evaluate_action():
    assert hasattr(AscendClient, "evaluate_action")
    assert callable(AscendClient.evaluate_action)


def test_client_has_evaluate_mcp_action():
    # FEAT-008 / 2.2.0: dedicated MCP evaluation path
    assert hasattr(AscendClient, "evaluate_mcp_action")
    assert callable(AscendClient.evaluate_mcp_action)


def test_client_has_log_action_completed_and_failed():
    assert hasattr(AscendClient, "log_action_completed")
    assert hasattr(AscendClient, "log_action_failed")


def test_top_level_exports_stable():
    # If any of these disappear, users of 2.1.x will break on upgrade.
    required = (
        "AscendClient",
        "FailMode",
        "AuthorizedAgent",
        "AgentAction",
        "Decision",
        "AuthorizationDecision",
        "mcp_governance",
        "MCPGovernanceConfig",
        "MCPKillSwitchConsumer",
    )
    for name in required:
        assert hasattr(ascend, name), f"missing public export: {name}"


def test_use_mcp_endpoint_default_true():
    # Default must post to /api/v1/mcp/actions/submit (FEAT-008 pipeline).
    # Flip to False for opt-out / rollback to legacy agent-action path.
    import inspect
    sig = inspect.signature(AscendClient.evaluate_mcp_action)
    param = sig.parameters.get("use_mcp_endpoint")
    assert param is not None
    assert param.default is True
