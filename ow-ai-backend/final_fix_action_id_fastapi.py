with open('routes/authorization_routes.py', 'r') as f:
    lines = f.readlines()

# Find the authorize endpoint and ensure it accepts str
fixed = False
for i in range(780, min(795, len(lines))):
    if '@router.post("/authorize/{action_id}")' in lines[i]:
        print(f"Found route decorator at line {i+1}")
        # Look for the function signature
        for j in range(i+1, min(i+10, len(lines))):
            if 'async def authorize_action' in lines[j]:
                # Check next few lines for action_id parameter
                for k in range(j, min(j+5, len(lines))):
                    if 'action_id:' in lines[k]:
                        if 'action_id: int' in lines[k]:
                            lines[k] = lines[k].replace('action_id: int', 'action_id: str')
                            print(f"✅ Fixed action_id type to str at line {k+1}")
                            fixed = True
                        elif 'action_id: str' in lines[k]:
                            print(f"✅ action_id already str at line {k+1}")
                            fixed = True
                        break

# Also ensure parse_action_id function exists
if 'def parse_action_id' not in ''.join(lines):
    # Add it near the top after imports
    for i, line in enumerate(lines):
        if 'router = APIRouter()' in line:
            parse_func = '''
def parse_action_id(action_id: str) -> int:
    """Parse ENT_ACTION_000194 to 194"""
    if isinstance(action_id, str) and "ENT_ACTION_" in action_id:
        return int(action_id.replace("ENT_ACTION_", "").lstrip("0"))
    return int(action_id)

'''
            lines.insert(i, parse_func)
            print("✅ Added parse_action_id function")
            break

with open('routes/authorization_routes.py', 'w') as f:
    f.writelines(lines)

if fixed:
    print("\n✅ Action ID parsing fix complete!")
else:
    print("\n⚠️ Could not find action_id parameter to fix")
