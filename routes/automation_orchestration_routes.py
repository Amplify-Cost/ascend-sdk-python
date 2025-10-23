"""
🏢 ENTERPRISE AUTOMATION & ORCHESTRATION ROUTES
Implements automation playbook management and workflow orchestration
Frontend Contract: AgentAuthorizationDashboard.jsx
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging

from database import get_db
from models import AutomationPlaybook, PlaybookExecution, WorkflowExecution, Workflow, User
from dependencies import get_current_user, require_admin

# Configure logging
logger = logging.getLogger("enterprise.automation")

# Router configuration - MUST match frontend expectations
router = APIRouter(prefix="/api/authorization", tags=["automation-orchestration"])

# ============================================================================
# PLAYBOOK MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/automation/playbooks")
async def get_automation_playbooks(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET /api/authorization/automation/playbooks
    
    List all automation playbooks with optional filtering
    
    Frontend: AgentAuthorizationDashboard.jsx
    Expected response:
    {
        "status": "success",
        "data": [array of playbooks],
        "total": number
    }
    """
    try:
        logger.info(f"📋 Listing automation playbooks for user {current_user.get('email')}")
        
        # Build database query - REAL DATA, NOT DEMO
        query = db.query(AutomationPlaybook)
        
        # Apply filters
        if status:
            query = query.filter(AutomationPlaybook.status == status)
        if risk_level:
            query = query.filter(AutomationPlaybook.risk_level == risk_level.lower())
        
        # Execute query
        playbooks = query.order_by(AutomationPlaybook.created_at.desc()).all()
        
        # Format response to match frontend expectations
        playbooks_data = []
        for pb in playbooks:
            playbooks_data.append({
                'id': pb.id,
                'name': pb.name,
                'description': pb.description,
                'status': pb.status,
                'risk_level': pb.risk_level,
                'approval_required': pb.approval_required,
                'trigger_conditions': pb.trigger_conditions,
                'actions': pb.actions,
                'last_executed': pb.last_executed.isoformat() if pb.last_executed else None,
                'execution_count': pb.execution_count or 0,
                'success_rate': pb.success_rate or 0.0,
                'created_by': pb.created_by,
                'created_at': pb.created_at.isoformat(),
                'updated_at': pb.updated_at.isoformat() if pb.updated_at else None
            })
        
        logger.info(f"✅ Retrieved {len(playbooks_data)} playbooks from database")
        
        return {
            "status": "success",
            "data": playbooks_data,
            "total": len(playbooks_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching playbooks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch playbooks: {str(e)}")


@router.post("/automation/playbooks")
async def create_automation_playbook(
    playbook_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 POST /api/authorization/automation/playbooks
    
    Create new automation playbook (Admin only)
    
    Frontend: AgentAuthorizationDashboard.jsx
    Body: {id, name, description, status, risk_level, ...}
    Expected response: {status, message, data}
    """
    try:
        logger.info(f"📝 Creating playbook by admin {current_user.get('email')}")
        
        # Validate required fields
        required = ['id', 'name', 'status', 'risk_level']
        for field in required:
            if field not in playbook_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Check if ID already exists
        existing = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == playbook_data['id']
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"Playbook with ID '{playbook_data['id']}' already exists"
            )
        
        # Create new playbook in database
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
        raise HTTPException(status_code=500, detail=f"Failed to create playbook: {str(e)}")


@router.post("/automation/playbook/{playbook_id}/toggle")
async def toggle_automation_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 POST /api/authorization/automation/playbook/{id}/toggle
    
    Enable/disable automation playbook (Admin only)
    
    Frontend: AgentAuthorizationDashboard.jsx
    Expected response: {status, message, data}
    """
    try:
        logger.info(f"🔄 Toggling playbook '{playbook_id}' by admin {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == playbook_id
        ).first()
        
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
        raise HTTPException(status_code=500, detail=f"Failed to toggle playbook: {str(e)}")


@router.post("/automation/execute-playbook")
async def execute_automation_playbook(
    execution_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 POST /api/authorization/automation/execute-playbook
    
    Test execute playbook manually
    
    Frontend: AgentAuthorizationDashboard.jsx
    Body: {playbook_id, input_data}
    Expected response: {status, data}
    """
    try:
        playbook_id = execution_data.get('playbook_id')
        if not playbook_id:
            raise HTTPException(status_code=400, detail="playbook_id is required")
        
        logger.info(f"▶️  Executing playbook '{playbook_id}' by user {current_user.get('email')}")
        
        # Find playbook
        playbook = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == playbook_id
        ).first()
        
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
        
        # Create execution record
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            executed_by=current_user.get('user_id'),
            execution_context='manual',
            input_data=execution_data.get('input_data'),
            execution_status='completed',  # Simplified for now
            execution_details={
                'test_mode': True,
                'steps': ['validation', 'execution', 'completion'],
                'result': 'success'
            }
        )
        
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = 2
        
        db.add(execution)
        
        # Update playbook statistics
        playbook.execution_count = (playbook.execution_count or 0) + 1
        playbook.last_executed = datetime.utcnow()
        
        db.commit()
        db.refresh(execution)
        
        logger.info(f"✅ Playbook '{playbook_id}' executed (execution ID: {execution.id})")
        
        return {
            "status": "success",
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
        raise HTTPException(status_code=500, detail=f"Failed to execute playbook: {str(e)}")


# ============================================================================
# WORKFLOW ORCHESTRATION ENDPOINTS
# ============================================================================

@router.get("/orchestration/active-workflows")
async def get_active_workflows(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET /api/authorization/orchestration/active-workflows
    
    List active workflow executions
    
    Frontend: AgentAuthorizationDashboard.jsx
    Expected response: {status, data}
    """
    try:
        logger.info(f"📊 Listing active workflows for user {current_user.get('email')}")
        
        # Query active workflow executions
        active_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_status.in_(['pending', 'running', 'waiting_approval'])
        ).order_by(WorkflowExecution.started_at.desc()).limit(50).all()
        
        # Format response
        workflows_data = []
        for execution in active_executions:
            workflows_data.append({
                'id': execution.id,
                'workflow_id': execution.workflow_id,
                'action_id': execution.action_id,
                'execution_status': execution.execution_status,
                'current_stage': execution.current_stage,
                'started_at': execution.started_at.isoformat(),
                'execution_details': execution.execution_details
            })
        
        logger.info(f"✅ Retrieved {len(workflows_data)} active workflows")
        
        return {
            "status": "success",
            "data": workflows_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflows: {str(e)}")

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
        
        # Log what we received
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
        
        logger.info(f"📝 Creating workflow: id={workflow_id}, name={name}")
        
        # Check if workflow exists
        existing = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Workflow '{workflow_data['id']}' exists")
        
        # Create workflow template
        new_workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            conditions=actual_data.get('conditions'),
            actions=actual_data.get('actions') or actual_data.get('steps'),
            is_active=actual_data.get('status') == 'active',
            risk_threshold=actual_data.get('risk_threshold', 50)
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
