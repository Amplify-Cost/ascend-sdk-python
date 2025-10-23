"""Fix workflow endpoint to handle nested workflow_data structure"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find the workflow create function
old_code = '''        # Log what we received
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

new_code = '''        # Log what we received
        logger.info(f"📦 Received workflow data: {workflow_data}")
        
        # CRITICAL FIX: Frontend nests data inside 'workflow_data' key
        if 'workflow_data' in workflow_data:
            actual_data = workflow_data['workflow_data']
            logger.info(f"✅ Extracted nested workflow_data")
        else:
            actual_data = workflow_data
        
        # Extract fields from actual data
        name = actual_data.get('name', 'Unnamed Workflow')
        description = actual_data.get('description', '')
        workflow_id = actual_data.get('id') or workflow_data.get('workflow_id') or f"wf-{int(datetime.now().timestamp())}"
        
        logger.info(f"📝 Creating workflow: id={workflow_id}, name={name}")'''

content = content.replace(old_code, new_code)

# Also update the Workflow creation to handle all fields
old_workflow = '''        # Create workflow template
        new_workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            trigger_type=workflow_data.get('trigger_type', 'manual'),
            conditions=workflow_data.get('conditions'),
            actions=workflow_data.get('actions'),
            is_active=workflow_data.get('is_active', True),
            risk_threshold=workflow_data.get('risk_threshold', 50)
        )'''

new_workflow = '''        # Create workflow template
        new_workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            trigger_type=actual_data.get('trigger_type', 'manual'),
            conditions=actual_data.get('conditions'),
            actions=actual_data.get('actions') or actual_data.get('steps'),
            is_active=actual_data.get('status') == 'active',
            risk_threshold=actual_data.get('risk_threshold', 50)
        )'''

content = content.replace(old_workflow, new_workflow)

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Fixed workflow endpoint to handle nested data structure")
