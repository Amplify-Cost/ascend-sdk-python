import re

# Read the current main.py
with open('main.py', 'r') as f:
    content = f.read()

# Find and replace the problematic INSERT statement in the MCP ingest endpoint
old_pattern = r'INSERT INTO agent_actions \(\s*agent_id, action_type, description, risk_level, risk_score,\s*status, approved, user_id, tool_name, created_at\s*\) VALUES \(\s*%(agent_id)s, %(action_type)s, %(description)s, %(risk_level)s, %(risk_score)s,\s*%(status)s, %(approved)s, %(user_id)s, %(tool_name)s, %(created_at)s\s*\)'

new_pattern = '''INSERT INTO agent_actions (
                agent_id, action_type, description, risk_level, risk_score, 
                status, approved, user_id, created_at
            ) VALUES (
                %(agent_id)s, %(action_type)s, %(description)s, %(risk_level)s, %(risk_score)s,
                %(status)s, %(approved)s, %(user_id)s, %(created_at)s
            )'''

content = re.sub(old_pattern, new_pattern, content, flags=re.DOTALL)

# Remove the tool_name parameter from the parameter dictionary
content = content.replace("'tool_name': 'enterprise_mcp',\n            ", "")
content = content.replace("'tool_name': 'enterprise_mcp',", "")

# Write the fixed content back
with open('main.py', 'w') as f:
    f.write(content)

print("Fixed MCP endpoint to match actual database schema")
