with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Replace the entire try block for policy compilation
old_block = '''            try:
                # ENTERPRISE FIX: Check if policy has structured format in extra_data
                if policy.extra_data and isinstance(policy.extra_data, dict):
                    
                    # Check for structured policy format
                    structured = policy.extra_data.get('structured_policy')
                    if structured:
                        compiled = {
                            "id": policy.id,
                            "effect": structured['effect'].lower(),
                            "actions": structured['actions'],
                            "resources": structured['resource_types'],
                            "conditions": structured.get('conditions', {}),
                            "natural_language": policy.description
                        }
                        compiled_policies.append(compiled)
                        logger.info(f"✅ Loaded structured policy {policy.id}: {policy.description[:50]}")
                        continue
                    
                    # Check for enterprise template-based policy
                    if 'resource_types' in policy.extra_data and 'actions' in policy.extra_data:
                        compiled = {
                            "id": policy.id,
                            "effect": policy.extra_data.get('effect', 'deny').lower(),
                            "actions": policy.extra_data.get('actions', []),
                            "resources": policy.extra_data.get('resource_types', []),
                            "conditions": policy.extra_data.get('conditions', {}),
                            "natural_language": policy.description
                        }
                        compiled_policies.append(compiled)
                        logger.info(f"✅ Loaded enterprise template policy {policy.id}: {policy.description[:50]}")
                        continue'''

new_block = '''            try:
                # Use EnterprisePolicy columns directly (no extra_data)
                compiled = {
                    "id": policy.id,
                    "effect": policy.effect.lower() if policy.effect else "deny",
                    "actions": policy.actions if policy.actions else [],
                    "resources": policy.resources if policy.resources else [],
                    "conditions": policy.conditions if policy.conditions else {},
                    "natural_language": policy.description,
                    "policy_name": policy.policy_name
                }
                compiled_policies.append(compiled)
                logger.info(f"✅ Loaded policy {policy.id}: {policy.policy_name}")
                continue'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('routes/unified_governance_routes.py', 'w') as f:
        f.write(content)
    print("✅ Policy compilation fixed")
else:
    print("❌ Pattern not found")
    exit(1)
