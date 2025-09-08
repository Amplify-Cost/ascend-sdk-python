import re

with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Find and fix the malformed parameter section
old_params = r'''("action_id": action_id,\s+"status": decision,\s+"approved": decision == "approved",\s+"reviewed_by": admin_user\.get\("email", "enterprise_admin"\),\s+"reviewed_at": datetime\.now\(UTC\)\s+"reviewed_at": authorization_timestamp\s+}\.update\(\{"metadata": json\.dumps\(enterprise_metadata\)\}\)\))'''

new_params = '''("action_id": action_id,
                "status": decision,
                "approved": decision == "approved",
                "reviewed_by": admin_user.get("email", "enterprise_admin"),
                "reviewed_at": datetime.now(UTC)
            })'''

content = re.sub(old_params, new_params, content, flags=re.DOTALL)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Fixed parameter dictionary syntax errors")
