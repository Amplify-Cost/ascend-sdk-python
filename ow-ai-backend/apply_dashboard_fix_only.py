with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Just fix the dashboard query
content = content.replace(
    '"total_pending": "SELECT COUNT(*) FROM workflow_executions WHERE current_stage IN (\'pending_stage_1\', \'pending_stage_2\', \'pending_stage_3\')"',
    '"total_pending": "SELECT COUNT(*) FROM agent_actions WHERE status IN (\'pending\', \'pending_approval\')"'
)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("✅ Applied dashboard fix only")
