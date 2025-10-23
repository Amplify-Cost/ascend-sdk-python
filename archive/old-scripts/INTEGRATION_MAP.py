"""
Map which frontend components call which backend endpoints
This shows us what's actually being used
"""
import re
from pathlib import Path
import json

print("🔗 FRONTEND-BACKEND INTEGRATION MAP")
print("=" * 80)

# Read backend endpoints
backend_endpoints = {}
routes_dir = Path('routes')

for route_file in routes_dir.glob('*.py'):
    if any(x in route_file.name for x in ['backup', 'bak', 'deprecated', '__']):
        continue
    
    try:
        with open(route_file, 'r') as f:
            content = f.read()
        
        prefix_match = re.search(r'router = APIRouter\([^)]*prefix=["\']([^"\']+)', content)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        endpoints = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)', content)
        
        for method, path in endpoints:
            full_path = prefix + path
            backend_endpoints[full_path] = {
                'method': method.upper(),
                'file': route_file.name,
                'called_by': []
            }
    except:
        pass

# Read frontend calls
frontend_dir = Path('../owkai-pilot-frontend/src/components')
if frontend_dir.exists():
    for comp in frontend_dir.glob('*.jsx'):
        if any(x in comp.name for x in ['backup', 'bak', 'broken']):
            continue
        
        try:
            with open(comp, 'r') as f:
                content = f.read()
            
            api_calls = re.findall(r'fetch\([`"\']([^`"\']+)', content)
            
            for call in api_calls:
                # Clean up the URL
                clean_call = call.split('?')[0].split('${')[0]
                
                # Match against backend endpoints
                for endpoint in backend_endpoints:
                    if endpoint in clean_call or clean_call in endpoint:
                        backend_endpoints[endpoint]['called_by'].append(comp.name)
        except:
            pass

# Report
print("\n📊 ENDPOINT USAGE ANALYSIS:")
print("-" * 80)

used_endpoints = {k: v for k, v in backend_endpoints.items() if v['called_by']}
unused_endpoints = {k: v for k, v in backend_endpoints.items() if not v['called_by']}

print(f"\n✅ USED ENDPOINTS ({len(used_endpoints)}):")
for endpoint, data in sorted(used_endpoints.items()):
    print(f"\n{data['method']:6} {endpoint}")
    print(f"       File: {data['file']}")
    print(f"       Called by: {', '.join(set(data['called_by']))}")

print(f"\n⚠️  UNUSED ENDPOINTS ({len(unused_endpoints)}):")
for endpoint, data in sorted(unused_endpoints.items()):
    print(f"  {data['method']:6} {endpoint} ({data['file']})")

# Save JSON report
report = {
    'used_endpoints': used_endpoints,
    'unused_endpoints': unused_endpoints,
    'summary': {
        'total_endpoints': len(backend_endpoints),
        'used': len(used_endpoints),
        'unused': len(unused_endpoints),
        'usage_rate': f"{len(used_endpoints)/len(backend_endpoints)*100:.1f}%"
    }
}

with open('INTEGRATION_MAP.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n📊 Summary:")
print(f"  Total Endpoints: {report['summary']['total_endpoints']}")
print(f"  Used: {report['summary']['used']}")
print(f"  Unused: {report['summary']['unused']}")
print(f"  Usage Rate: {report['summary']['usage_rate']}")

print("\n✅ Integration map saved to INTEGRATION_MAP.json")
