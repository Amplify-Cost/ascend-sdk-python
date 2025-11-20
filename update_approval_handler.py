with open('src/components/AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

# Find and replace the approval endpoint call
old_code = '''    let endpoint;
    if (action?.action_type === 'mcp_server_action') {
      endpoint = `${API_BASE_URL}/api/mcp-governance/evaluate-action`;
    } else {
      // PRESERVE: Use existing agent approval endpoint
      endpoint = `${API_BASE_URL}/api/authorization/authorize/${actionId}`;
    }'''

new_code = '''    let endpoint;
    if (action?.action_type === 'mcp_server_action') {
      endpoint = `${API_BASE_URL}/api/mcp-governance/evaluate-action`;
    } else if (action?.workflow_execution_id) {
      // Phase 3: Use workflow approval endpoint
      endpoint = `${API_BASE_URL}/api/governance/workflows/${action.workflow_execution_id}/approve`;
    } else {
      // Fallback: Use existing agent approval endpoint
      endpoint = `${API_BASE_URL}/api/authorization/authorize/${actionId}`;
    }'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Updated approval endpoint routing")
else:
    print("❌ Code pattern not found - manual update needed")
    exit(1)

with open('src/components/AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)
