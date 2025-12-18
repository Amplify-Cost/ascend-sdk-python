"""
🏢 ENTERPRISE: Unified Policy Evaluation Service

This service provides a SINGLE policy engine for BOTH agent and MCP actions,
ensuring consistent risk scoring, policy evaluation, and governance decisions.

Features:
- Uses EnterpriseRealTimePolicyEngine for both action types
- 4-category comprehensive risk scoring (financial, data, security, compliance)
- Natural language policy support
- Sub-200ms evaluation performance
- Option 4 Policy Fusion support (hybrid risk scoring)
- Unified audit trail

Author: Enterprise Security Team
Version: 1.0.0
Security Level: Enterprise
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from sqlalchemy.orm import Session

# Import unified policy engine
from policy_engine import (
    EnterpriseRealTimePolicyEngine,
    PolicyEvaluationContext,
    PolicyEvaluationResult,
    create_evaluation_context
)

# Import models
from models import AgentAction, User
from models_mcp_governance import MCPServerAction

logger = logging.getLogger(__name__)


class UnifiedPolicyEvaluationService:
    """
    🏢 ENTERPRISE: Evaluates both agent and MCP actions using SAME policy engine

    This service eliminates duplicate policy logic by providing a single
    policy evaluation engine for all action types in the system.
    """

    def __init__(self, db: Session):
        """
        Initialize unified policy evaluation service.

        Args:
            db: Database session for policy engine queries
        """
        self.db = db
        self.policy_engine = EnterpriseRealTimePolicyEngine(db)
        logger.info("🏢 ENTERPRISE: UnifiedPolicyEvaluationService initialized")

    async def evaluate_agent_action(
        self,
        action: AgentAction,
        user_context: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluate agent action using EnterpriseRealTimePolicyEngine.

        Args:
            action: AgentAction model instance
            user_context: Optional additional user context

        Returns:
            PolicyEvaluationResult with decision, risk score, and matched policies
        """
        try:
            logger.info(f"🤖 Evaluating agent action {action.id} with unified policy engine")

            # Get user email (from user_id or created_by field)
            user_email = "unknown"
            user_role = "user"

            if user_context:
                user_email = user_context.get("email", "unknown")
                user_role = user_context.get("role", "user")
            elif action.created_by:
                user_email = action.created_by
            elif action.user_id:
                # Lookup user email from users table
                user = self.db.query(User).filter(User.id == action.user_id).first()
                if user:
                    user_email = user.email
                    user_role = user.role or "user"

            # Create policy evaluation context for agent action
            context = create_evaluation_context(
                user_id=str(action.user_id or 1),
                user_email=user_email,
                user_role=user_role,
                action_type=action.action_type,
                resource=action.target_resource or action.description or "unknown",
                namespace="agent",  # Virtual namespace for agent actions
                environment="production",
                client_ip="",
                session_data={}
            )

            # Prepare action metadata for risk scoring
            action_metadata = {
                "tool_name": action.tool_name,
                "risk_level": action.risk_level,
                "cvss_score": action.cvss_score,
                "nist_control": action.nist_control,
                "mitre_tactic": action.mitre_tactic,
                "mitre_technique": action.mitre_technique,
                "description": action.description
            }

            # Evaluate using policy engine
            result = await self.policy_engine.evaluate_policy(context, action_metadata)

            # 🏢 OPTION 4: Update action with policy results (Policy Fusion)
            action.policy_evaluated = True
            action.policy_decision = result.decision.value
            action.policy_risk_score = result.risk_score.total_score

            # Calculate hybrid risk fusion formula (80% CVSS, 20% Policy)
            if action.cvss_score:
                # Option 4 Hybrid: 80% CVSS + 20% Policy
                fused_risk = int((action.cvss_score * 10 * 0.8) + (result.risk_score.total_score * 0.2))
                action.risk_fusion_formula = f"hybrid_80_20_cvss_{action.cvss_score}_policy_{result.risk_score.total_score}_fused_{fused_risk}"
                # SEC-PHASE9-001-V11: Preserve highest risk score (code analysis may have set higher)
                action.risk_score = max(action.risk_score, float(fused_risk))
            else:
                # No CVSS score, use 100% policy risk
                action.risk_fusion_formula = f"policy_only_{result.risk_score.total_score}"
                # SEC-PHASE9-001-V11: Preserve highest risk score
                action.risk_score = max(action.risk_score, float(result.risk_score.total_score))

            # SEC-PHASE9-001-V11: Sync risk_level to match risk_score
            if action.risk_score >= 90:
                action.risk_level = "critical"
            elif action.risk_score >= 70:
                action.risk_level = "high"
            elif action.risk_score >= 40:
                action.risk_level = "medium"
            else:
                action.risk_level = "low"

            logger.info(
                f"SEC-PHASE9-001-V11: Risk fusion complete - "
                f"fused_risk={fused_risk if action.cvss_score else result.risk_score.total_score}, "
                f"final_risk_score={action.risk_score}, risk_level={action.risk_level}"
            )

            # Update approval level based on policy result
            if result.risk_score.requires_approval:
                action.approval_level = result.risk_score.approval_level
                action.required_approval_level = result.risk_score.approval_level

            self.db.commit()

            logger.info(
                f"✅ Agent action {action.id} evaluated: "
                f"decision={result.decision.value}, "
                f"policy_risk={result.risk_score.total_score}, "
                f"fused_risk={action.risk_score}, "
                f"time={result.evaluation_time_ms:.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Agent action {action.id} policy evaluation failed: {e}", exc_info=True)
            # Don't fail the action creation, just log the error
            self.db.rollback()
            raise

    async def evaluate_mcp_action(
        self,
        action: MCPServerAction,
        user_context: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluate MCP action using SAME EnterpriseRealTimePolicyEngine.

        This is the KEY integration point - MCP actions now use the SAME policy
        engine as agent actions, ensuring consistent risk scoring and governance.

        Args:
            action: MCPServerAction model instance
            user_context: Optional additional user context

        Returns:
            PolicyEvaluationResult with decision, risk score, and matched policies
        """
        try:
            logger.info(f"🔌 Evaluating MCP action {action.id} with unified policy engine")

            # Get user context (from action or user_context parameter)
            user_email = action.user_email or user_context.get("email", "unknown") if user_context else "unknown"
            user_role = action.user_role or user_context.get("role", "user") if user_context else "user"
            user_id = str(action.agent_id or "unknown")  # MCP reuses agent_id column for server ID

            # Create policy evaluation context for MCP action
            context = create_evaluation_context(
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                action_type=action.verb or action.action_type or "unknown",  # MCP verb → action_type
                resource=action.resource or "unknown",
                namespace=action.namespace or "mcp",  # MCP namespace (filesystem, database, etc.)
                environment="production",
                client_ip="",
                session_data={}
            )

            # Prepare action metadata for risk scoring
            action_metadata = {
                "mcp_server_id": action.agent_id,  # Server ID stored in agent_id column
                "namespace": action.namespace,
                "verb": action.verb,
                "parameters": action.context or {},  # Parameters stored in context JSONB
                "description": f"MCP {action.namespace}.{action.verb} on {action.resource}"
            }

            # Evaluate using SAME policy engine as agent actions ✅
            result = await self.policy_engine.evaluate_policy(context, action_metadata)

            # 🏢 OPTION 4: Update action with policy results (Policy Fusion)
            action.policy_evaluated = True
            action.policy_decision = result.decision.value
            action.policy_risk_score = result.risk_score.total_score
            action.risk_fusion_formula = f"policy_mcp_{result.risk_score.total_score}"

            # Update overall risk_score (MCP actions use 100% policy risk)
            action.risk_score = float(result.risk_score.total_score)

            # Map policy risk level to action risk_level
            action.risk_level = result.risk_score.risk_level

            self.db.commit()

            logger.info(
                f"✅ MCP action {action.id} evaluated: "
                f"decision={result.decision.value}, "
                f"policy_risk={result.risk_score.total_score}, "
                f"namespace={action.namespace}, "
                f"verb={action.verb}, "
                f"time={result.evaluation_time_ms:.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ MCP action {action.id} policy evaluation failed: {e}", exc_info=True)
            self.db.rollback()
            raise

    async def evaluate_action_by_type(
        self,
        action_id: Any,
        action_source: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluate any action type by source identifier.

        This is a convenience method for unified evaluation when you know
        the action source but not the model instance.

        Args:
            action_id: Action ID (integer for both types)
            action_source: "agent" or "mcp_server"
            user_context: Optional user context

        Returns:
            PolicyEvaluationResult
        """
        if action_source == "agent":
            action = self.db.query(AgentAction).filter(AgentAction.id == action_id).first()
            if not action:
                raise ValueError(f"Agent action {action_id} not found")
            return await self.evaluate_agent_action(action, user_context)

        elif action_source == "mcp_server" or action_source == "mcp":
            action = self.db.query(MCPServerAction).filter(MCPServerAction.id == action_id).first()
            if not action:
                raise ValueError(f"MCP action {action_id} not found")
            return await self.evaluate_mcp_action(action, user_context)

        else:
            raise ValueError(f"Unknown action source: {action_source}")

    def get_policy_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about policy evaluations.

        Returns:
            Dictionary with evaluation statistics
        """
        return self.policy_engine.get_policy_statistics()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for policy engine.

        Returns:
            Dictionary with performance metrics
        """
        return self.policy_engine.get_performance_metrics()

    def clear_policy_cache(self) -> Dict[str, int]:
        """
        Clear policy evaluation cache.

        Useful after policy changes to force re-evaluation.

        Returns:
            Dictionary with cache statistics
        """
        logger.info("🔄 Clearing unified policy engine cache")
        return self.policy_engine.clear_cache()


# ========== FACTORY FUNCTION ==========

def create_unified_policy_service(db: Session) -> UnifiedPolicyEvaluationService:
    """
    Factory function to create unified policy evaluation service.

    Args:
        db: Database session

    Returns:
        UnifiedPolicyEvaluationService instance
    """
    return UnifiedPolicyEvaluationService(db)


# Export main class and factory
__all__ = [
    'UnifiedPolicyEvaluationService',
    'create_unified_policy_service'
]
