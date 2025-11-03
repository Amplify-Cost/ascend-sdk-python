with open('routes/authorization_routes.py', 'r') as f:
    lines = f.readlines()

# Find and replace the dashboard query line safely
fixed = False
for i in range(len(lines)):
    if 'workflow_executions WHERE current_stage' in lines[i]:
        lines[i] = '            "total_pending": "SELECT COUNT(*) FROM agent_actions WHERE status IN (\'pending\', \'pending_approval\')",\n'
        print(f"✅ Fixed dashboard query at line {i+1}")
        fixed = True
        break

if fixed:
    with open('routes/authorization_routes.py', 'w') as f:
        f.writelines(lines)
    print("✅ Dashboard fix applied successfully")
else:
    print("⚠️ Dashboard query line not found")
