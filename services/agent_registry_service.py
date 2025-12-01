"""
OW-AI Enterprise Agent Registry Service
=======================================

Enterprise-grade service for managing AI agent registrations.
Handles CRUD operations, versioning, policy management, and audit logging.

Features:
- Full CRUD with multi-tenant isolation
- Version control with rollback
- Policy evaluation and enforcement
- MCP server discovery and governance
- Comprehensive audit logging

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, UTC
import logging
import json
import re
import secrets
import hashlib

from models_agent_registry import (
    RegisteredAgent, AgentVersion, AgentPolicy, AgentActivityLog,
    MCPServerConfig, AgentType, AgentStatus
)

logger = logging.getLogger(__name__)


class AgentRegistryService:
    """
    Enterprise Agent Registry Service

    Provides comprehensive agent management with:
    - Multi-tenant data isolation
    - Version control and rollback
    - Policy configuration
    - Audit trail compliance
    """

    # =========================================================================
    # AGENT REGISTRATION
    # =========================================================================

    @staticmethod
    def register_agent(
        db: Session,
        organization_id: int,
        agent_data: Dict[str, Any],
        created_by: str
    ) -> Tuple[RegisteredAgent, bool]:
        """
        Register a new AI agent with the governance platform.

        Args:
            db: Database session
            organization_id: Tenant isolation
            agent_data: Agent configuration
            created_by: User performing registration

        Returns:
            Tuple of (RegisteredAgent, created_new)

        Compliance: SOC 2 CC6.1, NIST AC-2
        """
        try:
            # Validate agent_id format (alphanumeric with dashes)
            agent_id = agent_data.get("agent_id", "")
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_]{2,63}$', agent_id):
                raise ValueError(
                    "agent_id must be 3-64 characters, alphanumeric with dashes/underscores, "
                    "starting with alphanumeric"
                )

            # Check for existing agent (idempotency)
            existing = db.query(RegisteredAgent).filter(
                and_(
                    RegisteredAgent.agent_id == agent_id,
                    RegisteredAgent.organization_id == organization_id
                )
            ).first()

            if existing:
                logger.info(f"Agent already registered: {agent_id} (org: {organization_id})")
                return existing, False

            # Validate agent type
            agent_type = agent_data.get("agent_type", AgentType.SUPERVISED.value)
            if agent_type not in [t.value for t in AgentType]:
                agent_type = AgentType.SUPERVISED.value

            # Create new agent registration
            agent = RegisteredAgent(
                agent_id=agent_id,
                display_name=agent_data.get("display_name", agent_id),
                description=agent_data.get("description"),
                agent_type=agent_type,
                status=AgentStatus.DRAFT.value,
                version="1.0.0",
                version_notes=agent_data.get("version_notes", "Initial registration"),
                organization_id=organization_id,

                # Risk Configuration
                default_risk_score=agent_data.get("default_risk_score", 50),
                max_risk_threshold=agent_data.get("max_risk_threshold", 80),
                auto_approve_below=agent_data.get("auto_approve_below", 30),
                requires_mfa_above=agent_data.get("requires_mfa_above", 70),

                # Capabilities
                allowed_action_types=agent_data.get("allowed_action_types", []),
                allowed_resources=agent_data.get("allowed_resources", []),
                blocked_resources=agent_data.get("blocked_resources", []),

                # MCP Integration
                is_mcp_server=agent_data.get("is_mcp_server", False),
                mcp_server_url=agent_data.get("mcp_server_url"),
                mcp_capabilities=agent_data.get("mcp_capabilities", {}),

                # Notifications
                alert_on_high_risk=agent_data.get("alert_on_high_risk", True),
                alert_recipients=agent_data.get("alert_recipients", []),
                webhook_url=agent_data.get("webhook_url"),

                # Audit
                created_at=datetime.now(UTC),
                created_by=created_by,
                updated_at=datetime.now(UTC),
                updated_by=created_by,

                # Metadata
                tags=agent_data.get("tags", []),
                metadata=agent_data.get("metadata", {})
            )

            db.add(agent)
            db.flush()

            # Create initial version record
            version = AgentVersion(
                agent_id=agent.id,
                version="1.0.0",
                version_notes="Initial registration",
                is_active=True,
                config_snapshot=AgentRegistryService._create_config_snapshot(agent),
                created_at=datetime.now(UTC),
                created_by=created_by
            )
            db.add(version)

            # Log activity
            activity = AgentActivityLog(
                agent_id=agent.id,
                organization_id=organization_id,
                activity_type="registered",
                activity_description=f"Agent '{agent_id}' registered with type '{agent_type}'",
                performed_by=created_by,
                performed_via="api",
                previous_state=None,
                new_state=AgentRegistryService._create_config_snapshot(agent),
                timestamp=datetime.now(UTC)
            )
            db.add(activity)

            db.commit()
            db.refresh(agent)

            logger.info(f"Agent registered: {agent_id} (id: {agent.id}, org: {organization_id})")
            return agent, True

        except ValueError as e:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Agent registration failed: {e}")
            raise

    @staticmethod
    def get_agent(
        db: Session,
        organization_id: int,
        agent_id: str = None,
        internal_id: int = None
    ) -> Optional[RegisteredAgent]:
        """
        Get agent by agent_id or internal ID with tenant isolation.

        Compliance: Multi-tenant isolation enforced
        """
        query = db.query(RegisteredAgent).filter(
            RegisteredAgent.organization_id == organization_id
        )

        if internal_id:
            query = query.filter(RegisteredAgent.id == internal_id)
        elif agent_id:
            query = query.filter(RegisteredAgent.agent_id == agent_id)
        else:
            return None

        return query.first()

    @staticmethod
    def list_agents(
        db: Session,
        organization_id: int,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[RegisteredAgent], int]:
        """
        List all agents for an organization with filtering.

        Returns:
            Tuple of (agents, total_count)

        Compliance: Multi-tenant isolation enforced
        """
        query = db.query(RegisteredAgent).filter(
            RegisteredAgent.organization_id == organization_id
        )

        if status_filter:
            query = query.filter(RegisteredAgent.status == status_filter)

        if type_filter:
            query = query.filter(RegisteredAgent.agent_type == type_filter)

        total = query.count()

        agents = query.order_by(
            RegisteredAgent.created_at.desc()
        ).offset(offset).limit(limit).all()

        return agents, total

    @staticmethod
    def update_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        updates: Dict[str, Any],
        updated_by: str,
        create_version: bool = True
    ) -> Optional[RegisteredAgent]:
        """
        Update agent configuration with version control.

        Args:
            db: Database session
            organization_id: Tenant isolation
            agent_id: Agent identifier
            updates: Fields to update
            updated_by: User performing update
            create_version: Whether to create a new version

        Compliance: SOC 2 CC8.1 (change management)
        """
        try:
            agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
            if not agent:
                return None

            # Capture previous state
            previous_state = AgentRegistryService._create_config_snapshot(agent)

            # Fields that trigger version bump
            version_trigger_fields = {
                "allowed_action_types", "allowed_resources", "blocked_resources",
                "auto_approve_below", "max_risk_threshold", "requires_mfa_above",
                "mcp_capabilities", "agent_type"
            }

            should_bump_version = any(
                field in updates for field in version_trigger_fields
            ) and create_version

            # Apply updates
            allowed_fields = {
                "display_name", "description", "agent_type", "default_risk_score",
                "max_risk_threshold", "auto_approve_below", "requires_mfa_above",
                "allowed_action_types", "allowed_resources", "blocked_resources",
                "is_mcp_server", "mcp_server_url", "mcp_capabilities",
                "alert_on_high_risk", "alert_recipients", "webhook_url",
                "tags", "metadata", "version_notes"
            }

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(agent, field, value)

            agent.updated_at = datetime.now(UTC)
            agent.updated_by = updated_by

            # Version management
            if should_bump_version:
                new_version = AgentRegistryService._increment_version(agent.version)
                agent.version = new_version
                agent.version_notes = updates.get("version_notes", f"Updated: {', '.join(updates.keys())}")

                # Mark old versions as inactive
                db.query(AgentVersion).filter(
                    AgentVersion.agent_id == agent.id
                ).update({"is_active": False})

                # Create new version record
                version = AgentVersion(
                    agent_id=agent.id,
                    version=new_version,
                    version_notes=agent.version_notes,
                    is_active=True,
                    config_snapshot=AgentRegistryService._create_config_snapshot(agent),
                    created_at=datetime.now(UTC),
                    created_by=updated_by
                )
                db.add(version)

            # Log activity
            new_state = AgentRegistryService._create_config_snapshot(agent)
            activity = AgentActivityLog(
                agent_id=agent.id,
                organization_id=organization_id,
                activity_type="updated",
                activity_description=f"Agent '{agent_id}' updated: {', '.join(updates.keys())}",
                performed_by=updated_by,
                performed_via="api",
                previous_state=previous_state,
                new_state=new_state,
                timestamp=datetime.now(UTC)
            )
            db.add(activity)

            db.commit()
            db.refresh(agent)

            logger.info(f"Agent updated: {agent_id} (version: {agent.version})")
            return agent

        except Exception as e:
            db.rollback()
            logger.error(f"Agent update failed: {e}")
            raise

    @staticmethod
    def activate_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        approved_by: str
    ) -> Optional[RegisteredAgent]:
        """
        Activate an agent for production use.

        Requires admin approval for compliance.

        Compliance: SOC 2 CC6.2 (access authorization)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        if agent.status not in [AgentStatus.DRAFT.value, AgentStatus.PENDING_APPROVAL.value, AgentStatus.SUSPENDED.value]:
            raise ValueError(f"Cannot activate agent in status: {agent.status}")

        previous_status = agent.status
        agent.status = AgentStatus.ACTIVE.value
        agent.approved_at = datetime.now(UTC)
        agent.approved_by = approved_by
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = approved_by

        # Log activation
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="activated",
            activity_description=f"Agent '{agent_id}' activated (previous: {previous_status})",
            performed_by=approved_by,
            performed_via="api",
            previous_state={"status": previous_status},
            new_state={"status": AgentStatus.ACTIVE.value},
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.info(f"Agent activated: {agent_id} by {approved_by}")
        return agent

    @staticmethod
    def suspend_agent(
        db: Session,
        organization_id: int,
        agent_id: str,
        suspended_by: str,
        reason: str = None
    ) -> Optional[RegisteredAgent]:
        """
        Suspend an agent (emergency disable).

        Used for security incidents or policy violations.

        Compliance: SOC 2 CC6.2, NIST AC-2(3)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        previous_status = agent.status
        agent.status = AgentStatus.SUSPENDED.value
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = suspended_by

        # Log suspension with reason
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="suspended",
            activity_description=f"Agent '{agent_id}' suspended. Reason: {reason or 'Not specified'}",
            performed_by=suspended_by,
            performed_via="api",
            previous_state={"status": previous_status},
            new_state={"status": AgentStatus.SUSPENDED.value, "reason": reason},
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.warning(f"Agent SUSPENDED: {agent_id} by {suspended_by} - Reason: {reason}")
        return agent

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    @staticmethod
    def list_versions(
        db: Session,
        organization_id: int,
        agent_id: str
    ) -> List[AgentVersion]:
        """List all versions of an agent."""
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return []

        return db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent.id
        ).order_by(AgentVersion.created_at.desc()).all()

    @staticmethod
    def rollback_to_version(
        db: Session,
        organization_id: int,
        agent_id: str,
        target_version: str,
        performed_by: str
    ) -> Optional[RegisteredAgent]:
        """
        Rollback agent to a previous version.

        Compliance: SOC 2 CC8.1 (rollback capability)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return None

        # Find target version
        version_record = db.query(AgentVersion).filter(
            and_(
                AgentVersion.agent_id == agent.id,
                AgentVersion.version == target_version
            )
        ).first()

        if not version_record:
            raise ValueError(f"Version {target_version} not found")

        # Restore configuration from snapshot
        snapshot = version_record.config_snapshot
        previous_state = AgentRegistryService._create_config_snapshot(agent)

        # Apply rollback
        for field, value in snapshot.items():
            if hasattr(agent, field) and field not in ['id', 'organization_id', 'created_at', 'created_by']:
                setattr(agent, field, value)

        agent.version = target_version
        agent.version_notes = f"Rollback from {previous_state.get('version')} to {target_version}"
        agent.updated_at = datetime.now(UTC)
        agent.updated_by = performed_by

        # Mark target version as active
        db.query(AgentVersion).filter(AgentVersion.agent_id == agent.id).update({"is_active": False})
        version_record.is_active = True

        # Log rollback
        activity = AgentActivityLog(
            agent_id=agent.id,
            organization_id=organization_id,
            activity_type="rollback",
            activity_description=f"Agent '{agent_id}' rolled back to version {target_version}",
            performed_by=performed_by,
            performed_via="api",
            previous_state=previous_state,
            new_state=snapshot,
            timestamp=datetime.now(UTC)
        )
        db.add(activity)

        db.commit()
        db.refresh(agent)

        logger.info(f"Agent rollback: {agent_id} -> {target_version} by {performed_by}")
        return agent

    # =========================================================================
    # POLICY MANAGEMENT
    # =========================================================================

    @staticmethod
    def add_policy(
        db: Session,
        organization_id: int,
        agent_id: str,
        policy_data: Dict[str, Any],
        created_by: str
    ) -> AgentPolicy:
        """
        Add a policy to an agent.

        Compliance: NIST AC-3 (access enforcement)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        policy = AgentPolicy(
            agent_id=agent.id,
            organization_id=organization_id,
            policy_name=policy_data.get("policy_name", "Unnamed Policy"),
            policy_description=policy_data.get("policy_description"),
            is_active=policy_data.get("is_active", True),
            priority=policy_data.get("priority", 100),
            conditions=policy_data.get("conditions", {}),
            policy_action=policy_data.get("policy_action", "require_approval"),
            action_params=policy_data.get("action_params", {}),
            created_at=datetime.now(UTC),
            created_by=created_by
        )

        db.add(policy)
        db.commit()
        db.refresh(policy)

        logger.info(f"Policy added to agent {agent_id}: {policy.policy_name}")
        return policy

    @staticmethod
    def evaluate_policies(
        db: Session,
        organization_id: int,
        agent_id: str,
        action_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate all policies for an agent against an action context.

        Returns:
            Policy evaluation result with decision and matching policies

        Compliance: NIST AC-3 (access enforcement)
        """
        agent = AgentRegistryService.get_agent(db, organization_id, agent_id=agent_id)
        if not agent:
            return {"decision": "deny", "reason": "Agent not registered", "policies": []}

        # Check agent status
        if agent.status != AgentStatus.ACTIVE.value:
            return {
                "decision": "deny",
                "reason": f"Agent not active (status: {agent.status})",
                "policies": []
            }

        # Get active policies ordered by priority
        policies = db.query(AgentPolicy).filter(
            and_(
                AgentPolicy.agent_id == agent.id,
                AgentPolicy.is_active == True
            )
        ).order_by(AgentPolicy.priority).all()

        matched_policies = []
        final_decision = "allow"  # Default allow if no policies match

        for policy in policies:
            if AgentRegistryService._policy_matches(policy.conditions, action_context):
                matched_policies.append({
                    "policy_id": policy.id,
                    "policy_name": policy.policy_name,
                    "action": policy.policy_action,
                    "params": policy.action_params
                })

                # First matching policy determines decision (sorted by priority)
                if final_decision == "allow":
                    final_decision = policy.policy_action

        # Apply agent-level risk thresholds
        risk_score = action_context.get("risk_score", agent.default_risk_score)

        if risk_score < agent.auto_approve_below:
            return {
                "decision": "auto_approve",
                "reason": f"Risk score {risk_score} below auto-approve threshold {agent.auto_approve_below}",
                "policies": matched_policies,
                "risk_score": risk_score
            }

        if risk_score > agent.max_risk_threshold:
            return {
                "decision": "escalate",
                "reason": f"Risk score {risk_score} exceeds max threshold {agent.max_risk_threshold}",
                "policies": matched_policies,
                "risk_score": risk_score
            }

        return {
            "decision": final_decision,
            "reason": f"Policy evaluation complete. {len(matched_policies)} policies matched.",
            "policies": matched_policies,
            "risk_score": risk_score,
            "requires_mfa": risk_score >= agent.requires_mfa_above
        }

    # =========================================================================
    # MCP SERVER MANAGEMENT
    # =========================================================================

    @staticmethod
    def register_mcp_server(
        db: Session,
        organization_id: int,
        server_data: Dict[str, Any],
        created_by: str
    ) -> MCPServerConfig:
        """
        Register an MCP server for governance.

        Compliance: SOC 2 CC6.1
        """
        server = MCPServerConfig(
            server_name=server_data.get("server_name"),
            display_name=server_data.get("display_name", server_data.get("server_name")),
            description=server_data.get("description"),
            server_url=server_data.get("server_url"),
            transport_type=server_data.get("transport_type", "stdio"),
            connection_config=server_data.get("connection_config", {}),
            organization_id=organization_id,
            discovered_tools=server_data.get("tools", []),
            discovered_prompts=server_data.get("prompts", []),
            discovered_resources=server_data.get("resources", []),
            governance_enabled=server_data.get("governance_enabled", True),
            auto_approve_tools=server_data.get("auto_approve_tools", []),
            blocked_tools=server_data.get("blocked_tools", []),
            tool_risk_overrides=server_data.get("tool_risk_overrides", {}),
            is_active=True,
            health_status="unknown",
            created_at=datetime.now(UTC),
            created_by=created_by
        )

        db.add(server)
        db.commit()
        db.refresh(server)

        logger.info(f"MCP Server registered: {server.server_name} (org: {organization_id})")
        return server

    @staticmethod
    def list_mcp_servers(
        db: Session,
        organization_id: int
    ) -> List[MCPServerConfig]:
        """List all MCP servers for an organization."""
        return db.query(MCPServerConfig).filter(
            MCPServerConfig.organization_id == organization_id
        ).all()

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def _create_config_snapshot(agent: RegisteredAgent) -> Dict[str, Any]:
        """Create a JSON-serializable snapshot of agent configuration."""
        return {
            "agent_id": agent.agent_id,
            "display_name": agent.display_name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "version": agent.version,
            "default_risk_score": agent.default_risk_score,
            "max_risk_threshold": agent.max_risk_threshold,
            "auto_approve_below": agent.auto_approve_below,
            "requires_mfa_above": agent.requires_mfa_above,
            "allowed_action_types": agent.allowed_action_types,
            "allowed_resources": agent.allowed_resources,
            "blocked_resources": agent.blocked_resources,
            "is_mcp_server": agent.is_mcp_server,
            "mcp_server_url": agent.mcp_server_url,
            "mcp_capabilities": agent.mcp_capabilities,
            "alert_on_high_risk": agent.alert_on_high_risk,
            "tags": agent.tags,
            "metadata": agent.metadata
        }

    @staticmethod
    def _increment_version(current_version: str) -> str:
        """Increment semantic version (patch level)."""
        try:
            parts = current_version.split(".")
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                return ".".join(parts)
        except:
            pass
        return f"{current_version}.1"

    @staticmethod
    def _policy_matches(conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if policy conditions match the action context."""
        if not conditions:
            return True  # Empty conditions = always match

        for key, value in conditions.items():
            context_value = context.get(key)

            if key.endswith("_above"):
                actual_key = key.replace("_above", "")
                if context.get(actual_key, 0) <= value:
                    return False
            elif key.endswith("_below"):
                actual_key = key.replace("_below", "")
                if context.get(actual_key, 0) >= value:
                    return False
            elif key.endswith("_in"):
                actual_key = key.replace("_in", "")
                if context.get(actual_key) not in value:
                    return False
            elif key.endswith("_not_in"):
                actual_key = key.replace("_not_in", "")
                if context.get(actual_key) in value:
                    return False
            elif isinstance(value, list):
                if context_value not in value:
                    return False
            elif context_value != value:
                return False

        return True


# Global service instance
agent_registry_service = AgentRegistryService()
