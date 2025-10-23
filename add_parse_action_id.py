with open('routes/authorization_routes.py', 'r') as f:
    lines = f.readlines()

# Find where parse_action_id is being called (line 1182)
# We need to add the function definition before that

# Look for a good place to add it (after imports, before routes)
insert_line = -1
for i, line in enumerate(lines):
    if 'router = APIRouter()' in line:
        insert_line = i + 1
        break

if insert_line > 0:
    # Check if function already exists
    content = ''.join(lines)
    if 'def parse_action_id' not in content:
        # Add the function
        parse_func = '''
def parse_action_id(action_id):
    """Parse ENT_ACTION_000194 to 194 or return int as-is"""
    if isinstance(action_id, str):
        if "ENT_ACTION_" in action_id:
            return int(action_id.replace("ENT_ACTION_", "").lstrip("0"))
        return int(action_id)
    return action_id

'''
        lines.insert(insert_line, parse_func)
        print(f"✅ Added parse_action_id function at line {insert_line + 1}")
    else:
        print("⚠️ parse_action_id already exists somewhere")
else:
    print("❌ Could not find router = APIRouter() line")

with open('routes/authorization_routes.py', 'w') as f:
    f.writelines(lines)

print("\n✅ parse_action_id function added successfully")
