with open('src/components/AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

# Find the problematic section around line 2921
# The error is an extra }} after the EnhancedPolicyTab
content = content.replace(
    '''        <EnhancedPolicyTab
          policies={policies}
          onCreatePolicy={createEnterprisePolicy}
          onDeletePolicy={handleDeletePolicy}
          API_BASE_URL={API_BASE_URL}
          getAuthHeaders={getAuthHeaders}
        />
      )}
        }}''',
    '''        <EnhancedPolicyTab
          policies={policies}
          onCreatePolicy={createEnterprisePolicy}
          onDeletePolicy={handleDeletePolicy}
          API_BASE_URL={API_BASE_URL}
          getAuthHeaders={getAuthHeaders}
        />
      )}'''
)

with open('src/components/AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)

print("✅ Fixed syntax error")
