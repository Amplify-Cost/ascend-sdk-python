"""
Dynamic Approver Selection Service
Intelligently routes approval requests based on risk, department, and availability
"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ApproverSelector:
    """
    Selects appropriate approvers based on:
    - Risk level of the action
    - Department/resource type
    - Approval level required
    - Approver availability and workload
    """
    
    def select_approvers(
        self,
        db: Session,
        risk_score: float,
        approval_level: int,
        department: str = "Engineering",
        resource_type: str = None
    ) -> List[Dict]:
        """
        Main entry point - select best approvers for an action
        
        Returns list of approvers sorted by priority:
        - Primary approver (best match)
        - Secondary approvers (fallbacks)
        - Emergency approvers (if needed)
        """
        logger.info(
            f"Selecting approvers: risk={risk_score}, level={approval_level}, "
            f"dept={department}"
        )
        
        # Map risk score to risk category
        risk_category = self._get_risk_category(risk_score)
        
        # Get qualified approvers
        qualified = self._find_qualified_approvers(
            db, approval_level, risk_category, department
        )
        
        if not qualified:
            logger.warning("No qualified approvers found, using emergency approvers")
            return self._get_emergency_approvers(db)
        
        # Sort by workload (least busy first)
        sorted_approvers = self._sort_by_workload(db, qualified)
        
        logger.info(f"Found {len(sorted_approvers)} qualified approvers")
        return sorted_approvers
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Convert 0-100 risk score to category"""
        if risk_score >= 90:
            return "CRITICAL"
        elif risk_score >= 70:
            return "HIGH"
        elif risk_score >= 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _find_qualified_approvers(
        self,
        db: Session,
        approval_level: int,
        risk_category: str,
        department: str
    ) -> List[Dict]:
        """Find users qualified to approve at this level and risk"""
        
        # Risk hierarchy: CRITICAL > HIGH > MEDIUM > LOW
        risk_hierarchy = {
            "LOW": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "MEDIUM": ["MEDIUM", "HIGH", "CRITICAL"],
            "HIGH": ["HIGH", "CRITICAL"],
            "CRITICAL": ["CRITICAL"]
        }
        
        allowed_risks = risk_hierarchy.get(risk_category, ["CRITICAL"])
        
        query = text("""
            SELECT 
                id,
                email,
                role,
                department,
                approval_level,
                max_risk_approval,
                is_emergency_approver
            FROM users
            WHERE approval_level >= :level
              AND max_risk_approval = ANY(:risks)
              AND is_active = true
              AND status = 'active'
              AND (department = :dept OR role = 'admin')
            ORDER BY 
                CASE WHEN department = :dept THEN 0 ELSE 1 END,
                approval_level ASC
        """)
        
        result = db.execute(query, {
            "level": approval_level,
            "risks": allowed_risks,
            "dept": department
        })
        
        approvers = []
        for row in result:
            approvers.append({
                "id": row[0],
                "email": row[1],
                "role": row[2],
                "department": row[3],
                "approval_level": row[4],
                "max_risk_approval": row[5],
                "is_emergency": row[6]
            })
        
        return approvers
    
    def _sort_by_workload(
        self,
        db: Session,
        approvers: List[Dict]
    ) -> List[Dict]:
        """Sort approvers by current workload (pending approvals)"""
        
        # Count pending approvals per approver
        query = text("""
            SELECT 
                user_id,
                COUNT(*) as pending_count
            FROM agent_actions
            WHERE workflow_stage LIKE 'pending_%'
              AND user_id = ANY(:user_ids)
            GROUP BY user_id
        """)
        
        user_ids = [a["id"] for a in approvers]
        result = db.execute(query, {"user_ids": user_ids})
        
        workload = {row[0]: row[1] for row in result}
        
        # Add workload count to each approver
        for approver in approvers:
            approver["pending_count"] = workload.get(approver["id"], 0)
        
        # Sort by workload (least busy first), then by approval level
        approvers.sort(key=lambda x: (x["pending_count"], x["approval_level"]))
        
        return approvers
    
    def _get_emergency_approvers(self, db: Session) -> List[Dict]:
        """Get emergency approvers as last resort"""
        query = text("""
            SELECT id, email, role, department, approval_level
            FROM users
            WHERE is_emergency_approver = true
              AND is_active = true
            ORDER BY approval_level DESC
        """)
        
        result = db.execute(query)
        
        approvers = []
        for row in result:
            approvers.append({
                "id": row[0],
                "email": row[1],
                "role": row[2],
                "department": row[3],
                "approval_level": row[4],
                "is_emergency": True,
                "pending_count": 0
            })
        
        return approvers


# Singleton instance
approver_selector = ApproverSelector()
