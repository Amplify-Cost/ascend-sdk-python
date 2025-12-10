"""
SEC-103/104/105: Agent Control Service - Kill-Switch Infrastructure

Enterprise-grade agent control via SNS/SQS for real-time kill-switch capability.

Architecture:
    Admin Dashboard          Backend                    SNS Topic                    SQS Queues
    ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
    │ BLOCK Agent │───▶│ agent_control_   │───▶│ ascend-agent-       │───▶│ org-34 queue        │
    │ Button      │    │ service.py       │    │ control             │    │ (filter: org_id=34) │
    └─────────────┘    │                  │    │                     │    └─────────────────────┘
                       │ - Validate       │    │ - Fan out to        │           │
                       │ - Audit log      │    │   per-org queues    │           ▼
                       │ - Publish SNS    │    │                     │    ┌─────────────────────┐
                       └──────────────────┘    └─────────────────────┘    │ SDK Agent polls     │
                                                                          │ → Receives BLOCK    │
                                                                          │ → Stops operations  │
                                                                          └─────────────────────┘

Target Latency: < 500ms from button click to agent stop

Compliance:
- SOC 2 CC6.2: Logical access controls
- NIST IR-4: Incident handling
- HIPAA 164.308(a)(6): Security incident procedures

Authored-By: ASCEND Engineering Team
"""
import boto3
import json
import uuid
import logging
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Session

from models_agent_registry import AgentControlCommand, ControlCommandType

logger = logging.getLogger(__name__)

# AWS Configuration
SNS_TOPIC_ARN = "arn:aws:sns:us-east-2:110948415588:ascend-agent-control"
AWS_REGION = "us-east-2"


class AgentControlService:
    """
    Enterprise agent control service for real-time kill-switch commands.

    Usage:
        service = AgentControlService()
        result = service.send_block_command(
            db=db,
            organization_id=34,
            agent_id="boto3-agent-001",
            reason="Security incident detected",
            issued_by="admin@company.com"
        )
    """

    def __init__(self):
        """Initialize SNS client."""
        self.sns_client = boto3.client('sns', region_name=AWS_REGION)
        self.topic_arn = SNS_TOPIC_ARN

    def send_control_command(
        self,
        db: Session,
        organization_id: int,
        command_type: str,
        reason: str,
        issued_by: str,
        agent_id: Optional[str] = None,
        parameters: Optional[dict] = None,
        issued_via: str = "api",
        expires_at: Optional[datetime] = None
    ) -> dict:
        """
        Send a control command to agent(s) via SNS.

        Args:
            db: Database session
            organization_id: Target organization
            command_type: BLOCK, UNBLOCK, SUSPEND, RESUME, RATE_LIMIT, QUARANTINE
            reason: Human-readable reason for audit
            issued_by: Email of admin issuing command
            agent_id: Specific agent (None = broadcast to all org agents)
            parameters: Additional command parameters
            issued_via: Channel used (api, dashboard, automation)
            expires_at: Command expiration timestamp

        Returns:
            dict with command_id, status, and SNS message_id
        """
        # Generate unique command ID
        command_id = str(uuid.uuid4())

        # Validate command type
        valid_commands = [e.value for e in ControlCommandType]
        if command_type not in valid_commands:
            raise ValueError(f"Invalid command_type: {command_type}. Must be one of: {valid_commands}")

        # Create audit record FIRST (before SNS publish)
        control_command = AgentControlCommand(
            command_id=command_id,
            organization_id=organization_id,
            agent_id=agent_id,
            command_type=command_type,
            reason=reason,
            parameters=parameters or {},
            status="pending",
            issued_by=issued_by,
            issued_via=issued_via,
            expires_at=expires_at
        )
        db.add(control_command)
        db.flush()  # Get ID before SNS publish

        # Build SNS message
        message_payload = {
            "command_id": command_id,
            "organization_id": organization_id,
            "agent_id": agent_id,  # None = broadcast
            "command_type": command_type,
            "reason": reason,
            "parameters": parameters or {},
            "issued_by": issued_by,
            "issued_at": datetime.now(UTC).isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None
        }

        # Publish to SNS with organization filter attribute
        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(message_payload),
                MessageAttributes={
                    "organization_id": {
                        "DataType": "String",
                        "StringValue": str(organization_id)
                    },
                    "command_type": {
                        "DataType": "String",
                        "StringValue": command_type
                    }
                }
            )

            sns_message_id = response.get('MessageId')

            # Update audit record with SNS message ID
            control_command.sns_message_id = sns_message_id
            control_command.status = "delivered"
            control_command.delivered_at = datetime.now(UTC)
            db.commit()

            logger.info(
                f"SEC-103: Control command sent - "
                f"command_id={command_id}, type={command_type}, "
                f"org={organization_id}, agent={agent_id or 'ALL'}, "
                f"sns_message_id={sns_message_id}"
            )

            return {
                "success": True,
                "command_id": command_id,
                "status": "delivered",
                "sns_message_id": sns_message_id,
                "organization_id": organization_id,
                "agent_id": agent_id,
                "command_type": command_type,
                "message": f"Control command {command_type} sent successfully"
            }

        except Exception as e:
            # Update audit record with failure
            control_command.status = "failed"
            db.commit()

            logger.error(f"SEC-103: Failed to send control command: {e}")
            raise

    def send_block_command(
        self,
        db: Session,
        organization_id: int,
        reason: str,
        issued_by: str,
        agent_id: Optional[str] = None,
        issued_via: str = "api"
    ) -> dict:
        """
        Convenience method to send BLOCK (kill-switch) command.

        This is the primary kill-switch method for immediate agent shutdown.
        """
        return self.send_control_command(
            db=db,
            organization_id=organization_id,
            command_type=ControlCommandType.BLOCK.value,
            reason=reason,
            issued_by=issued_by,
            agent_id=agent_id,
            issued_via=issued_via
        )

    def send_unblock_command(
        self,
        db: Session,
        organization_id: int,
        reason: str,
        issued_by: str,
        agent_id: Optional[str] = None,
        issued_via: str = "api"
    ) -> dict:
        """
        Convenience method to send UNBLOCK command.

        Resumes agent operations after a BLOCK command.
        """
        return self.send_control_command(
            db=db,
            organization_id=organization_id,
            command_type=ControlCommandType.UNBLOCK.value,
            reason=reason,
            issued_by=issued_by,
            agent_id=agent_id,
            issued_via=issued_via
        )

    def acknowledge_command(
        self,
        db: Session,
        command_id: str,
        agent_id: str
    ) -> bool:
        """
        Record that an agent has acknowledged a control command.

        Called when SDK agent confirms receipt of command.
        """
        command = db.query(AgentControlCommand).filter(
            AgentControlCommand.command_id == command_id
        ).first()

        if not command:
            logger.warning(f"SEC-103: Acknowledge for unknown command: {command_id}")
            return False

        # Add agent to acknowledged list
        acknowledged = command.acknowledged_by_agents or []
        if agent_id not in acknowledged:
            acknowledged.append(agent_id)
            command.acknowledged_by_agents = acknowledged
            command.status = "acknowledged"
            command.acknowledged_at = datetime.now(UTC)
            db.commit()

            logger.info(f"SEC-103: Command {command_id} acknowledged by {agent_id}")

        return True

    def get_pending_commands(
        self,
        db: Session,
        organization_id: int,
        agent_id: Optional[str] = None
    ) -> list:
        """
        Get pending control commands for an organization/agent.

        Used for SDK polling fallback (if SQS delivery fails).
        """
        query = db.query(AgentControlCommand).filter(
            AgentControlCommand.organization_id == organization_id,
            AgentControlCommand.status.in_(["pending", "delivered"])
        )

        if agent_id:
            # Get commands for specific agent OR broadcast commands
            query = query.filter(
                (AgentControlCommand.agent_id == agent_id) |
                (AgentControlCommand.agent_id.is_(None))
            )

        return query.order_by(AgentControlCommand.created_at.desc()).limit(10).all()


# Singleton instance
agent_control_service = AgentControlService()
