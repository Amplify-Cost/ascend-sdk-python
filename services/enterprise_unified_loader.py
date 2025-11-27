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

    def load_all_pending_actions(self, db: Session, org_id: int = None) -> Dict:
        """
        Load ALL pending actions from both tables
        Returns unified, sorted list with common schema

        SEC-023: Now filters by organization_id for multi-tenant isolation

        Args:
            db: Database session
            org_id: Organization ID for multi-tenant filtering (required for data isolation)

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

        # Query 1: Agent Actions (ENTERPRISE: Handle NULL status + multiple status fields)
        try:
            from sqlalchemy import or_, and_

            # 🏢 ENTERPRISE FIX: Query using status field for pending actions
            # Handles: status='pending_stage_1/2/3', status='pending', status='pending_approval', workflow-based approvals
            query = db.query(AgentAction).filter(
                or_(
                    # Workflow stage statuses (pending_stage_1, pending_stage_2, pending_stage_3)
                    AgentAction.status.like("pending%"),
                    # Standard status values
                    AgentAction.status.in_(["submitted", "active"]),
                    # NULL status with pending workflow
                    and_(
                        AgentAction.status.is_(None),
                        AgentAction.workflow_stage.like("pending%")
                    )
                )
            )

            # SEC-023: Filter by organization_id for multi-tenant isolation
            if org_id is not None:
                query = query.filter(AgentAction.organization_id == org_id)
                logger.info(f"🏢 SEC-023: Filtering agent actions by org_id={org_id}")

            agent_actions = query.all()
            logger.info(f"✅ ENTERPRISE: Loaded {len(agent_actions)} agent actions (org_id={org_id})")
        except Exception as e:
            logger.error(f"Failed to query agent_actions: {e}")
            agent_actions = []

        # Query 2: MCP Server Actions (status = 'pending'/'PENDING' or 'evaluate'/'EVALUATE')
        # 🏢 ENTERPRISE FIX: Handle both uppercase and lowercase status values
        try:
            mcp_query = db.query(MCPServerAction).filter(
                MCPServerAction.status.in_(["PENDING", "EVALUATE", "pending", "evaluate"])
            )

            # SEC-023: Filter by organization_id for multi-tenant isolation
            if org_id is not None:
                mcp_query = mcp_query.filter(MCPServerAction.organization_id == org_id)
                logger.info(f"🏢 SEC-023: Filtering MCP actions by org_id={org_id}")

            mcp_actions = mcp_query.all()
            logger.info(f"Loaded {len(mcp_actions)} MCP actions (org_id={org_id})")
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
            "created_by": getattr(action, 'created_by', None),  # 🏢 ENTERPRISE FIX: Field doesn't exist on AgentAction
            "user_email": getattr(action, 'created_by', None) or "Unknown",

            # 🏢 ENTERPRISE PHASE 2: Action-specific NIST/MITRE controls
            **self._get_nist_mitre_controls(action),
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
        🏢 ENTERPRISE: Transform MCPServerAction to common schema with Policy Fusion support

        NOW SUPPORTS: Option 4 policy fusion fields (policy_evaluated, policy_decision, policy_risk_score)
        """
        # MCP risk_score is Float 0-100 (now standardized to match agent_actions)
        risk_score = float(mcp.risk_score) if mcp.risk_score else 0.0

        # Extract MCP server name and namespace from fields (after migration they exist)
        mcp_server_name = mcp.agent_id or "unknown"  # Server ID stored in agent_id column
        namespace = mcp.namespace or "mcp"
        verb = mcp.verb or mcp.action_type or "unknown"
        resource = mcp.resource or "unknown"

        return {
            # Identification (prefixed with integer ID)
            "id": f"mcp-{mcp.id}",
            "numeric_id": mcp.id,  # Original integer ID for API calls
            "action_id": f"MCP_ACTION_{mcp.id}",
            "action_source": "mcp_server",
            "_original_type": "MCPServerAction",
            "_original_id": mcp.id,

            # Display fields
            "action_type": "mcp_server_action",  # 🏢 FIX (2025-11-18): Frontend expects this exact value
            "verb": verb,  # Store actual verb separately
            "description": f"{verb} on {resource}" if verb and resource else "MCP server action",
            "target_system": mcp_server_name,
            "agent_id": f"mcp:{mcp_server_name}",

            # Risk assessment (standardized to Float 0-100)
            "risk_score": risk_score,
            "enterprise_risk_score": risk_score,
            "risk_level": mcp.risk_level or self._risk_score_to_level(risk_score),
            "ai_risk_score": risk_score,  # Compatibility field

            # 🏢 OPTION 4 POLICY FUSION FIELDS (NEW!)
            "policy_evaluated": mcp.policy_evaluated or False,
            "policy_decision": mcp.policy_decision,
            "policy_risk_score": mcp.policy_risk_score,
            "risk_fusion_formula": mcp.risk_fusion_formula,

            # Status (normalize to lowercase for consistency)
            "status": self._normalize_mcp_status(mcp.status),
            "authorization_status": "pending_approval" if mcp.status == "pending" else mcp.status,
            "execution_status": "pending_approval" if mcp.status == "pending" else mcp.status,
            "requires_approval": True,  # MCP actions always require approval

            # Timestamps
            "created_at": mcp.created_at.isoformat() if mcp.created_at else datetime.now(UTC).isoformat(),
            "requested_at": mcp.created_at.isoformat() if mcp.created_at else datetime.now(UTC).isoformat(),
            "reviewed_at": mcp.reviewed_at.isoformat() if mcp.reviewed_at else None,
            "approved_at": mcp.approved_at.isoformat() if mcp.approved_at else None,

            # Approval details (now using migration-added fields)
            "approved_by": mcp.approved_by,
            "reviewed_by": mcp.reviewed_by,
            "created_by": mcp.created_by or mcp.user_email or "system",
            "user_email": mcp.user_email or "unknown",

            # MCP-specific fields
            "namespace": namespace,
            "verb": verb,
            "resource": resource,
            "mcp_server_name": mcp_server_name,
            "mcp_server_id": mcp.agent_id,  # Server ID stored in agent_id column
            "parameters": mcp.context or {},  # Parameters stored in context JSONB

            # MCP data structure (for compatibility with frontend)
            "mcp_data": {
                "server": mcp_server_name,
                "namespace": namespace,
                "verb": verb,
                "resource": resource,
                "params": mcp.context or {}
            },
            "is_mcp_action": True,
            "is_agent_action": False,

            # Enterprise compliance (map from MCP fields or defaults)
            "nist_control": "AC-3",  # Default for MCP actions (Access Control)
            "nist_controls": ["AC-3"],
            "nist_description": f"MCP server action requiring authorization",
            "mitre_tactic": "TA0009",  # Collection
            "mitre_technique": "T1078",  # Valid Accounts
            "mitre_techniques": ["T1078"],
            "recommendation": f"Review {verb} operation on {resource}",
            "compliance_frameworks": ["SOX", "PCI_DSS"],  # Default compliance

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

    def _get_nist_mitre_controls(self, action: AgentAction) -> Dict:
        """
        🏢 ENTERPRISE PHASE 2: Map action_type to specific NIST/MITRE controls
        Returns action-specific controls instead of generic defaults

        Based on NIST SP 800-53 Rev. 5 and MITRE ATT&CK Framework
        """

        # If action already has controls, use them
        if action.nist_control and action.mitre_tactic:
            return {
                "nist_control": action.nist_control,
                "nist_controls": [action.nist_control],
                "nist_description": action.nist_description or "",
                "mitre_tactic": action.mitre_tactic,
                "mitre_technique": action.mitre_technique or "T1078",
                "mitre_techniques": [action.mitre_technique] if action.mitre_technique else ["T1078"]
            }

        # 🏢 Action-type specific mappings (NIST SP 800-53 + MITRE ATT&CK)
        action_type_mappings = {
            "file_write": {
                "nist_control": "AC-3",
                "nist_description": "Access Enforcement - File System Write Operations",
                "mitre_tactic": "TA0005",  # Defense Evasion
                "mitre_technique": "T1070"  # Indicator Removal on Host
            },
            "file_read": {
                "nist_control": "AC-4",
                "nist_description": "Information Flow Enforcement - Data Access",
                "mitre_tactic": "TA0009",  # Collection
                "mitre_technique": "T1005"  # Data from Local System
            },
            "file_delete": {
                "nist_control": "AC-3",
                "nist_description": "Access Enforcement - File Deletion",
                "mitre_tactic": "TA0005",  # Defense Evasion
                "mitre_technique": "T1485"  # Data Destruction
            },
            "api_call": {
                "nist_control": "AC-6",
                "nist_description": "Least Privilege - API Access Control",
                "mitre_tactic": "TA0002",  # Execution
                "mitre_technique": "T1106"  # Native API
            },
            "database_query": {
                "nist_control": "AC-3",
                "nist_description": "Access Enforcement - Database Read",
                "mitre_tactic": "TA0009",  # Collection
                "mitre_technique": "T1005"  # Data from Information Repositories
            },
            "database_execute": {
                "nist_control": "AC-6",
                "nist_description": "Least Privilege - Database Execution",
                "mitre_tactic": "TA0002",  # Execution
                "mitre_technique": "T1505"  # Server Software Component
            },
            "database_delete": {
                "nist_control": "AC-3",
                "nist_description": "Access Enforcement - Data Deletion",
                "mitre_tactic": "TA0040",  # Impact
                "mitre_technique": "T1485"  # Data Destruction
            },
            "system_command": {
                "nist_control": "CM-7",
                "nist_description": "Least Functionality - Command Execution",
                "mitre_tactic": "TA0002",  # Execution
                "mitre_technique": "T1059"  # Command and Scripting Interpreter
            },
            "external_api": {
                "nist_control": "AC-20",
                "nist_description": "Use of External Systems",
                "mitre_tactic": "TA0011",  # Command and Control
                "mitre_technique": "T1071"  # Application Layer Protocol
            },
            "network_access": {
                "nist_control": "AC-4",
                "nist_description": "Information Flow Enforcement - Network",
                "mitre_tactic": "TA0011",  # Command and Control
                "mitre_technique": "T1095"  # Non-Application Layer Protocol
            }
        }

        # Get mapping for action type, or use defaults
        mapping = action_type_mappings.get(
            action.action_type,
            {
                "nist_control": "AC-2",
                "nist_description": "Account Management - General Action Authorization",
                "mitre_tactic": "TA0001",  # Initial Access
                "mitre_technique": "T1078"  # Valid Accounts
            }
        )

        return {
            "nist_control": mapping["nist_control"],
            "nist_controls": [mapping["nist_control"]],
            "nist_description": mapping["nist_description"],
            "mitre_tactic": mapping["mitre_tactic"],
            "mitre_technique": mapping["mitre_technique"],
            "mitre_techniques": [mapping["mitre_technique"]]
        }

    def _normalize_mcp_status(self, status: str) -> str:
        """
        🏢 ENTERPRISE: Normalize MCP status to lowercase for consistency

        MCP actions use uppercase status (PENDING, APPROVED, etc.)
        Agent actions use lowercase (pending_approval, approved, etc.)
        This normalizes for consistent frontend display
        """
        if not status:
            return "pending_approval"

        status_upper = status.upper()

        # Map MCP statuses to agent-compatible statuses
        status_map = {
            "PENDING": "pending_approval",
            "EVALUATE": "pending_approval",
            "APPROVED": "approved",
            "DENIED": "denied",
            "EXECUTED": "executed",
            "FAILED": "failed"
        }

        return status_map.get(status_upper, status.lower())


# Singleton instance
enterprise_unified_loader = EnterpriseUnifiedLoader()
