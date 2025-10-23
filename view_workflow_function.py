with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find the workflow create function
import re
match = re.search(r'@router\.post\("/workflows/create"\).*?(?=@router\.|$)', content, re.DOTALL)
if match:
    print("Current /workflows/create endpoint:")
    print("=" * 80)
    print(match.group(0)[:2000])  # First 2000 chars
else:
    print("Could not find /workflows/create endpoint")
