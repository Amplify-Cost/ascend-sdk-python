#!/usr/bin/env python3
"""
OW-AI Integration Example 5: Automated Scripts and Cron Jobs

USE CASE: Scheduled automation scripts (cron jobs, Airflow DAGs, Jenkins pipelines)
          that perform database maintenance, data processing, or system operations
          with enterprise governance and audit trails.

This example shows how to:
1. Wrap automation scripts with OW-AI governance
2. Handle approval workflows in batch/scheduled contexts
3. Queue actions for later approval (async workflow)
4. Generate compliance reports for scheduled operations

ARCHITECTURE:
    Cron/Scheduler → Automation Script → OW-AI Governance
                                              ↓
                            Submit Action → Check Policy
                                              ↓
                    ┌─────────────────────────────────────┐
                    │ Auto-Approve      │ Require Approval│
                    │ (Low Risk)        │ (High Risk)     │
                    └─────────────────────────────────────┘
                            │                    │
                            ▼                    ▼
                    Execute Immediately    Queue for Review
                            │                    │
                            └────────────────────┘
                                     │
                                     ▼
                            Audit Log + Report

SCHEDULING PATTERNS:
    ┌──────────────────────────────────────────────────────────┐
    │ Pattern 1: Synchronous (Wait for approval)               │
    │ → Best for: Critical operations that must complete       │
    │ → Risk: May block if no approver available               │
    │                                                          │
    │ Pattern 2: Async Queue (Submit and continue)             │
    │ → Best for: Non-urgent operations, batch processing      │
    │ → Risk: Actions may remain pending                       │
    │                                                          │
    │ Pattern 3: Pre-Approved Window (Scheduled approval)      │
    │ → Best for: Regular maintenance with known risk          │
    │ → Risk: Requires pre-coordination with security team     │
    └──────────────────────────────────────────────────────────┘

Engineer: OW-AI Enterprise
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass, field
from enum import Enum
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/automation_governance.log')
    ]
)
logger = logging.getLogger("automation")

# ============================================
# CONFIGURATION
# ============================================

OWAI_API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
OWAI_BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")
AGENT_ID = os.environ.get("AUTOMATION_AGENT_ID", "scheduled-automation-agent")

# Approval timeout for sync operations (seconds)
SYNC_APPROVAL_TIMEOUT = int(os.environ.get("SYNC_APPROVAL_TIMEOUT", "300"))


# ============================================
# GOVERNANCE MODES
# ============================================

class GovernanceMode(Enum):
    """How to handle approval requirements."""
    SYNC = "sync"           # Wait for approval (blocking)
    ASYNC = "async"         # Queue and continue
    FAIL_FAST = "fail_fast" # Abort if approval required
    PRE_APPROVED = "pre_approved"  # Use pre-approved window


@dataclass
class GovernanceResult:
    """Result of governance check."""
    allowed: bool
    action_id: Optional[int] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    decision: Optional[str] = None
    queued: bool = False
    error: Optional[str] = None
    approved_by: Optional[str] = None
    execution_time_ms: float = 0


# ============================================
# OW-AI CLIENT FOR AUTOMATION
# ============================================

class AutomationGovernanceClient:
    """
    Governance client optimized for automation/batch contexts.

    Features:
    - Sync and async approval modes
    - Batch action submission
    - Compliance reporting
    - Error recovery
    """

    def __init__(self, api_key: str, base_url: str, agent_id: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.client = httpx.Client(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        self.pending_actions: List[int] = []
        self.completed_actions: List[GovernanceResult] = []

    def submit_action(
        self,
        action_type: str,
        description: str,
        tool_name: str,
        mode: GovernanceMode = GovernanceMode.SYNC,
        target_system: Optional[str] = None,
        risk_context: Optional[Dict] = None,
        timeout: int = SYNC_APPROVAL_TIMEOUT
    ) -> GovernanceResult:
        """
        Submit action for governance with specified mode.

        Args:
            action_type: Type of action (database_delete, file_cleanup, etc.)
            description: Human-readable description
            tool_name: Tool being used
            mode: Governance mode (sync, async, fail_fast, pre_approved)
            target_system: Target system identifier
            risk_context: Additional context for risk assessment
            timeout: Approval timeout for sync mode

        Returns:
            GovernanceResult with decision and metadata
        """
        start_time = time.time()

        logger.info(f"🔒 Submitting action: {action_type} ({mode.value})")
        logger.info(f"   Description: {description}")

        try:
            # Submit to OW-AI
            payload = {
                "agent_id": self.agent_id,
                "action_type": action_type,
                "description": description,
                "tool_name": tool_name,
                "target_system": target_system or "automation",
                "risk_context": {
                    **(risk_context or {}),
                    "automation_mode": mode.value,
                    "scheduled": True,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            }

            response = self.client.post(
                f"{self.base_url}/api/authorization/agent-action",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            action_id = result.get("action_id")
            risk_score = result.get("risk_score", 0)
            risk_level = result.get("risk_level", "unknown")
            requires_approval = result.get("requires_approval", False)

            logger.info(f"📊 Risk: {risk_score} ({risk_level}), "
                       f"Approval Required: {requires_approval}")

            # Handle based on mode
            if not requires_approval:
                # Auto-approved
                execution_time = (time.time() - start_time) * 1000
                governance_result = GovernanceResult(
                    allowed=True,
                    action_id=action_id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    decision="auto_approved",
                    execution_time_ms=execution_time
                )
                self.completed_actions.append(governance_result)
                logger.info(f"✅ Auto-approved ({execution_time:.0f}ms)")
                return governance_result

            # Approval required - handle based on mode
            if mode == GovernanceMode.FAIL_FAST:
                logger.warning(f"⚠️ Approval required - aborting (fail_fast mode)")
                return GovernanceResult(
                    allowed=False,
                    action_id=action_id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    decision="requires_approval",
                    error="Approval required but mode is fail_fast"
                )

            elif mode == GovernanceMode.ASYNC:
                # Queue for later approval
                self.pending_actions.append(action_id)
                logger.info(f"📬 Queued for approval (action_id: {action_id})")
                return GovernanceResult(
                    allowed=False,
                    action_id=action_id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    decision="queued",
                    queued=True
                )

            elif mode == GovernanceMode.SYNC:
                # Wait for approval
                logger.info(f"⏳ Waiting for approval (timeout: {timeout}s)...")

                approval_result = self._wait_for_approval(action_id, timeout)

                execution_time = (time.time() - start_time) * 1000

                if approval_result.get("approved"):
                    governance_result = GovernanceResult(
                        allowed=True,
                        action_id=action_id,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        decision="approved",
                        approved_by=approval_result.get("reviewed_by"),
                        execution_time_ms=execution_time
                    )
                    self.completed_actions.append(governance_result)
                    logger.info(f"✅ Approved by {approval_result.get('reviewed_by')}")
                    return governance_result
                else:
                    reason = approval_result.get("reason", "Unknown")
                    logger.warning(f"❌ Not approved: {reason}")
                    return GovernanceResult(
                        allowed=False,
                        action_id=action_id,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        decision="rejected" if not approval_result.get("timeout") else "timeout",
                        error=reason,
                        execution_time_ms=execution_time
                    )

            elif mode == GovernanceMode.PRE_APPROVED:
                # Check for pre-approved maintenance window
                # This would integrate with a maintenance schedule system
                logger.info(f"🔑 Checking pre-approved window...")
                # For demo: simulate pre-approval check
                return GovernanceResult(
                    allowed=True,
                    action_id=action_id,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    decision="pre_approved",
                    execution_time_ms=(time.time() - start_time) * 1000
                )

        except Exception as e:
            logger.error(f"❌ Governance error: {e}")
            return GovernanceResult(
                allowed=False,
                error=str(e)
            )

    def _wait_for_approval(self, action_id: int, timeout: int) -> Dict[str, Any]:
        """Poll for approval status."""
        start_time = time.time()
        poll_interval = 5

        while time.time() - start_time < timeout:
            try:
                response = self.client.get(
                    f"{self.base_url}/api/agent-action/status/{action_id}"
                )
                response.raise_for_status()
                status = response.json()

                if status.get("status") == "approved":
                    return {
                        "approved": True,
                        "reviewed_by": status.get("reviewed_by"),
                        "comments": status.get("comments")
                    }
                elif status.get("status") == "rejected":
                    return {
                        "approved": False,
                        "reason": status.get("comments", "Rejected by approver"),
                        "reviewed_by": status.get("reviewed_by")
                    }

                # Progress indicator
                elapsed = int(time.time() - start_time)
                logger.debug(f"   ... waiting ({elapsed}s / {timeout}s)")

                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Poll error: {e}")
                time.sleep(poll_interval)

        return {
            "approved": False,
            "reason": "Approval timeout",
            "timeout": True
        }

    def check_pending_actions(self) -> List[Dict[str, Any]]:
        """Check status of all pending actions."""
        results = []

        for action_id in self.pending_actions[:]:  # Copy to allow modification
            try:
                response = self.client.get(
                    f"{self.base_url}/api/agent-action/status/{action_id}"
                )
                response.raise_for_status()
                status = response.json()

                results.append({
                    "action_id": action_id,
                    "status": status.get("status"),
                    "reviewed_by": status.get("reviewed_by"),
                    "comments": status.get("comments")
                })

                # Remove from pending if final
                if status.get("status") in ("approved", "rejected"):
                    self.pending_actions.remove(action_id)

            except Exception as e:
                results.append({
                    "action_id": action_id,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for all actions in this session."""
        return {
            "report_timestamp": datetime.now(UTC).isoformat(),
            "agent_id": self.agent_id,
            "summary": {
                "total_actions": len(self.completed_actions) + len(self.pending_actions),
                "completed": len(self.completed_actions),
                "pending": len(self.pending_actions),
                "auto_approved": sum(1 for a in self.completed_actions if a.decision == "auto_approved"),
                "manually_approved": sum(1 for a in self.completed_actions if a.decision == "approved"),
                "rejected": sum(1 for a in self.completed_actions if a.decision == "rejected")
            },
            "completed_actions": [
                {
                    "action_id": a.action_id,
                    "risk_score": a.risk_score,
                    "risk_level": a.risk_level,
                    "decision": a.decision,
                    "approved_by": a.approved_by,
                    "execution_time_ms": a.execution_time_ms
                }
                for a in self.completed_actions
            ],
            "pending_actions": self.pending_actions
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# ============================================
# EXAMPLE AUTOMATION TASKS
# ============================================

def task_database_cleanup(client: AutomationGovernanceClient, mode: GovernanceMode):
    """
    Example: Database cleanup task (DELETE old records).

    Risk Level: HIGH
    Typical Schedule: Weekly
    """
    logger.info("\n" + "=" * 60)
    logger.info("TASK: Database Cleanup")
    logger.info("=" * 60)

    governance = client.submit_action(
        action_type="database_delete",
        description="Delete user sessions older than 90 days from production database",
        tool_name="postgresql",
        mode=mode,
        target_system="production-db",
        risk_context={
            "table": "user_sessions",
            "condition": "created_at < NOW() - INTERVAL '90 days'",
            "estimated_rows": 50000,
            "is_production": True
        }
    )

    if governance.allowed:
        # Execute the actual cleanup
        logger.info("📦 Executing database cleanup...")
        # In production: db.execute("DELETE FROM user_sessions WHERE ...")
        logger.info("✅ Cleanup completed (simulated)")
        return True
    else:
        logger.warning(f"⚠️ Cleanup blocked: {governance.error or governance.decision}")
        return False


def task_log_rotation(client: AutomationGovernanceClient, mode: GovernanceMode):
    """
    Example: Log file rotation task.

    Risk Level: MEDIUM
    Typical Schedule: Daily
    """
    logger.info("\n" + "=" * 60)
    logger.info("TASK: Log Rotation")
    logger.info("=" * 60)

    governance = client.submit_action(
        action_type="file_delete",
        description="Rotate and compress log files older than 7 days",
        tool_name="logrotate",
        mode=mode,
        target_system="application-servers",
        risk_context={
            "log_directory": "/var/log/app",
            "retention_days": 7,
            "compression": "gzip"
        }
    )

    if governance.allowed:
        logger.info("📦 Executing log rotation...")
        # In production: subprocess.run(["logrotate", "-f", "/etc/logrotate.conf"])
        logger.info("✅ Log rotation completed (simulated)")
        return True
    else:
        logger.warning(f"⚠️ Log rotation blocked: {governance.error or governance.decision}")
        return False


def task_backup_verification(client: AutomationGovernanceClient, mode: GovernanceMode):
    """
    Example: Backup verification task (read-only).

    Risk Level: LOW
    Typical Schedule: Daily
    """
    logger.info("\n" + "=" * 60)
    logger.info("TASK: Backup Verification")
    logger.info("=" * 60)

    governance = client.submit_action(
        action_type="backup_verify",
        description="Verify integrity of latest database backup",
        tool_name="pg_restore",
        mode=mode,
        target_system="backup-storage",
        risk_context={
            "backup_type": "full",
            "verification_method": "checksum",
            "is_read_only": True
        }
    )

    if governance.allowed:
        logger.info("📦 Verifying backup integrity...")
        # In production: subprocess.run(["pg_restore", "--list", backup_file])
        logger.info("✅ Backup verification completed (simulated)")
        return True
    else:
        logger.warning(f"⚠️ Backup verification blocked: {governance.error or governance.decision}")
        return False


def task_data_export(client: AutomationGovernanceClient, mode: GovernanceMode):
    """
    Example: Data export task (potential data exfiltration).

    Risk Level: HIGH
    Typical Schedule: Monthly
    """
    logger.info("\n" + "=" * 60)
    logger.info("TASK: Monthly Data Export")
    logger.info("=" * 60)

    governance = client.submit_action(
        action_type="data_export",
        description="Export customer usage data for monthly analytics report",
        tool_name="data-exporter",
        mode=mode,
        target_system="analytics-pipeline",
        risk_context={
            "data_type": "usage_metrics",
            "contains_pii": False,
            "destination": "s3://analytics-bucket/monthly/",
            "encryption": "AES-256",
            "estimated_size_gb": 5
        }
    )

    if governance.allowed:
        logger.info("📦 Executing data export...")
        # In production: export_data_to_s3(...)
        logger.info("✅ Data export completed (simulated)")
        return True
    else:
        logger.warning(f"⚠️ Data export blocked: {governance.error or governance.decision}")
        return False


def task_security_scan(client: AutomationGovernanceClient, mode: GovernanceMode):
    """
    Example: Security vulnerability scan.

    Risk Level: MEDIUM (can trigger alerts)
    Typical Schedule: Weekly
    """
    logger.info("\n" + "=" * 60)
    logger.info("TASK: Security Vulnerability Scan")
    logger.info("=" * 60)

    governance = client.submit_action(
        action_type="security_scan",
        description="Run automated vulnerability scan on production infrastructure",
        tool_name="vulnerability-scanner",
        mode=mode,
        target_system="production-infrastructure",
        risk_context={
            "scan_type": "full",
            "targets": ["web-servers", "api-servers", "databases"],
            "intensity": "normal",
            "may_trigger_ids": True
        }
    )

    if governance.allowed:
        logger.info("📦 Executing security scan...")
        # In production: run_vulnerability_scan(...)
        logger.info("✅ Security scan completed (simulated)")
        return True
    else:
        logger.warning(f"⚠️ Security scan blocked: {governance.error or governance.decision}")
        return False


# ============================================
# MAIN AUTOMATION RUNNER
# ============================================

def run_automation_suite(
    tasks: List[str],
    mode: GovernanceMode = GovernanceMode.SYNC
):
    """
    Run automation task suite with OW-AI governance.

    Args:
        tasks: List of task names to run
        mode: Governance mode for all tasks
    """
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OW-AI Integration Example: Automation & Cron Jobs         ║
║                                                               ║
║     This example demonstrates governance for scheduled        ║
║     automation tasks like database cleanup, backups, etc.     ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Initialize governance client
    client = AutomationGovernanceClient(
        api_key=OWAI_API_KEY,
        base_url=OWAI_BASE_URL,
        agent_id=AGENT_ID
    )

    # Task registry
    task_registry = {
        "database_cleanup": task_database_cleanup,
        "log_rotation": task_log_rotation,
        "backup_verification": task_backup_verification,
        "data_export": task_data_export,
        "security_scan": task_security_scan
    }

    logger.info(f"🚀 Starting automation suite")
    logger.info(f"   Mode: {mode.value}")
    logger.info(f"   Tasks: {tasks}")
    logger.info(f"   Agent ID: {AGENT_ID}")

    # Run tasks
    results = {}
    for task_name in tasks:
        if task_name in task_registry:
            try:
                success = task_registry[task_name](client, mode)
                results[task_name] = "success" if success else "blocked"
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                results[task_name] = f"error: {str(e)}"
        else:
            logger.warning(f"Unknown task: {task_name}")
            results[task_name] = "unknown"

    # Check pending actions (for async mode)
    if mode == GovernanceMode.ASYNC and client.pending_actions:
        logger.info("\n📬 Pending Actions:")
        for status in client.check_pending_actions():
            logger.info(f"   Action {status['action_id']}: {status['status']}")

    # Generate compliance report
    report = client.generate_compliance_report()

    logger.info("\n" + "=" * 60)
    logger.info("COMPLIANCE REPORT")
    logger.info("=" * 60)
    logger.info(f"Total Actions: {report['summary']['total_actions']}")
    logger.info(f"Auto-Approved: {report['summary']['auto_approved']}")
    logger.info(f"Manually Approved: {report['summary']['manually_approved']}")
    logger.info(f"Pending: {report['summary']['pending']}")
    logger.info(f"Rejected: {report['summary']['rejected']}")

    # Save report to file
    report_file = f"/tmp/automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"\n📄 Report saved to: {report_file}")

    # Cleanup
    client.close()

    return results


# ============================================
# CLI INTERFACE
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description="Run automated tasks with OW-AI governance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tasks in sync mode (wait for approval)
  python 05_automation_cron.py --tasks all --mode sync

  # Run specific tasks in async mode (queue for approval)
  python 05_automation_cron.py --tasks database_cleanup,log_rotation --mode async

  # Run with fail-fast (abort if approval needed)
  python 05_automation_cron.py --tasks backup_verification --mode fail_fast

Crontab Example:
  # Run daily at 2 AM in async mode
  0 2 * * * /path/to/python /path/to/05_automation_cron.py --tasks log_rotation --mode async

  # Run weekly cleanup (Sunday 3 AM) in sync mode
  0 3 * * 0 /path/to/python /path/to/05_automation_cron.py --tasks database_cleanup --mode sync
        """
    )

    parser.add_argument(
        "--tasks",
        type=str,
        default="all",
        help="Comma-separated task names or 'all' (default: all)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["sync", "async", "fail_fast", "pre_approved"],
        default="sync",
        help="Governance mode (default: sync)"
    )

    args = parser.parse_args()

    # Parse tasks
    if args.tasks == "all":
        tasks = [
            "backup_verification",  # Low risk first
            "log_rotation",         # Medium risk
            "security_scan",        # Medium risk
            "database_cleanup",     # High risk
            "data_export"           # High risk
        ]
    else:
        tasks = [t.strip() for t in args.tasks.split(",")]

    # Parse mode
    mode = GovernanceMode(args.mode)

    # Run
    results = run_automation_suite(tasks, mode)

    # Exit code based on results
    if all(r == "success" for r in results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
