"""
Enterprise Pending Actions Service
==================================

SINGLE SOURCE OF TRUTH for pending action business logic.

Business Rules (defined once, used everywhere):
-----------------------------------------------
1. "pending_approval" = HIGH-RISK actions requiring human review
   - Shows in Authorization Center
   - Counts in dashboard metrics
   - Requires Level 5+ approval

2. "pending" = Low-risk actions auto-approved by system
   - Does NOT show in Authorization Center
   - Does NOT count in dashboard metrics
   - Historical/test data only

Why This Matters:
-----------------
- Prevents dashboard showing 44 when only 2 need review
- Single place to update business logic
- Clear documentation for future developers
- Eliminates "chase the API call" debugging

Usage:
------
From any route:
    from services.pending_actions_service import pending_service

    # Get count for dashboard (ONBOARD-018: org_id required for tenant isolation)
    count = pending_service.get_pending_count(db, org_id=org_id)

    # Get full list for Authorization Center (ONBOARD-018: org_id required)
    actions = pending_service.get_pending_actions(db, org_id=org_id)
"""

import logging
from typing import List
from sqlalchemy.orm import Session
from models import AgentAction

logger = logging.getLogger(__name__)


class PendingActionsService:
    """
    Centralized business logic for pending actions
    """
    
    # Business rule: Only these statuses need human review
    REQUIRES_APPROVAL_STATUSES = ["pending_approval"]
    
    def get_pending_count(self, db: Session, org_id: int = None) -> int:
        """
        Get count of actions requiring human approval

        ONBOARD-018: Added org_id parameter for tenant isolation
        Security: Tenant-isolated via organization_id filter
        Compliance: SOC 2 CC6.1, HIPAA 164.312(a)(1)

        Args:
            db: Database session
            org_id: Organization ID for tenant filtering (required for isolation)

        Returns:
            int: Count of actions in Authorization Center for this organization
        """
        query = db.query(AgentAction).filter(
            AgentAction.status.in_(self.REQUIRES_APPROVAL_STATUSES)
        )

        # ONBOARD-018: Filter by organization_id for tenant isolation
        if org_id is not None:
            query = query.filter(AgentAction.organization_id == org_id)
        else:
            logger.warning("SECURITY: get_pending_count called without org_id - returning 0 for safety")
            return 0

        count = query.count()
        logger.debug(f"Pending approval count for org_id={org_id}: {count}")
        return count

    def get_pending_actions(self, db: Session, org_id: int = None) -> List[AgentAction]:
        """
        Get all actions requiring human approval

        ONBOARD-018: Added org_id parameter for tenant isolation
        Security: Tenant-isolated via organization_id filter
        Compliance: SOC 2 CC6.1, HIPAA 164.312(a)(1)

        Args:
            db: Database session
            org_id: Organization ID for tenant filtering (required for isolation)

        Returns:
            List[AgentAction]: Actions for Authorization Center for this organization
        """
        query = db.query(AgentAction).filter(
            AgentAction.status.in_(self.REQUIRES_APPROVAL_STATUSES)
        )

        # ONBOARD-018: Filter by organization_id for tenant isolation
        if org_id is not None:
            query = query.filter(AgentAction.organization_id == org_id)
        else:
            logger.warning("SECURITY: get_pending_actions called without org_id - returning empty for safety")
            return []

        actions = query.all()
        logger.debug(f"Retrieved {len(actions)} pending approval actions for org_id={org_id}")
        return actions
    
    def explain_status(self, status: str) -> str:
        """
        Explain what a status means (for documentation/debugging)
        """
        explanations = {
            "pending_approval": "HIGH-RISK: Requires human review in Authorization Center",
            "pending": "Low-risk: Auto-approved, does not need human review",
            "approved": "Human approved and executed",
            "rejected": "Human denied",
            "executed": "Successfully executed",
            "execution_failed": "Execution failed"
        }
        return explanations.get(status, "Unknown status")


# Singleton instance
pending_service = PendingActionsService()
