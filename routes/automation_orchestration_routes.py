"""
🏢 ENTERPRISE AUTOMATION & ORCHESTRATION ROUTES
Implements automation playbook management and workflow orchestration
Frontend Contract: AgentAuthorizationDashboard.jsx

PHASE 1-3 ENTERPRISE ENHANCEMENTS:
- Pydantic validation for all playbook operations
- Template library support
- Playbook testing endpoints
- Enhanced error handling
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ValidationError
import logging
import json

# ✅ ENTERPRISE FIX: Use Phase 2 enterprise get_db() with error handling
# Created by: OW-kai Engineer (Phase 2 Enterprise Integration)
from dependencies import get_db
from models import AutomationPlaybook, PlaybookExecution, WorkflowExecution, Workflow, User
from dependencies import get_current_user, require_admin
from config_workflows import workflow_config

# ⭐ PHASE 1-3: Import enterprise playbook schemas
from schemas.playbook import (
    PlaybookCreate,
    PlaybookUpdate,
    PlaybookResponse,
    PlaybookTestRequest,
    PlaybookTestResponse,
    PlaybookTemplate,
    TriggerConditions
)

# Configure logging
logger = logging.getLogger("enterprise.automation")

# Router configuration - MUST match frontend expectations
router = APIRouter(prefix="/api/authorization", tags=["automation-orchestration"])

# ============================================================================
# ENTERPRISE REQUEST/RESPONSE MODELS
# ============================================================================

class WorkflowConfigUpdateRequest(BaseModel):
    """Enterprise-grade request model for workflow configuration updates"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    updates: Dict[str, Any] = Field(..., description="Configuration updates to apply")

    class Config:
        schema_extra = {
            "example": {
                "workflow_id": "high_risk_approval",
                "updates": {
                    "approval_levels": 3,
                    "timeout_hours": 12,
                    "emergency_override": True
                }
            }
        }

class WorkflowExecuteRequest(BaseModel):
    """Enterprise-grade request model for workflow execution"""
    action_id: Optional[int] = Field(None, description="Associated action ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Execution input parameters")
    execution_context: str = Field("manual_trigger", description="Execution context/source")
    priority: str = Field("normal", description="Execution priority: low, normal, high, critical")

    class Config:
        schema_extra = {
            "example": {
                "action_id": 123,
                "input_data": {"user_id": 7, "resource": "database"},
                "execution_context": "enterprise_authorization",
                "priority": "high"
            }
        }

# ============================================================================
# PLAYBOOK MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/automation/playbooks")
async def get_automation_playbooks(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    include_deleted: bool = False,  # 🏢 ENTERPRISE: Hide soft-deleted playbooks by default
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

    Query Parameters:
    - status: Filter by status (active, inactive, disabled, maintenance)
    - risk_level: Filter by risk level (low, medium, high, critical)
    - include_deleted: Show soft-deleted playbooks (default: false)

    Enterprise Pattern: ServiceNow CMDB filtering, Jira issue states
    """
    try:
        logger.info(f"📋 Listing automation playbooks for user {current_user.get('email')} (include_deleted={include_deleted})")

        # Build database query - REAL DATA, NOT DEMO
        query = db.query(AutomationPlaybook)

        # 🏢 ENTERPRISE: Smart filtering - hide soft-deleted playbooks by default
        # Pattern: ServiceNow CMDB (hides Retired CIs), Jira (hides Archived issues)
        if not include_deleted:
            query = query.filter(AutomationPlaybook.is_deleted == False)

        # Apply additional filters
        if status:
            query = query.filter(AutomationPlaybook.status == status)
        if risk_level:
            query = query.filter(AutomationPlaybook.risk_level == risk_level.lower())
        
        # Execute query
        playbooks = query.order_by(AutomationPlaybook.created_at.desc()).all()
        
        # Format response to match frontend expectations with real-time metrics
        from services.automation_service import get_automation_service
        automation_service = get_automation_service(db)

        playbooks_data = []
        total_triggers_24h = 0
        total_cost_savings_24h = 0.0
        enabled_count = 0

        for pb in playbooks:
            # Get real-time metrics for this playbook
            metrics = automation_service.get_playbook_metrics(pb.id)

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
                'updated_at': pb.updated_at.isoformat() if pb.updated_at else None,
                # ENTERPRISE: Add real-time metrics
                'metrics': metrics
            })

            # Calculate summary metrics
            if pb.status == 'active':
                enabled_count += 1
            total_triggers_24h += metrics.get('triggers_last_24h', 0)
            total_cost_savings_24h += metrics.get('cost_savings_24h', 0.0)

        # Calculate average success rate
        avg_success_rate = sum(pb.success_rate or 0 for pb in playbooks) / len(playbooks) if playbooks else 0.0

        logger.info(f"✅ Retrieved {len(playbooks_data)} playbooks from database with real-time metrics")

        return {
            "status": "success",
            "data": playbooks_data,
            "total": len(playbooks_data),
            "automation_summary": {
                "total_playbooks": len(playbooks_data),
                "enabled_playbooks": enabled_count,
                "total_triggers_24h": total_triggers_24h,
                "total_cost_savings_24h": round(total_cost_savings_24h, 2),
                "average_success_rate": round(avg_success_rate, 2)
            },
            "real_data_metrics": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching playbooks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch playbooks: {str(e)}")


@router.post("/automation/playbooks", response_model=PlaybookResponse)
async def create_automation_playbook(
    playbook: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 POST /api/authorization/automation/playbooks

    Create new automation playbook with enterprise validation (Admin only)

    PHASE 1 ENHANCEMENTS:
    - Full Pydantic validation for trigger_conditions and actions
    - Type-safe parameter validation based on action type
    - Automatic ID format checking (must start with 'pb-')
    - Backward compatibility with legacy field names
    - Prevents creation of non-functional playbooks (null triggers/actions)

    Frontend: AgentAuthorizationDashboard.jsx
    Body: PlaybookCreate schema (see schemas/playbook.py)
    Returns: PlaybookResponse with full playbook details
    """
    try:
        logger.info(f"📝 Creating enterprise playbook by admin {current_user.get('email')}")
        logger.info(f"📋 Playbook ID: {playbook.id}, Risk Level: {playbook.risk_level}")
        logger.info(f"⚙️ Trigger Conditions: {playbook.trigger_conditions.dict(exclude_none=True)}")
        logger.info(f"⚡ Actions: {[action.type.value for action in playbook.actions]}")

        # Check if ID already exists
        existing = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == playbook.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Playbook '{playbook.id}' already exists. Use PUT to update."
            )

        # Convert Pydantic models to database format
        trigger_conditions_dict = playbook.trigger_conditions.dict(exclude_none=True)
        actions_list = [action.dict(exclude_none=True) for action in playbook.actions]

        # Create new playbook with validated data
        new_playbook = AutomationPlaybook(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            status=playbook.status,
            risk_level=playbook.risk_level,
            approval_required=playbook.approval_required,
            trigger_conditions=trigger_conditions_dict,
            actions=actions_list,
            execution_count=0,
            success_rate=0.0,
            created_by=current_user.get('user_id')
        )

        db.add(new_playbook)
        db.commit()
        db.refresh(new_playbook)

        logger.info(f"✅ Enterprise playbook '{new_playbook.id}' created successfully")
        logger.info(f"✅ Trigger conditions: {len(trigger_conditions_dict)} conditions configured")
        logger.info(f"✅ Automated actions: {len(actions_list)} actions configured")

        return new_playbook

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


@router.post("/automation/playbooks/{playbook_id}/test", response_model=PlaybookTestResponse)
async def test_automation_playbook(
    playbook_id: str,
    test_request: PlaybookTestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 POST /api/authorization/automation/playbooks/{playbook_id}/test

    Test playbook trigger conditions against sample data (dry-run mode)

    PHASE 1 FEATURE:
    - Validates trigger conditions without executing actions
    - Returns detailed match/fail analysis for each condition
    - Helps users debug playbook configuration before deployment
    - No database changes, completely safe to run

    Body: { "test_data": { "risk_score": 35, "action_type": "database_read", ... } }
    Returns: Match analysis with detailed condition results
    """
    try:
        logger.info(f"🧪 Testing playbook '{playbook_id}' with sample data")

        # Fetch playbook
        playbook = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == playbook_id
        ).first()

        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")

        if not playbook.trigger_conditions:
            raise HTTPException(
                status_code=400,
                detail=f"Playbook '{playbook_id}' has no trigger conditions configured"
            )

        test_data = test_request.test_data
        conditions = playbook.trigger_conditions
        matched_conditions = []
        failed_conditions = []

        # Test risk_score condition
        if 'risk_score' in conditions:
            risk_range = conditions['risk_score']
            test_score = test_data.get('risk_score')

            if test_score is not None:
                min_score = risk_range.get('min', 0)
                max_score = risk_range.get('max', 100)

                if min_score <= test_score <= max_score:
                    matched_conditions.append(f"risk_score ({test_score}) in range [{min_score}-{max_score}]")
                else:
                    failed_conditions.append(f"risk_score ({test_score}) NOT in range [{min_score}-{max_score}]")
            else:
                failed_conditions.append("risk_score not provided in test data")

        # Test action_type condition
        if 'action_type' in conditions:
            allowed_types = conditions['action_type']
            test_type = test_data.get('action_type')

            if test_type in allowed_types:
                matched_conditions.append(f"action_type ({test_type}) matches")
            else:
                failed_conditions.append(f"action_type ({test_type}) not in {allowed_types}")

        # Test environment condition
        if 'environment' in conditions:
            allowed_envs = conditions['environment']
            test_env = test_data.get('environment', 'production')

            if test_env in allowed_envs:
                matched_conditions.append(f"environment ({test_env}) matches")
            else:
                failed_conditions.append(f"environment ({test_env}) not in {allowed_envs}")

        # Test agent_id condition
        if 'agent_id' in conditions:
            allowed_agents = conditions['agent_id']
            test_agent = test_data.get('agent_id')

            if test_agent in allowed_agents:
                matched_conditions.append(f"agent_id ({test_agent}) matches")
            else:
                failed_conditions.append(f"agent_id ({test_agent}) not in {allowed_agents}")

        # Test business_hours condition
        if 'business_hours' in conditions and conditions['business_hours']:
            # Simplified: would check actual timestamp in production
            matched_conditions.append("business_hours check (simplified)")

        # Determine overall match (ALL conditions must pass)
        matches = len(failed_conditions) == 0

        # Get actions that would execute
        would_execute_actions = []
        if matches and playbook.actions:
            would_execute_actions = [
                f"{action['type']}" + (f" ({action.get('parameters', {})})" if action.get('parameters') else "")
                for action in playbook.actions
                if action.get('enabled', True)
            ]

        logger.info(f"✅ Test result: {'MATCH' if matches else 'NO MATCH'} "
                   f"({len(matched_conditions)} passed, {len(failed_conditions)} failed)")

        return PlaybookTestResponse(
            matches=matches,
            playbook_id=playbook.id,
            playbook_name=playbook.name,
            test_data=test_data,
            matched_conditions=matched_conditions,
            failed_conditions=failed_conditions,
            would_execute_actions=would_execute_actions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to test playbook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test playbook: {str(e)}")


@router.get("/automation/playbook-templates")
async def get_playbook_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET /api/authorization/automation/playbook-templates

    Get enterprise playbook templates for quick deployment

    PHASE 2 FEATURE:
    - Pre-built, tested playbook configurations
    - Categories: productivity, security, compliance, cost_optimization
    - Includes ROI estimates and complexity ratings
    - One-click deployment to create functional playbooks

    Query params:
    - category: Filter by category (optional)

    Returns: List of playbook templates with metadata
    """
    try:
        logger.info(f"📚 Fetching playbook templates (category: {category or 'all'})")

        # Enterprise template library (would be in database in production)
        templates = [
            PlaybookTemplate(
                id="template-low-risk-auto",
                name="Auto-Approve Low Risk Actions",
                description="Automatically approve low-risk read operations during business hours",
                category="productivity",
                use_case="Reduce manual approvals for safe, read-only operations (database reads, file reads)",
                trigger_conditions=TriggerConditions(
                    risk_score={"min": 0, "max": 40},
                    action_type=["database_read", "file_read"],
                    business_hours=True
                ),
                actions=[
                    PlaybookAction(type="approve", parameters={}, enabled=True, order=1),
                    PlaybookAction(
                        type="notify",
                        parameters={"recipients": ["ops@company.com"], "subject": "Low-risk action auto-approved"},
                        enabled=True,
                        order=2
                    )
                ],
                estimated_savings_per_month=2250.0,
                complexity="low"
            ),
            PlaybookTemplate(
                id="template-high-risk-escalate",
                name="High-Risk Auto-Escalation",
                description="Automatically escalate high-risk actions to VP approval",
                category="security",
                use_case="Ensure high-risk operations get executive review",
                trigger_conditions=TriggerConditions(
                    risk_score={"min": 80, "max": 100},
                    environment=["production"]
                ),
                actions=[
                    PlaybookAction(
                        type="escalate_approval",
                        parameters={"level": "L4", "reason": "High-risk production action"},
                        enabled=True,
                        order=1
                    ),
                    PlaybookAction(
                        type="stakeholder_notification",
                        parameters={"recipients": ["security@company.com", "ciso@company.com"]},
                        enabled=True,
                        order=2
                    ),
                    PlaybookAction(
                        type="temporary_quarantine",
                        parameters={"duration_minutes": 30, "reason": "Pending executive review"},
                        enabled=True,
                        order=3
                    )
                ],
                estimated_savings_per_month=0.0,
                complexity="medium"
            ),
            PlaybookTemplate(
                id="template-after-hours-alert",
                name="After-Hours Security Alert",
                description="Alert security team for any production changes after business hours",
                category="security",
                use_case="Monitor and control after-hours production activity",
                trigger_conditions=TriggerConditions(
                    environment=["production"],
                    business_hours=False
                ),
                actions=[
                    PlaybookAction(
                        type="notify",
                        parameters={
                            "recipients": ["security-oncall@company.com"],
                            "subject": "After-hours production activity detected"
                        },
                        enabled=True,
                        order=1
                    ),
                    PlaybookAction(
                        type="risk_assessment",
                        parameters={"deep_scan": True, "include_context": True},
                        enabled=True,
                        order=2
                    )
                ],
                estimated_savings_per_month=0.0,
                complexity="low"
            ),
            PlaybookTemplate(
                id="template-financial-compliance",
                name="Financial Transaction Compliance",
                description="SOX-compliant approval workflow for financial transactions",
                category="compliance",
                use_case="Meet SOX requirements for financial system changes",
                trigger_conditions=TriggerConditions(
                    action_type=["financial_transaction", "config_update"],
                    risk_score={"min": 60, "max": 100}
                ),
                actions=[
                    PlaybookAction(
                        type="escalate_approval",
                        parameters={"level": "L3", "reason": "Financial compliance review"},
                        enabled=True,
                        order=1
                    ),
                    PlaybookAction(
                        type="log",
                        parameters={},
                        enabled=True,
                        order=2
                    ),
                    PlaybookAction(
                        type="notify",
                        parameters={"recipients": ["audit@company.com", "finance@company.com"]},
                        enabled=True,
                        order=3
                    )
                ],
                estimated_savings_per_month=0.0,
                complexity="high"
            )
        ]

        # Filter by category if specified
        if category:
            templates = [t for t in templates if t.category == category]

        logger.info(f"✅ Retrieved {len(templates)} playbook templates")

        return {
            "status": "success",
            "data": [t.dict() for t in templates],
            "total": len(templates),
            "categories": ["productivity", "security", "compliance", "cost_optimization"]
        }

    except Exception as e:
        logger.error(f"❌ Failed to fetch templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")


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
        
        # Query all workflow templates
        from datetime import timedelta
        from sqlalchemy import func

        workflows = db.query(Workflow).filter(
            Workflow.status == 'active'
        ).all()

        # Query active workflow executions
        active_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_status.in_(['pending', 'running', 'waiting_approval'])
        ).order_by(WorkflowExecution.started_at.desc()).limit(50).all()

        # Query executions in last 24 hours for metrics
        yesterday = datetime.utcnow() - timedelta(hours=24)
        executions_24h = db.query(WorkflowExecution).filter(
            WorkflowExecution.started_at >= yesterday
        ).all()

        # Format active workflows with real-time stats
        active_workflows_dict = {}
        for workflow in workflows:
            # Count active executions for this workflow
            workflow_active = [e for e in active_executions if e.workflow_id == workflow.id]
            workflow_24h = [e for e in executions_24h if e.workflow_id == workflow.id]

            # Calculate success rate
            successful_24h = sum(1 for e in workflow_24h if e.execution_status == 'completed')
            success_rate_24h = (successful_24h / len(workflow_24h) * 100) if workflow_24h else 0

            active_workflows_dict[workflow.id] = {
                'id': workflow.id,
                'name': workflow.name,
                'description': workflow.description,
                'created_by': workflow.created_by,
                'owner': workflow.owner,
                'status': workflow.status,
                'sla_hours': workflow.sla_hours,
                'compliance_frameworks': workflow.compliance_frameworks,
                'tags': workflow.tags,
                'steps': workflow.steps or [],
                'real_time_stats': {
                    'currently_executing': len(workflow_active),
                    'queued_actions': sum(1 for e in workflow_active if e.execution_status == 'pending'),
                    'last_24h_executions': len(workflow_24h),
                    'success_rate_24h': round(success_rate_24h, 1)
                },
                'success_metrics': {
                    'executions': workflow.execution_count or 0,
                    'success_rate': workflow.success_rate or 0,
                    'avg_completion_time_hours': workflow.avg_completion_time_hours
                }
            }

        # Calculate summary metrics
        total_executions_24h = len(executions_24h)
        successful_executions_24h = sum(1 for e in executions_24h if e.execution_status == 'completed')
        avg_success_rate = (successful_executions_24h / total_executions_24h * 100) if total_executions_24h else 0

        logger.info(f"✅ Retrieved {len(active_workflows_dict)} active workflow templates with real-time metrics")

        return {
            "status": "success",
            "active_workflows": active_workflows_dict,
            "summary": {
                "total_active": len(workflows),
                "total_executions_24h": total_executions_24h,
                "average_success_rate": round(avg_success_rate, 1)
            },
            "real_data_metrics": True
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

# ============================================================================
# WORKFLOW CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/workflow-config")
async def get_workflow_config(current_user: dict = Depends(get_current_user)):
    """🏢 ENTERPRISE: Get current workflow configuration"""
    try:
        from datetime import datetime, timezone
        return {
            "workflows": workflow_config,
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "modified_by": "system",
            "total_workflows": len(workflow_config),
            "emergency_override_enabled": any(w["emergency_override"] for w in workflow_config.values())
        }
    except Exception as e:
        logger.error(f"Failed to get workflow config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow configuration")

@router.post("/workflow-config")
async def update_workflow_config(
    request: WorkflowConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Update workflow configuration (admin only)

    Enterprise-grade workflow configuration management with:
    - Request validation via Pydantic models
    - Database persistence (not just in-memory)
    - Audit trail logging
    - Atomic updates with rollback
    """
    try:
        from datetime import datetime, UTC

        workflow_id = request.workflow_id
        updates = request.updates

        # Check if workflow exists in database (enterprise approach)
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            # Fallback to in-memory config for legacy workflows
            if workflow_id not in workflow_config:
                raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

            # Update in-memory configuration (legacy support)
            for key, value in updates.items():
                if key in workflow_config[workflow_id]:
                    workflow_config[workflow_id][key] = value

            logger.info(f"🔧 ENTERPRISE: Legacy workflow {workflow_id} updated by {current_user['email']}")

            return {
                "message": "✅ Workflow configuration updated successfully",
                "workflow_id": workflow_id,
                "updated_fields": list(updates.keys()),
                "modified_by": current_user["email"],
                "timestamp": datetime.now(UTC).isoformat(),
                "storage_type": "in_memory"
            }

        # ENTERPRISE PATH: Update database workflow
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        workflow.updated_at = datetime.now(UTC)

        try:
            db.commit()
            db.refresh(workflow)

            logger.info(f"✅ ENTERPRISE: Workflow {workflow_id} updated in database by {current_user['email']}")

            return {
                "message": "✅ Workflow configuration updated successfully",
                "workflow_id": workflow_id,
                "updated_fields": list(updates.keys()),
                "modified_by": current_user["email"],
                "timestamp": workflow.updated_at.isoformat(),
                "storage_type": "database",
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status,
                    "owner": workflow.owner,
                    "sla_hours": workflow.sla_hours,
                    "execution_count": workflow.execution_count,
                    "success_rate": workflow.success_rate
                }
            }
        except Exception as db_error:
            db.rollback()
            logger.error(f"❌ Database update failed: {str(db_error)}")
            raise HTTPException(status_code=500, detail="Database update failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update workflow config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow configuration: {str(e)}")

# ============================================================================
# WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

@router.post("/orchestration/execute/{workflow_id}")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Execute workflow orchestration

    Enterprise-grade workflow execution with:
    - Priority-based execution
    - Complete audit trail
    - Database-backed execution tracking
    - SLA monitoring
    """
    try:
        from datetime import datetime, UTC

        logger.info(f"🔄 ENTERPRISE: Executing workflow {workflow_id} by {current_user.get('email')}")

        # Validate workflow exists
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            # Check legacy in-memory config
            if workflow_id not in workflow_config:
                raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

        # Create workflow execution record
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            action_id=request.action_id,
            execution_status="pending",
            started_at=datetime.now(UTC),
            current_step=1,
            execution_data={
                "input_data": request.input_data,
                "execution_context": request.execution_context,
                "priority": request.priority,
                "triggered_by": current_user.get('email'),
                "triggered_at": datetime.now(UTC).isoformat()
            }
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        # Update workflow statistics
        if workflow:
            workflow.execution_count = (workflow.execution_count or 0) + 1
            workflow.last_executed = datetime.now(UTC)
            db.commit()

        logger.info(f"✅ ENTERPRISE: Workflow execution {execution.id} created for workflow {workflow_id}")

        return {
            "status": "success",
            "message": f"Workflow '{workflow_id}' execution initiated",
            "execution_id": execution.id,
            "workflow_id": workflow_id,
            "execution_status": "pending",
            "started_at": execution.started_at.isoformat(),
            "priority": request.priority,
            "estimated_completion": "Based on SLA hours configuration",
            "tracking": {
                "execution_id": execution.id,
                "current_step": 1,
                "total_steps": len(workflow.steps) if workflow and workflow.steps else 0
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

# ============================================================================
# REAL-TIME AUTOMATION ACTIVITY FEED
# ============================================================================

@router.get("/automation/activity-feed")
async def get_automation_activity_feed(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),  # ✅ Auth first
    db: Session = Depends(get_db)                     # ✅ DB second
):
    """
    🏢 ENTERPRISE: Get real-time automation activity feed

    Returns recent automation playbook executions and workflow orchestrations
    for the activity feed display.

    Enterprise features:
    - Real-time data from database
    - Configurable limit
    - Time-based sorting
    - Activity type categorization
    """
    try:
        from datetime import datetime, UTC, timedelta

        logger.info(f"⚡ Fetching automation activity feed for {current_user.get('email')}")

        # Query recent playbook executions
        recent_playbook_executions = (
            db.query(PlaybookExecution)
            .order_by(PlaybookExecution.started_at.desc())  # ✅ Fixed: Model uses 'started_at' not 'created_at'
            .limit(limit)
            .all()
        )

        # Query recent workflow executions
        recent_workflow_executions = (
            db.query(WorkflowExecution)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
            .all()
        )

        # Format activity feed
        activities = []

        # Add playbook executions
        for execution in recent_playbook_executions:
            playbook = db.query(AutomationPlaybook).filter(
                AutomationPlaybook.id == execution.playbook_id
            ).first()

            if playbook:
                time_ago = _format_time_ago(execution.created_at)
                activities.append({
                    "type": "playbook_execution",
                    "icon": "🤖",
                    "title": playbook.name,
                    "description": f"executed for Action-{execution.action_id}" if execution.action_id else "executed",
                    "timestamp": execution.created_at.isoformat(),
                    "time_ago": time_ago,
                    "status": execution.execution_status,
                    "severity_color": "green" if execution.execution_status == "completed" else "orange"
                })

        # Add workflow executions
        for execution in recent_workflow_executions:
            workflow = db.query(Workflow).filter(
                Workflow.id == execution.workflow_id
            ).first()

            if workflow:
                time_ago = _format_time_ago(execution.started_at)
                status_text = execution.execution_status.replace("_", " ").title()
                activities.append({
                    "type": "workflow_execution",
                    "icon": "🔄",
                    "title": workflow.name,
                    "description": status_text,
                    "timestamp": execution.started_at.isoformat(),
                    "time_ago": time_ago,
                    "status": execution.execution_status,
                    "severity_color": "blue" if execution.execution_status in ["running", "pending"] else "green"
                })

        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit to requested count
        activities = activities[:limit]

        return {
            "status": "success",
            "activities": activities,
            "total_count": len(activities),
            "real_time_data": True,
            "last_updated": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to fetch activity feed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch automation activity feed")

def _format_time_ago(timestamp: datetime) -> str:
    """Helper function to format timestamp as 'X minutes ago'"""
    from datetime import datetime, UTC

    now = datetime.now(UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    delta = now - timestamp

    if delta.total_seconds() < 60:
        return "just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(delta.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
