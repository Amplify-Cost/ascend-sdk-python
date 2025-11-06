"""
Seed Automation Playbooks
Creates default automation playbooks for enterprise deployment

This script is idempotent and safe to run multiple times.
Existing playbooks with the same ID will be updated, not duplicated.

Author: OW-kai Engineer
Version: 1.0.0
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import AutomationPlaybook
from core.logging import logger


def seed_playbooks(db: Session) -> None:
    """
    Seed default automation playbooks

    Creates 3 enterprise-grade playbooks:
    1. Low Risk Auto-Approval - Automatically approve very low risk actions
    2. Business Hours Auto-Approval - Auto-approve moderate risk during business hours
    3. Weekend Escalation - Alert security team for weekend high-risk actions
    """

    playbooks = [
        {
            "id": "low_risk_auto_approve",
            "name": "Low Risk Auto-Approval",
            "description": "Automatically approve very low risk actions (risk score ≤ 30) without human intervention. Ideal for routine operations like file reads, status checks, and informational queries.",
            "status": "active",
            "risk_level": "low",
            "approval_required": False,
            "trigger_conditions": {
                "risk_score_max": 30,
                "action_types": [
                    "read_file",
                    "list_directory",
                    "check_status",
                    "get_info",
                    "search",
                    "query_database_read"
                ]
            },
            "actions": {
                "approve": True,
                "notify": False,
                "escalate": False,
                "log_level": "info"
            },
            "execution_count": 0,
            "success_rate": 100.0,
            "last_executed": None
        },
        {
            "id": "business_hours_auto_approve",
            "name": "Business Hours Auto-Approval",
            "description": "Auto-approve moderate risk actions (risk score ≤ 40) during business hours (9am-5pm EST, weekdays). Provides faster approvals during monitored hours while maintaining security standards.",
            "status": "active",
            "risk_level": "medium",
            "approval_required": False,
            "trigger_conditions": {
                "risk_score_max": 40,
                "business_hours": True,
                "weekend": False,
                "action_types": [
                    "read_file",
                    "write_file",
                    "create_file",
                    "update_record",
                    "api_call_get",
                    "api_call_post"
                ]
            },
            "actions": {
                "approve": True,
                "notify": True,
                "notify_channels": ["slack_security"],
                "escalate": False,
                "log_level": "info"
            },
            "execution_count": 0,
            "success_rate": 100.0,
            "last_executed": None
        },
        {
            "id": "weekend_escalation",
            "name": "Weekend High-Risk Escalation",
            "description": "Automatically escalate high-risk actions (risk score > 50) occurring on weekends to security team. Ensures 24/7 monitoring of critical operations while alerting appropriate personnel.",
            "status": "active",
            "risk_level": "high",
            "approval_required": True,
            "trigger_conditions": {
                "risk_score_min": 50,
                "weekend": True,
                "action_types": [
                    "delete_file",
                    "delete_record",
                    "database_write",
                    "database_delete",
                    "system_config_change",
                    "user_privilege_change",
                    "api_call_delete"
                ]
            },
            "actions": {
                "approve": False,
                "notify": True,
                "notify_channels": ["pagerduty_security", "slack_security_oncall"],
                "escalate": True,
                "escalation_team": "security_oncall",
                "log_level": "warning",
                "require_2fa": True
            },
            "execution_count": 0,
            "success_rate": 100.0,
            "last_executed": None
        }
    ]

    logger.info("🌱 Starting automation playbook seeding...")

    created_count = 0
    updated_count = 0

    for playbook_data in playbooks:
        try:
            # Check if playbook already exists
            existing = db.query(AutomationPlaybook).filter(
                AutomationPlaybook.id == playbook_data["id"]
            ).first()

            if existing:
                # Update existing playbook
                for key, value in playbook_data.items():
                    if key not in ["created_at"]:  # Don't update creation metadata
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                logger.info(f"✏️  Updated playbook: {playbook_data['id']}")
                updated_count += 1
            else:
                # Create new playbook
                # created_by and updated_by are foreign keys to users table, set to None for system
                playbook_data["created_by"] = None
                playbook_data["updated_by"] = None
                playbook = AutomationPlaybook(**playbook_data)
                db.add(playbook)
                logger.info(f"✅ Created playbook: {playbook_data['id']}")
                created_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to seed playbook {playbook_data['id']}: {e}")
            db.rollback()
            raise

    # Commit all changes
    try:
        db.commit()
        logger.info(f"""
╔══════════════════════════════════════════╗
║   Automation Playbook Seeding Complete   ║
╠══════════════════════════════════════════╣
║  Created: {created_count:2d} playbooks                    ║
║  Updated: {updated_count:2d} playbooks                    ║
║  Total:   {created_count + updated_count:2d} playbooks                    ║
╚══════════════════════════════════════════╝
        """)
    except Exception as e:
        logger.error(f"❌ Failed to commit playbooks: {e}")
        db.rollback()
        raise


def verify_playbooks(db: Session) -> None:
    """
    Verify that playbooks were created successfully
    """
    playbooks = db.query(AutomationPlaybook).all()

    logger.info(f"\n📊 Verification: Found {len(playbooks)} automation playbooks in database")

    for playbook in playbooks:
        logger.info(f"""
  → {playbook.id}
    Name: {playbook.name}
    Status: {playbook.status}
    Risk Level: {playbook.risk_level}
    Trigger Conditions: {playbook.trigger_conditions}
    Actions: {playbook.actions}
    Executions: {playbook.execution_count}
    Success Rate: {playbook.success_rate}%
        """)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AUTOMATION PLAYBOOK SEED SCRIPT")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Seed playbooks
        seed_playbooks(db)

        # Verify creation
        verify_playbooks(db)

        logger.info("\n✅ Automation playbook seeding completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {e}")
        logger.info("=" * 60)
        sys.exit(1)

    finally:
        db.close()
