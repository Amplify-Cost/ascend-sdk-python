with open('routes/automation_orchestration_routes.py', 'r') as f:
    lines = f.readlines()

with open('routes/automation_orchestration_routes.py', 'w') as f:
    for line in lines:
        # Remove any line with trigger_type
        if 'trigger_type' not in line:
            f.write(line)

print("✅ Removed all trigger_type references")
