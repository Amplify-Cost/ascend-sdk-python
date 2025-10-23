with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# The bug is here - it's checking workflow_data['id'] AFTER we extract actual_data
# This line causes KeyError:
old_bug = "existing = db.query(Workflow).filter(Workflow.id == workflow_data['id']).first()"

if old_bug in content:
    # Fix it to use workflow_id which we already extracted
    new_fix = "existing = db.query(Workflow).filter(Workflow.id == workflow_id).first()"
    content = content.replace(old_bug, new_fix)
    print("✅ Fixed KeyError: using workflow_id instead of workflow_data['id']")
else:
    print("⚠️  Could not find the bug line, checking alternatives...")
    # Try alternative patterns
    if "workflow_data['id']" in content:
        print(f"   Found workflow_data['id'] in content")
        # Show context
        idx = content.find("workflow_data['id']")
        print(f"   Context: {content[idx-100:idx+100]}")

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)
