"""
Smoke test: MCP governance surface is importable and wired.

Covers FEAT-008 / SDK 2.2.0 additions:
  - MCPKillSwitchConsumer exported from ascend.mcp and from top-level ascend
  - Consumer honors target_type=mcp_server BLOCK / UNBLOCK
  - Malformed messages do not raise
"""
from ascend.mcp import MCPKillSwitchConsumer
from ascend import MCPKillSwitchConsumer as TopLevelConsumer


def test_kill_switch_consumer_importable():
    assert MCPKillSwitchConsumer is not None
    assert TopLevelConsumer is MCPKillSwitchConsumer


def test_kill_switch_block_by_server_name():
    c = MCPKillSwitchConsumer()
    c.apply_message({
        "target_type": "mcp_server",
        "command_type": "BLOCK",
        "parameters": {"mcp_server": "fs-server"},
    })
    assert c.is_blocked("fs-server") is True
    assert c.is_blocked("other") is False


def test_kill_switch_unblock_clears():
    c = MCPKillSwitchConsumer()
    c.apply_message({
        "target_type": "mcp_server",
        "command_type": "BLOCK",
        "target_mcp_server_config_id": 42,
    })
    assert c.is_blocked(mcp_server_config_id=42) is True
    c.apply_message({
        "target_type": "mcp_server",
        "command_type": "UNBLOCK",
        "target_mcp_server_config_id": 42,
    })
    assert c.is_blocked(mcp_server_config_id=42) is False


def test_kill_switch_ignores_agent_messages():
    c = MCPKillSwitchConsumer()
    c.apply_message({"target_type": "agent", "command_type": "BLOCK"})
    assert c.blocked_servers == []


def test_kill_switch_malformed_message_is_safe():
    c = MCPKillSwitchConsumer()
    c.apply_message(None)  # type: ignore[arg-type]
    c.apply_message({"target_type": "mcp_server"})
    assert c.blocked_servers == []


def test_kill_switch_reset():
    c = MCPKillSwitchConsumer()
    c.apply_message({
        "target_type": "mcp_server",
        "command_type": "BLOCK",
        "parameters": {"mcp_server": "x"},
    })
    assert c.is_blocked("x") is True
    c.reset()
    assert c.is_blocked("x") is False
