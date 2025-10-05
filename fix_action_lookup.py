with open('src/components/AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

# Fix the action lookup
old_code = "const action = pendingActions.find(a => a.id === actionId);"

new_code = """const action = pendingActions.find(a => 
      a.id === actionId || 
      a.workflow_execution_id === actionId || 
      a.workflow_id === actionId
    );"""

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fixed action lookup")
else:
    print("❌ Pattern not found")
    exit(1)

with open('src/components/AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)
