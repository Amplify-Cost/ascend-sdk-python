# Read the file
with open('main.py', 'r') as f:
    content = f.read()

# Replace is_active with status == 'active'
content = content.replace(
    "db.query(Workflow).filter(\n                    Workflow.is_active == True\n                ).all()",
    "db.query(Workflow).filter(\n                    Workflow.status == 'active'\n                ).all()"
)

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Fixed: Changed Workflow.is_active to Workflow.status == 'active'")
