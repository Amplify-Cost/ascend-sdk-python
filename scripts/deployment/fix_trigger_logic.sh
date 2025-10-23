#!/bin/bash

# Backup
cp main.py main.py.backup_trigger_$(date +%Y%m%d_%H%M%S)

# Replace lines 1426-1429 with correct risk_score logic
python3 << 'PYEOF'
with open('main.py', 'r') as f:
    lines = f.readlines()

# Find and replace the specific section (around line 1426)
new_lines = []
skip_until_if = False

for i, line in enumerate(lines, 1):
    if i == 1426 and 'should_trigger = (' in line:
        # Replace the 4-line block with new logic
        new_lines.append('                        # Match based on risk_score range\n')
        new_lines.append('                        should_trigger = False\n')
        new_lines.append('                        if trigger_conditions and "min_risk" in trigger_conditions:\n')
        new_lines.append('                            # Get action risk_score from database\n')
        new_lines.append('                            risk_result = db.execute(text(\n')
        new_lines.append('                                "SELECT risk_score FROM agent_actions WHERE id = :id"\n')
        new_lines.append('                            ), {"id": action_id}).fetchone()\n')
        new_lines.append('                            if risk_result and risk_result[0]:\n')
        new_lines.append('                                risk_score = risk_result[0]\n')
        new_lines.append('                                min_risk = trigger_conditions.get("min_risk", 0)\n')
        new_lines.append('                                max_risk = trigger_conditions.get("max_risk", 100)\n')
        new_lines.append('                                should_trigger = (min_risk <= risk_score <= max_risk)\n')
        new_lines.append('                        elif not trigger_conditions:\n')
        new_lines.append('                            should_trigger = True\n')
        skip_until_if = True
    elif skip_until_if and 'if should_trigger:' in line:
        # Found the end, stop skipping
        skip_until_if = False
        new_lines.append(line)
    elif not skip_until_if:
        new_lines.append(line)

# Write back
with open('main.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed workflow trigger logic (lines 1426-1429)")
PYEOF
