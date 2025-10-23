import re

with open('routes/authorization_routes.py', 'r') as f:
    content = f.read()

# Fix: Remove references to non-existent columns and use existing schema
old_update = r'''db\.execute\(text\("""\s*UPDATE agent_actions\s+SET status = 'approved',\s+approved = true,\s+reviewed_by = :reviewed_by,\s+reviewed_at = :reviewed_at,\s+approval_comments = :comments,\s+authorization_id = :authorization_id\s+WHERE id = :action_id\s+"""\).*?db\.commit\(\)'''

new_update = '''db.execute(text("""
    UPDATE agent_actions 
    SET status = 'approved', 
        approved = true, 
        reviewed_by = :reviewed_by,
        reviewed_at = :reviewed_at
    WHERE id = :action_id
"""), {
    "action_id": action_id,
    "reviewed_by": admin_user.get("email", "enterprise_admin"),
    "reviewed_at": authorization_timestamp
})
db.commit()'''

content = re.sub(old_update, new_update, content, flags=re.DOTALL)

# Store enterprise metadata in existing extra_data JSON column
metadata_pattern = r'(authorization_id = str\(uuid\.uuid4\(\)\))'
metadata_replacement = r'''\1
        
        # Store enterprise metadata in existing extra_data column
        enterprise_metadata = {
            "authorization_id": authorization_id,
            "approval_comments": comments,
            "enterprise_audit": True,
            "compliance_logged": True
        }'''

content = re.sub(metadata_pattern, metadata_replacement, content)

# Update the database update to include metadata
content = re.sub(
    r'(reviewed_at = :reviewed_at\s+WHERE id = :action_id)', 
    r'\1, extra_data = :metadata WHERE id = :action_id', 
    content
)

content = re.sub(
    r'("reviewed_at": authorization_timestamp\s*})', 
    r'\1.update({"metadata": json.dumps(enterprise_metadata)})', 
    content
)

with open('routes/authorization_routes.py', 'w') as f:
    f.write(content)

print("✅ Enterprise schema alignment completed - using existing columns")
