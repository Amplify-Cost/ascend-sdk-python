"""Fix workflow validation to see what data frontend sends"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find the workflow create function and add logging
old_validation = '''        # Validate required fields
        required = ['id', 'name', 'description']
        for field in required:
            if field not in workflow_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")'''

new_validation = '''        # Log what we received
        logger.info(f"📦 Received workflow data: {workflow_data}")
        
        # Validate required fields - make more flexible
        if 'name' not in workflow_data and 'workflow_name' not in workflow_data:
            raise HTTPException(status_code=400, detail=f"Missing name field. Received keys: {list(workflow_data.keys())}")
        
        # Use name or workflow_name
        name = workflow_data.get('name') or workflow_data.get('workflow_name')
        description = workflow_data.get('description', '')
        
        # Generate ID if not provided
        if 'id' not in workflow_data:
            from datetime import datetime
            workflow_id = f"wf-{int(datetime.now().timestamp())}"
        else:
            workflow_id = workflow_data['id']
        
        logger.info(f"📝 Creating workflow: id={workflow_id}, name={name}")'''

content = content.replace(old_validation, new_validation)

# Update the Workflow creation to use the new variables
old_create = '''        # Create workflow template
        new_workflow = Workflow(
            id=workflow_data['id'],
            name=workflow_data['name'],
            description=workflow_data['description'],'''

new_create = '''        # Create workflow template
        new_workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,'''

content = content.replace(old_create, new_create)

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Updated workflow validation with better error messages")
