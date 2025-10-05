import re

with open('src/components/AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

# 1. Add import at the top (after other imports)
if 'EnhancedPolicyTab' not in content:
    # Find the last import statement
    import_pattern = r"(import.*?from.*?;)\n"
    imports = list(re.finditer(import_pattern, content))
    if imports:
        last_import_pos = imports[-1].end()
        new_import = "import { EnhancedPolicyTab } from './EnhancedPolicyTab';\n"
        content = content[:last_import_pos] + new_import + content[last_import_pos:]
        print("✅ Added EnhancedPolicyTab import")

# 2. Find and replace the policies tab section
# Find the start of policies tab
start_pattern = r'{activeTab === "policies" && \('
start_match = re.search(start_pattern, content)

if start_match:
    start_pos = start_match.start()
    
    # Find the matching closing brace - count braces to find the end
    brace_count = 0
    in_section = False
    end_pos = start_pos
    
    for i in range(start_pos, len(content)):
        char = content[i]
        if char == '(':
            brace_count += 1
            in_section = True
        elif char == ')' and in_section:
            brace_count -= 1
            if brace_count == 0:
                end_pos = i + 1
                break
    
    # Replace the entire section
    new_section = '''{activeTab === "policies" && (
        <EnhancedPolicyTab
          policies={policies}
          onCreatePolicy={createEnterprisePolicy}
          onDeletePolicy={handleDeletePolicy}
          API_BASE_URL={API_BASE_URL}
          getAuthHeaders={getAuthHeaders}
        />
      )}'''
    
    content = content[:start_pos] + new_section + content[end_pos:]
    print("✅ Replaced policies tab with EnhancedPolicyTab")
else:
    print("❌ Could not find policies tab section")

# Write back
with open('src/components/AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)

print("✅ Dashboard updated successfully")
