"""
Enterprise Batch Loader v2 - Correct Status Filtering
Only returns HIGH-RISK actions requiring human approval
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import AgentAction

logger = logging.getLogger(__name__)

class EnterpriseBatchLoaderV2:
    """
    Optimized loader for ONLY pending_approval actions
    Performance: 4 queries instead of 6+ per action
    """
    
    def load_pending_approval_actions(self, db: Session) -> Dict:
        """
        Load ONLY pending_approval actions (high-risk, needs human review)
        Returns in original dict format expected by frontend
        """
        
        # Query 1: Get ONLY pending_approval actions (not 'pending')
        pending_actions = db.query(AgentAction).filter(
            AgentAction.status == "pending_approval"
        ).all()
        
        if not pending_actions:
            return {
                "success": True,
                "pending_actions": [],
                "actions": [],
                "total": 0
            }
        
        action_ids = [a.id for a in pending_actions]
        logger.info(f"Found {len(action_ids)} pending_approval actions")
        
        # Query 2-4: Batch load assessments
        cvss_map = {}
        nist_map = {}
        mitre_map = {}
        
        try:
            # CVSS assessments
            cvss_results = db.execute(text("""
                SELECT action_id, base_score, severity 
                FROM cvss_assessments 
                WHERE action_id = ANY(:ids)
            """), {"ids": action_ids}).fetchall()
            
            for row in cvss_results:
                cvss_map[row[0]] = {
                    "base_score": row[1],
                    "severity": row[2],
                    "risk_score": int(row[1] * 10)
                }
            
            # NIST controls
            nist_results = db.execute(text("""
                SELECT action_id, control_id 
                FROM nist_control_mappings 
                WHERE action_id = ANY(:ids)
            """), {"ids": action_ids}).fetchall()
            
            for row in nist_results:
                if row[0] not in nist_map:
                    nist_map[row[0]] = []
                nist_map[row[0]].append(row[1])
            
            # MITRE techniques
            mitre_results = db.execute(text("""
                SELECT action_id, technique_id 
                FROM mitre_technique_mappings 
                WHERE action_id = ANY(:ids)
            """), {"ids": action_ids}).fetchall()
            
            for row in mitre_results:
                if row[0] not in mitre_map:
                    mitre_map[row[0]] = []
                mitre_map[row[0]].append(row[1])
                
        except Exception as e:
            logger.warning(f"Assessment query failed: {e}")
        
        # Build transformed actions (matching original format exactly)
        transformed_actions = []

        for action in pending_actions:
            cvss = cvss_map.get(action.id, {})
            # ARCH-004: Use agent_actions table columns (populated by enrichment.py)
            nist_controls = [action.nist_control] if action.nist_control else nist_map.get(action.id, ["AC-3"])
            mitre_techniques = [action.mitre_technique] if action.mitre_technique else mitre_map.get(action.id, ["T1078"])

            # 🏢 ENTERPRISE FIX: Use agent_actions.risk_score first (from CVSS calculation during creation)
            if action.risk_score:
                risk_score = float(action.risk_score)
                logger.debug(f"Action {action.id}: Using stored risk_score from agent_actions: {risk_score}")
            elif cvss.get("risk_score"):
                risk_score = float(cvss.get("risk_score"))
                logger.debug(f"Action {action.id}: Using risk_score from cvss_assessments: {risk_score}")
            else:
                # 🏢 ENTERPRISE: Intelligent fallback based on risk_level (not always 50!)
                risk_level_scores = {"low": 30, "medium": 50, "high": 75, "critical": 95}
                risk_level = action.risk_level.lower() if action.risk_level else "medium"
                risk_score = float(risk_level_scores.get(risk_level, 50))
                logger.warning(f"Action {action.id} missing risk_score - using fallback from risk_level '{risk_level}': {risk_score}")
            
            transformed_action = {
                "id": action.id,
                "action_id": f"ENT_ACTION_{action.id:06d}",
                "agent_id": action.agent_id,
                "action_type": action.action_type,
                "description": action.description or f"{action.action_type} operation",
                "target_system": action.target_system or "Unknown",
                "risk_level": action.risk_level,
                "status": action.status,
                "created_at": action.timestamp.isoformat() if action.timestamp else None,
                "tool_name": "enterprise-mcp",
                "user_id": 1,
                "can_approve": True,
                "requires_approval": True,
                "estimated_impact": "Enterprise security enhancement",
                "execution_time_estimate": "45 seconds",
                "enterprise_risk_score": risk_score,
                "risk_score": risk_score,
                "requires_executive_approval": risk_score >= 80,
                "requires_board_notification": False,
                "compliance_frameworks": ["SOX", "PCI_DSS", "NIST"],
                # ARCH-004: Use database columns from agent_actions table
                "nist_control": action.nist_control or nist_controls[0] if nist_controls else "AC-3",
                "nist_controls": nist_controls,
                "nist_description": action.nist_description or "",
                "mitre_tactic": action.mitre_tactic or "TA0009",
                "mitre_technique": action.mitre_technique or mitre_techniques[0] if mitre_techniques else "T1078",
                "mitre_techniques": mitre_techniques,
                "recommendation": action.recommendation or "",
                "workflow_stage": "pending_stage_1",
                "current_approval_level": 0,
                "required_approval_level": 2 if risk_score >= 70 else 1
            }
            transformed_actions.append(transformed_action)
        
        logger.info(f"✅ Batch loaded {len(transformed_actions)} pending_approval actions in 4 queries")
        
        # Return in ORIGINAL format (dict, not list)
        return {
            "success": True,
            "pending_actions": transformed_actions,
            "actions": transformed_actions,
            "total": len(transformed_actions)
        }

enterprise_loader_v2 = EnterpriseBatchLoaderV2()
