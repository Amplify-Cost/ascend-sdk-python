with open('src/components/AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

old_filter = "const updated = prev.filter(action => action.id !== actionId);"

new_filter = """const updated = prev.filter(action => 
          action.id !== actionId && 
          action.workflow_execution_id !== actionId && 
          action.workflow_id !== actionId
        );"""

if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print("✅ Fixed action filter")
else:
    print("❌ Pattern not found")
    exit(1)

with open('src/components/AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)
