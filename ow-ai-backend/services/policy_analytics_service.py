"""
Policy Analytics Service

Provides database-backed analytics for policy evaluation tracking.
Replaces fake random data with real metrics from policy_evaluations table.

Author: OW-KAI Engineer
Date: 2025-11-04
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from models import PolicyEvaluation, EnterprisePolicy, User

logger = logging.getLogger(__name__)


class PolicyAnalyticsService:
    """
    Tracks and analyzes policy evaluations for compliance and performance monitoring.
    """

    def __init__(self, db: Session):
        self.db = db

    async def log_evaluation(self,
                            evaluation_result: Dict[str, Any],
                            principal: str,
                            action: str,
                            resource: str,
                            context: Optional[Dict] = None,
                            user_id: Optional[int] = None,
                            policy_id: Optional[int] = None) -> PolicyEvaluation:
        """
        Log a policy evaluation to the database.

        Called after Cedar engine evaluates a policy to create audit trail.

        Args:
            evaluation_result: Result from EnforcementEngine.evaluate()
                {
                    "decision": "ALLOW|DENY|REQUIRE_APPROVAL",
                    "allowed": bool,
                    "policies_triggered": [...],
                    "evaluation_time_ms": int,
                    "timestamp": str
                }
            principal: Who made the request (e.g., "ai_agent:openai_gpt4")
            action: What action was requested (e.g., "database:write")
            resource: What resource (e.g., "arn:aws:db:prod/table")
            context: Additional request context (optional)
            user_id: Associated user ID (optional)
            policy_id: Primary policy ID if single policy evaluation (optional)

        Returns:
            PolicyEvaluation: Created database record

        Example:
            result = enforcement_engine.evaluate(principal, action, resource, context)
            await policy_analytics_service.log_evaluation(
                result, principal, action, resource, context, user_id=7
            )
        """
        try:
            evaluation = PolicyEvaluation(
                policy_id=policy_id,
                user_id=user_id,
                principal=principal,
                action=action,
                resource=resource,
                decision=evaluation_result.get("decision", "DENY"),
                allowed=evaluation_result.get("allowed", False),
                evaluation_time_ms=evaluation_result.get("evaluation_time_ms", 0),
                cache_hit=evaluation_result.get("cache_hit", False),
                policies_triggered=evaluation_result.get("policies_triggered", []),
                matched_conditions=context,
                context=context,
                error_message=evaluation_result.get("error")
            )

            self.db.add(evaluation)
            self.db.commit()
            self.db.refresh(evaluation)

            logger.info(f"Logged policy evaluation: {evaluation.id} - {evaluation.decision}")
            return evaluation

        except Exception as e:
            logger.error(f"Failed to log policy evaluation: {str(e)}")
            self.db.rollback()
            raise

    async def get_engine_metrics(self,
                                  time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Calculate real-time policy engine metrics from database.

        REPLACES the fake random.randint() metrics in unified_governance_routes.py:881-893

        Args:
            time_range_hours: Look back period (default 24 hours)

        Returns:
            Dict with metrics:
            {
                "total_evaluations": int,
                "evaluations_today": int,
                "denials": int,
                "approvals_required": int,
                "average_response_time_ms": float,
                "success_rate": float,
                "cache_hit_rate": float,
                "active_policies": int,
                "total_policies": int,
                "evaluation_throughput": int,  # per hour
                "last_updated": str
            }
        """
        try:
            start_time = datetime.now(UTC) - timedelta(hours=time_range_hours)

            # Query: Total evaluations in time range
            total_evaluations = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= start_time
            ).scalar() or 0

            # Query: Evaluations today
            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            evaluations_today = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= today_start
            ).scalar() or 0

            # Query: Denials count
            denials = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.decision == "DENY"
                )
            ).scalar() or 0

            # Query: Approvals required count
            approvals_required = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.decision == "REQUIRE_APPROVAL"
                )
            ).scalar() or 0

            # Query: Average response time
            avg_response_time = self.db.query(func.avg(PolicyEvaluation.evaluation_time_ms)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.evaluation_time_ms.isnot(None)
                )
            ).scalar() or 0.2

            # Query: Cache hit rate
            total_with_cache_data = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= start_time
            ).scalar() or 1

            cache_hits = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.cache_hit == True
                )
            ).scalar() or 0

            cache_hit_rate = (cache_hits / total_with_cache_data * 100) if total_with_cache_data > 0 else 0.0

            # Query: Success rate (non-errors)
            errors = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.error_message.isnot(None)
                )
            ).scalar() or 0

            success_rate = ((total_evaluations - errors) / total_evaluations * 100) if total_evaluations > 0 else 100.0

            # Query: Active policies
            active_policies = self.db.query(func.count(EnterprisePolicy.id)).filter(
                EnterprisePolicy.status == 'active'
            ).scalar() or 0

            # Query: Total policies
            total_policies = self.db.query(func.count(EnterprisePolicy.id)).scalar() or 0

            # Calculate: Throughput (evaluations per hour)
            evaluation_throughput = int(total_evaluations / time_range_hours) if time_range_hours > 0 else 0

            return {
                "total_evaluations": total_evaluations,
                "evaluations_today": evaluations_today,
                "denials": denials,
                "approvals_required": approvals_required,
                "average_response_time_ms": round(float(avg_response_time), 2),
                "success_rate": round(success_rate, 1),
                "cache_hit_rate": round(cache_hit_rate, 1),
                "active_policies": active_policies,
                "total_policies": total_policies,
                "evaluation_throughput": evaluation_throughput,
                "last_updated": datetime.now(UTC).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get engine metrics: {str(e)}")
            # Fail gracefully with empty metrics rather than crashing
            return {
                "total_evaluations": 0,
                "evaluations_today": 0,
                "denials": 0,
                "approvals_required": 0,
                "average_response_time_ms": 0.0,
                "success_rate": 0.0,
                "cache_hit_rate": 0.0,
                "active_policies": 0,
                "total_policies": 0,
                "evaluation_throughput": 0,
                "last_updated": datetime.now(UTC).isoformat(),
                "error": str(e)
            }

    async def get_policy_effectiveness(self,
                                       policy_id: int,
                                       time_range_days: int = 30) -> Dict[str, Any]:
        """
        Analyze effectiveness of a specific policy.

        Args:
            policy_id: Policy to analyze
            time_range_days: Analysis period

        Returns:
            Dict with policy statistics:
            {
                "policy_id": int,
                "evaluations": int,
                "denials": int,
                "approvals": int,
                "approval_requests": int,
                "avg_evaluation_time_ms": float,
                "triggered_count": int,
                "effectiveness_score": float  # 0-100
            }
        """
        start_time = datetime.now(UTC) - timedelta(days=time_range_days)

        # Evaluations where this policy was primary
        evaluations = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Denials
        denials = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "DENY",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Approvals
        approvals = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "ALLOW",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Approval requests
        approval_requests = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "REQUIRE_APPROVAL",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Average evaluation time
        avg_time = self.db.query(func.avg(PolicyEvaluation.evaluation_time_ms)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0.0

        # Calculate effectiveness score (denials + approval_requests = active protection)
        active_protections = denials + approval_requests
        effectiveness_score = (active_protections / evaluations * 100) if evaluations > 0 else 0.0

        return {
            "policy_id": policy_id,
            "evaluations": evaluations,
            "denials": denials,
            "approvals": approvals,
            "approval_requests": approval_requests,
            "avg_evaluation_time_ms": round(float(avg_time), 2),
            "triggered_count": evaluations,
            "effectiveness_score": round(effectiveness_score, 1)
        }


# Singleton instance
def get_policy_analytics_service(db: Session) -> PolicyAnalyticsService:
    """Factory function to create PolicyAnalyticsService instance"""
    return PolicyAnalyticsService(db)
