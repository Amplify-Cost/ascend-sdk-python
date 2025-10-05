with open('services/workflow_bridge.py', 'r') as f:
    content = f.read()

# Fix the current_stage value
content = content.replace(
    'current_stage="stage_1",',
    'current_stage="pending_stage_1",'
)

with open('services/workflow_bridge.py', 'w') as f:
    f.write(content)

print("✅ Fixed current_stage value")
