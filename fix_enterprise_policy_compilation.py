# Read the file
with open('routes/unified_governance_routes.py', 'r') as f:
    lines = f.readlines()

# Find and replace the policy compilation loop (lines 1233-1265 approximately)
old_section_start = "        compiled_policies = []\n"
old_section_end = "                        continue\n"

# New correct code for EnterprisePolicy
new_section = '''        compiled_policies = []
        for policy in active_policies:
            try:
                # Use EnterprisePolicy columns directly
                compiled = {
                    "id": policy.id,
                    "effect": policy.effect.lower() if policy.effect else "deny",
                    "actions": policy.actions if policy.actions else [],
                    "resources": policy.resources if policy.resources else [],
                    "conditions": policy.conditions if policy.conditions else {},
                    "natural_language": policy.description,
                    "policy_name": policy.policy_name,
                    "priority": policy.priority if hasattr(policy, 'priority') else 100
                }
                compiled_policies.append(compiled)
                logger.info(f"✅ Loaded policy {policy.id}: {policy.policy_name}")
                continue
'''

# Find the start line
start_idx = None
for i, line in enumerate(lines):
    if line == old_section_start:
        start_idx = i
        break

if start_idx is None:
    print("❌ Could not find section start")
    exit(1)

# Find the end of the old try block
end_idx = None
for i in range(start_idx, min(start_idx + 50, len(lines))):
    if "continue" in lines[i] and i > start_idx + 10:
        end_idx = i + 1
        break

if end_idx is None:
    print("❌ Could not find section end")
    exit(1)

# Replace the section
new_lines = lines[:start_idx] + [new_section] + lines[end_idx:]

# Write back
with open('routes/unified_governance_routes.py', 'w') as f:
    f.writelines(new_lines)

print(f"✅ Replaced lines {start_idx+1} to {end_idx}")
