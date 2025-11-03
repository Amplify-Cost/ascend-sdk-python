#!/usr/bin/env python3
"""
Enterprise Alert Seeding Script
Backfill alerts table from existing high-risk agent actions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, UTC
from sqlalchemy import text
from database import get_db

def seed_alerts_from_actions():
    """
    Seed alerts table with historical data from agent_actions

    Business Rules:
    - Only create alerts for high-risk actions (risk_score >= 60)
    - Alert severity based on risk_score:
        * 90-100: critical
        * 75-89: high
        * 60-74: medium
    - Set appropriate status based on action status
    """
    db = next(get_db())

    try:
        print("🚀 Starting alert seeding from agent_actions...")

        # Get high-risk actions that don't have alerts yet
        high_risk_actions = db.execute(text("""
            SELECT
                aa.id,
                aa.action_type,
                aa.risk_score,
                aa.created_at,
                aa.status,
                aa.agent_id
            FROM agent_actions aa
            LEFT JOIN alerts a ON a.agent_action_id = aa.id
            WHERE aa.risk_score >= 60
                AND a.id IS NULL  -- No alert exists yet
            ORDER BY aa.created_at DESC
        """)).fetchall()

        if not high_risk_actions:
            print("✅ No high-risk actions found needing alerts")
            return

        print(f"📊 Found {len(high_risk_actions)} high-risk actions needing alerts")

        alerts_created = 0

        for action in high_risk_actions:
            action_id, action_type, risk_score, created_at, status, agent_id = action

            # Determine severity based on risk score
            if risk_score >= 90:
                severity = "critical"
            elif risk_score >= 75:
                severity = "high"
            else:
                severity = "medium"

            # Determine alert status based on action status
            if status == "approved":
                alert_status = "acknowledged"
            elif status == "rejected":
                alert_status = "resolved"
            elif status == "executed":
                alert_status = "resolved"
            else:  # pending_approval, pending, etc.
                alert_status = "new"

            # Create alert message
            message = f"High-risk {action_type} action (ID: {action_id}, Risk: {risk_score})"

            # Use action's created_at or current time
            timestamp = created_at if created_at else datetime.now(UTC)

            # Insert alert
            result = db.execute(text("""
                INSERT INTO alerts (
                    agent_action_id,
                    alert_type,
                    severity,
                    status,
                    message,
                    timestamp,
                    agent_id
                )
                VALUES (
                    :action_id,
                    'High Risk Agent Action',
                    :severity,
                    :status,
                    :message,
                    :timestamp,
                    :agent_id
                )
                RETURNING id
            """), {
                "action_id": action_id,
                "severity": severity,
                "status": alert_status,
                "message": message,
                "timestamp": timestamp,
                "agent_id": agent_id or "system"
            })

            alert_id = result.fetchone()[0]
            alerts_created += 1

            print(f"  ✅ Created alert {alert_id} for action {action_id} (severity: {severity}, status: {alert_status})")

        db.commit()

        print(f"\n🎉 Successfully created {alerts_created} alerts!")

        # Verification query
        total_alerts = db.execute(text("SELECT COUNT(*) FROM alerts")).fetchone()[0]
        print(f"📊 Total alerts in database: {total_alerts}")

        # Show alert distribution
        distribution = db.execute(text("""
            SELECT severity, COUNT(*) as count
            FROM alerts
            GROUP BY severity
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """)).fetchall()

        print("\n📈 Alert Distribution by Severity:")
        for severity, count in distribution:
            print(f"  {severity}: {count}")

        # Show status distribution
        status_dist = db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM alerts
            GROUP BY status
        """)).fetchall()

        print("\n📊 Alert Distribution by Status:")
        for alert_status, count in status_dist:
            print(f"  {alert_status}: {count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding alerts: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_alerts_from_actions()
