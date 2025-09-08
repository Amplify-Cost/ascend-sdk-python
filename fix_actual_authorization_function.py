import re

with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Fix the malformed SQL query
old_sql = r'WHERE id = :action_id, extra_data = :metadata WHERE id = :action_id'
new_sql = 'WHERE id = :action_id'

content = content.replace(old_sql, new_sql)

# Fix the variable reference error 
content = content.replace('"approval_comments": comments,', '"approval_comments": justification,')

# Add the missing parameter binding for reviewed_at
old_params = r'("reviewed_by": admin_user.get\("email", "enterprise_admin"\),)'
new_params = r'\1\n                "reviewed_at": datetime.now(UTC)'

content = re.sub(old_params, new_params, content)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Fixed SQL syntax and variable reference errors")
