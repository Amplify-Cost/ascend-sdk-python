# Read the file
with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Fix the duplicate reviewed_at parameters
content = content.replace(
    '"reviewed_at": datetime.now(UTC)\n                "reviewed_at": datetime.now(UTC)',
    '"reviewed_at": datetime.now(UTC)'
)

# Fix the malformed parameter dictionary around line 911-913
content = content.replace(
    '"reviewed_by": admin_user.get("email", "enterprise_admin"),\n                "reviewed_at": datetime.now(UTC)\n    "reviewed_at": authorization_timestamp\n}.update({"metadata": json.dumps(enterprise_metadata)})',
    '"reviewed_by": admin_user.get("email", "enterprise_admin"),\n    "reviewed_at": authorization_timestamp'
)

# Write the corrected file
with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("Manual syntax corrections applied")
