import re

# Read the current authorization routes
with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Fix 1: Replace SELECT * with explicit columns to ensure predictable ordering
old_pattern = r'db\.execute\(text\("SELECT \* FROM agent_actions WHERE id = :action_id"\)\)'
new_pattern = '''db.execute(text("""
    SELECT id, agent_id, action_type, description, risk_level, risk_score, status, 
           created_at, updated_at, approved_by, extra_data, timestamp, is_false_positive, reviewed_by
    FROM agent_actions WHERE id = :action_id
"""))'''

content = re.sub(old_pattern, new_pattern, content)

# Fix 2: Update column index references - status is now column 6, not 5
content = re.sub(r'result\[5\](?=.*status)', 'result[6]', content)
content = re.sub(r'status = result\[5\]', 'status = result[6]', content)
content = re.sub(r'current_status = result\[5\]', 'current_status = result[6]', content)

# Write the fixed file
with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("✅ Enterprise execution column bug fixed!")
