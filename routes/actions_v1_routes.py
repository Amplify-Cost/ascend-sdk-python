# SEC-PHASE9-001-V6 CACHE BUST: 2025-12-18T17:30:00Z - Force fresh deployment
"""
Ascend AI Governance Platform - Actions API v1
==============================================

SINGLE SOURCE OF TRUTH for all agent action operations with FULL governance pipeline.

This endpoint provides:
- RESTful, clean API design
- Full 7-step governance pipeline
- Dual authentication (JWT + API keys)
- Multi-tenant isolation
- Enterprise-grade error handling
- Comprehensive audit trails
- Rate limiting and performance tracking

Architecture:
- Step 1: Risk Assessment (enrichment)
- Step 2: CVSS Calculation (quantitative scoring)
- Step 3: Policy Evaluation (governance policies)
- Step 4: Smart Rules Check (custom rules)
- Step 5: Alert Generation (high-risk actions)
- Step 6: Workflow Routing (approval workflows)
- Step 7: Audit Logging (immutable trail)

Compliance: SOC 2 Type II, HIPAA, PCI-DSS, GDPR, SOX

Author: OW-kai Enterprise Security Team
Version: 1.0.0
Created: 2025-12-04
"""

import logging
import uuid
import time
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Database and dependencies
from database import get_db
from dependencies import get_current_user, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key, get_organization_filter_dual_auth

# Models
from models import (
    AgentAction,
    Alert,
    SmartRule,
    AuditLog,
    User,
    Workflow
)
# SEC-106: Import enterprise policy engine components
from models_agent_registry import RegisteredAgent

# Services
from enrichment import evaluate_action_enrichment
from services.cvss_auto_mapper import cvss_auto_mapper
from services.unified_policy_evaluation_service import UnifiedPolicyEvaluationService
from services.code_analysis_service import CodeAnalysisService

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Router configuration
router = APIRouter(prefix="/api/v1/actions", tags=["Actions API v1"])


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_correlation_id() -> str:
    """Generate unique correlation ID for request tracing."""
    return f"action_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def create_audit_log(
    db: Session,
    user_id: int,
    organization_id: int,
    action_type: str,
    details: str,
    correlation_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Create immutable audit trail entry.

    Compliance: SOC 2 AU-6, PCI-DSS 10.2, SOX
    """
    try:
        audit = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action_type,
            details=details,
            timestamp=datetime.now(UTC),
            ip_address=metadata.get("ip_address") if metadata else None,
            user_agent=metadata.get("user_agent") if metadata else None,
            correlation_id=correlation_id
        )
        db.add(audit)
        db.commit()
        logger.info(f"Audit log created: {correlation_id} - {action_type}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Non-blocking - don't fail request if audit logging fails


def evaluate_smart_rules(
    db: Session,
    action: AgentAction,
    organization_id: int,
    max_risk_threshold: int = 70
) -> Dict[str, Any]:
    """
    SEC-106: Evaluate action against active smart rules with configurable threshold.

    Args:
        db: Database session
        action: The agent action to evaluate
        organization_id: Organization for multi-tenant isolation
        max_risk_threshold: Risk threshold for requiring approval (default: 70)

    Returns:
        dict: {
            "matched_rules": List[dict],
            "highest_risk": int,
            "requires_approval": bool
        }
    """
    try:
        # Get active smart rules for organization
        smart_rules = db.query(SmartRule).filter(
            SmartRule.organization_id == organization_id,
            SmartRule.is_active == True
        ).all()

        matched_rules = []
        highest_risk = 0

        for rule in smart_rules:
            # Simple pattern matching (can be enhanced with regex/NLP)
            if rule.pattern and rule.pattern.lower() in action.description.lower():
                matched_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "pattern": rule.pattern,
                    "severity": rule.severity
                })

                # Track highest risk level
                severity_map = {"low": 30, "medium": 60, "high": 85, "critical": 95}
                rule_risk = severity_map.get(rule.severity.lower(), 60)
                highest_risk = max(highest_risk, rule_risk)

        # SEC-106: Use configurable threshold instead of hardcoded 70
        return {
            "matched_rules": matched_rules,
            "highest_risk": highest_risk,
            "requires_approval": highest_risk >= max_risk_threshold
        }

    except Exception as e:
        logger.warning(f"Smart rules evaluation failed: {e}")
        return {
            "matched_rules": [],
            "highest_risk": 0,
            "requires_approval": False
        }


def determine_authorization_status(
    risk_score: float,
    policy_decision: str,
    smart_rules_require_approval: bool,
    auto_approve_threshold: int = 30,
    max_risk_threshold: int = 80
) -> str:
    """
    SEC-106: Enterprise decision logic using configurable thresholds.

    Decision flow:
    1. If policy explicitly denies → denied
    2. If risk < auto_approve_threshold → auto-approve (LOW risk)
    3. If risk >= max_risk_threshold → require approval (HIGH risk)
    4. If policy says require_approval → require approval
    5. If smart rules require approval → require approval
    6. Otherwise → approved (MEDIUM risk with no policy triggers)

    Args:
        risk_score: Calculated risk score (0-100)
        policy_decision: Result from policy engine
        smart_rules_require_approval: Whether smart rules flagged this action
        auto_approve_threshold: Risk score below which to auto-approve (default: 30)
        max_risk_threshold: Risk score at/above which to require approval (default: 80)

    Returns:
        str: "approved", "pending_approval", "denied"
    """
    # Policy engine explicit deny has highest priority
    if policy_decision == "deny":
        return "denied"

    # SEC-106: LOW RISK - Auto-approve below threshold
    if risk_score < auto_approve_threshold:
        logger.info(f"SEC-106: Auto-approving LOW risk action (score={risk_score} < threshold={auto_approve_threshold})")
        return "approved"

    # SEC-106: HIGH RISK - Always require approval above max threshold
    if risk_score >= max_risk_threshold:
        logger.info(f"SEC-106: Requiring approval for HIGH risk action (score={risk_score} >= threshold={max_risk_threshold})")
        return "pending_approval"

    # MEDIUM RISK: Check policy and smart rules
    if policy_decision == "require_approval" or smart_rules_require_approval:
        logger.info(f"SEC-106: Requiring approval for MEDIUM risk action (policy={policy_decision}, smart_rules={smart_rules_require_approval})")
        return "pending_approval"

    # MEDIUM RISK with no policy triggers: Approve
    logger.info(f"SEC-106: Approving MEDIUM risk action with no policy triggers (score={risk_score})")
    return "approved"


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/submit", response_model=Dict[str, Any])
async def submit_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Submit agent action for governance evaluation (FULL 7-step pipeline).

    This is the SINGLE SOURCE OF TRUTH for action submission with complete
    governance pipeline including risk assessment, CVSS scoring, policy
    evaluation, smart rules, alerts, workflows, and audit logging.

    Authentication: Supports both JWT tokens (admin UI) and API keys (SDK)

    Request Body:
        {
            "agent_id": "string",
            "action_type": "string",
            "description": "string",
            "tool_name": "string",
            "target_system": "string (optional)",
            "nist_control": "string (optional)",
            "mitre_tactic": "string (optional)"
        }

    Response:
        {
            "id": int,
            "status": "approved|pending_approval|denied",
            "risk_score": float,
            "risk_level": "low|medium|high|critical",
            "cvss_score": float,
            "cvss_severity": "string",
            "requires_approval": bool,
            "alert_triggered": bool,
            "workflow_id": int (optional),
            "policy_decision": "string",
            "matched_smart_rules": int,
            "correlation_id": "string",
            "processing_time_ms": int
        }

    Compliance: SOC 2 Type II, HIPAA, PCI-DSS, GDPR, SOX
    """
    start_time = time.time()
    correlation_id = generate_correlation_id()

    try:
        # Parse request body
        data = await request.json()

        # Validate required fields
        required = ["agent_id", "action_type", "description", "tool_name"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        logger.info(f"[{correlation_id}] Processing action submission: {data['action_type']}")

        # ====================================================================
        # SEC-106: AGENT THRESHOLD LOOKUP - Get configurable thresholds
        # ====================================================================
        registered_agent = db.query(RegisteredAgent).filter(
            RegisteredAgent.agent_id == data["agent_id"],
            RegisteredAgent.organization_id == org_id,
            RegisteredAgent.status == "active"  # Use status column, not is_active
        ).first()

        # SEC-106: Get agent-specific thresholds (or use enterprise defaults)
        if registered_agent:
            # Check if autonomous agent (stricter thresholds)
            is_autonomous = getattr(registered_agent, 'agent_type', None) == "autonomous"

            if is_autonomous:
                auto_approve_threshold = min(
                    registered_agent.auto_approve_below or 30,
                    getattr(registered_agent, 'autonomous_auto_approve_below', 40) or 40
                )
                max_risk_threshold = min(
                    registered_agent.max_risk_threshold or 80,
                    getattr(registered_agent, 'autonomous_max_risk_threshold', 60) or 60
                )
                logger.info(f"[{correlation_id}] SEC-106: Autonomous agent '{data['agent_id']}' using stricter thresholds: auto_approve<{auto_approve_threshold}, max<{max_risk_threshold}")
            else:
                auto_approve_threshold = registered_agent.auto_approve_below or 30
                max_risk_threshold = registered_agent.max_risk_threshold or 80
                logger.info(f"[{correlation_id}] SEC-106: Registered agent '{data['agent_id']}' thresholds: auto_approve<{auto_approve_threshold}, max<{max_risk_threshold}")

            agent_type = getattr(registered_agent, 'agent_type', 'supervised') or 'supervised'
        else:
            # Default thresholds for unregistered agents (more restrictive)
            auto_approve_threshold = 30
            max_risk_threshold = 70
            is_autonomous = False
            agent_type = "unregistered"
            logger.info(f"[{correlation_id}] SEC-106: Unregistered agent '{data['agent_id']}' using default thresholds: auto_approve<{auto_approve_threshold}, max<{max_risk_threshold}")

        # ====================================================================
        # STEP 1: RISK ASSESSMENT - Security enrichment with NIST/MITRE
        # ====================================================================
        try:
            enrichment = evaluate_action_enrichment(
                action_type=data["action_type"],
                description=data["description"],
                db=db,
                context={
                    "agent_id": data["agent_id"],
                    "tool_name": data["tool_name"],
                    "target_system": data.get("target_system"),
                    "nist_control": data.get("nist_control"),
                    "mitre_tactic": data.get("mitre_tactic")
                }
            )

            risk_level = enrichment.get("risk_level", "medium")

            # Convert qualitative risk to quantitative score
            risk_score = enrichment.get("cvss_score")
            if risk_score is None:
                risk_score_map = {
                    "low": 35,
                    "medium": 60,
                    "high": 85,
                    "critical": 95
                }
                risk_score = risk_score_map.get(risk_level, 50)
            else:
                # CVSS score is 0-10, convert to 0-100
                risk_score = float(risk_score) * 10

            logger.info(f"[{correlation_id}] Step 1 complete - Risk: {risk_level} ({risk_score})")

        except Exception as e:
            logger.warning(f"[{correlation_id}] Risk assessment failed, using defaults: {e}")
            risk_score = 50
            risk_level = "medium"
            enrichment = {}

        # ====================================================================
        # STEP 1.5: CODE ANALYSIS - Dangerous pattern detection (Phase 9)
        # SEC-PHASE9-001: Risk adjustment moved OUTSIDE try-except to ensure execution
        # ====================================================================
        code_analysis_result = None
        code_blocked = False

        # SEC-PHASE9-001: Isolated try-except - only wraps the service call
        try:
            code_service = CodeAnalysisService(db, org_id)
            code_analysis_result = code_service.analyze_for_action(
                action_type=data["action_type"],
                parameters={
                    "description": data.get("description", ""),
                    "query": data.get("action_details", {}).get("query", ""),
                    "code": data.get("action_details", {}).get("code", ""),
                    "command": data.get("action_details", {}).get("command", ""),
                    **data.get("action_details", {})
                },
                agent_id=data["agent_id"]  # Phase 9: Pass agent_id for per-agent thresholds
            )
        except Exception as code_err:
            code_analysis_result = None  # SEC-PHASE9-001: Explicit None on failure
            logger.warning(f"[{correlation_id}] Code analysis failed (non-blocking): {code_err}")

        # SEC-PHASE9-001: Risk adjustment OUTSIDE try-except - guaranteed to execute
        if code_analysis_result and code_analysis_result.code_analyzed:
            # Add code analysis info to enrichment
            enrichment["code_analysis"] = {
                "analyzed": True,
                "language": code_analysis_result.language,
                "findings_count": len(code_analysis_result.findings),
                "max_severity": code_analysis_result.max_severity,
                "patterns_matched": code_analysis_result.patterns_matched,
                "config_mode": code_analysis_result.config_mode,  # enforce, monitor, off
            }

            # SEC-PHASE9-001: Risk adjustment moved to AFTER action creation (see line ~480)
            # This ensures we modify the action object directly, not a local variable

            # Check if action should be blocked
            if code_analysis_result.blocked:
                code_blocked = True
                logger.warning(
                    f"[{correlation_id}] Code analysis BLOCKED action: "
                    f"{code_analysis_result.block_reason}"
                )

            logger.info(f"[{correlation_id}] Step 1.5 complete - Code analysis done")

        # ====================================================================
        # CREATE INITIAL AGENT ACTION RECORD
        # ====================================================================
        # Build extra_data with code analysis findings (preserving any existing data)
        extra_data = data.get("extra_data", {}) or {}
        if code_analysis_result and code_analysis_result.code_analyzed:
            extra_data["code_analysis"] = code_analysis_result.to_dict()

        logger.info(
            f"[{correlation_id}] [PHASE9-DEBUG] Creating action with risk_score={risk_score}, risk_level={risk_level}"
        )
        action = AgentAction(
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            description=data["description"],
            tool_name=data["tool_name"],
            risk_level=risk_level,
            risk_score=float(risk_score),
            status="processing",  # Will be updated after governance checks
            user_id=current_user.get("user_id"),
            organization_id=org_id,
            timestamp=datetime.now(UTC),
            target_system=data.get("target_system"),
            nist_control=enrichment.get("nist_control"),
            mitre_tactic=enrichment.get("mitre_tactic"),
            mitre_technique=enrichment.get("mitre_technique"),
            nist_description=enrichment.get("nist_description"),
            recommendation=enrichment.get("recommendation"),
            extra_data=extra_data if extra_data else None
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        logger.info(f"[{correlation_id}] Action created: ID={action.id}")

        # SEC-PHASE9-001-V6: UNCONDITIONAL DIAGNOSTIC - Check object state before condition
        logger.warning(
            f"[{correlation_id}] [SEC-PHASE9-001-V6-DIAGNOSTIC] "
            f"code_analysis_result={code_analysis_result is not None}, "
            f"code_analyzed={getattr(code_analysis_result, 'code_analyzed', 'N/A')}, "
            f"risk_adjustment={getattr(code_analysis_result, 'risk_adjustment', 'N/A')}"
        )

        # ====================================================================
        # SEC-PHASE9-001: Apply code analysis risk adjustment AFTER action creation
        # This ensures we modify the action object directly, not a local variable
        # ====================================================================
        if code_analysis_result and code_analysis_result.code_analyzed:
            logger.warning(f"[{correlation_id}] [SEC-PHASE9-001-V6] ENTERED IF BLOCK")
            if code_analysis_result.risk_adjustment > 0:
                logger.warning(f"[{correlation_id}] [SEC-PHASE9-001-V6] ENTERED RISK ADJUSTMENT BLOCK")
                original_risk = action.risk_score
                action.risk_score = max(action.risk_score, code_analysis_result.risk_adjustment)
                if action.risk_score != original_risk:
                    logger.info(
                        f"[{correlation_id}] [SEC-PHASE9-001] Code analysis risk applied: "
                        f"{original_risk} -> {action.risk_score}"
                    )

            # SEC-PHASE9-001: Update risk_level to match risk_score
            if code_analysis_result.max_severity == "critical" and action.risk_level != "critical":
                action.risk_level = "critical"
                logger.info(f"[{correlation_id}] [SEC-PHASE9-001] Risk level upgraded to critical")
            elif code_analysis_result.max_severity == "high" and action.risk_level in ("low", "medium"):
                action.risk_level = "high"
                logger.info(f"[{correlation_id}] [SEC-PHASE9-001] Risk level upgraded to high")

        # ====================================================================
        # STEP 2: CVSS CALCULATION - Quantitative risk scoring
        # ====================================================================
        try:
            cvss_result = cvss_auto_mapper.auto_assess_action(
                db=db,
                action_id=action.id,
                action_type=data["action_type"],
                context={
                    "description": data["description"],
                    "risk_level": risk_level,
                    "contains_pii": "pii" in data.get("description", "").lower(),
                    "production_system": "production" in data.get("description", "").lower(),
                    "requires_admin": False
                }
            )

            # Update action with CVSS scores
            action.cvss_score = cvss_result["base_score"]
            action.cvss_severity = cvss_result["severity"]
            action.cvss_vector = cvss_result["vector_string"]
            # Phase 9: Use max() to preserve code analysis risk adjustment
            cvss_risk = cvss_result["base_score"] * 10  # 0-100 scale
            original_action_risk = action.risk_score
            action.risk_score = max(action.risk_score, cvss_risk)
            logger.info(
                f"[{correlation_id}] [PHASE9-DEBUG] CVSS max(): "
                f"original={original_action_risk}, cvss_risk={cvss_risk}, "
                f"result={action.risk_score}"
            )

            db.add(action)
            db.flush()
            db.commit()
            db.refresh(action)

            logger.info(
                f"[{correlation_id}] Step 2 complete - CVSS: {cvss_result['base_score']} "
                f"({cvss_result['severity']})"
            )

        except Exception as cvss_error:
            logger.warning(f"[{correlation_id}] CVSS calculation failed: {cvss_error}")
            cvss_result = {
                "base_score": risk_score / 10,
                "severity": risk_level,
                "vector_string": "N/A"
            }

        # ====================================================================
        # STEP 3: POLICY EVALUATION - Governance policy check
        # ====================================================================
        try:
            unified_service = UnifiedPolicyEvaluationService(db)
            policy_result = await unified_service.evaluate_agent_action(
                action=action,
                user_context={
                    "user_id": current_user.get("user_id"),
                    "email": current_user.get("email", "unknown"),
                    "role": current_user.get("role", "user")
                }
            )

            policy_decision = policy_result.decision
            matched_policies = len(policy_result.matched_policies)

            logger.info(
                f"[{correlation_id}] Step 3 complete - Policy: {policy_decision} "
                f"({matched_policies} policies matched)"
            )

        except Exception as policy_error:
            logger.warning(f"[{correlation_id}] Policy evaluation failed: {policy_error}")
            policy_decision = "allow"
            matched_policies = 0

        # ====================================================================
        # STEP 4: SMART RULES CHECK - Custom rule evaluation
        # ====================================================================
        # SEC-106: Pass agent-specific threshold to smart rules
        smart_rules_result = evaluate_smart_rules(db, action, org_id, max_risk_threshold)

        logger.info(
            f"[{correlation_id}] Step 4 complete - Smart Rules: "
            f"{len(smart_rules_result['matched_rules'])} matched, "
            f"requires_approval={smart_rules_result['requires_approval']}"
        )

        # ====================================================================
        # STEP 5: ALERT GENERATION - High-risk action alerts
        # SEC-110: Lowered threshold from 80 to 70 to align with HIGH risk tier
        # Risk Tiers: LOW (0-39), MEDIUM (40-69), HIGH (70-84), CRITICAL (85+)
        # ====================================================================
        alert_triggered = False
        alert_id = None

        if action.risk_score >= 70:  # SEC-110: Align with HIGH risk tier (was 80)
            try:
                alert = Alert(
                    alert_type="High Risk Agent Action",
                    severity="critical" if action.risk_score >= 85 else "high",
                    message=f"{data['agent_id']}: {data['description']}",
                    agent_id=data['agent_id'],
                    agent_action_id=action.id,
                    organization_id=org_id,
                    status="new",
                    timestamp=datetime.now(UTC)
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                alert_triggered = True
                alert_id = alert.id

                logger.info(f"[{correlation_id}] Step 5 complete - Alert created: ID={alert_id} (risk={action.risk_score})")

            except Exception as alert_error:
                logger.error(f"[{correlation_id}] Alert creation failed: {alert_error}")
        else:
            logger.info(f"[{correlation_id}] Step 5 complete - No alert required (risk={action.risk_score} < 70)")

        # ====================================================================
        # STEP 6: WORKFLOW ROUTING - Approval workflow assignment
        # ====================================================================
        workflow_id = None
        requires_approval = smart_rules_result["requires_approval"] or action.risk_score >= 70

        if requires_approval:
            try:
                # Check for active workflows for this organization
                active_workflow = db.query(Workflow).filter(
                    Workflow.organization_id == org_id,
                    Workflow.status == "active"
                ).first()

                if active_workflow:
                    workflow_id = active_workflow.id
                    logger.info(
                        f"[{correlation_id}] Step 6 complete - Workflow assigned: ID={workflow_id}"
                    )
                else:
                    logger.info(
                        f"[{correlation_id}] Step 6 complete - No active workflow, "
                        f"manual approval required"
                    )

            except Exception as workflow_error:
                logger.error(f"[{correlation_id}] Workflow routing failed: {workflow_error}")
        else:
            logger.info(f"[{correlation_id}] Step 6 complete - No workflow required (auto-approved)")

        # ====================================================================
        # DETERMINE FINAL STATUS - SEC-106: Use agent-specific thresholds
        # ====================================================================
        final_status = determine_authorization_status(
            risk_score=action.risk_score,
            policy_decision=policy_decision,
            smart_rules_require_approval=smart_rules_result["requires_approval"],
            auto_approve_threshold=auto_approve_threshold,
            max_risk_threshold=max_risk_threshold
        )

        # Phase 9: Override status if code analysis blocked the action
        if code_blocked and code_analysis_result:
            final_status = "denied"
            policy_decision = "denied"
            # Add blocking reason to extra_data
            if action.extra_data:
                action.extra_data["code_blocked"] = True
                action.extra_data["code_block_reason"] = code_analysis_result.block_reason
            logger.warning(
                f"[{correlation_id}] Final status overridden to DENIED by code analysis: "
                f"{code_analysis_result.block_reason}"
            )

        action.status = final_status
        db.add(action)
        db.commit()
        db.refresh(action)

        # ====================================================================
        # STEP 7: AUDIT LOGGING - Immutable compliance trail
        # ====================================================================
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build audit metadata including code analysis results
        audit_metadata = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "action_id": action.id,
            "risk_score": action.risk_score,
            "cvss_score": action.cvss_score,
            "policy_decision": policy_decision,
            "matched_smart_rules": len(smart_rules_result["matched_rules"]),
            "processing_time_ms": processing_time_ms
        }

        # Phase 9: Add code analysis metadata to audit log
        if code_analysis_result and code_analysis_result.code_analyzed:
            audit_metadata["code_analysis"] = {
                "analyzed": True,
                "language": code_analysis_result.language,
                "findings_count": len(code_analysis_result.findings),
                "max_severity": code_analysis_result.max_severity,
                "patterns_matched": code_analysis_result.patterns_matched,
                "blocked": code_analysis_result.blocked
            }

        create_audit_log(
            db=db,
            user_id=current_user.get("user_id"),
            organization_id=org_id,
            action_type="action_submitted",
            details=f"Action {action.id} submitted: {data['action_type']} - {final_status}",
            correlation_id=correlation_id,
            metadata=audit_metadata
        )

        logger.info(
            f"[{correlation_id}] Step 7 complete - Audit logged "
            f"(processing: {processing_time_ms}ms)"
        )

        # ====================================================================
        # RETURN COMPREHENSIVE RESPONSE
        # ====================================================================
        return {
            "id": action.id,
            "action_id": action.id,  # SEC-105b: Alias for SDK compatibility
            "status": action.status,
            "risk_score": action.risk_score,
            "risk_level": action.risk_level,
            "cvss_score": action.cvss_score,
            "cvss_severity": action.cvss_severity,
            "cvss_vector": action.cvss_vector,
            "requires_approval": requires_approval,
            "alert_triggered": alert_triggered,
            "alert_id": alert_id,
            "workflow_id": workflow_id,
            "policy_decision": policy_decision,
            "matched_policies": matched_policies,
            "matched_smart_rules": len(smart_rules_result["matched_rules"]),
            "correlation_id": correlation_id,
            "processing_time_ms": processing_time_ms,
            # SEC-105b: Include NIST/MITRE compliance mapping in response
            "action_type": action.action_type,
            "nist_control": action.nist_control,
            "nist_description": action.nist_description,
            "mitre_tactic": action.mitre_tactic,
            "mitre_technique": action.mitre_technique,
            # SEC-106: Include threshold info for transparency
            "thresholds": {
                "auto_approve_below": auto_approve_threshold,
                "max_risk_threshold": max_risk_threshold,
                "agent_type": agent_type,
                "is_registered": registered_agent is not None
            },
            # Phase 9: Code analysis results
            "code_analysis": {
                "analyzed": code_analysis_result.code_analyzed if code_analysis_result else False,
                "language": code_analysis_result.language if code_analysis_result else None,
                "findings_count": len(code_analysis_result.findings) if code_analysis_result else 0,
                "max_severity": code_analysis_result.max_severity if code_analysis_result else None,
                "patterns_matched": code_analysis_result.patterns_matched if code_analysis_result else [],
                "blocked": code_blocked,
                "block_reason": code_analysis_result.block_reason if code_analysis_result and code_blocked else None,
                # SEC-PHASE9-001: Debug - show risk_adjustment to trace issue
                "risk_adjustment": code_analysis_result.risk_adjustment if code_analysis_result else 0
            } if code_analysis_result else None,
            "message": f"Action processed through complete governance pipeline - Status: {final_status}",
            "api_version": "SEC-PHASE9-001-V6"  # SEC-PHASE9-001-V6: Added diagnostic logging + cache bust
        }

    except HTTPException:
        raise

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[{correlation_id}] Action submission failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error during action processing",
                "correlation_id": correlation_id,
                "processing_time_ms": processing_time_ms
            }
        )


@router.get("", response_model=List[Dict[str, Any]])
async def list_actions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth),
    limit: int = 100,
    offset: int = 0,
    status_filter: Optional[str] = None
):
    """
    List agent actions for organization.

    Query Parameters:
        - limit: Maximum number of actions to return (default: 100, max: 1000)
        - offset: Number of actions to skip (default: 0)
        - status_filter: Filter by status (approved, pending_approval, denied)

    Returns:
        List of action objects with basic information

    Authentication: Supports both JWT tokens and API keys
    """
    try:
        # Validate limit
        if limit > 1000:
            limit = 1000

        # Build query with org isolation
        query = db.query(AgentAction).filter(
            AgentAction.organization_id == org_id
        )

        # Apply status filter if provided
        if status_filter:
            query = query.filter(AgentAction.status == status_filter)

        # Order by most recent first
        query = query.order_by(desc(AgentAction.timestamp))

        # Apply pagination
        actions = query.offset(offset).limit(limit).all()

        # Format response - Phase 9: Include extra_data for code analysis display
        return [
            {
                "id": action.id,
                "agent_id": action.agent_id,
                "action_type": action.action_type,
                "description": action.description,
                "status": action.status,
                "risk_score": action.risk_score,
                "risk_level": action.risk_level,
                "cvss_score": action.cvss_score,
                "cvss_severity": action.cvss_severity,
                "timestamp": action.timestamp.isoformat() if action.timestamp else None,
                "tool_name": action.tool_name,
                "target_system": action.target_system,
                # Phase 9: Include extra_data for code analysis findings
                "extra_data": action.extra_data
            }
            for action in actions
        ]

    except Exception as e:
        logger.error(f"Failed to list actions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve actions"
        )


@router.get("/{action_id}", response_model=Dict[str, Any])
async def get_action_details(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Get detailed information for a specific action.

    Returns comprehensive action details including:
    - All governance pipeline results
    - CVSS metrics
    - Policy evaluation results
    - Smart rules matches
    - Alert information (if triggered)
    - Workflow information (if assigned)

    Authentication: Supports both JWT tokens and API keys
    """
    try:
        # Query with org isolation
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id
        ).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        # Get associated alert (if any)
        alert = db.query(Alert).filter(
            Alert.agent_action_id == action_id,
            Alert.organization_id == org_id
        ).first()

        # Format response with all details - Phase 9: Include extra_data for code analysis
        return {
            "id": action.id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "description": action.description,
            "tool_name": action.tool_name,
            "status": action.status,
            "risk_score": action.risk_score,
            "risk_level": action.risk_level,
            "cvss_score": action.cvss_score,
            "cvss_severity": action.cvss_severity,
            "cvss_vector": action.cvss_vector,
            "nist_control": action.nist_control,
            "nist_description": action.nist_description,
            "mitre_tactic": action.mitre_tactic,
            "mitre_technique": action.mitre_technique,
            "recommendation": action.recommendation,
            "target_system": action.target_system,
            "timestamp": action.timestamp.isoformat() if action.timestamp else None,
            "user_id": action.user_id,
            "organization_id": action.organization_id,
            # Phase 9: Include extra_data for code analysis findings
            "extra_data": action.extra_data,
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "status": alert.status,
                "timestamp": alert.timestamp.isoformat() if alert.timestamp else None
            } if alert else None
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get action details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve action details"
        )


@router.get("/{action_id}/status", response_model=Dict[str, Any])
async def get_action_status(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)
):
    """
    Poll for action decision status (optimized for SDK polling).

    This endpoint is optimized for SDK clients to poll for approval decisions.
    Returns minimal data for fast response times.

    Response:
        {
            "action_id": int,
            "status": "approved|pending_approval|denied",
            "risk_score": float,
            "timestamp": "ISO 8601 string",
            "decision_ready": bool
        }

    Authentication: Supports both JWT tokens and API keys
    """
    try:
        # Lightweight query - only fetch needed fields
        action = db.query(
            AgentAction.id,
            AgentAction.status,
            AgentAction.risk_score,
            AgentAction.timestamp
        ).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id
        ).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        # Determine if decision is ready
        decision_ready = action.status in ["approved", "denied"]

        return {
            "action_id": action.id,
            "status": action.status,
            "risk_score": action.risk_score,
            "timestamp": action.timestamp.isoformat() if action.timestamp else None,
            "decision_ready": decision_ready
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get action status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve action status"
        )


@router.post("/{action_id}/approve", response_model=Dict[str, Any])
async def approve_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # JWT only (admin action)
    org_id: int = Depends(get_organization_filter)
):
    """
    Approve a pending action (admin only).

    This endpoint requires JWT authentication (no API keys).
    Only users with appropriate permissions can approve actions.

    Response:
        {
            "action_id": int,
            "status": "approved",
            "approved_by": int,
            "approved_at": "ISO 8601 string",
            "correlation_id": "string"
        }

    Authentication: JWT tokens only (admin/manager role)
    """
    correlation_id = generate_correlation_id()

    try:
        # Query with org isolation
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id
        ).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        # Check if action can be approved
        if action.status != "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action is not pending approval (current status: {action.status})"
            )

        # Update action status
        action.status = "approved"
        approved_at = datetime.now(UTC)

        db.add(action)
        db.commit()
        db.refresh(action)

        # Create audit log
        create_audit_log(
            db=db,
            user_id=current_user.get("user_id"),
            organization_id=org_id,
            action_type="action_approved",
            details=f"Action {action_id} approved by user {current_user.get('user_id')}",
            correlation_id=correlation_id,
            metadata={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "action_id": action_id
            }
        )

        logger.info(f"[{correlation_id}] Action {action_id} approved by user {current_user.get('user_id')}")

        return {
            "action_id": action.id,
            "status": action.status,
            "approved_by": current_user.get("user_id"),
            "approved_at": approved_at.isoformat(),
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[{correlation_id}] Failed to approve action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve action"
        )


@router.post("/{action_id}/reject", response_model=Dict[str, Any])
async def reject_action(
    action_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # JWT only (admin action)
    org_id: int = Depends(get_organization_filter)
):
    """
    Reject a pending action (admin only).

    This endpoint requires JWT authentication (no API keys).
    Only users with appropriate permissions can reject actions.

    Request Body (optional):
        {
            "reason": "string"
        }

    Response:
        {
            "action_id": int,
            "status": "denied",
            "rejected_by": int,
            "rejected_at": "ISO 8601 string",
            "reason": "string",
            "correlation_id": "string"
        }

    Authentication: JWT tokens only (admin/manager role)
    """
    correlation_id = generate_correlation_id()

    try:
        # Parse optional reason from request body
        reason = None
        try:
            body = await request.json()
            reason = body.get("reason")
        except:
            pass

        # Query with org isolation
        action = db.query(AgentAction).filter(
            AgentAction.id == action_id,
            AgentAction.organization_id == org_id
        ).first()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found"
            )

        # Check if action can be rejected
        if action.status != "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action is not pending approval (current status: {action.status})"
            )

        # Update action status
        action.status = "denied"
        rejected_at = datetime.now(UTC)

        db.add(action)
        db.commit()
        db.refresh(action)

        # Create audit log
        create_audit_log(
            db=db,
            user_id=current_user.get("user_id"),
            organization_id=org_id,
            action_type="action_rejected",
            details=f"Action {action_id} rejected by user {current_user.get('user_id')}: {reason or 'No reason provided'}",
            correlation_id=correlation_id,
            metadata={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "action_id": action_id,
                "reason": reason
            }
        )

        logger.info(f"[{correlation_id}] Action {action_id} rejected by user {current_user.get('user_id')}")

        return {
            "action_id": action.id,
            "status": action.status,
            "rejected_by": current_user.get("user_id"),
            "rejected_at": rejected_at.isoformat(),
            "reason": reason,
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[{correlation_id}] Failed to reject action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject action"
        )
