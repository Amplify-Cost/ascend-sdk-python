"""
🏢 ENTERPRISE DEEP DIVE AUDIT
Complete analysis of what's actually running vs what's just files
"""
import os
import re
from pathlib import Path
import ast

print("=" * 80)
print("🏢 ENTERPRISE DEEP DIVE AUDIT")
print("=" * 80)
print()

# ============================================================================
# 1. MAIN.PY ANALYSIS - What's Actually Registered
# ============================================================================
print("📡 SECTION 1: REGISTERED ROUTERS (What's Actually Active)")
print("-" * 80)

with open('main.py', 'r') as f:
    main_content = f.read()

# Find all include_router calls
router_includes = re.findall(r'app\.include_router\(([\w_]+)', main_content)
print(f"Total routers registered: {len(router_includes)}")
print()

# Find router imports
router_imports = re.findall(r'from routes\.([\w_]+) import router as ([\w_]+)', main_content)
print("Active Route Imports:")
for route_file, router_name in router_imports:
    print(f"  • routes/{route_file}.py → {router_name}")

print()
print("Router Registration Calls:")
for router in router_includes:
    print(f"  • {router}")

# ============================================================================
# 2. ROUTES DIRECTORY ANALYSIS
# ============================================================================
print()
print("=" * 80)
print("📁 SECTION 2: ROUTES DIRECTORY ANALYSIS")
print("-" * 80)

routes_dir = Path('routes')
all_route_files = [f for f in routes_dir.glob('*.py') if f.name != '__init__.py']

# Categorize files
active_files = []
backup_files = []
deprecated_files = []
unknown_files = []

for file in all_route_files:
    filename = file.name
    if any(x in filename for x in ['backup', 'bak', '.old', '.broken']):
        backup_files.append(filename)
    elif 'deprecated' in filename:
        deprecated_files.append(filename)
    else:
        # Check if imported in main.py
        base_name = filename.replace('.py', '')
        if base_name in [route for route, _ in router_imports]:
            active_files.append(filename)
        else:
            unknown_files.append(filename)

print(f"\n✅ ACTIVE FILES (Imported in main.py): {len(active_files)}")
for f in sorted(active_files):
    print(f"  • {f}")

print(f"\n⚠️  UNKNOWN FILES (Not imported, but not backup): {len(unknown_files)}")
for f in sorted(unknown_files):
    print(f"  • {f}")

print(f"\n📦 BACKUP FILES (Can likely be deleted): {len(backup_files)}")
for f in sorted(backup_files):
    print(f"  • {f}")

print(f"\n🗑️  DEPRECATED FILES: {len(deprecated_files)}")
for f in sorted(deprecated_files):
    print(f"  • {f}")

# ============================================================================
# 3. ENDPOINT ANALYSIS - What APIs Exist
# ============================================================================
print()
print("=" * 80)
print("🔌 SECTION 3: ENDPOINT ANALYSIS")
print("-" * 80)

endpoint_map = {}

for file in active_files:
    filepath = routes_dir / file
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find router prefix
        prefix_match = re.search(r'router = APIRouter\([^)]*prefix=["\']([^"\']+)', content)
        prefix = prefix_match.group(1) if prefix_match else "/"
        
        # Find all endpoints
        endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
        
        if endpoints:
            endpoint_map[file] = {
                'prefix': prefix,
                'endpoints': endpoints
            }
    except Exception as e:
        print(f"  ⚠️  Error reading {file}: {e}")

print("\nAPI Endpoints by Route File:")
for file, data in sorted(endpoint_map.items()):
    print(f"\n{file} (prefix: {data['prefix']})")
    for method, path in data['endpoints']:
        full_path = data['prefix'] + path if not path.startswith('/') else data['prefix'] + path
        print(f"  • {method.upper():6} {full_path}")

# ============================================================================
# 4. FRONTEND COMPONENT ANALYSIS
# ============================================================================
print()
print("=" * 80)
print("🖥️  SECTION 4: FRONTEND API CALLS")
print("-" * 80)

frontend_dir = Path('../owkai-pilot-frontend/src/components')
if frontend_dir.exists():
    components = list(frontend_dir.glob('*.jsx'))
    
    # Track which endpoints are called from frontend
    frontend_calls = {}
    
    for comp in components:
        if any(x in comp.name for x in ['backup', 'bak', 'broken']):
            continue
            
        try:
            with open(comp, 'r') as f:
                content = f.read()
            
            # Find fetch calls
            api_calls = re.findall(r'fetch\([`"\']([^`"\']+)', content)
            if api_calls:
                frontend_calls[comp.name] = api_calls
        except:
            pass
    
    print("\nFrontend Components and Their API Calls:")
    for comp, calls in sorted(frontend_calls.items()):
        print(f"\n{comp}:")
        unique_calls = set(calls)
        for call in sorted(unique_calls):
            if 'api' in call.lower() or call.startswith('/'):
                print(f"  • {call}")

print()
print("=" * 80)

# Save detailed report
with open('DEEP_AUDIT_REPORT.txt', 'w') as f:
    f.write("ENTERPRISE DEEP DIVE AUDIT REPORT\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Active Routes: {len(active_files)}\n")
    f.write(f"Unknown Routes: {len(unknown_files)}\n")
    f.write(f"Backup Files: {len(backup_files)}\n")
    f.write(f"Deprecated Files: {len(deprecated_files)}\n")
    f.write(f"\nTotal API Endpoints: {sum(len(d['endpoints']) for d in endpoint_map.values())}\n")

print("✅ Detailed report saved to DEEP_AUDIT_REPORT.txt")
