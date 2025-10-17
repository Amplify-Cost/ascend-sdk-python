#!/usr/bin/env python3
"""
Add MCP endpoints to main.py
"""

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Add import at the top (after other imports)
import_line = "from enterprise_mcp_service import create_enterprise_mcp_endpoints"

# Find where to add the import (after other from imports)
import_pos = content.find("from analytics_router import router as analytics_router")
if import_pos != -1:
    # Find end of that line
    end_line = content.find('\n', import_pos)
    content = content[:end_line+1] + import_line + '\n' + content[end_line+1:]
    print("✅ Added import statement")
else:
    print("⚠️  Could not find import location, adding at beginning")
    content = import_line + '\n' + content

# Add endpoint creation after routers are included
# Find where health_router is included
health_pos = content.find("app.include_router(health_router")
if health_pos != -1:
    # Find end of that line
    end_line = content.find('\n', health_pos)
    mcp_setup = '\n# Register Enterprise MCP endpoints\ncreate_enterprise_mcp_endpoints(app, Depends(get_db), Depends(get_current_user))\n'
    content = content[:end_line+1] + mcp_setup + content[end_line+1:]
    print("✅ Added MCP endpoint registration")
else:
    print("❌ Could not find location to add MCP endpoints")
    exit(1)

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print("✅ main.py updated successfully!")
print("🚀 Deploy to see changes: git add main.py && git commit -m 'Add MCP endpoints' && git push")
