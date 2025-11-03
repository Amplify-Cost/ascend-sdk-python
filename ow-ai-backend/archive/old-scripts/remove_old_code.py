"""Remove old dataclass and hardcoded data that conflicts with model"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    lines = f.readlines()

# Find and remove the dataclass and ENTERPRISE_PLAYBOOKS
new_lines = []
skip_until = None
dataclass_started = False
enterprise_playbooks_started = False

for i, line in enumerate(lines):
    # Skip dataclass definition
    if '@dataclass' in line and 'AutomationPlaybook' in lines[i+1] if i+1 < len(lines) else False:
        dataclass_started = True
        continue
    
    if dataclass_started:
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            dataclass_started = False
        else:
            continue
    
    # Skip ENTERPRISE_PLAYBOOKS list
    if 'ENTERPRISE_PLAYBOOKS = [' in line:
        enterprise_playbooks_started = True
        continue
    
    if enterprise_playbooks_started:
        if ']' in line and 'AutomationPlaybook(' not in line:
            enterprise_playbooks_started = False
            continue
        else:
            continue
    
    new_lines.append(line)

# Write back
with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Removed old dataclass and ENTERPRISE_PLAYBOOKS")
print("✅ Routes file now uses only models.AutomationPlaybook")
