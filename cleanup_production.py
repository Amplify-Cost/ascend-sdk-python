import re

with open('main.py', 'r') as f:
    content = f.read()

# Remove temporary endpoints
temp_endpoints = [
    'reset_admin_password',
    'fix_admin_bcrypt', 
    'fix_admin_auth',
    'test_mcp_ingest_public',
    'mcp_test_ingest_public',
    'check_database_schema',
    'debug_actions_table',
    'debug_mcp_insert',
    'admin_debug_actions'
]

for endpoint in temp_endpoints:
    pattern = rf'@app\.(get|post)\([^)]*{endpoint}[^)]*\).*?(?=\n@app\.|\n\nif __name__|$)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Remove temporary comments and markers
content = re.sub(r'# TEMPORARY:.*?\n', '', content)
content = re.sub(r'# ENTERPRISE DEPLOYMENT REFRESH.*?\n', '', content)
content = re.sub(r'DEPLOYMENT_TIMESTAMP=.*?\n', '', content)

with open('main.py', 'w') as f:
    f.write(content)

print("Production cleanup complete - removed temporary endpoints")
