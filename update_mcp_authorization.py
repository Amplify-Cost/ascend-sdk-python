# Find MCP authorization code and update to use enforcement_engine

import os
import re

# Check if MCP authorization exists
mcp_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py') and 'mcp' in file.lower():
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                if 'MCPPolicy' in content or 'mcp_polic' in content.lower():
                    mcp_files.append(filepath)

if mcp_files:
    print("Found MCP authorization files:")
    for f in mcp_files:
        print(f"  - {f}")
else:
    print("No MCP-specific authorization files found")
    print("MCP actions likely already use unified governance")

