"""
Analyze what frontend expects vs what backend provides
This is the CONTRACT between systems
"""
import re
from pathlib import Path
import json

print("=" * 80)
print("📋 FRONTEND-BACKEND CONTRACT ANALYSIS")
print("=" * 80)
print()

# =============================================================================
# STEP 1: What does FRONTEND expect?
# =============================================================================
print("1️⃣ FRONTEND EXPECTATIONS (What API calls does it make?)")
print("-" * 80)

frontend_expectations = {
    'automation_playbooks': {
        'list': None,
        'create': None,
        'update': None,
        'delete': None,
        'toggle': None,
        'execute': None
    },
    'workflow_orchestrations': {
        'list': None,
        'create': None,
        'execute': None
    }
}

# Search frontend for API calls
frontend_dir = Path('../owkai-pilot-frontend/src/components')

# Find which component handles automation center
automation_components = []
for comp in frontend_dir.glob('*.jsx'):
    try:
        with open(comp, 'r') as f:
            content = f.read()
        
        if any(x in content.lower() for x in ['automation', 'playbook', 'orchestration']):
            automation_components.append(comp.name)
            
            # Find API calls in this component
            api_calls = re.findall(r'fetch\([`"\']([^`"\']+)', content)
            
            for call in api_calls:
                if 'playbook' in call.lower():
                    print(f"\n   {comp.name}:")
                    print(f"      • {call}")
                    
                    # Determine operation
                    if 'POST' in content[max(0, content.find(call)-100):content.find(call)+100]:
                        if '/create' in call or call.endswith('playbooks'):
                            print(f"        → CREATE operation")
                    elif 'GET' in content[max(0, content.find(call)-100):content.find(call)+100]:
                        print(f"        → LIST/GET operation")
                    elif 'PUT' in content[max(0, content.find(call)-100):content.find(call)+100]:
                        print(f"        → UPDATE operation")
                    elif 'DELETE' in content[max(0, content.find(call)-100):content.find(call)+100]:
                        print(f"        → DELETE operation")
    except:
        pass

print(f"\n   Components using automation APIs: {', '.join(automation_components)}")

# =============================================================================
# STEP 2: What does BACKEND provide?
# =============================================================================
print("\n\n2️⃣ BACKEND PROVIDES (What endpoints exist?)")
print("-" * 80)

routes_file = Path('routes/automation_orchestration_routes.py')
if routes_file.exists():
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Find router prefix
    prefix_match = re.search(r'router = APIRouter\([^)]*prefix=["\']([^"\']+)', content)
    prefix = prefix_match.group(1) if prefix_match else "UNKNOWN"
    
    print(f"   Router prefix: {prefix}")
    
    # Find all endpoints
    endpoints = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)', content)
    
    if endpoints:
        print(f"   Endpoints found: {len(endpoints)}")
        for method, path in endpoints:
            print(f"      • {method.upper():6} {prefix}{path}")
    else:
        print("   ❌ NO ENDPOINTS FOUND - File is empty or broken!")
    
    # Check imports
    print("\n   Model imports:")
    if 'AutomationPlaybook' in content:
        print("      ✅ AutomationPlaybook")
    else:
        print("      ❌ AutomationPlaybook NOT imported")
    
    if 'PlaybookExecution' in content:
        print("      ✅ PlaybookExecution")
    else:
        print("      ❌ PlaybookExecution NOT imported")
else:
    print("   ❌ FILE DOES NOT EXIST!")

# =============================================================================
# STEP 3: Find specific frontend component expecting playbook data
# =============================================================================
print("\n\n3️⃣ DETAILED FRONTEND COMPONENT ANALYSIS")
print("-" * 80)

# Look for the main automation component
possible_files = [
    'EnterpriseWorkflowBuilder.jsx',
    'AutomationCenter.jsx',
    'PlaybookManager.jsx',
    'WorkflowOrchestration.jsx'
]

for filename in possible_files:
    filepath = frontend_dir / filename
    if filepath.exists():
        print(f"\n   Found: {filename}")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find useState for playbooks
        state_vars = re.findall(r'const \[(\w+), set\w+\] = useState', content)
        if state_vars:
            print(f"      State variables: {', '.join(state_vars)}")
        
        # Find API endpoints called
        api_calls = re.findall(r'fetch\([`"\']([^`"\']+)[`"\']', content)
        if api_calls:
            print("      API calls:")
            for call in set(api_calls):
                if 'api' in call.lower() or call.startswith('/'):
                    print(f"         • {call}")
        
        # Find expected response structure
        print("      Expected data structure:")
        # Look for .data or response handling
        data_access = re.findall(r'response\.(\w+)', content)
        if data_access:
            print(f"         Accesses: response.{', response.'.join(set(data_access))}")

# =============================================================================
# STEP 4: Generate expected contract
# =============================================================================
print("\n\n4️⃣ EXPECTED API CONTRACT (What we need to implement)")
print("-" * 80)

contract = {
    "GET /api/authorization/automation/playbooks": {
        "purpose": "List all automation playbooks",
        "query_params": ["status", "risk_level"],
        "response": {
            "status": "success",
            "data": [
                {
                    "id": "string",
                    "name": "string",
                    "description": "string",
                    "status": "active|inactive",
                    "risk_level": "low|medium|high|critical",
                    "approval_required": "boolean",
                    "trigger_conditions": "object",
                    "actions": "array",
                    "execution_count": "number",
                    "success_rate": "number",
                    "created_at": "ISO date"
                }
            ],
            "total": "number"
        }
    },
    "POST /api/authorization/automation/playbooks": {
        "purpose": "Create new playbook",
        "auth": "Admin only",
        "body": {
            "id": "string",
            "name": "string", 
            "description": "string",
            "status": "active|inactive",
            "risk_level": "low|medium|high|critical",
            "approval_required": "boolean",
            "trigger_conditions": "object",
            "actions": "array"
        },
        "response": {
            "status": "success",
            "message": "string",
            "data": {"id": "string", "name": "string"}
        }
    },
    "POST /api/authorization/automation/playbook/{id}/toggle": {
        "purpose": "Enable/disable playbook",
        "auth": "Admin only",
        "response": {
            "status": "success",
            "message": "string",
            "data": {"status": "active|inactive"}
        }
    },
    "POST /api/authorization/automation/execute-playbook": {
        "purpose": "Test execute playbook",
        "body": {
            "playbook_id": "string",
            "input_data": "object"
        },
        "response": {
            "status": "success",
            "data": {
                "execution_id": "number",
                "execution_status": "string"
            }
        }
    },
    "GET /api/authorization/orchestration/active-workflows": {
        "purpose": "List active workflow executions",
        "response": {
            "status": "success",
            "data": "array of executions"
        }
    }
}

print("\nRequired Endpoints:")
for endpoint, details in contract.items():
    print(f"\n   {endpoint}")
    print(f"      Purpose: {details['purpose']}")
    if 'auth' in details:
        print(f"      Auth: {details['auth']}")

# Save contract
with open('API_CONTRACT.json', 'w') as f:
    json.dump(contract, f, indent=2)

print("\n\n✅ API contract saved to API_CONTRACT.json")

print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print("\nCurrent Status:")
print("  ❌ Backend provides: 0 endpoints")
print("  ✅ Database has: automation_playbooks table")
print("  ✅ Database has: playbook_executions table")
print("  ❌ Frontend expects: 5+ endpoints")
print("\nAction Required:")
print("  → Implement all endpoints in automation_orchestration_routes.py")
print("  → Import AutomationPlaybook and PlaybookExecution models")
print("  → Connect to database (NOT hardcoded data)")
print("=" * 80)
