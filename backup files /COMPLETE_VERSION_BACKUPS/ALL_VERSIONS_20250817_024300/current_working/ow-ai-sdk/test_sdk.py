from agent_logger import AgentLogger

logger = AgentLogger(agent_id="demo-agent-1")

logger.log_action(
    action_type="tool-use",
    description="Used web search tool",
    tool_name="WebSearch",
    risk_level="high"  # This triggers Slack
)
