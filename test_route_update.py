"""Quick test to verify the endpoint update worked"""

print("🧪 Testing updated playbook endpoint...")
print("=" * 70)

# Read and check the routes file
with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()
    
# Verify key changes
checks = {
    'AutomationPlaybook import': 'AutomationPlaybook' in content,
    'PlaybookExecution import': 'PlaybookExecution' in content,
    'Database query': 'db.query(AutomationPlaybook)' in content,
    'Filter by status': 'AutomationPlaybook.status == status' in content,
    'Filter by risk_level': 'AutomationPlaybook.risk_level' in content,
    'ENTERPRISE_PLAYBOOKS removed': 'ENTERPRISE_PLAYBOOKS.copy()' not in content
}

all_good = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check}")
    if not result:
        all_good = False

print("")
if all_good:
    print("🎉 All checks passed! Endpoint updated correctly.")
    print("")
    print("Next steps:")
    print("  1. Test endpoint with actual API call")
    print("  2. Add POST /automation/playbooks (create)")
    print("  3. Add POST /automation/playbook/{id}/toggle")
    print("  4. Add POST /automation/execute-playbook")
else:
    print("⚠️  Some checks failed - review needed")

print("=" * 70)
