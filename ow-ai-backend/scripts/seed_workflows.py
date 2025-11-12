"""
Seed Workflow Orchestrations
Creates default workflow orchestrations for enterprise deployment

This script is idempotent and safe to run multiple times.
Existing workflows with the same ID will be updated, not duplicated.

Author: OW-kai Engineer
Version: 1.0.0
"""
import sys
import os
from datetime import datetime, UTC

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Workflow
from core.logging import logger


def seed_workflows(db: Session) -> None:
    """
    Seed default workflow orchestrations

    Creates 3 enterprise-grade workflows:
    1. High Risk Approval Workflow - Multi-level approval for high-risk actions
    2. Critical Action Workflow - Emergency response for critical operations
    3. Data Access Workflow - Compliance-focused data access approval
    """

    workflows = [
        {
            "id": "high_risk_approval",
            "name": "High Risk Approval Workflow",
            "description": "Multi-level approval process for high-risk actions (risk score 50-79). Requires security team review and optional manager approval before execution.",
            "status": "active",
            "created_by": "system_admin",
            "owner": "security_team",
            "sla_hours": 8,
            "auto_approve_on_timeout": False,
            "execution_count": 0,
            "success_rate": 100.0,
            "compliance_frameworks": ["SOX", "PCI-DSS", "HIPAA"],
            "tags": ["high-risk", "multi-approval", "security-review"],
            "trigger_conditions": {
                "risk_score_min": 50,
                "risk_score_max": 79,
                "action_types": [
                    "database_write",
                    "file_delete",
                    "system_config_change",
                    "api_call_delete",
                    "user_permission_change"
                ]
            },
            "steps": [
                {
                    "step_number": 1,
                    "step_name": "Security Team Review",
                    "step_type": "approval",
                    "approvers": ["security_team"],
                    "timeout_hours": 4,
                    "escalation_on_timeout": True
                },
                {
                    "step_number": 2,
                    "step_name": "Manager Approval",
                    "step_type": "approval",
                    "approvers": ["manager"],
                    "timeout_hours": 2,
                    "escalation_on_timeout": True
                },
                {
                    "step_number": 3,
                    "step_name": "Execute Action",
                    "step_type": "execution",
                    "notify_on_complete": True,
                    "notify_channels": ["slack_security", "email_audit"]
                }
            ]
        },
        {
            "id": "critical_action_workflow",
            "name": "Critical Action Emergency Workflow",
            "description": "Emergency escalation workflow for critical risk actions (risk score ≥ 80). Immediate notification to security oncall team with expedited approval process.",
            "status": "active",
            "created_by": "system_admin",
            "owner": "security_team",
            "sla_hours": 4,
            "auto_approve_on_timeout": False,
            "execution_count": 0,
            "success_rate": 100.0,
            "compliance_frameworks": ["SOX", "PCI-DSS", "HIPAA", "GDPR"],
            "tags": ["critical-risk", "emergency", "executive-approval", "24x7"],
            "trigger_conditions": {
                "risk_score_min": 80,
                "action_types": [
                    "database_delete",
                    "system_shutdown",
                    "privilege_escalation",
                    "security_policy_change",
                    "production_deployment",
                    "data_export_pii"
                ]
            },
            "steps": [
                {
                    "step_number": 1,
                    "step_name": "Immediate Security Alert",
                    "step_type": "notification",
                    "notify_channels": ["pagerduty_security", "slack_security_oncall", "sms_security_lead"],
                    "priority": "critical"
                },
                {
                    "step_number": 2,
                    "step_name": "Security Lead Approval",
                    "step_type": "approval",
                    "approvers": ["security_lead"],
                    "require_2fa": True,
                    "timeout_hours": 1,
                    "escalation_on_timeout": True,
                    "escalation_target": "ciso"
                },
                {
                    "step_number": 3,
                    "step_name": "CISO Approval",
                    "step_type": "approval",
                    "approvers": ["ciso"],
                    "require_2fa": True,
                    "require_justification": True,
                    "timeout_hours": 2,
                    "escalation_on_timeout": True
                },
                {
                    "step_number": 4,
                    "step_name": "Execute with Audit Trail",
                    "step_type": "execution",
                    "create_incident_record": True,
                    "notify_on_complete": True,
                    "notify_channels": ["slack_security", "email_exec_team", "audit_log_system"]
                }
            ]
        },
        {
            "id": "data_access_workflow",
            "name": "Data Access Compliance Workflow",
            "description": "Compliance-focused workflow for sensitive data access requests. Ensures proper authorization and audit trail for PII, PHI, and financial data access.",
            "status": "active",
            "created_by": "system_admin",
            "owner": "compliance_team",
            "sla_hours": 48,
            "auto_approve_on_timeout": False,
            "execution_count": 0,
            "success_rate": 100.0,
            "compliance_frameworks": ["HIPAA", "GDPR", "PCI-DSS", "SOX"],
            "tags": ["data-access", "compliance", "audit-trail", "pii", "phi"],
            "trigger_conditions": {
                "risk_score_min": 40,
                "risk_score_max": 70,
                "action_types": [
                    "query_database_read",
                    "data_export",
                    "report_generation",
                    "api_call_get"
                ],
                "data_classification": ["pii", "phi", "financial", "confidential"]
            },
            "steps": [
                {
                    "step_number": 1,
                    "step_name": "Data Classification Check",
                    "step_type": "validation",
                    "validate_data_classification": True,
                    "require_business_justification": True
                },
                {
                    "step_number": 2,
                    "step_name": "Compliance Officer Review",
                    "step_type": "approval",
                    "approvers": ["compliance_officer"],
                    "timeout_hours": 24,
                    "escalation_on_timeout": True
                },
                {
                    "step_number": 3,
                    "step_name": "Data Owner Approval",
                    "step_type": "approval",
                    "approvers": ["data_owner"],
                    "timeout_hours": 12,
                    "escalation_on_timeout": True
                },
                {
                    "step_number": 4,
                    "step_name": "Grant Access with Monitoring",
                    "step_type": "execution",
                    "enable_access_monitoring": True,
                    "set_access_expiration": True,
                    "access_duration_hours": 168,  # 7 days
                    "notify_on_complete": True,
                    "notify_channels": ["slack_compliance", "email_audit"]
                }
            ]
        }
    ]

    logger.info("🌱 Starting workflow orchestration seeding...")

    created_count = 0
    updated_count = 0

    for workflow_data in workflows:
        try:
            # Check if workflow already exists
            existing = db.query(Workflow).filter(
                Workflow.id == workflow_data["id"]
            ).first()

            if existing:
                # Update existing workflow
                for key, value in workflow_data.items():
                    if key not in ["created_at", "created_by"]:  # Don't update creation metadata
                        setattr(existing, key, value)
                existing.updated_at = datetime.now(UTC)
                logger.info(f"✏️  Updated workflow: {workflow_data['id']}")
                updated_count += 1
            else:
                # Create new workflow
                workflow = Workflow(**workflow_data)
                db.add(workflow)
                logger.info(f"✅ Created workflow: {workflow_data['id']}")
                created_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to seed workflow {workflow_data['id']}: {e}")
            db.rollback()
            raise

    # Commit all changes
    try:
        db.commit()
        logger.info(f"""
╔══════════════════════════════════════════╗
║  Workflow Orchestration Seeding Complete ║
╠══════════════════════════════════════════╣
║  Created: {created_count:2d} workflows                    ║
║  Updated: {updated_count:2d} workflows                    ║
║  Total:   {created_count + updated_count:2d} workflows                    ║
╚══════════════════════════════════════════╝
        """)
    except Exception as e:
        logger.error(f"❌ Failed to commit workflows: {e}")
        db.rollback()
        raise


def verify_workflows(db: Session) -> None:
    """
    Verify that workflows were created successfully
    """
    workflows = db.query(Workflow).all()

    logger.info(f"\n📊 Verification: Found {len(workflows)} workflow orchestrations in database")

    for workflow in workflows:
        logger.info(f"""
  → {workflow.id}
    Name: {workflow.name}
    Status: {workflow.status}
    Owner: {workflow.owner}
    Created By: {workflow.created_by}
    Trigger Conditions: {workflow.trigger_conditions}
    Steps: {len(workflow.steps or [])} steps
    SLA: {workflow.sla_hours} hours
    Compliance: {workflow.compliance_frameworks}
    Tags: {workflow.tags}
    Executions: {workflow.execution_count}
    Success Rate: {workflow.success_rate}%
        """)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("WORKFLOW ORCHESTRATION SEED SCRIPT")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Seed workflows
        seed_workflows(db)

        # Verify creation
        verify_workflows(db)

        logger.info("\n✅ Workflow orchestration seeding completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {e}")
        logger.info("=" * 60)
        sys.exit(1)

    finally:
        db.close()
