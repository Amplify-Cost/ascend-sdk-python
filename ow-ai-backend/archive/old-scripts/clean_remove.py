"""Clean removal of dataclass and hardcoded playbooks"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Remove the entire section from PlaybookStatus enum to end of ENTERPRISE_PLAYBOOKS
# Find start: "class PlaybookStatus"
# Find end: line after the last ']' of ENTERPRISE_PLAYBOOKS

lines = content.split('\n')
new_lines = []
skip_mode = False

for i, line in enumerate(lines):
    # Start skipping at PlaybookStatus enum
    if 'class PlaybookStatus(str, Enum):' in line:
        skip_mode = True
        continue
    
    # Stop skipping after ENTERPRISE_PLAYBOOKS ends
    if skip_mode and line.strip() == ']':
        # Check if this is the end of ENTERPRISE_PLAYBOOKS
        if i > 0 and 'AutomationPlaybook(' in '\n'.join(lines[max(0, i-20):i]):
            skip_mode = False
            continue
    
    if not skip_mode:
        new_lines.append(line)

# Write back
with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Cleaned routes file")
