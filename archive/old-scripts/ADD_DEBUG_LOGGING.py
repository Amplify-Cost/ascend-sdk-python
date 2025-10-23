"""Add debug logging to see exactly where it fails"""

with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find the workflow creation section
old_code = '''        # Create workflow template - CORRECT SCHEMA
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

new_code = '''        # Create workflow template - CORRECT SCHEMA with DEBUG
        logger.info(f"📝 About to create Workflow with:")
        logger.info(f"   id={workflow_id}")
        logger.info(f"   name={name}")
        logger.info(f"   description={description}")
        logger.info(f"   created_by={current_user.get('email')}")
        logger.info(f"   status=active")
        logger.info(f"   steps={actual_data.get('steps', [])}")
        
        try:
            new_workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                created_by=current_user.get('email'),
                status='active',
                steps=actual_data.get('steps', []),
                trigger_conditions=actual_data.get('trigger_conditions'),
                workflow_metadata=actual_data.get('real_time_stats') or actual_data.get('success_metrics')
            )
            logger.info(f"✅ Workflow object created successfully")
        except Exception as create_error:
            logger.error(f"❌ Error creating Workflow object: {create_error}")
            logger.error(f"   Error type: {type(create_error).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            raise'''

content = content.replace(old_code, new_code)

with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging")
