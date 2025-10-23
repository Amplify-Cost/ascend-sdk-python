with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# 1. Fix dashboard query
content = content.replace(
    '"total_pending": "SELECT COUNT(*) FROM workflow_executions WHERE current_stage IN (\'pending_stage_1\', \'pending_stage_2\', \'pending_stage_3\')"',
    '"total_pending": "SELECT COUNT(*) FROM agent_actions WHERE status IN (\'pending\', \'pending_approval\')"'
)

# 2. Fix authorize endpoint to handle both ID formats
content = content.replace(
    '@router.post("/authorize/{action_id}")\nasync def authorize_action(\n    action_id: int,',
    '@router.post("/authorize/{action_id}")\nasync def authorize_action(\n    action_id: str,  # Handle both formats'
)

# Add ID parsing after the function definition
import re
pattern = r'(async def authorize_action.*?current_user.*?\):)(.*?)(try:)'
parsing = '''
    # Parse action ID (handle both "194" and "ENT_ACTION_000194" formats)
    if isinstance(action_id, str) and action_id.startswith("ENT_ACTION_"):
        action_id = int(action_id.replace("ENT_ACTION_", "").lstrip("0"))
    else:
        action_id = int(action_id)
'''
replacement = r'\1\2' + parsing + r'\3'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("✅ Applied essential fixes")
