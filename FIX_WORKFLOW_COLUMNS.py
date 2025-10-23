"""Fix Workflow creation to match actual database columns"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Replace the Workflow creation with actual schema
old_create = '''        # Create workflow template (match actual schema)
        new_workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            trigger_type=actual_data.get('trigger_type', 'manual'),
            conditions=actual_data.get('conditions'),
            actions=actual_data.get('steps')  # Frontend sends 'steps'
        )'''

new_create = '''        # Create workflow template - CORRECT SCHEMA
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

content = content.replace(old_create, new_create)

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Fixed Workflow creation with correct columns")
