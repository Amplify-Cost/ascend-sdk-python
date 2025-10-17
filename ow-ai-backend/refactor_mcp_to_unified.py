# Update services/mcp_governance_service.py to use enforcement_engine

with open('services/mcp_governance_service.py', 'r') as f:
    content = f.read()

# Add enforcement_engine import at top
if 'from services.cedar_enforcement_service import enforcement_engine' not in content:
    import_section = content.find('from models_audit')
    content = content[:import_section] + 'from services.cedar_enforcement_service import enforcement_engine\n' + content[import_section:]

# Replace MCPPolicy queries with enforcement_engine calls
# Find the evaluate_mcp_action method and add enforcement
old_evaluate = '''    async def evaluate_mcp_action(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str],
        session_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluate MCP action using same risk assessment as agent actions
        Returns governance decision with risk score and required approvals
        """'''

new_evaluate = '''    async def evaluate_mcp_action(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str],
        session_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluate MCP action using UNIFIED Cedar enforcement engine
        Returns governance decision with risk score and required approvals
        """
        # Use unified policy enforcement
        policy_decision = enforcement_engine.evaluate(
            principal=f"mcp_server:{server_id}",
            action=verb,
            resource=f"mcp:server:{server_id}:{namespace}:{resource}",
            context={
                "user": user_context.get("user_id"),
                "namespace": namespace,
                **session_context
            }
        )'''

content = content.replace(old_evaluate, new_evaluate)

with open('services/mcp_governance_service.py', 'w') as f:
    f.write(content)

print("✅ Updated MCP governance to use unified enforcement engine")
