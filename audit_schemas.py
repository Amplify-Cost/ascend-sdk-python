"""
Enterprise Schema Audit
Find ALL schema imports needed across the entire codebase
"""
import os
import re
from collections import defaultdict

print("=" * 80)
print("🔍 ENTERPRISE SCHEMA AUDIT")
print("=" * 80)
print()

# Find all Python files
python_files = []
for root, dirs, files in os.walk('.'):
    # Skip virtual env, cache, etc
    if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
        continue
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

# Track all schema imports
schema_imports = defaultdict(list)

print(f"📁 Scanning {len(python_files)} Python files...\n")

for filepath in python_files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
            # Find "from schemas import ..."
            matches = re.findall(r'from schemas import ([^;\n]+)', content)
            for match in matches:
                # Clean up the import list
                imports = [s.strip() for s in match.replace('(', '').replace(')', '').split(',')]
                for imp in imports:
                    if imp and not imp.startswith('#'):
                        schema_imports[imp.strip()].append(filepath)
    except Exception as e:
        print(f"⚠️  Error reading {filepath}: {e}")

# Display results
print("📊 REQUIRED SCHEMAS:")
print("-" * 80)

all_schemas = sorted(schema_imports.keys())
for schema in all_schemas:
    files = schema_imports[schema]
    print(f"\n✓ {schema}")
    print(f"  Used in: {len(files)} file(s)")
    for f in files[:3]:  # Show first 3 files
        print(f"    - {f}")
    if len(files) > 3:
        print(f"    ... and {len(files) - 3} more")

print("\n" + "=" * 80)
print(f"📋 TOTAL: {len(all_schemas)} unique schemas required")
print("=" * 80)

# Generate schema checklist
print("\n📝 SCHEMA IMPLEMENTATION CHECKLIST:\n")
for schema in all_schemas:
    print(f"[ ] {schema}")

print("\n💡 Next: Create these schemas in schemas/ directory")
