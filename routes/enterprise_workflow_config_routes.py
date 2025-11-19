"""
🏢 ENTERPRISE WORKFLOW CONFIGURATION ROUTES

Real database-backed workflow management with:
- Full CRUD operations on workflow configurations
- Real-time persistence (no hardcoded config files)
- Audit trail with user tracking
- Dynamic approver management
- Risk threshold editing
- SLA and escalation configuration

NO MORE HARDCODED DATA - Everything stored in PostgreSQL.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC
import json
import logging

from database import get_db
from dependencies import get_current_user, require_admin
from models import Workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/authorization", tags=["Enterprise Workflow Config"])


# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# ============================================================================

class WorkflowConfigResponse(BaseModel):
    """Response model for workflow configuration"""
    id: str
    name: str
    risk_threshold_min: Optional[int] = None
    risk_threshold_max: Optional[int] = None
    approval_levels: int
    approvers: List[str]
    timeout_hours: int
    emergency_override: bool
    escalation_minutes: int
    is_active: bool
    modified_by: Optional[str] = None
    last_modified: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowConfigUpdateRequest(BaseModel):
    """Request model for updating workflow configuration"""
    workflow_id: str = Field(..., description="Workflow ID to update (e.g., 'risk_70_89')")
    updates: Dict[str, Any] = Field(..., description="Fields to update")


class WorkflowConfigCreateRequest(BaseModel):
    """Request model for creating new workflow configuration"""
    id: str = Field(..., description="Unique workflow ID")
    name: str = Field(..., description="Human-readable workflow name")
    risk_threshold_min: int = Field(..., ge=0, le=100)
    risk_threshold_max: int = Field(..., ge=0, le=100)
    approval_levels: int = Field(default=1, ge=0, le=5)
    approvers: List[str] = Field(default_factory=list)
    timeout_hours: int = Field(default=24, ge=1)
    emergency_override: bool = Field(default=False)
    escalation_minutes: int = Field(default=480, ge=0)


# ============================================================================
# GET: Retrieve All Workflow Configurations
# ============================================================================

@router.get("/workflow-config")
async def get_workflow_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    active_only: bool = Query(default=True, description="Filter for active workflows only")
):
    """
    🏢 ENTERPRISE: Get real-time workflow configurations from database

    Returns all workflow configurations with their current settings.
    NO HARDCODED DATA - Everything from PostgreSQL.

    Query Parameters:
    - active_only: If true, returns only is_active=true workflows

    Response includes:
    - All workflow configurations
    - Last modification metadata
    - Total count
    - Storage confirmation (database, not in-memory)
    """
    try:
        # Query database for workflows
        query = db.query(Workflow)

        if active_only:
            query = query.filter(Workflow.is_active == True)

        workflows = query.all()

        if not workflows:
            logger.warning("⚠️  No workflows found in database. Database may need seeding.")
            return {
                "workflows": {},
                "last_modified": datetime.now(UTC).isoformat(),
                "modified_by": "system",
                "total_workflows": 0,
                "emergency_override_enabled": False,
                "storage_type": "database",
                "warning": "No workflows found. Run database migration to seed workflows."
            }

        # Convert to dict format expected by frontend
        workflow_data = {}
        for wf in workflows:
            # Parse approvers JSON if it's a string
            approvers_list = []
            if wf.approvers:
                if isinstance(wf.approvers, str):
                    try:
                        approvers_list = json.loads(wf.approvers)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse approvers for workflow {wf.id}")
                        approvers_list = []
                elif isinstance(wf.approvers, list):
                    approvers_list = wf.approvers

            workflow_data[wf.id] = {
                "name": wf.name,
                "risk_threshold_min": wf.risk_threshold_min,
                "risk_threshold_max": wf.risk_threshold_max,
                "approval_levels": wf.approval_levels or 1,
                "approvers": approvers_list,
                "timeout_hours": wf.timeout_hours or 24,
                "emergency_override": wf.emergency_override or False,
                "escalation_minutes": wf.escalation_minutes or 480,
                "is_active": wf.is_active if wf.is_active is not None else True,
                "modified_by": wf.modified_by,
                "last_modified": wf.last_modified.isoformat() if wf.last_modified else None
            }

        # Calculate metadata
        latest_modified = max(
            (wf.last_modified for wf in workflows if wf.last_modified),
            default=datetime.now(UTC)
        )

        logger.info(f"✅ ENTERPRISE: Loaded {len(workflows)} workflow configs from database")

        return {
            "workflows": workflow_data,
            "last_modified": latest_modified.isoformat(),
            "modified_by": "database",
            "total_workflows": len(workflows),
            "emergency_override_enabled": any(wf.emergency_override for wf in workflows),
            "storage_type": "database",  # ← REAL PERSISTENCE!
            "active_count": len([wf for wf in workflows if wf.is_active])
        }

    except Exception as e:
        logger.error(f"❌ Failed to get workflow config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow configuration: {str(e)}")


# ============================================================================
# POST: Update Workflow Configuration
# ============================================================================

@router.post("/workflow-config")
async def update_workflow_config(
    request: WorkflowConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Update workflow configuration in database (admin only)

    Full persistence - changes saved to PostgreSQL and survive server restarts.
    NO IN-MEMORY FALLBACK - Database only.

    Request Body:
    {
        "workflow_id": "risk_70_89",
        "updates": {
            "timeout_hours": 6,
            "approval_levels": 3,
            "approvers": ["user1@company.com", "user2@company.com"]
        }
    }

    Updateable Fields:
    - name, description
    - risk_threshold_min, risk_threshold_max
    - approval_levels (0-5)
    - approvers (list of emails/user IDs)
    - timeout_hours
    - emergency_override (boolean)
    - escalation_minutes
    - is_active (boolean)

    Returns:
    - Confirmation message
    - Updated workflow data
    - Audit metadata (modified_by, timestamp)
    - storage_type: "database" (always)
    """
    try:
        workflow_id = request.workflow_id
        updates = request.updates

        # Query workflow from database
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            logger.error(f"❌ Workflow '{workflow_id}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' not found in database. Available workflows: Check /api/authorization/workflow-config"
            )

        # Track what fields are being updated
        updated_fields = []

        # Update workflow attributes
        for key, value in updates.items():
            if not hasattr(workflow, key):
                logger.warning(f"⚠️  Skipping invalid field: {key}")
                continue

            # Handle JSON fields (approvers)
            if key == "approvers":
                if isinstance(value, list):
                    setattr(workflow, key, value)  # JSONB handles list directly
                    updated_fields.append(key)
                else:
                    logger.warning(f"⚠️  Approvers must be a list, got: {type(value)}")
            else:
                # Standard fields
                setattr(workflow, key, value)
                updated_fields.append(key)

        # Update audit fields
        workflow.modified_by = current_user.get("email", f"user_{current_user.get('user_id')}")
        workflow.last_modified = datetime.now(UTC)
        workflow.updated_at = datetime.now(UTC)

        try:
            db.commit()
            db.refresh(workflow)

            logger.info(
                f"✅ ENTERPRISE: Workflow {workflow_id} updated in database "
                f"by {workflow.modified_by}: {updated_fields}"
            )

            # Parse approvers for response
            approvers_list = workflow.approvers if isinstance(workflow.approvers, list) else []

            return {
                "message": "✅ Workflow configuration updated successfully",
                "workflow_id": workflow_id,
                "updated_fields": updated_fields,
                "modified_by": workflow.modified_by,
                "timestamp": workflow.last_modified.isoformat(),
                "storage_type": "database",  # ← REAL PERSISTENCE!
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "risk_threshold_min": workflow.risk_threshold_min,
                    "risk_threshold_max": workflow.risk_threshold_max,
                    "approval_levels": workflow.approval_levels,
                    "approvers": approvers_list,
                    "timeout_hours": workflow.timeout_hours,
                    "emergency_override": workflow.emergency_override,
                    "escalation_minutes": workflow.escalation_minutes,
                    "is_active": workflow.is_active
                }
            }

        except Exception as db_error:
            db.rollback()
            logger.error(f"❌ Database commit failed: {str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database update failed: {str(db_error)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update workflow config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update workflow configuration: {str(e)}"
        )


# ============================================================================
# POST: Create New Workflow Configuration
# ============================================================================

@router.post("/workflow-config/create")
async def create_workflow_config(
    request: WorkflowConfigCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Create new workflow configuration (admin only)

    Allows creating custom workflows beyond the default risk-based ones.
    Useful for specialized approval workflows.
    """
    try:
        # Check if workflow ID already exists
        existing = db.query(Workflow).filter(Workflow.id == request.id).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow with ID '{request.id}' already exists"
            )

        # Create new workflow
        workflow = Workflow(
            id=request.id,
            name=request.name,
            description=f"Custom workflow created by {current_user.get('email')}",
            status="active",
            risk_threshold_min=request.risk_threshold_min,
            risk_threshold_max=request.risk_threshold_max,
            approval_levels=request.approval_levels,
            approvers=request.approvers,  # JSONB handles list directly
            timeout_hours=request.timeout_hours,
            emergency_override=request.emergency_override,
            escalation_minutes=request.escalation_minutes,
            is_active=True,
            created_by=current_user.get("email"),
            modified_by=current_user.get("email"),
            last_modified=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        logger.info(f"✅ ENTERPRISE: New workflow '{request.id}' created by {current_user.get('email')}")

        return {
            "message": "✅ Workflow configuration created successfully",
            "workflow_id": workflow.id,
            "created_by": workflow.created_by,
            "timestamp": workflow.created_at.isoformat(),
            "storage_type": "database"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


# ============================================================================
# DELETE: Delete Workflow Configuration
# ============================================================================

@router.delete("/workflow-config/{workflow_id}")
async def delete_workflow_config(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ENTERPRISE: Soft-delete workflow configuration (admin only)

    Sets is_active=false instead of deleting record.
    Preserves audit trail.
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

        # Soft delete
        workflow.is_active = False
        workflow.modified_by = current_user.get("email")
        workflow.last_modified = datetime.now(UTC)
        workflow.status = "inactive"

        db.commit()

        logger.info(f"✅ ENTERPRISE: Workflow '{workflow_id}' deactivated by {current_user.get('email')}")

        return {
            "message": f"✅ Workflow '{workflow_id}' deactivated successfully",
            "workflow_id": workflow_id,
            "modified_by": current_user.get("email"),
            "timestamp": workflow.last_modified.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")


# ============================================================================
# GET: Get Single Workflow Configuration
# ============================================================================

@router.get("/workflow-config/{workflow_id}")
async def get_single_workflow_config(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Get specific workflow configuration

    Returns detailed configuration for a single workflow.
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

        # Parse approvers
        approvers_list = workflow.approvers if isinstance(workflow.approvers, list) else []

        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "risk_threshold_min": workflow.risk_threshold_min,
            "risk_threshold_max": workflow.risk_threshold_max,
            "approval_levels": workflow.approval_levels,
            "approvers": approvers_list,
            "timeout_hours": workflow.timeout_hours,
            "emergency_override": workflow.emergency_override,
            "escalation_minutes": workflow.escalation_minutes,
            "is_active": workflow.is_active,
            "created_by": workflow.created_by,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "modified_by": workflow.modified_by,
            "last_modified": workflow.last_modified.isoformat() if workflow.last_modified else None,
            "storage_type": "database"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")
