with open('src/components/EnhancedPolicyTabComplete.jsx', 'r') as f:
    content = f.read()

# Replace window.location.reload() with proper state management
content = content.replace(
    '''      if (response.ok) {
        alert('Policy created from template!');
        setView('list');
        window.location.reload();
      }''',
    '''      if (response.ok) {
        alert('Policy created from template!');
        setView('list');
        // Trigger parent refresh without full page reload
        if (onCreatePolicy) onCreatePolicy();
      }'''
)

with open('src/components/EnhancedPolicyTabComplete.jsx', 'w') as f:
    f.write(content)

print("✅ Fixed page refresh issue")
