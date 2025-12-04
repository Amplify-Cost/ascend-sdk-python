"""
SEC-064: Enterprise Risk Assessment Pipeline

Enterprise-grade unified risk assessment service following industry standards:
- Datadog: Unified telemetry pipeline pattern
- Wiz.io: Security graph centralization
- Splunk: Multi-stage processing pipeline
- PagerDuty: Event orchestration pattern

This service provides a SINGLE SOURCE OF TRUTH for risk assessment across all
agent action endpoints, ensuring consistent evaluation and centralized audit.

Compliance:
- SOC 2 Type II: CC3.2, CC6.1, CC7.1, CC7.2
- PCI-DSS: 6.1, 7.1, 12.10
- NIST 800-30: Risk Assessment
- NIST 800-53: AC-3, AU-12, IR-4, IR-6, RA-3, SI-3, SI-4

Document ID: SEC-064
Publisher: OW-kai Corporation
Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from models import AgentAction, Alert

logger = logging.getLogger(__name__)


# =============================================================================
# ENTERPRISE DATA STRUCTURES
# Following Datadog's structured telemetry pattern
# =============================================================================

@dataclass
class CVSSResult:
    """CVSS 3.1 calculation result"""
    base_score: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    vector_string: Optional[str] = None
    exploitability_score: Optional[float] = None
    impact_score: Optional[float] = None


@dataclass
class ComplianceMapping:
    """Security framework mapping result"""
    mitre_tactic: str = "Unknown"
    mitre_technique: str = "Unknown"
    mitre_subtechnique: Optional[str] = None
    nist_control: str = "Unknown"
    nist_description: Optional[str] = None
    nist_family: Optional[str] = None


@dataclass
class PolicyEvaluation:
    """Policy engine evaluation result"""
    evaluated: bool = False
    risk_score: Optional[int] = None
    decision: Optional[str] = None  # allow, deny, require_approval
    matched_policies: List[str] = field(default_factory=list)


@dataclass
class RiskFusion:
    """Risk fusion calculation details"""
    policy_risk: Optional[int] = None
    hybrid_risk: Optional[int] = None
    fused_score: int = 0
    fusion_applied: bool = False
    formula: str = ""
    safety_rules_applied: List[str] = field(default_factory=list)


@dataclass
class AutomationResult:
    """Automation service result"""
    playbook_matched: bool = False
    playbook_name: Optional[str] = None
    playbook_executed: bool = False
    auto_approved: bool = False
    workflow_triggered: bool = False
    workflow_id: Optional[str] = None
    alert_created: bool = False
    alert_id: Optional[int] = None


@dataclass
class EnterpriseRiskResult:
    """
    SEC-064: Comprehensive enterprise risk assessment result

    This dataclass captures the complete output of the 9-stage risk pipeline,
    providing full transparency for audit and compliance requirements.

    Enterprise Pattern: Follows Datadog's structured telemetry approach
    """
    # Core risk assessment
    risk_score: int                          # 0-100 final score
    risk_level: str                          # low/medium/high/critical
    requires_approval: bool                  # Based on risk thresholds
    status: str                              # approved/pending/denied
    approved: bool                           # Final approval status

    # Compliance data
    cvss: Optional[CVSSResult] = None
    compliance: ComplianceMapping = field(default_factory=ComplianceMapping)

    # Risk breakdown
    policy: PolicyEvaluation = field(default_factory=PolicyEvaluation)
    fusion: RiskFusion = field(default_factory=RiskFusion)

    # Automation results
    automation: AutomationResult = field(default_factory=AutomationResult)

    # Audit metadata
    pipeline_version: str = "1.0.0"
    processing_time_ms: float = 0.0
    stages_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "status": self.status,
            "approved": self.approved,
            "compliance": {
                "cvss_score": self.cvss.base_score if self.cvss else None,
                "cvss_severity": self.cvss.severity if self.cvss else None,
                "mitre_tactic": self.compliance.mitre_tactic,
                "mitre_technique": self.compliance.mitre_technique,
                "nist_control": self.compliance.nist_control
            },
            "risk_assessment": {
                "policy_evaluated": self.policy.evaluated,
                "policy_risk": self.fusion.policy_risk,
                "hybrid_risk": self.fusion.hybrid_risk,
                "fusion_applied": self.fusion.fusion_applied,
                "fusion_formula": self.fusion.formula,
                "safety_rules_applied": self.fusion.safety_rules_applied
            },
            "automation": {
                "playbook": {
                    "matched": self.automation.playbook_matched,
                    "name": self.automation.playbook_name,
                    "auto_approved": self.automation.auto_approved
                },
                "workflow": {
                    "triggered": self.automation.workflow_triggered,
                    "workflow_id": self.automation.workflow_id
                },
                "alert": {
                    "created": self.automation.alert_created,
                    "alert_id": self.automation.alert_id
                }
            },
            "meta": {
                "pipeline_version": self.pipeline_version,
                "processing_time_ms": round(self.processing_time_ms, 2),
                "stages_completed": self.stages_completed
            }
        }


# =============================================================================
# ENTERPRISE RISK PIPELINE
# Following Splunk's multi-stage processing pattern
# =============================================================================

class EnterpriseRiskPipeline:
    """
    SEC-064: Unified Enterprise Risk Assessment Pipeline

    This class provides a centralized, enterprise-grade risk assessment pipeline
    that consolidates all risk evaluation logic into a single source of truth.

    Enterprise Patterns Applied:
    - Datadog: Structured telemetry and metrics
    - Wiz.io: Centralized security graph
    - Splunk: Multi-stage processing pipeline
    - PagerDuty: Event orchestration

    9-Stage Pipeline:
    1. CVSS Calculator - Vulnerability scoring
    2. MITRE ATT&CK Mapper - Threat intelligence
    3. NIST 800-53 Mapper - Compliance controls
    4. Policy Engine - Organization policies
    5. Hybrid Risk Calculator - Multi-factor scoring
    6. Risk Fusion - 80% Policy + 20% Hybrid
    7. Safety Rules - Hard override rules
    8. Automation Service - Playbook matching
    9. Orchestration Service - Workflow triggering

    Compliance:
    - SOC 2 CC3.2, CC6.1, CC7.1, CC7.2
    - PCI-DSS 6.1, 7.1, 12.10
    - NIST 800-30, 800-53 (AC-3, AU-12, IR-4, IR-6, RA-3, SI-3, SI-4)
    """

    PIPELINE_VERSION = "1.0.0"

    # Risk level thresholds (enterprise standard)
    THRESHOLD_CRITICAL = 85
    THRESHOLD_HIGH = 70
    THRESHOLD_MEDIUM = 45

    # Safety rule floors
    SAFETY_CVSS_CRITICAL_FLOOR = 85
    SAFETY_POLICY_DENY_SCORE = 100
    SAFETY_PII_PRODUCTION_FLOOR = 70

    # Risk fusion weights
    POLICY_WEIGHT = 0.8
    HYBRID_WEIGHT = 0.2

    def __init__(self, db: Session):
        """
        Initialize enterprise risk pipeline.

        Args:
            db: SQLAlchemy database session for service queries
        """
        self.db = db
        logger.info(f"SEC-064: EnterpriseRiskPipeline initialized (v{self.PIPELINE_VERSION})")

    def _validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate required fields before pipeline execution.

        Defense-in-depth validation ensuring pipeline receives complete data
        even if calling endpoints change their validation logic.

        Args:
            data: Request data dictionary to validate

        Raises:
            ValueError: If required fields are missing or empty

        Compliance:
            - PCI-DSS 6.5.1: Input Validation
            - NIST 800-53 SI-10: Information Input Validation
        """
        required_fields = ["agent_id", "action_type", "description", "tool_name"]
        missing = [f for f in required_fields if f not in data or not data[f]]

        if missing:
            error_msg = f"SEC-064: Missing required fields: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"SEC-064: Input validation passed - all required fields present")

    async def evaluate_action(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        current_user: Dict[str, Any],
        organization_id: int,
        source: str = "unknown"
    ) -> EnterpriseRiskResult:
        """
        Execute full 9-stage enterprise risk assessment pipeline.

        This is the SINGLE ENTRY POINT for all risk assessment in the platform,
        ensuring consistent evaluation across SDK, Auth API, and all other endpoints.

        Args:
            action: AgentAction model instance (already created in DB)
            data: Original request data containing action details
            current_user: Authenticated user/agent context
            organization_id: Tenant isolation ID
            source: Calling endpoint identifier for audit

        Returns:
            EnterpriseRiskResult with complete assessment data

        Compliance:
            - SOC 2 CC7.2: Consistent risk evaluation
            - NIST 800-30: Standardized risk assessment
            - PCI-DSS 6.1: Secure development practices
        """
        start_time = time.time()
        result = EnterpriseRiskResult(
            risk_score=action.risk_score or 0,
            risk_level=action.risk_level or "medium",
            requires_approval=action.requires_approval or False,
            status=action.status or "pending",
            approved=action.approved or False
        )

        logger.info(f"SEC-064: Pipeline started for action {action.id} from {source} (org: {organization_id})")

        # SEC-064 FIX: Defense-in-depth input validation
        # Compliance: PCI-DSS 6.5.1, NIST 800-53 SI-10
        self._validate_input(data)

        try:
            # Stage 1: CVSS Calculator
            result.cvss = await self._stage_cvss(action, data, result)

            # Stage 2: MITRE ATT&CK Mapping
            await self._stage_mitre(action, data, result)

            # Stage 3: NIST 800-53 Mapping
            await self._stage_nist(action, data, result)

            # Stage 4: Policy Engine Evaluation
            await self._stage_policy(action, data, current_user, result)

            # Stage 5: Hybrid Risk Calculator
            hybrid_risk = await self._stage_hybrid_risk(action, data, current_user, result)

            # Stage 6: Risk Fusion (80% Policy + 20% Hybrid)
            await self._stage_risk_fusion(action, result)

            # Stage 7: Safety Rules
            await self._stage_safety_rules(action, data, result)

            # Stage 8: Update action with final assessment
            self._update_action(action, result)

            # Stage 9: Automation Service (Playbooks)
            await self._stage_automation(action, result)

            # Stage 10: Orchestration Service (Workflows)
            await self._stage_orchestration(action, result)

            # Stage 11: Alert Generation (if high/critical)
            await self._stage_alert_generation(action, data, organization_id, result)

            # Commit all changes
            self.db.commit()
            self.db.refresh(action)

        except Exception as e:
            logger.error(f"SEC-064: Pipeline error for action {action.id}: {e}")
            result.errors.append(str(e))

            # SEC-064 FIX: Explicit rollback on exception
            # Compliance: SOC 2 CC8.1, PCI-DSS 6.5.5 (Transaction Integrity)
            try:
                self.db.rollback()
                logger.info(f"SEC-064: Database changes rolled back for action {action.id}")
            except Exception as rollback_error:
                logger.error(f"SEC-064: Rollback failed for action {action.id}: {rollback_error}")

            # Don't re-raise - return partial result for graceful degradation

        # Calculate processing time
        result.processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"SEC-064: Pipeline completed for action {action.id} - "
            f"score={result.risk_score}, level={result.risk_level}, "
            f"stages={len(result.stages_completed)}, time={result.processing_time_ms:.1f}ms"
        )

        return result

    # =========================================================================
    # STAGE 1: CVSS Calculator
    # Compliance: PCI-DSS 6.1, NIST 800-53 RA-5
    # =========================================================================
    async def _stage_cvss(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> Optional[CVSSResult]:
        """Calculate CVSS 3.1 score for the action."""
        try:
            from services.cvss_calculator import cvss_calculator

            cvss_data = cvss_calculator.calculate_base_score({
                "action_type": data["action_type"],
                "tool_name": data["tool_name"],
                "description": data["description"],
                "environment": data.get("environment", "production")
            })

            if cvss_data:
                cvss_result = CVSSResult(
                    base_score=cvss_data.get("base_score", 0),
                    severity=cvss_data.get("severity", "UNKNOWN"),
                    vector_string=cvss_data.get("vector_string"),
                    exploitability_score=cvss_data.get("exploitability_score"),
                    impact_score=cvss_data.get("impact_score")
                )

                # Update action
                action.cvss_score = cvss_result.base_score
                action.cvss_severity = cvss_result.severity
                self.db.flush()

                result.stages_completed.append("cvss")
                logger.info(f"SEC-064: Stage 1 CVSS complete - {cvss_result.base_score} ({cvss_result.severity})")
                return cvss_result

        except Exception as e:
            logger.warning(f"SEC-064: Stage 1 CVSS failed: {e}")
            result.errors.append(f"cvss: {e}")

        return None

    # =========================================================================
    # STAGE 2: MITRE ATT&CK Mapping
    # Compliance: NIST 800-53 SI-4, SOC 2 CC7.2
    # =========================================================================
    async def _stage_mitre(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> None:
        """Map action to MITRE ATT&CK framework."""
        try:
            from services.mitre_mapper import mitre_mapper

            mitre_data = mitre_mapper.map_action_to_techniques(
                db=self.db,
                action_id=action.id,
                action_type=data["action_type"]
            )

            if mitre_data and mitre_data.get("mapped"):
                result.compliance.mitre_tactic = mitre_data.get("tactic", "Unknown")
                result.compliance.mitre_technique = mitre_data.get("technique", "Unknown")
                result.compliance.mitre_subtechnique = mitre_data.get("subtechnique")

                # Update action
                action.mitre_tactic = result.compliance.mitre_tactic
                action.mitre_technique = result.compliance.mitre_technique
                self.db.flush()

                result.stages_completed.append("mitre")
                logger.info(f"SEC-064: Stage 2 MITRE complete - {result.compliance.mitre_tactic}/{result.compliance.mitre_technique}")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 2 MITRE failed: {e}")
            result.errors.append(f"mitre: {e}")

    # =========================================================================
    # STAGE 3: NIST 800-53 Mapping
    # Compliance: SOC 2 CC6.1, PCI-DSS 12.1
    # =========================================================================
    async def _stage_nist(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> None:
        """Map action to NIST 800-53 controls."""
        try:
            from services.nist_mapper import nist_mapper

            nist_data = nist_mapper.map_action_to_controls(
                db=self.db,
                action_id=action.id,
                action_type=data["action_type"]
            )

            if nist_data and nist_data.get("mapped"):
                result.compliance.nist_control = nist_data.get("control", "Unknown")
                result.compliance.nist_description = nist_data.get("description")
                result.compliance.nist_family = nist_data.get("family")

                # Update action
                action.nist_control = result.compliance.nist_control
                action.nist_description = result.compliance.nist_description
                self.db.flush()

                result.stages_completed.append("nist")
                logger.info(f"SEC-064: Stage 3 NIST complete - {result.compliance.nist_control}")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 3 NIST failed: {e}")
            result.errors.append(f"nist: {e}")

    # =========================================================================
    # STAGE 4: Policy Engine Evaluation
    # Compliance: NIST 800-53 AC-3, SOC 2 CC6.1, PCI-DSS 7.1
    # =========================================================================
    async def _stage_policy(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        current_user: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> None:
        """Evaluate organization policies."""
        try:
            from policy_engine import create_policy_engine, create_evaluation_context

            policy_engine = create_policy_engine(self.db)

            policy_context = create_evaluation_context(
                user_id=str(current_user.get("user_id", "unknown")),
                user_email=current_user.get("email", "agent@system"),
                user_role=current_user.get("role", "agent"),
                action_type=data["action_type"],
                resource=data.get("target_system", data.get("resource", data["description"])),
                namespace="enterprise_risk_pipeline",
                environment=data.get("environment", "production"),
                client_ip=""
            )

            action_metadata = {
                "tool_name": data["tool_name"],
                "action_type": data["action_type"],
                "description": data["description"],
                "cvss_score": result.cvss.base_score if result.cvss else None,
                "mitre_tactic": result.compliance.mitre_tactic,
                "nist_control": result.compliance.nist_control,
                "pipeline_source": True
            }

            policy_result = await policy_engine.evaluate_policy(policy_context, action_metadata)

            result.policy.evaluated = True
            result.policy.risk_score = policy_result.risk_score.total_score
            result.policy.decision = policy_result.decision.value if hasattr(policy_result.decision, 'value') else str(policy_result.decision)
            result.fusion.policy_risk = result.policy.risk_score

            # Update action
            action.policy_evaluated = True
            action.policy_decision = result.policy.decision
            action.policy_risk_score = result.policy.risk_score
            self.db.flush()

            result.stages_completed.append("policy")
            logger.info(f"SEC-064: Stage 4 Policy complete - score={result.policy.risk_score}, decision={result.policy.decision}")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 4 Policy failed: {e}")
            result.errors.append(f"policy: {e}")

    # =========================================================================
    # STAGE 5: Hybrid Risk Calculator v2
    # Formula: (Env × 35%) + (Data × 30%) + (CVSS × 25%) + (Context × 10%) × Multiplier
    # Compliance: NIST 800-30, SOC 2 CC3.2
    # =========================================================================
    async def _stage_hybrid_risk(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        current_user: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> Optional[int]:
        """Calculate hybrid risk score using multi-factor analysis."""
        try:
            from services.enterprise_risk_calculator_v2 import enterprise_risk_calculator

            hybrid_data = enterprise_risk_calculator.calculate_hybrid_risk_score(
                cvss_score=result.cvss.base_score if result.cvss else None,
                environment=data.get("environment", "production"),
                action_type=data["action_type"],
                contains_pii=data.get("contains_pii", False) or "pii" in data["description"].lower(),
                resource_name=data.get("target_system", data.get("resource", data["description"])),
                resource_type=data.get("resource_type", "unknown"),
                description=data["description"],
                action_metadata={
                    "user_id": current_user.get("user_id"),
                    "action_id": action.id,
                    "pipeline_source": True
                },
                db=self.db
            )

            result.fusion.hybrid_risk = hybrid_data["risk_score"]

            result.stages_completed.append("hybrid_risk")
            logger.info(f"SEC-064: Stage 5 Hybrid Risk complete - {result.fusion.hybrid_risk}/100")

            return result.fusion.hybrid_risk

        except Exception as e:
            logger.warning(f"SEC-064: Stage 5 Hybrid Risk failed: {e}")
            result.errors.append(f"hybrid_risk: {e}")
            result.fusion.hybrid_risk = action.risk_score  # Fallback
            return result.fusion.hybrid_risk

    # =========================================================================
    # STAGE 6: Risk Fusion (80% Policy + 20% Hybrid)
    # Compliance: SOC 2 CC3.2, NIST 800-30
    # =========================================================================
    async def _stage_risk_fusion(
        self,
        action: AgentAction,
        result: EnterpriseRiskResult
    ) -> None:
        """Fuse policy and hybrid risk scores."""
        policy_risk = result.fusion.policy_risk
        hybrid_risk = result.fusion.hybrid_risk

        if result.policy.evaluated and policy_risk is not None and hybrid_risk is not None:
            # Enterprise formula: 80% policy weight, 20% hybrid weight
            fused_score = (policy_risk * self.POLICY_WEIGHT) + (hybrid_risk * self.HYBRID_WEIGHT)

            result.fusion.fused_score = int(fused_score)
            result.fusion.fusion_applied = True
            result.fusion.formula = f"({policy_risk} × {self.POLICY_WEIGHT}) + ({hybrid_risk} × {self.HYBRID_WEIGHT}) = {fused_score:.1f}"

            result.stages_completed.append("risk_fusion")
            logger.info(f"SEC-064: Stage 6 Risk Fusion complete - {result.fusion.formula}")
        else:
            # No fusion possible, use hybrid or existing
            result.fusion.fused_score = hybrid_risk if hybrid_risk else action.risk_score or 0
            result.fusion.fusion_applied = False
            logger.info(f"SEC-064: Stage 6 Risk Fusion skipped - using direct score: {result.fusion.fused_score}")

    # =========================================================================
    # STAGE 7: Safety Rules (Hard Overrides)
    # Compliance: SOC 2 CC7.1, PCI-DSS 12.10
    # =========================================================================
    async def _stage_safety_rules(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        result: EnterpriseRiskResult
    ) -> None:
        """Apply safety rules that override calculated scores."""
        fused_score = result.fusion.fused_score

        # Safety Rule 1: CRITICAL CVSS sets minimum floor of 85
        if result.cvss and result.cvss.severity == "CRITICAL":
            if fused_score < self.SAFETY_CVSS_CRITICAL_FLOOR:
                fused_score = self.SAFETY_CVSS_CRITICAL_FLOOR
                result.fusion.safety_rules_applied.append("CRITICAL_CVSS_FLOOR_85")
                logger.info("SEC-064: Safety Rule 1 applied - CRITICAL CVSS, floor set to 85")

        # Safety Rule 2: Policy DENY sets score to 100
        if result.policy.decision and result.policy.decision.lower() == "deny":
            fused_score = self.SAFETY_POLICY_DENY_SCORE
            result.fusion.safety_rules_applied.append("POLICY_DENY_OVERRIDE_100")
            logger.info("SEC-064: Safety Rule 2 applied - Policy DENY, score set to 100")

        # Safety Rule 3: PII in production sets minimum floor of 70
        is_production = data.get("environment", "production") == "production"
        has_pii = "pii" in data["description"].lower() or data.get("contains_pii", False)
        if is_production and has_pii:
            if fused_score < self.SAFETY_PII_PRODUCTION_FLOOR:
                fused_score = self.SAFETY_PII_PRODUCTION_FLOOR
                result.fusion.safety_rules_applied.append("PII_PRODUCTION_FLOOR_70")
                logger.info("SEC-064: Safety Rule 3 applied - PII in production, floor set to 70")

        result.fusion.fused_score = int(fused_score)
        result.risk_score = int(fused_score)

        result.stages_completed.append("safety_rules")
        logger.info(f"SEC-064: Stage 7 Safety Rules complete - final score: {result.risk_score}")

    # =========================================================================
    # Update Action with Final Assessment
    # =========================================================================
    def _update_action(self, action: AgentAction, result: EnterpriseRiskResult) -> None:
        """Update action model with final risk assessment."""
        action.risk_score = result.risk_score

        # Determine risk level based on thresholds
        if result.risk_score >= self.THRESHOLD_CRITICAL:
            result.risk_level = "critical"
        elif result.risk_score >= self.THRESHOLD_HIGH:
            result.risk_level = "high"
        elif result.risk_score >= self.THRESHOLD_MEDIUM:
            result.risk_level = "medium"
        else:
            result.risk_level = "low"

        action.risk_level = result.risk_level

        # Determine approval requirement
        result.requires_approval = result.risk_level != "low"
        result.status = "approved" if not result.requires_approval else "pending"
        result.approved = not result.requires_approval

        action.requires_approval = result.requires_approval
        action.status = result.status
        action.approved = result.approved

        self.db.add(action)
        self.db.flush()

        logger.info(f"SEC-064: Action {action.id} updated - score={result.risk_score}, level={result.risk_level}, status={result.status}")

    # =========================================================================
    # STAGE 8: Automation Service (Playbook Matching)
    # Compliance: SOC 2 CC7.1, NIST 800-53 IR-4
    # =========================================================================
    async def _stage_automation(
        self,
        action: AgentAction,
        result: EnterpriseRiskResult
    ) -> None:
        """Match and execute automation playbooks."""
        try:
            from services.automation_service import get_automation_service

            automation_service = get_automation_service(self.db)

            action_data = {
                "risk_score": action.risk_score or 0,
                "action_type": action.action_type,
                "agent_id": action.agent_id,
                "timestamp": action.timestamp
            }

            matched_playbook = automation_service.match_playbooks(action_data)

            if matched_playbook:
                result.automation.playbook_matched = True

                execution_result = automation_service.execute_playbook(
                    playbook_id=matched_playbook.id,
                    action_id=action.id
                )

                if execution_result.get("success"):
                    result.automation.playbook_name = execution_result.get("playbook_name")
                    result.automation.playbook_executed = True
                    result.automation.auto_approved = True
                    logger.info(f"SEC-064: Stage 8 Playbook executed - {result.automation.playbook_name}")
                else:
                    logger.warning(f"SEC-064: Stage 8 Playbook execution failed")

            result.stages_completed.append("automation")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 8 Automation failed: {e}")
            result.errors.append(f"automation: {e}")

    # =========================================================================
    # STAGE 9: Orchestration Service (Workflow Triggering)
    # Compliance: SOC 2 CC7.2, NIST 800-53 IR-6
    # =========================================================================
    async def _stage_orchestration(
        self,
        action: AgentAction,
        result: EnterpriseRiskResult
    ) -> None:
        """Trigger approval workflows if needed."""
        try:
            from services.orchestration_service import get_orchestration_service

            orchestration_service = get_orchestration_service(self.db)

            orchestration_result = orchestration_service.orchestrate_action(
                action_id=action.id,
                risk_level=action.risk_level,
                risk_score=action.risk_score or 0,
                action_type=action.action_type
            )

            result.automation.workflow_triggered = orchestration_result.get("workflow_triggered", False)
            result.automation.workflow_id = orchestration_result.get("workflow_id")

            if result.automation.workflow_triggered:
                logger.info(f"SEC-064: Stage 9 Workflow triggered - {result.automation.workflow_id}")

            result.stages_completed.append("orchestration")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 9 Orchestration failed: {e}")
            result.errors.append(f"orchestration: {e}")

    # =========================================================================
    # STAGE 10: Alert Generation
    # Compliance: SOC 2 CC7.2, PCI-DSS 12.10, NIST 800-53 IR-6
    # =========================================================================
    async def _stage_alert_generation(
        self,
        action: AgentAction,
        data: Dict[str, Any],
        organization_id: int,
        result: EnterpriseRiskResult
    ) -> None:
        """Generate alerts for high-risk actions."""
        if result.risk_level not in ("high", "critical"):
            return

        try:
            # Check for existing alert
            existing_alert = self.db.query(Alert).filter(
                Alert.agent_action_id == action.id
            ).first()

            if existing_alert:
                result.automation.alert_id = existing_alert.id
                result.automation.alert_created = True
                logger.info(f"SEC-064: Alert already exists for action {action.id}: {existing_alert.id}")
                return

            # Create new alert
            severity = "critical" if result.risk_level == "critical" else "high"
            alert = Alert(
                agent_action_id=action.id,
                organization_id=organization_id,
                alert_type=f"{severity.title()} Risk Agent Action",
                severity=severity,
                message=(
                    f"Enterprise Alert: Agent '{data['agent_id']}' requesting {result.risk_level}-risk action: "
                    f"{data['action_type']} - {data['description'][:100]} | "
                    f"Score: {result.risk_score}/100 | "
                    f"NIST: {result.compliance.nist_control} | "
                    f"MITRE: {result.compliance.mitre_tactic}"
                ),
                timestamp=datetime.now(UTC)
            )

            self.db.add(alert)
            self.db.flush()

            result.automation.alert_id = alert.id
            result.automation.alert_created = True

            result.stages_completed.append("alert_generation")
            logger.info(f"SEC-064: Stage 10 Alert created - {alert.id} ({severity})")

        except Exception as e:
            logger.warning(f"SEC-064: Stage 10 Alert generation failed: {e}")
            result.errors.append(f"alert: {e}")


# =============================================================================
# FACTORY FUNCTION
# Following enterprise singleton pattern
# =============================================================================

def get_enterprise_risk_pipeline(db: Session) -> EnterpriseRiskPipeline:
    """
    Factory function to get EnterpriseRiskPipeline instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        EnterpriseRiskPipeline instance
    """
    return EnterpriseRiskPipeline(db)
