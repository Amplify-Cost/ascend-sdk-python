"""
Add missing /workflows/create endpoint that frontend is calling
"""

# Read current routes file
with open('routes/automation_orchestration_routes.py', 'r') as f:
    content = f.read()

# Add workflow creation endpoint
workflow_endpoint = '''

# ============================================================================
# WORKFLOW TEMPLATE MANAGEMENT (Separate from Playbooks)
# ============================================================================

@router.post("/workflows/create")
async def create_workflow_template(
    workflow_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 POST /api/authorization/workflows/create
    
    Create workflow template (NOT playbook)
    This is for workflow templates, playbooks use /automation/playbooks
    
    Frontend: AgentAuthorizationDashboard.jsx (workflow section)
    """
    try:
        logger.info(f"📝 Creating workflow template by {current_user.get('email')}")
        
        # Validate required fields
        required = ['id', 'name', 'description']
        for field in required:
            if field not in workflow_data:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Check if workflow exists
        existing = db.query(Workflow).filter(Workflow.id == workflow_data['id']).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Workflow '{workflow_data['id']}' exists")
        
        # Create workflow template
        new_workflow = Workflow(
            id=workflow_data['id'],
            name=workflow_data['name'],
            description=workflow_data['description'],
            trigger_type=workflow_data.get('trigger_type', 'manual'),
            conditions=workflow_data.get('conditions'),
            actions=workflow_data.get('actions'),
            is_active=workflow_data.get('is_active', True),
            risk_threshold=workflow_data.get('risk_threshold', 50)
        )
        
        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)
        
        logger.info(f"✅ Workflow template '{new_workflow.id}' created")
        
        return {
            "status": "success",
            "message": f"Workflow '{new_workflow.name}' created successfully",
            "data": {
                "id": new_workflow.id,
                "name": new_workflow.name,
                "is_active": new_workflow.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.get("/workflows")
async def list_workflow_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET /api/authorization/workflows
    
    List all workflow templates
    """
    try:
        workflows = db.query(Workflow).all()
        
        workflows_data = []
        for wf in workflows:
            workflows_data.append({
                'id': wf.id,
                'name': wf.name,
                'description': wf.description,
                'trigger_type': wf.trigger_type,
                'is_active': wf.is_active,
                'risk_threshold': wf.risk_threshold
            })
        
        return {
            "status": "success",
            "data": workflows_data,
            "total": len(workflows_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
'''

# Insert before the final line
content = content.rstrip() + workflow_endpoint

# Write back
with open('routes/automation_orchestration_routes.py', 'w') as f:
    f.write(content)

print("✅ Added /workflows/create and /workflows endpoints")
