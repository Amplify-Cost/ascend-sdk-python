"""Diagnose why CREATE playbook doesn't work"""
import re

print("=" * 80)
print("🔍 DIAGNOSING CREATE PLAYBOOK ISSUE")
print("=" * 80)
print()

# Read the current routes file
with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Check 1: Is it using database or hardcoded data?
print("1️⃣ DATA SOURCE CHECK:")
if 'ENTERPRISE_PLAYBOOKS' in content:
    print("   ❌ FOUND HARDCODED DATA: Still using ENTERPRISE_PLAYBOOKS")
    print("   This is demo data, not real database!")
else:
    print("   ✅ No hardcoded ENTERPRISE_PLAYBOOKS found")

if 'db.query(AutomationPlaybook)' in content:
    print("   ✅ Database queries found")
else:
    print("   ❌ No database queries found")

# Check 2: What endpoints exist?
print("\n2️⃣ ENDPOINTS FOUND:")
endpoints = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
for method, path in endpoints:
    print(f"   • {method.upper():6} {path}")

if not any(method == 'post' and '/automation/playbooks' in path for method, path in endpoints):
    print("\n   ❌ POST /automation/playbooks NOT FOUND!")
    print("   This is why CREATE doesn't work!")
else:
    print("\n   ✅ POST endpoint exists")

# Check 3: Is AutomationPlaybook model imported?
print("\n3️⃣ MODEL IMPORTS:")
if 'from models import' in content and 'AutomationPlaybook' in content:
    print("   ✅ AutomationPlaybook model imported")
else:
    print("   ❌ AutomationPlaybook model NOT imported")

# Check 4: Look at the GET endpoint implementation
print("\n4️⃣ GET ENDPOINT IMPLEMENTATION:")
get_impl = re.search(r'@router\.get\(["\']/?automation/playbooks["\'].*?(?=@router\.|$)', content, re.DOTALL)
if get_impl:
    impl_text = get_impl.group(0)
    if 'db.query' in impl_text:
        print("   ✅ GET uses database queries")
    elif 'ENTERPRISE_PLAYBOOKS' in impl_text:
        print("   ❌ GET uses hardcoded ENTERPRISE_PLAYBOOKS")
        print("   You're seeing DEMO DATA, not real database!")
    else:
        print("   ⚠️  Unknown data source")
else:
    print("   ❌ GET endpoint not found")

print("\n" + "=" * 80)
