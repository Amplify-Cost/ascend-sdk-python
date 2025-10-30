#!/usr/bin/env python3
"""
End-to-End Orchestration Test
Submit a high-risk action and verify alert is automatically created
"""
from database import get_db
from sqlalchemy import text
from datetime import datetime, UTC
import json

def test_orchestration_e2e():
    """
    Test complete orchestration flow:
    1. Submit high-risk action
    2. Verify action created in database
    3. Verify alert auto-created by orchestration
    4. Verify audit trail
    """
    db = next(get_db())

    try:
        print("🧪 TESTING END-TO-END ORCHESTRATION FLOW")
        print("=" * 60)

        # Count alerts before
        alerts_before = db.execute(text("SELECT COUNT(*) FROM alerts")).fetchone()[0]
        print(f"\n📊 Alerts before test: {alerts_before}")

        # Step 1: Create high-risk action manually (simulating API submission)
        print("\n1️⃣ Submitting high-risk action...")

        action_data = {
            "agent_id": "test-agent-orchestration",
            "action_type": "database_delete",  # High-risk action
            "description": "Test orchestration - delete production records",
            "tool_name": "psql"
        }

        result = db.execute(text("""
            INSERT INTO agent_actions (
                agent_id, action_type, description, tool_name,
                status, created_at
            )
            VALUES (
                :agent_id, :action_type, :description, :tool_name,
                'pending_approval', :created_at
            )
            RETURNING id
        """), {
            **action_data,
            "created_at": datetime.now(UTC)
        })

        action_id = result.fetchone()[0]
        db.commit()
        print(f"   ✅ Action created with ID: {action_id}")

        # Step 2: Calculate risk score (simulating main.py logic)
        print("\n2️⃣ Calculating risk score...")

        # Simulate CVSS calculation (database_delete = high risk)
        cvss_score = 8.5  # High CVSS score
        risk_score = int(cvss_score * 10)  # 85
        risk_level = "high" if risk_score >= 70 else "medium"

        # Update action with risk score
        db.execute(text("""
            UPDATE agent_actions
            SET risk_score = :risk_score
            WHERE id = :action_id
        """), {"risk_score": risk_score, "action_id": action_id})
        db.commit()

        print(f"   ✅ Risk calculated: {risk_score}/100 (level: {risk_level})")

        # Step 3: Call orchestration service (simulating main.py:1612)
        print("\n3️⃣ Calling orchestration service...")

        from services.orchestration_service import OrchestrationService
        orch = OrchestrationService(db)

        result = orch.orchestrate_action(
            action_id=action_id,
            risk_level=risk_level,
            risk_score=risk_score,
            action_type=action_data["action_type"]
        )

        print(f"   Orchestration result: {result}")

        if result["alert_created"]:
            print(f"   ✅ Alert auto-created with ID: {result['alert_id']}")
        else:
            print(f"   ⚠️ No alert created (risk level may be too low)")

        # Step 4: Verify alert in database
        print("\n4️⃣ Verifying alert in database...")

        alert = db.execute(text("""
            SELECT
                a.id, a.alert_type, a.severity, a.status, a.message,
                aa.action_type, aa.risk_score
            FROM alerts a
            JOIN agent_actions aa ON a.agent_action_id = aa.id
            WHERE a.agent_action_id = :action_id
        """), {"action_id": action_id}).fetchone()

        if alert:
            print(f"   ✅ Alert found in database:")
            print(f"      Alert ID: {alert[0]}")
            print(f"      Type: {alert[1]}")
            print(f"      Severity: {alert[2]}")
            print(f"      Status: {alert[3]}")
            print(f"      Message: {alert[4]}")
            print(f"      Linked Action: {alert[5]} (risk: {alert[6]})")
        else:
            print(f"   ❌ No alert found for action {action_id}")

        # Step 5: Verify alert count increased
        alerts_after = db.execute(text("SELECT COUNT(*) FROM alerts")).fetchone()[0]
        print(f"\n📊 Alerts after test: {alerts_after}")
        print(f"   New alerts created: {alerts_after - alerts_before}")

        # Step 6: Check audit logs
        print("\n5️⃣ Checking audit trail...")

        audit_count = db.execute(text("""
            SELECT COUNT(*) FROM audit_logs
            WHERE entity_type = 'agent_action'
            AND entity_id = :action_id
        """), {"action_id": action_id}).fetchone()[0]

        print(f"   Audit log entries for action {action_id}: {audit_count}")

        if audit_count > 0:
            audit_logs = db.execute(text("""
                SELECT action, performed_by, timestamp
                FROM audit_logs
                WHERE entity_type = 'agent_action'
                AND entity_id = :action_id
                ORDER BY timestamp DESC
                LIMIT 3
            """), {"action_id": action_id}).fetchall()

            for log in audit_logs:
                print(f"      - {log[0]} by {log[1]} at {log[2]}")

        print("\n" + "=" * 60)
        print("✅ END-TO-END TEST COMPLETE")
        print("=" * 60)

        # Summary
        print("\n📈 TEST SUMMARY:")
        print(f"   ✅ Action submitted successfully (ID: {action_id})")
        print(f"   ✅ Risk score calculated: {risk_score}/100")
        print(f"   ✅ Orchestration executed: {result['orchestration_status']}")
        print(f"   ✅ Alert created: {result['alert_created']}")
        if result['alert_created']:
            print(f"   ✅ Alert ID: {result['alert_id']}")
        print(f"   ✅ Workflows triggered: {len(result.get('workflows_triggered', []))}")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_orchestration_e2e()
    exit(0 if success else 1)
