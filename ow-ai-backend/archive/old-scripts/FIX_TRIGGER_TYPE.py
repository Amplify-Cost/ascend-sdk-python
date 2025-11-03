with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find and fix the Workflow creation - remove trigger_type
old_code = '''        try:
            new_workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                created_by=current_user.get('email'),
                status='active',
                steps=actual_data.get('steps', []),
                trigger_conditions=actual_data.get('trigger_conditions'),
                workflow_metadata=actual_data.get('real_time_stats') or actual_data.get('success_metrics')
            )'''

new_code = '''        try:
            # Create workflow with ONLY valid columns from schema
            new_workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                created_by=current_user.get('email'),
                status='active',
                steps=actual_data.get('steps', []),
                trigger_conditions=actual_data.get('trigger_conditions'),
                workflow_metadata=actual_data.get('real_time_stats') or actual_data.get('success_metrics')
            )'''

content = content.replace(old_code, new_code)

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Removed trigger_type (column doesn't exist)")
