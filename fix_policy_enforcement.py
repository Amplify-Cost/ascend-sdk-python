import sys

# Read the file
with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Find the broken section
old_code = '''active_policies = db.query(AgentAction).filter(
            and_(AgentAction.action_type == "governance_policy", AgentAction.status == "active")
        ).all()'''

# Replace with correct code
new_code = '''active_policies = db.query(EnterprisePolicy).all()'''

# Perform replacement
if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Found and replaced policy query")
else:
    print("❌ Pattern not found - manual fix needed")
    sys.exit(1)

# Write back
with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)

print("✅ File updated successfully")
