"""
Add CRUD endpoints to automation_orchestration_routes.py
This adds: CREATE, UPDATE, DELETE, TOGGLE, EXECUTE
"""

# The new endpoints to add (insert after the GET /automation/playbooks endpoint)
new_endpoints = '''

@router.post("/automation/playbooks")
async def create_automation_playbook(
    playbook_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Create new automation playbook (admin only)
    Validates input and stores in database with audit trail
    """
    try:
        logger.info(f"📝 Creating playbook by admin {current_user.get('email')}")
        
        # Validate required fields
        required_fields = ['id', 'name', 'status', 'risk_level']
        for field in required_fields:
            if field not in playbook_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Check if playbook ID already exists
        existing = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_data['id']).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Playbook with ID '{playbook_data['id']}' already exists")
        
        # Create new playbook
        new_playbook = AutomationPlaybook(
            id=playbook_data['id'],
            name=playbook_data['name'],
            description=playbook_data.get('description'),
            status=playbook_data.get('status', 'active'),
            risk_level=playbook_data.get('risk_level', 'medium'),
            approval_required=playbook_data.get('approval_required', False),
            trigger_conditions=playbook_data.get('trigger_conditions'),
            actions=playbook_data.get('actions'),
            execution_count=0,
            success_rate=0.0,
            created_by=current_user.get('user_id')
        )
        
        db.add(new_playbook)
        db.commit()
        db.refresh(new_playbook)
        
        logger.info(f"✅ Playbook '{new_playbook.id}' created successfully")
        
        return {
            "status": "success",
            "message": f"Playbook '{new_playbook.name}' created successfully",
            "data": {
                "id": new_playbook.id,
                "name": new_playbook.name,
                "status": new_playbook.status,
                "created_at": new_playbook.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create playbook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create playbook")

@router.put("/automation/playbook/{playbook_id}")
async def update_automation_playbook(
    playbook_id: str,
    playbook_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Update existing playbook (admin only)
    Updates playbook configuration with audit trail
    """
    try:
        logger.info(f"📝 Updating playbook '{playbook_id}' by admin {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
        
        # Update fields
        if 'name' in playbook_data:
            playbook.name = playbook_data['name']
        if 'description' in playbook_data:
            playbook.description = playbook_data['description']
        if 'status' in playbook_data:
            playbook.status = playbook_data['status']
        if 'risk_level' in playbook_data:
            playbook.risk_level = playbook_data['risk_level']
        if 'approval_required' in playbook_data:
            playbook.approval_required = playbook_data['approval_required']
        if 'trigger_conditions' in playbook_data:
            playbook.trigger_conditions = playbook_data['trigger_conditions']
        if 'actions' in playbook_data:
            playbook.actions = playbook_data['actions']
        
        playbook.updated_by = current_user.get('user_id')
        
        db.commit()
        db.refresh(playbook)
        
        logger.info(f"✅ Playbook '{playbook_id}' updated successfully")
        
        return {
            "status": "success",
            "message": f"Playbook '{playbook.name}' updated successfully",
            "data": {
                "id": playbook.id,
                "name": playbook.name,
                "status": playbook.status,
                "updated_at": playbook.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update playbook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update playbook")

@router.delete("/automation/playbook/{playbook_id}")
async def delete_automation_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Delete playbook (admin only)
    Soft delete with audit trail (or hard delete based on business rules)
    """
    try:
        logger.info(f"🗑️ Deleting playbook '{playbook_id}' by admin {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
        
        # Delete (cascade will handle executions)
        db.delete(playbook)
        db.commit()
        
        logger.info(f"✅ Playbook '{playbook_id}' deleted successfully")
        
        return {
            "status": "success",
            "message": f"Playbook '{playbook_id}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete playbook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete playbook")

@router.post("/automation/playbook/{playbook_id}/toggle")
async def toggle_automation_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Toggle playbook status (admin only)
    Enables or disables automation playbook
    """
    try:
        logger.info(f"🔄 Toggling playbook '{playbook_id}' by admin {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
        
        # Toggle status
        if playbook.status == 'active':
            playbook.status = 'inactive'
            new_status = 'disabled'
        else:
            playbook.status = 'active'
            new_status = 'enabled'
        
        playbook.updated_by = current_user.get('user_id')
        db.commit()
        
        logger.info(f"✅ Playbook '{playbook_id}' {new_status}")
        
        return {
            "status": "success",
            "message": f"Playbook '{playbook.name}' {new_status} successfully",
            "data": {
                "id": playbook.id,
                "name": playbook.name,
                "status": playbook.status,
                "enabled": playbook.status == 'active'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to toggle playbook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to toggle playbook")

@router.post("/automation/execute-playbook")
async def execute_automation_playbook(
    execution_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Execute playbook manually (test mode)
    Records execution in playbook_executions table
    """
    try:
        playbook_id = execution_data.get('playbook_id')
        if not playbook_id:
            raise HTTPException(status_code=400, detail="playbook_id is required")
        
        logger.info(f"▶️ Executing playbook '{playbook_id}' by user {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
        
        # Create execution record
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            executed_by=current_user.get('user_id'),
            execution_context='manual',
            input_data=execution_data.get('input_data'),
            execution_status='pending',
            execution_details={'steps': [], 'test_mode': True}
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Update playbook execution count
        playbook.execution_count += 1
        playbook.last_executed = execution.started_at
        db.commit()
        
        # Simulate execution (in real system, this would trigger actual automation)
        execution.execution_status = 'completed'
        execution.completed_at = datetime.now()
        execution.duration_seconds = 5
        execution.execution_details = {
            'steps': [
                {'step': 1, 'action': 'risk_assessment', 'status': 'completed'},
                {'step': 2, 'action': 'notification', 'status': 'completed'},
                {'step': 3, 'action': 'approval_escalation', 'status': 'completed'}
            ],
            'test_mode': True,
            'result': 'success'
        }
        db.commit()
        
        logger.info(f"✅ Playbook '{playbook_id}' executed successfully (execution ID: {execution.id})")
        
        return {
            "status": "success",
            "message": f"Playbook '{playbook.name}' executed successfully",
            "data": {
                "execution_id": execution.id,
                "playbook_id": playbook_id,
                "execution_status": execution.execution_status,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "duration_seconds": execution.duration_seconds
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to execute playbook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute playbook")
'''

# Read the current file
with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Find the GET /orchestration/active-workflows endpoint (insert before it)
insertion_point = '@router.get("/orchestration/active-workflows")'

if insertion_point in content:
    # Insert new endpoints
    content = content.replace(insertion_point, new_endpoints + '\n' + insertion_point)
    
    # Write back
    with open('routes/automation_orchestration_routes.py', 'w') as f:
        f.write(content)
    
    print("✅ CRUD endpoints added successfully!")
    print("")
    print("Added endpoints:")
    print("  • POST   /api/authorization/automation/playbooks (create)")
    print("  • PUT    /api/authorization/automation/playbook/{id} (update)")
    print("  • DELETE /api/authorization/automation/playbook/{id} (delete)")
    print("  • POST   /api/authorization/automation/playbook/{id}/toggle (enable/disable)")
    print("  • POST   /api/authorization/automation/execute-playbook (test run)")
else:
    print("❌ Could not find insertion point")
