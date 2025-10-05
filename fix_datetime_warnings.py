"""Replace deprecated datetime.utcnow() with datetime.now(UTC)"""
import os
import re

files_to_fix = [
    'main.py',
    'auth_utils.py',
    'token_utils.py',
    'jwt_manager.py',
    'enterprise_risk_assessment.py',
    'routes/siem_simple.py',
    'routes/siem_integration.py',
    'routes/analytics_routes.py',
    'routes/smart_rules_routes.py',
    'routes/unified_governance_routes.py',
    'services/cedar_enforcement_service.py',
    'services/security_bridge_service.py'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if UTC is already imported
    has_utc_import = 'from datetime import' in content and 'UTC' in content
    
    # Replace datetime.utcnow() with datetime.now(UTC)
    new_content = content.replace('datetime.utcnow()', 'datetime.now(UTC)')
    
    # Add UTC to imports if needed and not already there
    if new_content != content and not has_utc_import:
        # Find the datetime import line
        new_content = re.sub(
            r'from datetime import (.*?)(\n)',
            lambda m: f'from datetime import {m.group(1)}, UTC{m.group(2)}' if 'UTC' not in m.group(1) else m.group(0),
            new_content,
            count=1
        )
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"✅ Fixed {filepath}")

print("\n✅ All datetime warnings fixed")
