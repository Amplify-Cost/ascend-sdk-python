"""
Enterprise Unified Authorization Loader
Merges Agent Actions + MCP Server Actions into single approval queue

Author: Donald King, OW-kai Enterprise
Date: November 15, 2025

Purpose:
- Query both agent_actions and mcp_server_actions tables
- Transform to common schema with prefixed IDs
- Sort by risk_score DESC, created_at ASC
- Return unified queue for Authorization Center

Industry Alignment: Splunk, Palo Alto Networks governance patterns
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import AgentAction
from models_mcp_governance import MCPServerAction

logger = logging.getLogger(__name__)

class EnterpriseUnifiedLoader:
    """
    Unified loader for ALL pending authorization actions
    Merges agent_actions + mcp_server_actions into single queue
    """

    def load_all_pending_actions(self, db: Session) -> Dict:
        """
        Load ALL pending actions from both tables
        Returns unified, sorted list with common schema

        Returns:
            {
                "success": True,
                "pending_actions": [...],
                "actions": [...],  # Backward compatibility
                "total": N,
                "counts": {
                    "total": N,
                    "agent_actions": X,
                    "mcp_actions": Y,
                    "high_risk": Z
                }
            }
        """

        # Query 1: Agent Actions (status = 'pending_approval')
        try:
            agent_actions = db.query(AgentAction).filter(
                AgentAction.status == "pending_approval"
            ).all()
            logger.info(f"Loaded {len(agent_actions)} agent actions with status=pending_approval")
        except Exception as e:
            logger.error(f"Failed to query agent_actions: {e}")
            agent_actions = []

        # Query 2: MCP Server Actions (status = 'PENDING' or 'EVALUATE')
        try:
            mcp_actions = db.query(MCPServerAction).filter(
                MCPServerAction.status.in_(["PENDING", "EVALUATE"])
            ).all()
            logger.info(f"Loaded {len(mcp_actions)} MCP actions with status=PENDING/EVALUATE")
        except Exception as e:
            logger.error(f"Failed to query mcp_server_actions: {e}")
            mcp_actions = []

        # Transform both to unified schema
        unified_actions = []

        # Transform agent actions
        for action in agent_actions:
            try:
                unified_actions.append(self._transform_agent_action(action))
            except Exception as e:
                logger.error(f"Failed to transform agent action {action.id}: {e}")

        # Transform MCP actions
        for mcp in mcp_actions:
            try:
                unified_actions.append(self._transform_mcp_action(mcp))
            except Exception as e:
                logger.error(f"Failed to transform MCP action {mcp.id}: {e}")

        # Sort by risk score DESC, then created_at ASC (oldest first within risk level)
        unified_actions.sort(
            key=lambda x: (-x.get("risk_score", 0), x.get("created_at", ""))
        )

        # Calculate counts
        high_risk_count = len([a for a in unified_actions if a.get("risk_score", 0) >= 70])

        logger.info(f"✅ Unified {len(unified_actions)} total actions (agent={len(agent_actions)}, MCP={len(mcp_actions)}, high_risk={high_risk_count})")

        return {
            "success": True,
            "pending_actions": unified_actions,
            "actions": unified_actions,  # Backward compatibility
            "total": len(unified_actions),
            "counts": {
                "total": len(unified_actions),
                "agent_actions": len(agent_actions),
                "mcp_actions": len(mcp_actions),
                "high_risk": high_risk_count
            }
        }

    def _transform_agent_action(self, action: AgentAction) -> Dict:
        """
        Transform AgentAction to common schema
        """
        # Calculate risk score with intelligent fallback
        risk_score = self._get_agent_risk_score(action)

        return {
            # Identification (prefixed to avoid conflicts)
            "id": f"agent-{action.id}",
            "numeric_id": action.id,  # Original ID for API calls
            "action_id": f"ENT_ACTION_{action.id:06d}",
            "action_source": "agent",
            "_original_type": "AgentAction",
            "_original_id": action.id,

            # Display fields
            "action_type": action.action_type,
            "description": action.description or f"{action.action_type} operation",
            "target_system": action.target_system or "Unknown",
            "agent_id": action.agent_id,

            # Risk assessment
            "risk_score": risk_score,
            "enterprise_risk_score": risk_score,
            "risk_level": action.risk_level or self._risk_score_to_level(risk_score),

            # Status (normalized to uppercase)
            "status": "PENDING_APPROVAL",
            "authorization_status": "pending_approval",
            "execution_status": "pending_approval",
            "requires_approval": action.requires_approval if action.requires_approval is not None else True,

            # Timestamps
            "created_at": action.timestamp.isoformat() if action.timestamp else action.created_at.isoformat(),
            "requested_at": action.timestamp.isoformat() if action.timestamp else action.created_at.isoformat(),
            "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None,

            # Approval details
            "approved_by": action.approved_by,
            "reviewed_by": action.reviewed_by,
            "created_by": action.created_by,
            "user_email": action.created_by or "Unknown",

            # Enterprise compliance
            "nist_control": action.nist_control or "AC-3",
            "nist_controls": [action.nist_control] if action.nist_control else ["AC-3"],
            "nist_description": action.nist_description or "",
            "mitre_tactic": action.mitre_tactic or "TA0009",
            "mitre_technique": action.mitre_technique or "T1078",
            "mitre_techniques": [action.mitre_technique] if action.mitre_technique else ["T1078"],
            "recommendation": action.recommendation or "",
            "compliance_frameworks": ["SOX", "PCI_DSS", "NIST"],

            # Workflow
            "workflow_stage": action.workflow_stage or "pending_stage_1",
            "current_approval_level": action.current_approval_level or 0,
            "required_approval_level": action.required_approval_level or (2 if risk_score >= 70 else 1),
            "approval_level": action.approval_level or 1,

            # Policy fusion (Option 4 fields)
            "policy_evaluated": getattr(action, 'policy_evaluated', False),
            "policy_decision": getattr(action, 'policy_decision', None),
            "policy_risk_score": getattr(action, 'policy_risk_score', None),
            "risk_fusion_formula": getattr(action, 'risk_fusion_formula', None),

            # Additional fields
            "tool_name": action.tool_name or "enterprise-mcp",
            "user_id": action.user_id or 1,
            "can_approve": True,
            "is_emergency": risk_score >= 90,
            "requires_executive_approval": risk_score >= 80,
            "time_remaining": "No deadline",
            "sla_status": "normal"
        }

    def _transform_mcp_action(self, mcp: MCPServerAction) -> Dict:
        """
        Transform MCPServerAction to common schema
        """
        # MCP risk_score is Integer 0-100, convert to Float
        risk_score = float(mcp.risk_score) if mcp.risk_score else 0.0

        return {
            # Identification (prefixed with UUID string)
            "id": f"mcp-{str(mcp.id)}",
            "uuid_id": str(mcp.id),  # Original UUID for API calls
            "action_id": f"MCP_ACTION_{str(mcp.id)[:8]}",
            "action_source": "mcp_server",
            "_original_type": "MCPServerAction",
            "_original_id": str(mcp.id),

            # Display fields
            "action_type": "mcp_server_action",
            "description": f"{mcp.verb} on {mcp.resource}",
            "target_system": mcp.mcp_server_name,
            "agent_id": f"mcp:{mcp.mcp_server_name}",

            # Risk assessment (MCP uses Integer 0-100)
            "risk_score": risk_score,
            "enterprise_risk_score": risk_score,
            "risk_level": mcp.risk_level or self._risk_score_to_level(risk_score),

            # Status (already uppercase)
            "status": mcp.status,
            "authorization_status": "pending_approval",
            "execution_status": "pending_approval",
            "requires_approval": mcp.requires_approval,

            # Timestamps
            "created_at": mcp.created_at.isoformat(),
            "requested_at": mcp.created_at.isoformat(),
            "reviewed_at": mcp.approved_at.isoformat() if mcp.approved_at else None,

            # Approval details
            "approved_by": mcp.approver_email,
            "reviewed_by": mcp.approver_id,
            "created_by": mcp.user_email,
            "user_email": mcp.user_email,

            # MCP-specific fields
            "namespace": mcp.namespace,
            "verb": mcp.verb,
            "resource": mcp.resource,
            "mcp_server_name": mcp.mcp_server_name,
            "mcp_server_id": str(mcp.mcp_server_id) if mcp.mcp_server_id else None,
            "user_id": mcp.user_id,
            "parameters": mcp.parameters if mcp.parameters else {},

            # MCP data structure (for compatibility with frontend)
            "mcp_data": {
                "server": mcp.mcp_server_name,
                "namespace": mcp.namespace,
                "verb": mcp.verb,
                "resource": mcp.resource,
                "params": mcp.parameters if mcp.parameters else {}
            },
            "is_mcp_action": True,

            # Enterprise compliance (map from MCP fields)
            "nist_control": "AC-3",  # Default for MCP actions
            "nist_controls": ["AC-3"],
            "nist_description": f"MCP server action requiring authorization",
            "mitre_tactic": "TA0009",
            "mitre_technique": "T1078",
            "mitre_techniques": ["T1078"],
            "recommendation": f"Review {mcp.verb} operation on {mcp.resource}",
            "compliance_frameworks": mcp.compliance_tags if mcp.compliance_tags else ["SOX", "PCI_DSS"],

            # Workflow
            "workflow_stage": "pending_stage_1",
            "current_approval_level": 0,
            "required_approval_level": mcp.approval_level or (2 if risk_score >= 70 else 1),
            "approval_level": mcp.approval_level or 1,

            # Additional fields
            "tool_name": "mcp-server",
            "can_approve": True,
            "is_emergency": risk_score >= 90,
            "requires_executive_approval": risk_score >= 80,
            "time_remaining": "No deadline",
            "sla_status": "normal",

            # Policy fields (MCP has different structure)
            "policy_evaluated": mcp.policy_result != 'EVALUATE',
            "policy_decision": mcp.policy_result,
            "policy_risk_score": None,
            "risk_fusion_formula": None
        }

    def _get_agent_risk_score(self, action: AgentAction) -> float:
        """
        Get risk score for agent action with intelligent fallback
        Priority: risk_score > cvss_score*10 > risk_level mapping
        """
        # First: Use stored risk_score if available
        if action.risk_score:
            return float(action.risk_score)

        # Second: Use CVSS score if available (0.0-10.0 → 0-100)
        if action.cvss_score:
            return float(action.cvss_score * 10)

        # Third: Intelligent fallback based on risk_level
        risk_level_scores = {
            "low": 30,
            "medium": 50,
            "high": 75,
            "critical": 95
        }
        risk_level = action.risk_level.lower() if action.risk_level else "medium"
        return float(risk_level_scores.get(risk_level, 50))

    def _risk_score_to_level(self, risk_score: float) -> str:
        """
        Convert risk score (0-100) to risk level string
        """
        if risk_score >= 90:
            return "critical"
        elif risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


# Singleton instance
enterprise_unified_loader = EnterpriseUnifiedLoader()
