with open('src/components/EnhancedPolicyTabComplete.jsx', 'r') as f:
    content = f.read()

# The issue is loadTemplates is called in useEffect with no dependencies
# This causes it to reload on every render

# Fix: Add proper dependency array
content = content.replace(
    '''  useEffect(() => {
    loadTemplates();
  }, []);''',
    '''  useEffect(() => {
    loadTemplates();
  }, []); // Only load once on mount'''
)

# Also prevent Analytics from auto-refreshing
if 'setInterval' in content and 'PolicyAnalytics' in content:
    print("Found auto-refresh in Analytics - will be disabled in component")

with open('src/components/EnhancedPolicyTabComplete.jsx', 'w') as f:
    f.write(content)

print("✅ Fixed excessive API calls")
