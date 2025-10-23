import requests
import json

BASE_URL = "https://pilot.owkai.app"

print("=== API DOCUMENTATION ANALYSIS ===\n")

# Check for API docs
docs_endpoints = ["/docs", "/redoc", "/openapi.json", "/swagger.json"]

for endpoint in docs_endpoints:
    resp = requests.get(f"{BASE_URL}{endpoint}")
    print(f"{endpoint}: {resp.status_code}")
    if resp.status_code == 200 and endpoint.endswith('.json'):
        api_spec = resp.json()
        print(f"  Found OpenAPI spec: {api_spec.get('info', {}).get('title', 'Unknown')}")
        
        # Analyze paths
        if 'paths' in api_spec:
            alert_paths = [p for p in api_spec['paths'] if 'alert' in p.lower()]
            policy_paths = [p for p in api_spec['paths'] if 'polic' in p.lower()]
            
            print(f"\n  Alert endpoints: {len(alert_paths)}")
            for path in alert_paths[:5]:
                methods = list(api_spec['paths'][path].keys())
                print(f"    {path}: {methods}")
            
            print(f"\n  Policy endpoints: {len(policy_paths)}")
            for path in policy_paths[:5]:
                methods = list(api_spec['paths'][path].keys())
                print(f"    {path}: {methods}")
