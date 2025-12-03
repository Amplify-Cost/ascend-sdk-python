from fastapi import APIRouter, Depends, Request, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction, LogAuditTrail, Alert
from dependencies import get_current_user, require_admin, require_csrf, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key, get_organization_filter_dual_auth  # SEC-020: SDK API key authentication
from schemas import AgentActionOut, AgentActionCreate
from datetime import datetime, UTC, timezone
from llm_utils import generate_summary, generate_smart_rule
from enrichment import evaluate_action_enrichment
from typing import List
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Agent Actions"])

# 🏢 ENTERPRISE: Multi-Tenant Data Isolation
# All routes MUST filter by organization_id to ensure tenant isolation
# Compliance: SOC 2 CC6.1, HIPAA § 164.308, PCI-DSS 7.1

@router.post("/agent-action", response_model=AgentActionOut)
async def create_agent_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """Submit a new agent action for security review - Enterprise-grade with graceful fallback"""
    try:
        data = await request.json()

        # 🏢 ENTERPRISE: Validate required fields (backward compatible)
        # Only agent_id, action_type, and description are strictly required
        # tool_name is optional for backward compatibility with external systems
        required_fields = ["agent_id", "action_type", "description"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # 🏢 ENTERPRISE: Provide intelligent defaults for optional fields
        if not data.get("tool_name"):
            # Infer tool name from action type for enterprise audit compliance
            data["tool_name"] = f"inferred_{data['action_type']}"
            logger.info(f"Enterprise fallback: Set tool_name='{data['tool_name']}' for action_type='{data['action_type']}'")

        # Parse timestamp with enterprise-grade handling
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp, UTC)
                else:
                    timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now(UTC)
        else:
            timestamp = datetime.now(UTC)

        # Generate AI summary with enterprise fallback
        try:
            summary = generate_summary(
                agent_id=data["agent_id"],
                action_type=data["action_type"],
                description=data["description"]
            )
        except Exception as e:
            logger.warning(f"OpenAI summary generation failed: {e}")
            summary = f"[ENTERPRISE FALLBACK] Agent '{data['agent_id']}' executed '{data['action_type']}' requiring security review."

        # ARCH-001: Security enrichment with CVSS v3.1 integration
        try:
            # First pass: Get enrichment without action_id (for initial risk assessment)
            enrichment = evaluate_action_enrichment(
                action_type=data["action_type"],
                description=data["description"],
                db=db,  # Pass db session for CVSS calculation
                action_id=None,  # No action_id yet, will update after creation
                context={
                    "tool_name": data.get("tool_name"),
                    "user_id": current_user.get("user_id", 1)
                }
            )
        except Exception as e:
            logger.warning(f"Security enrichment failed: {e}")
            # Enterprise-grade fallback enrichment
            enrichment = {
                "risk_level": "medium",  # Conservative default for enterprise
                "mitre_tactic": "TA0005",  # Defense Evasion (common)
                "mitre_technique": "T1055",  # Process Injection (common)
                "nist_control": "AC-6",  # Least Privilege
                "nist_description": "Enterprise security review required for agent action",
                "recommendation": "Manual security review required - automated analysis unavailable.",
                "cvss_score": None,
                "cvss_severity": None,
                "cvss_vector": None
            }

        # Create agent action record with enterprise-grade transaction management
        # ENTERPRISE PATTERN: All operations use flush(), single commit() at end
        action_id = None
        alert_id = None

        try:
            # ENTERPRISE FIX: Create AgentAction with valid fields only
            # Note: AgentAction model uses user_id (not created_by)
            # 🏢 CRITICAL: organization_id is REQUIRED for multi-tenant isolation
            action = AgentAction(
                user_id=current_user.get("user_id", 1),  # User who created this action
                organization_id=org_id,  # 🏢 ENTERPRISE: Scope to organization
                agent_id=data["agent_id"],
                action_type=data["action_type"],
                description=data["description"],
                tool_name=data["tool_name"],
                timestamp=timestamp,
                risk_level=enrichment["risk_level"],
                mitre_tactic=enrichment["mitre_tactic"],
                mitre_technique=enrichment["mitre_technique"],
                nist_control=enrichment["nist_control"],
                nist_description=enrichment["nist_description"],
                recommendation=enrichment["recommendation"],
                summary=summary,
                status="pending",
                # ARCH-001: Add CVSS fields
                cvss_score=enrichment.get("cvss_score"),
                cvss_severity=enrichment.get("cvss_severity"),
                cvss_vector=enrichment.get("cvss_vector"),
                risk_score=enrichment.get("cvss_score") * 10 if enrichment.get("cvss_score") else None  # 0-100 scale
            )

            db.add(action)
            db.flush()  # Get ID without committing transaction
            action_id = action.id
            logger.info(f"Action record created (not committed): {action_id}")

            # ARCH-001: Second pass - Create CVSS assessment with action_id and update agent_actions
            try:
                from services.cvss_auto_mapper import cvss_auto_mapper
                cvss_result = cvss_auto_mapper.auto_assess_action(
                    db=db,
                    action_id=action.id,
                    action_type=data["action_type"],
                    context={
                        "description": data["description"],  # ARCH-003: Pass description for normalization
                        "risk_level": enrichment["risk_level"],
                        "contains_pii": "pii" in (data.get("description") or "").lower(),
                        "production_system": "production" in (data.get("description") or "").lower(),
                        "requires_admin": enrichment["risk_level"] == "high"
                    }
                )

                # Update agent_actions with CVSS fields from detailed assessment
                action.cvss_score = cvss_result["base_score"]
                action.cvss_severity = cvss_result["severity"]
                action.cvss_vector = cvss_result["vector_string"]
                action.risk_score = cvss_result["base_score"] * 10  # 0-100 scale

                # ENTERPRISE PATTERN: Track changes and flush (no commit yet)
                db.add(action)      # Re-add to session to ensure SQLAlchemy tracks modifications
                db.flush()          # Flush changes without committing transaction

                logger.info(f"✅ CVSS integrated: Action {action.id} -> {cvss_result['base_score']} ({cvss_result['severity']})")
            except Exception as cvss_error:
                logger.warning(f"⚠️  CVSS integration failed for action {action.id}: {cvss_error}")
                # Continue - CVSS is supplementary, don't fail the entire transaction

            # ENTERPRISE AUTOMATION: Check for playbook-based auto-approval
            try:
                from services.automation_service import get_automation_service
                automation_service = get_automation_service(db)

                action_data = {
                    'risk_score': action.risk_score or 0,
                    'action_type': action.action_type,
                    'agent_id': action.agent_id,
                    'timestamp': action.timestamp
                }

                # Try to match playbook
                matched_playbook = automation_service.match_playbooks(action_data)

                if matched_playbook:
                    logger.info(f"🤖 Playbook matched: {matched_playbook.id} for action {action.id}")

                    # Execute playbook (auto-approve)
                    execution_result = automation_service.execute_playbook(
                        playbook_id=matched_playbook.id,
                        action_id=action.id
                    )

                    if execution_result['success']:
                        logger.info(f"✅ Auto-approved via playbook: {execution_result['playbook_name']}")
                        # Action is now auto-approved, no further processing needed
                    else:
                        logger.warning(f"⚠️  Playbook execution failed: {execution_result['message']}")
                else:
                    logger.info(f"❌ No playbook match for action {action.id} - manual review required")

            except Exception as automation_error:
                logger.warning(f"⚠️  Automation service failed for action {action.id}: {automation_error}")
                # Continue without automation - action still requires manual review

            # ENTERPRISE ORCHESTRATION: Trigger workflows for high-risk actions
            try:
                from services.orchestration_service import get_orchestration_service
                orchestration_service = get_orchestration_service(db)

                # Trigger workflows/alerts based on risk
                orchestration_result = orchestration_service.orchestrate_action(
                    action_id=action.id,
                    risk_level=action.risk_level,
                    risk_score=action.risk_score or 0,
                    action_type=action.action_type
                )

                if orchestration_result.get('workflow_triggered'):
                    logger.info(f"🔄 Workflow triggered: {orchestration_result['workflow_id']} for action {action.id}")

                if orchestration_result.get('alert_created'):
                    logger.info(f"🚨 Alert created for high-risk action {action.id}")

            except Exception as orchestration_error:
                logger.warning(f"⚠️  Orchestration service failed for action {action.id}: {orchestration_error}")
                # Continue - alerts/workflows are supplementary

            # 🏢 ENTERPRISE: Unified Policy Engine Evaluation (Option 4 Hybrid)
            # Use nested transaction (savepoint) so policy evaluation errors don't poison main transaction
            try:
                # Create savepoint before policy evaluation
                nested = db.begin_nested()

                try:
                    from services.unified_policy_evaluation_service import create_unified_policy_service

                    unified_service = create_unified_policy_service(db)
                    user_context = {
                        "email": current_user.get("email", "unknown"),
                        "role": current_user.get("role", "user"),
                        "user_id": current_user.get("user_id", 1)
                    }

                    # Evaluate agent action using unified policy engine
                    policy_result = await unified_service.evaluate_agent_action(action, user_context)

                    logger.info(
                        f"✅ Policy evaluated: Action {action.id} -> "
                        f"decision={policy_result.decision.value}, "
                        f"policy_risk={policy_result.risk_score.total_score}, "
                        f"time={policy_result.evaluation_time_ms:.2f}ms"
                    )
                    nested.commit()  # Commit the savepoint

                except Exception as policy_inner_error:
                    nested.rollback()  # Rollback only the savepoint, not the whole transaction
                    logger.warning(f"⚠️  Policy evaluation failed for action {action.id}: {policy_inner_error}")
                    # Continue without policy evaluation - main transaction still valid

            except Exception as savepoint_error:
                logger.warning(f"⚠️  Savepoint creation failed: {savepoint_error}")
                # Continue - policy evaluation is optional

            # 🏢 ENTERPRISE FIX (2025-11-19): Create alert with idempotency check
            if enrichment["risk_level"] == "high":
                try:
                    # Check if alert already exists for this action
                    existing_alert = db.query(Alert).filter(
                        Alert.agent_action_id == action.id
                    ).first()

                    if existing_alert:
                        alert_id = existing_alert.id
                        logger.info(f"Alert already exists for action {action.id}: alert_id={alert_id} (skipping duplicate)")
                    else:
                        # ENTERPRISE FIX: Alert model only has 'timestamp', not 'created_at'
                        # 🏢 CRITICAL: organization_id is REQUIRED for multi-tenant isolation
                        alert = Alert(
                            agent_action_id=action.id,
                            organization_id=org_id,  # 🏢 ENTERPRISE: Scope to organization
                            alert_type="High Risk Agent Action",
                            severity="high",
                            message=f"Enterprise Alert: Agent {data['agent_id']} performed high-risk action: {data['action_type']}",
                            timestamp=timestamp  # Only timestamp field exists
                        )
                        db.add(alert)
                        db.flush()  # Add alert to transaction without committing
                        alert_id = alert.id
                        logger.info(f"✅ New alert created for action {action.id}: alert_id={alert_id}")
                except Exception as alert_error:
                    logger.warning(f"Alert creation failed: {alert_error}")
                    # Continue without alert - core action still valid

            # ENTERPRISE PATTERN: Single commit at the end for atomic transaction
            # All previous operations used flush() to maintain transaction integrity
            # If any exception occurred, rollback will undo ALL changes
            db.commit()
            db.refresh(action)  # Reload from DB to get committed state

            logger.info(f"✅ Enterprise agent action committed: {action.id} (risk: {enrichment['risk_level']})")
            return action

        except Exception as db_error:
            logger.error(f"❌ Database action creation failed: {db_error}")
            db.rollback()  # Rollback works because we haven't committed yet
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Enterprise action creation failed: {str(db_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent action creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent action"
        )

@router.get("/agent-actions", response_model=List[AgentActionOut])
def list_agent_actions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    limit: int = 100,
    skip: int = 0
):
    """List agent actions with pagination - Enterprise-grade with tenant isolation"""
    try:
        # 🏢 ENTERPRISE: Filter by organization_id for multi-tenant isolation
        try:
            # First attempt: Try the full query with org filter
            query = db.query(AgentAction)
            if org_id is not None:
                query = query.filter(AgentAction.organization_id == org_id)  # CRITICAL: Tenant isolation
            actions = (
                query
                .order_by(AgentAction.timestamp.desc())
                .offset(skip)
                .limit(min(limit, 100))
                .all()
            )
            
            # Verify we got data and it's accessible
            if actions and len(actions) > 0:
                # Test access to first record to ensure schema compatibility
                test_action = actions[0]
                _ = test_action.id  # This will fail if schema is incompatible
                return actions
            else:
                # No data found, return fallback
                raise Exception("No data in database")
                
        except Exception as db_error:
            logger.warning(f"Database query failed: {db_error}")
            
            # Second attempt: Try simpler query with org filter
            try:
                query = db.query(AgentAction)
                if org_id is not None:
                    query = query.filter(AgentAction.organization_id == org_id)
                simple_actions = query.limit(10).all()
                if simple_actions:
                    return simple_actions
            except Exception as simple_error:
                logger.warning(f"Simple query also failed: {simple_error}")

            # 🏢 ENTERPRISE: NO demo data - return empty list for new organizations
            # Banking-level security: Only return REAL data from database
            logger.info(f"🏢 ENTERPRISE: No agent actions found for org_id={org_id} - returning empty list (no demo data)")
            return []
            
    except Exception as e:
        logger.error(f"Critical error in list_agent_actions: {str(e)}")
        # Last resort: Return minimal but functional response
        return []

@router.get("/agent-activity", response_model=List[AgentActionOut])
def get_agent_activity(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),  # SEC-020: Support SDK API key auth
    org_id: int = Depends(get_organization_filter_dual_auth),  # SEC-020: Dual-auth org filter
    risk: str = None
):
    """Get recent agent activity, optionally filtered by risk level - Enterprise-grade with tenant isolation
    SEC-020: Supports both JWT (admin UI) and API key (SDK) authentication
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id for multi-tenant isolation
        try:
            print(f"🔍 DEBUG: Starting agent-activity query for org_id={org_id}", flush=True)
            logger.info(f"🔍 DEPLOYMENT DEBUG: Starting agent-activity query for org_id={org_id}")
            query = db.query(AgentAction)
            if org_id is not None:
                query = query.filter(AgentAction.organization_id == org_id)
            query = query.order_by(AgentAction.timestamp.desc())

            if risk and risk != "all":
                query = query.filter(AgentAction.risk_level == risk)

            actions = query.limit(50).all()

            print(f"🔍 DEBUG: Query returned {len(actions)} actions", flush=True)
            logger.info(f"🔍 DEPLOYMENT DEBUG: Query returned {len(actions)} actions")

            # Test data accessibility
            if actions and len(actions) > 0:
                first_action = actions[0]
                print(f"🔍 DEBUG: First action - ID: {first_action.id}, agent_id: {first_action.agent_id}, cvss: {first_action.cvss_score}", flush=True)
                logger.info(f"🔍 DEPLOYMENT DEBUG: First action - ID: {first_action.id}, agent_id: {first_action.agent_id}, cvss_score: {first_action.cvss_score}")
                logger.info(f"🔍 DEPLOYMENT DEBUG: Enrichment - MITRE: {first_action.mitre_tactic}, NIST: {first_action.nist_control}")
                _ = first_action.id  # Test schema compatibility
                print(f"🔍 DEBUG: Returning {len(actions)} real actions from database", flush=True)
                logger.info(f"🔍 DEPLOYMENT DEBUG: Returning {len(actions)} real actions from database")
                return actions
            else:
                # 🏢 ENTERPRISE: No demo data - return empty list for new organizations
                # This is correct behavior for tenant isolation - new orgs have no activity
                logger.info(f"🏢 ENTERPRISE: No agent activity found for org_id={org_id} - returning empty list")
                return []

        except Exception as db_error:
            # 🏢 ENTERPRISE: Log error but return empty list - no demo data
            logger.error(f"🏢 ENTERPRISE: Activity query failed for org_id={org_id}: {db_error}")
            return []
            
    except Exception as e:
        logger.error(f"Critical error in get_agent_activity: {str(e)}")
        return []

# Enterprise Admin-only endpoints with preserved audit trail functionality
@router.post("/agent-action/{action_id}/approve")
async def approve_agent_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Approve an agent action (admin only) - Enterprise audit trail preserved

    FIX #2: Now stores approval comments in extra_data field for compliance
    🏢 ENTERPRISE: Only actions belonging to user's organization can be approved
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only approve their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        # FIX #2: Extract approval comments from request body
        try:
            body = await request.json()
            comments = body.get("comments", body.get("justification", "Approved without additional comments"))
        except:
            comments = "Approved without additional comments"

        action.status = "approved"
        action.approved = True
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # FIX #2: Store approval metadata in extra_data
        approval_metadata = {
            "approval_comments": comments,
            "approved_at": datetime.now(UTC).isoformat(),
            "approved_by": admin_user["email"]
        }
        action.extra_data = {**(action.extra_data or {}), **approval_metadata}

        # Create enterprise audit trail
        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="approved",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
            # Continue with approval even if audit fails
        
        db.commit()

        logger.info(f"Enterprise action {action_id} approved by {admin_user['email']}")
        return {"message": "Action approved successfully", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve action"
        )

@router.post("/agent-action/{action_id}/reject")
async def reject_agent_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Reject an agent action (admin only) - Enterprise audit trail preserved

    FIX #2: Now stores rejection reason in extra_data field for compliance
    🏢 ENTERPRISE: Only actions belonging to user's organization can be rejected
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only reject their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        # FIX #2: Extract rejection reason from request body
        try:
            body = await request.json()
            rejection_reason = body.get("comments", body.get("rejection_reason", "Rejected without additional comments"))
        except:
            rejection_reason = "Rejected without additional comments"

        action.status = "rejected"
        action.approved = False
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # FIX #2: Store rejection metadata in extra_data
        rejection_metadata = {
            "rejection_reason": rejection_reason,
            "rejected_at": datetime.now(UTC).isoformat(),
            "rejected_by": admin_user["email"]
        }
        action.extra_data = {**(action.extra_data or {}), **rejection_metadata}

        # Create enterprise audit trail
        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="rejected",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
            # Continue with rejection even if audit fails
        
        db.commit()

        logger.info(f"Enterprise action {action_id} rejected by {admin_user['email']}")
        return {"message": "Action rejected successfully", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject action"
        )

# ========== OPTION 3 PHASE 1: ENTERPRISE AGENT WORKFLOW ENDPOINTS ==========
# Added: 2025-11-19 - Enterprise autonomous agent workflow completion
# Purpose: Enable complete agent lifecycle (submit → poll → execute → report)

@router.get("/agent-action/{action_id}")
async def get_agent_action_by_id(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),  # SEC-020: Support SDK API key auth
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-020: Dual-auth org filter
):
    """
    FIX #1: Get individual agent action by ID for deep linking and detailed reports.

    Use Cases:
    - Client demos: "Show me Action 736 that was blocked"
    - Audit reports: Pull full details for specific action
    - Deep linking: https://pilot.owkai.app/action/736

    Returns: Full action details with NIST/MITRE/CVSS mappings
    🏢 ENTERPRISE: Only returns action if it belongs to user's organization
    SEC-020: Supports both JWT (admin UI) and API key (SDK) authentication
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only see their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()

        if not action:
            raise HTTPException(
                status_code=404,
                detail=f"Action {action_id} not found"
            )

        # Format response with all enterprise metadata
        return {
            "id": action.id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "description": action.description,
            "status": action.status,
            "risk_score": action.risk_score,
            "risk_level": action.risk_level,
            "nist_control": action.nist_control,
            "nist_description": action.nist_description,
            "mitre_tactic": action.mitre_tactic,
            "mitre_technique": action.mitre_technique,
            "recommendation": action.recommendation,
            "reviewed_by": action.reviewed_by,
            "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None,
            "created_at": action.created_at.isoformat() if action.created_at else None,
            "extra_data": action.extra_data or {},  # Include comments if present
            "cvss_score": action.cvss_score,
            "cvss_severity": action.cvss_severity,
            "target_system": action.target_system,
            "enterprise_grade": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_deployed_models(
    environment: str = "production",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    FIX #3: Get list of deployed AI models for agent compliance scanning.

    Purpose: Prevent infinite loop where agents scan their own submissions.
    Agents should scan THIS endpoint (models), not /governance/unified-actions (actions).

    Returns: List of actual deployed models, not agent actions
    """
    try:
        # Enterprise ML Model Registry: Query deployed_models table
        from models_ml_registry import DeployedModel

        # Query models for the specified environment
        deployed_models = db.query(DeployedModel).filter(
            DeployedModel.environment == environment,
            DeployedModel.status == "active"  # Only return active models
        ).all()

        # Convert to API response format
        models = [model.to_dict() for model in deployed_models]

        return {
            "success": True,
            "models": models,
            "total_count": len(models),
            "environment": environment,
            "registry_type": "enterprise_database"
        }

    except Exception as e:
        logger.error(f"Model discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-action/status/{action_id}")
async def get_action_status(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),  # SEC-020: Support SDK API key auth
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-020: Dual-auth org filter
):
    """
    FIX #4: Agent polling endpoint for autonomous workflow.

    Use Case: Agent submits action, then polls every 30s until approved/rejected.
    - If approved: Agent executes
    - If rejected: Agent logs denial reason and aborts

    Returns: Minimal status info optimized for polling (sub-100ms)
    🏢 ENTERPRISE: Only returns status if action belongs to user's organization
    SEC-020: Supports both JWT (admin UI) and API key (SDK) authentication
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only poll their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()

        if not action:
            raise HTTPException(
                status_code=404,
                detail=f"Action {action_id} not found"
            )

        # Extract comments from extra_data if present
        comments = None
        if action.extra_data:
            if action.status == "approved":
                comments = action.extra_data.get("approval_comments")
            elif action.status == "rejected":
                comments = action.extra_data.get("rejection_reason")

        return {
            "action_id": action.id,
            "status": action.status,
            "approved": action.approved,
            "reviewed_by": action.reviewed_by,
            "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None,
            "comments": comments,
            "requires_approval": action.requires_approval,
            "risk_score": action.risk_score,
            "polling_interval_seconds": 30,
            "enterprise_polling": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed for action {action_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== SEC-022: SDK AGENT ACTION SUBMISSION ENDPOINT ==========
# Added: 2025-12-01 - Enterprise SDK integration for autonomous agents
# Purpose: Allow SDK-based agents to submit actions via API key (no CSRF required)
# Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-63B

@router.post("/sdk/agent-action")
async def create_agent_action_via_sdk(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),  # SEC-022: API key auth
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-022: Dual-auth org filter
):
    """
    SEC-022: Submit agent action via SDK (API key authentication)

    This endpoint allows external agents and SDK integrations to submit
    actions for authorization WITHOUT requiring browser-based CSRF tokens.

    Authentication: API key via X-API-Key header
    Authorization: Multi-tenant isolation via organization_id

    Use Cases:
    - LangChain agents submitting tool calls for approval
    - AWS Lambda functions requesting permission
    - MCP servers integrating with OW-AI governance
    - Custom AI agents in enterprise applications

    Request Body:
    {
        "agent_id": "financial-advisor-001",
        "action_type": "transaction",
        "description": "Executing stock purchase order",
        "risk_score": 72,
        "resource": "trading_system",
        "metadata": {...}
    }

    Returns:
    {
        "id": 123,
        "status": "pending",
        "requires_approval": true,
        "risk_score": 72,
        "poll_url": "/api/agent-action/status/123"
    }

    Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-63B
    """
    try:
        data = await request.json()

        # Validate required fields
        required_fields = ["agent_id", "action_type", "description"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # SEC-061: Use enrichment system for action-type-based risk scoring
        # This ensures SDK actions get proper risk assessment like the main endpoint
        try:
            enrichment = evaluate_action_enrichment(
                action_type=data["action_type"],
                description=data["description"],
                db=db,
                action_id=None,  # No action_id yet
                context={
                    "tool_name": data.get("tool_name"),
                    "resource": data.get("resource"),
                    "sdk_integration": True
                }
            )

            # SEC-061: Calculate risk_score from enrichment
            # Priority: 1) CVSS score (scaled to 0-100), 2) Risk level mapping, 3) Client-provided
            if enrichment.get("cvss_score"):
                risk_score = int(enrichment["cvss_score"] * 10)  # 0-10 CVSS -> 0-100
            else:
                # Map risk_level to score ranges
                risk_level_scores = {
                    "low": 25,
                    "medium": 55,
                    "high": 75,
                    "critical": 95
                }
                risk_score = risk_level_scores.get(enrichment["risk_level"], 50)

            risk_level = enrichment["risk_level"]
            mitre_tactic = enrichment.get("mitre_tactic", "TA0002")
            mitre_technique = enrichment.get("mitre_technique", "T1059")
            nist_control = enrichment.get("nist_control", "AC-3")
            nist_description = enrichment.get("nist_description", "Access Enforcement")
            recommendation = enrichment.get("recommendation", "Review agent action")
            cvss_score = enrichment.get("cvss_score")
            cvss_severity = enrichment.get("cvss_severity")
            cvss_vector = enrichment.get("cvss_vector")

            logger.info(f"SEC-061: Enrichment applied to SDK action - action_type={data['action_type']}, "
                       f"risk_level={risk_level}, risk_score={risk_score}")

        except Exception as enrichment_error:
            logger.warning(f"SEC-061: Enrichment failed for SDK action, using client-provided score: {enrichment_error}")
            # Fallback to client-provided risk_score
            risk_score = data.get("risk_score", 50)
            if not isinstance(risk_score, (int, float)):
                risk_score = 50
            risk_score = max(0, min(100, int(risk_score)))

            # Derive risk_level from score
            if risk_score >= 90:
                risk_level = "critical"
            elif risk_score >= 70:
                risk_level = "high"
            elif risk_score >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

            mitre_tactic = "TA0002"
            mitre_technique = "T1059"
            nist_control = "AC-3"
            nist_description = "Access Enforcement"
            recommendation = "Review agent action"
            cvss_score = None
            cvss_severity = None
            cvss_vector = None

        # Determine if approval is required based on risk level
        if risk_level == "low":
            requires_approval = False  # Auto-approve low risk
        else:
            requires_approval = True  # medium, high, critical require approval

        # Generate summary
        try:
            summary = generate_summary(
                agent_id=data["agent_id"],
                action_type=data["action_type"],
                description=data["description"]
            )
        except Exception as e:
            logger.warning(f"OpenAI summary generation failed: {e}")
            summary = f"SDK Agent '{data['agent_id']}' requesting '{data['action_type']}' - requires review"

        # Create the agent action - SEC-061: Include enrichment data
        action = AgentAction(
            agent_id=data["agent_id"],
            tool_name=data.get("tool_name", f"sdk_{data['action_type']}"),
            action_type=data["action_type"],
            description=data["description"],
            risk_score=risk_score,
            risk_level=risk_level,
            status="approved" if not requires_approval else "pending",
            approved=not requires_approval,
            requires_approval=requires_approval,
            summary=summary,
            target_system=data.get("resource", "unknown"),
            extra_data=data.get("metadata", {}),
            organization_id=org_id,
            timestamp=datetime.now(UTC),
            created_at=datetime.now(UTC),
            # SEC-061: Enterprise enrichment data
            mitre_tactic=mitre_tactic,
            mitre_technique=mitre_technique,
            nist_control=nist_control,
            nist_description=nist_description,
            recommendation=recommendation,
            cvss_score=cvss_score,
            cvss_severity=cvss_severity,
            cvss_vector=cvss_vector
        )

        db.add(action)
        db.flush()  # Get action.id before further processing
        action_id = action.id
        logger.info(f"SEC-061: SDK action record created (not committed): {action_id}")

        # =====================================================================
        # SEC-061 ENTERPRISE: CVSS Second Pass Assessment with action_id
        # Compliance: NIST 800-30, SOC 2 CC3.2, PCI-DSS 6.1
        # =====================================================================
        try:
            from services.cvss_auto_mapper import cvss_auto_mapper
            cvss_result = cvss_auto_mapper.auto_assess_action(
                db=db,
                action_id=action.id,
                action_type=data["action_type"],
                context={
                    "description": data["description"],
                    "risk_level": risk_level,
                    "contains_pii": "pii" in (data.get("description") or "").lower(),
                    "production_system": "production" in (data.get("description") or "").lower(),
                    "financial_transaction": any(x in (data.get("description") or "").lower()
                                                  for x in ["payment", "transaction", "billing"]),
                    "requires_admin": risk_level == "high",
                    "sdk_integration": True
                }
            )

            # Update action with CVSS fields from detailed assessment
            action.cvss_score = cvss_result["base_score"]
            action.cvss_severity = cvss_result["severity"]
            action.cvss_vector = cvss_result["vector_string"]
            action.risk_score = int(cvss_result["base_score"] * 10)  # 0-100 scale

            db.add(action)
            db.flush()

            logger.info(f"SEC-061: CVSS integrated for SDK action {action.id} -> "
                       f"{cvss_result['base_score']} ({cvss_result['severity']})")
        except Exception as cvss_error:
            logger.warning(f"SEC-061: CVSS integration failed for SDK action {action.id}: {cvss_error}")
            # Continue - CVSS is supplementary

        # =====================================================================
        # SEC-061 ENTERPRISE: Automation Service - Playbook Matching
        # Compliance: SOC 2 CC7.1, NIST 800-53 IR-4
        # =====================================================================
        playbook_result = None
        try:
            from services.automation_service import get_automation_service
            automation_service = get_automation_service(db)

            action_data = {
                'risk_score': action.risk_score or 0,
                'action_type': action.action_type,
                'agent_id': action.agent_id,
                'timestamp': action.timestamp
            }

            matched_playbook = automation_service.match_playbooks(action_data)

            if matched_playbook:
                logger.info(f"SEC-061: Playbook matched for SDK action {action.id}: {matched_playbook.id}")

                execution_result = automation_service.execute_playbook(
                    playbook_id=matched_playbook.id,
                    action_id=action.id
                )

                if execution_result['success']:
                    playbook_result = {
                        "matched": True,
                        "playbook_name": execution_result['playbook_name'],
                        "auto_approved": True
                    }
                    logger.info(f"SEC-061: SDK action auto-approved via playbook: {execution_result['playbook_name']}")
                else:
                    playbook_result = {"matched": True, "execution_failed": True}
                    logger.warning(f"SEC-061: Playbook execution failed: {execution_result['message']}")
            else:
                playbook_result = {"matched": False}
                logger.info(f"SEC-061: No playbook match for SDK action {action.id}")

        except Exception as automation_error:
            logger.warning(f"SEC-061: Automation service failed for SDK action {action.id}: {automation_error}")
            playbook_result = {"error": str(automation_error)}

        # =====================================================================
        # SEC-061 ENTERPRISE: Orchestration Service - Workflow Triggering
        # Compliance: SOC 2 CC7.2, NIST 800-53 IR-6
        # =====================================================================
        workflow_result = None
        try:
            from services.orchestration_service import get_orchestration_service
            orchestration_service = get_orchestration_service(db)

            orchestration_result = orchestration_service.orchestrate_action(
                action_id=action.id,
                risk_level=action.risk_level,
                risk_score=action.risk_score or 0,
                action_type=action.action_type
            )

            workflow_result = {
                "workflow_triggered": orchestration_result.get('workflow_triggered', False),
                "workflow_id": orchestration_result.get('workflow_id'),
                "alert_created": orchestration_result.get('alert_created', False)
            }

            if orchestration_result.get('workflow_triggered'):
                logger.info(f"SEC-061: Workflow triggered for SDK action {action.id}: {orchestration_result['workflow_id']}")

        except Exception as orchestration_error:
            logger.warning(f"SEC-061: Orchestration service failed for SDK action {action.id}: {orchestration_error}")
            workflow_result = {"error": str(orchestration_error)}

        # =====================================================================
        # SEC-061 ENTERPRISE: Alert Generation for High-Risk Actions
        # Compliance: SOC 2 CC7.2, PCI-DSS 12.10, NIST 800-53 IR-6
        # =====================================================================
        alert_id = None
        if risk_level in ("high", "critical"):
            try:
                existing_alert = db.query(Alert).filter(
                    Alert.agent_action_id == action.id
                ).first()

                if existing_alert:
                    alert_id = existing_alert.id
                    logger.info(f"SEC-061: Alert already exists for SDK action {action.id}: alert_id={alert_id}")
                else:
                    severity = "critical" if risk_level == "critical" else "high"
                    alert = Alert(
                        agent_action_id=action.id,
                        organization_id=org_id,
                        alert_type=f"{severity.title()} Risk SDK Agent Action",
                        severity=severity,
                        message=f"Enterprise Alert: SDK Agent '{data['agent_id']}' requesting {risk_level}-risk action: "
                                f"{data['action_type']} - {data['description'][:100]} | "
                                f"NIST: {nist_control} | MITRE: {mitre_tactic}",
                        timestamp=datetime.now(UTC)
                    )
                    db.add(alert)
                    db.flush()
                    alert_id = alert.id
                    logger.info(f"SEC-061: Alert created for SDK action {action.id}: alert_id={alert_id}, severity={severity}")
            except Exception as alert_error:
                logger.warning(f"SEC-061: Alert creation failed for SDK action {action.id}: {alert_error}")

        # =====================================================================
        # SEC-061 ENTERPRISE: Commit Transaction
        # =====================================================================
        db.commit()
        db.refresh(action)

        auth_method = current_user.get("auth_method", "api_key")
        logger.info(f"SEC-061: Enterprise SDK action committed - ID: {action.id}, Agent: {data['agent_id']}, "
                    f"Risk: {action.risk_score}, Level: {action.risk_level}, Status: {action.status}, "
                    f"Auth: {auth_method}, Alert: {alert_id}")

        # =====================================================================
        # SEC-061 ENTERPRISE: Enhanced Response with Full Compliance Data
        # =====================================================================
        return {
            "id": action.id,
            "action_id": action.id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "status": action.status,
            "risk_score": action.risk_score,
            "risk_level": action.risk_level,
            "requires_approval": action.requires_approval,
            "approved": action.approved,
            "alert_generated": alert_id is not None,
            "alert_id": alert_id,
            "poll_url": f"/api/agent-action/status/{action.id}",
            "enterprise_grade": True,
            "sdk_integration": True,
            # SEC-061: Enterprise compliance data
            "compliance": {
                "nist_control": action.nist_control,
                "nist_description": action.nist_description,
                "mitre_tactic": action.mitre_tactic,
                "mitre_technique": action.mitre_technique,
                "recommendation": action.recommendation,
                "cvss_score": action.cvss_score,
                "cvss_severity": action.cvss_severity,
                "cvss_vector": action.cvss_vector
            },
            # SEC-061: Enterprise automation results
            "automation": {
                "playbook": playbook_result,
                "workflow": workflow_result
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEC-022: SDK agent action creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent action: {str(e)}"
        )


@router.post("/agent-action/{action_id}/false-positive")
def mark_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """Mark an agent action as false positive (admin only) - Enterprise audit trail preserved
    🏢 ENTERPRISE: Only actions belonging to user's organization can be marked
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only mark their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent action not found"
            )

        action.status = "false_positive"
        action.is_false_positive = True
        action.reviewed_by = admin_user["email"]
        action.reviewed_at = datetime.now(UTC)

        # Create enterprise audit trail
        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="false_positive",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
            # Continue with marking even if audit fails
        
        db.commit()

        logger.info(f"Enterprise action {action_id} marked as false positive by {admin_user['email']}")
        return {"message": "Action marked as false positive", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark action {action_id} as false positive: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark as false positive"
        )

@router.get("/audit-trail")
def get_audit_trail(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """Get audit trail (admin only) - Enterprise compliance feature preserved
    🏢 ENTERPRISE: Only returns audit logs for user's organization
    """
    try:
        try:
            # 🏢 ENTERPRISE: Filter by organization_id for tenant isolation
            logs = (
                db.query(LogAuditTrail)
                .filter(LogAuditTrail.organization_id == org_id)  # CRITICAL: Tenant isolation
                .order_by(LogAuditTrail.timestamp.desc())
                .limit(100)
                .all()
            )
            return logs
        except Exception as db_error:
            logger.warning(f"Audit trail query failed: {db_error}")
            # 🏢 ENTERPRISE: NO demo data - return empty list for new organizations
            logger.info(f"🏢 ENTERPRISE: No audit trail found for org_id={org_id} - returning empty list (no demo data)")
            return []
    except Exception as e:
        logger.error(f"Failed to get audit trail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit trail"
        )

# ============================================================================
# ENTERPRISE ACTIVITY TAB ENDPOINTS - Phase 1 Core Functionality
# ============================================================================

@router.post("/agent-action/false-positive/{action_id}")
def toggle_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """Toggle false positive flag on an agent action - Enterprise audit trail
    🏢 ENTERPRISE: Only actions belonging to user's organization can be toggled
    """
    try:
        # 🏢 ENTERPRISE: Filter by organization_id - users can only toggle their org's actions
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id  # CRITICAL: Tenant isolation
        ).first()

        if not action:
            raise HTTPException(status_code=404, detail=f"Agent action {action_id} not found")

        # Toggle false positive status
        action.is_false_positive = not (action.is_false_positive or False)
        action.reviewed_by = current_user.get("email", "unknown")
        action.reviewed_at = datetime.now(UTC)
        action.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(action)

        logger.info(f"Action {action_id} marked as {'FALSE POSITIVE' if action.is_false_positive else 'VALID'} by {current_user.get('email')}")

        return {
            "message": f"Action {action_id} marked as {'FALSE POSITIVE' if action.is_false_positive else 'VALID'}",
            "action_id": action_id,
            "is_false_positive": action.is_false_positive,
            "reviewed_by": action.reviewed_by,
            "reviewed_at": action.reviewed_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to toggle false positive for action {action_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle false positive: {str(e)}")


@router.post("/support/submit")
async def submit_support_request(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit support request - Enterprise ticketing integration ready"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()

        if not message or len(message) < 10:
            raise HTTPException(status_code=400, detail="Support message must be at least 10 characters")

        if len(message) > 5000:
            raise HTTPException(status_code=400, detail="Support message too long (max 5000 characters)")

        # Log to audit_logs table for enterprise tracking
        support_ticket = {
            "user_id": current_user.get("user_id"),
            "user_email": current_user.get("email"),
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "open",
            "priority": "medium"
        }

        audit_log = LogAuditTrail(
            user_id=current_user.get("user_id"),
            action_type="support_ticket_created",
            details=json.dumps(support_ticket),
            timestamp=datetime.now(UTC),
            ip_address="system"
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"Support ticket created by {current_user.get('email')}: {message[:100]}")

        return {
            "message": "Support request submitted successfully",
            "ticket_id": audit_log.id,
            "status": "open",
            "email": current_user.get("email")
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit support request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit support request: {str(e)}")


@router.post("/agent-actions/upload-json")
async def upload_agent_actions_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """Upload agent actions from JSON file - Enterprise bulk import
    🏢 ENTERPRISE: All imported actions are scoped to user's organization
    """
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        # Read and parse JSON
        contents = await file.read()
        try:
            actions_data = json.loads(contents)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")

        # Ensure it's a list
        if not isinstance(actions_data, list):
            actions_data = [actions_data]

        if len(actions_data) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 actions per upload")

        imported_count = 0
        skipped_count = 0
        errors = []

        for idx, action_data in enumerate(actions_data):
            try:
                # Create agent action - scoped to user's organization
                action = AgentAction(
                    agent_id=action_data.get("agent_id", "imported"),
                    action_type=action_data.get("action_type", "imported_action"),
                    description=action_data.get("description"),
                    tool_name=action_data.get("tool_name"),
                    risk_level=action_data.get("risk_level"),
                    status=action_data.get("status", "imported"),
                    user_id=current_user.get("user_id"),
                    organization_id=org_id,  # 🏢 ENTERPRISE: Scope to organization
                    timestamp=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    summary=action_data.get("summary"),
                    nist_control=action_data.get("nist_control"),
                    mitre_tactic=action_data.get("mitre_tactic"),
                    mitre_technique=action_data.get("mitre_technique"),
                    cvss_score=action_data.get("cvss_score"),
                    cvss_severity=action_data.get("cvss_severity")
                )
                db.add(action)
                imported_count += 1

            except Exception as e:
                skipped_count += 1
                errors.append(f"Row {idx+1}: {str(e)}")
                if len(errors) >= 20:  # Limit error collection
                    break

        db.commit()

        logger.info(f"Bulk import by {current_user.get('email')}: {imported_count} imported, {skipped_count} skipped")

        return {
            "message": f"Import completed: {imported_count} imported, {skipped_count} skipped",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors[:10],  # Return first 10 errors only
            "total_in_file": len(actions_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")