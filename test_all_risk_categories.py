#!/usr/bin/env python3
"""
Test All Risk Categories: LOW, MEDIUM, HIGH, CRITICAL
Verify orchestration handles all risk levels correctly
"""
from database import get_db
from sqlalchemy import text
from datetime import datetime, UTC

def test_all_risk_categories():
    """
    Test orchestration for all risk categories:
    - LOW (risk_score: 0-49) → No alert created
    - MEDIUM (risk_score: 50-69) → No alert created (per orchestration logic)
    - HIGH (risk_score: 70-89) → Alert auto-created
    - CRITICAL (risk_score: 90-100) → Alert auto-created
    """
    db = next(get_db())

    try:
        print("🧪 TESTING ALL RISK CATEGORIES")
        print("=" * 80)

        test_cases = [
            {
                "risk_level": "low",
                "risk_score": 30,
                "action_type": "file_read",
                "description": "Read configuration file",
                "expect_alert": False
            },
            {
                "risk_level": "medium",
                "risk_score": 55,
                "action_type": "api_call",
                "description": "Call external API",
                "expect_alert": False  # Orchestration only creates for high/critical
            },
            {
                "risk_level": "high",
                "risk_score": 75,
                "action_type": "database_write",
                "description": "Update production database",
                "expect_alert": True
            },
            {
                "risk_level": "critical",
                "risk_score": 95,
                "action_type": "database_delete",
                "description": "Delete production records",
                "expect_alert": True
            }
        ]

        from services.orchestration_service import OrchestrationService
        orch = OrchestrationService(db)

        results = []

        for test_case in test_cases:
            print(f"\n{'='*80}")
            print(f"📋 TEST CASE: {test_case['risk_level'].upper()} RISK")
            print(f"{'='*80}")
            print(f"Risk Score: {test_case['risk_score']}/100")
            print(f"Action Type: {test_case['action_type']}")
            print(f"Expected Alert: {'YES' if test_case['expect_alert'] else 'NO'}")
            print()

            # Step 1: Create action
            result = db.execute(text("""
                INSERT INTO agent_actions (
                    agent_id, action_type, description, tool_name,
                    risk_score, risk_level, status, created_at
                )
                VALUES (
                    :agent_id, :action_type, :description, :tool_name,
                    :risk_score, :risk_level, 'pending_approval', :created_at
                )
                RETURNING id
            """), {
                "agent_id": f"test-risk-{test_case['risk_level']}",
                "action_type": test_case['action_type'],
                "description": test_case['description'],
                "tool_name": "test",
                "risk_score": test_case['risk_score'],
                "risk_level": test_case['risk_level'],
                "created_at": datetime.now(UTC)
            })

            action_id = result.fetchone()[0]
            db.commit()
            print(f"1️⃣ Created action ID: {action_id}")

            # Step 2: Call orchestration
            print(f"2️⃣ Calling orchestration service...")
            orch_result = orch.orchestrate_action(
                action_id=action_id,
                risk_level=test_case['risk_level'],
                risk_score=test_case['risk_score'],
                action_type=test_case['action_type']
            )

            alert_created = orch_result['alert_created']
            print(f"3️⃣ Orchestration Result:")
            print(f"   Alert Created: {alert_created}")
            print(f"   Alert ID: {orch_result.get('alert_id', 'N/A')}")
            print(f"   Status: {orch_result['orchestration_status']}")

            # Step 3: Verify expectation
            passed = alert_created == test_case['expect_alert']
            if passed:
                print(f"✅ PASSED: Alert creation matches expectation")
            else:
                print(f"❌ FAILED: Expected alert={test_case['expect_alert']}, got alert={alert_created}")

            # Step 4: Verify in database
            if alert_created:
                alert = db.execute(text("""
                    SELECT id, severity, status, message
                    FROM alerts
                    WHERE agent_action_id = :action_id
                """), {"action_id": action_id}).fetchone()

                if alert:
                    print(f"4️⃣ Alert verified in database:")
                    print(f"   Alert ID: {alert[0]}")
                    print(f"   Severity: {alert[1]}")
                    print(f"   Status: {alert[2]}")
                    print(f"   Message: {alert[3]}")
                else:
                    print(f"❌ Alert not found in database!")
                    passed = False

            results.append({
                "risk_level": test_case['risk_level'],
                "risk_score": test_case['risk_score'],
                "action_id": action_id,
                "alert_created": alert_created,
                "expected": test_case['expect_alert'],
                "passed": passed
            })

        # Summary
        print(f"\n{'='*80}")
        print("📊 TEST SUMMARY")
        print(f"{'='*80}\n")

        print(f"{'Risk Level':<12} {'Score':<8} {'Action ID':<12} {'Alert':<8} {'Expected':<10} {'Status':<10}")
        print("-" * 80)

        passed_count = 0
        for result in results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            if result['passed']:
                passed_count += 1

            print(f"{result['risk_level']:<12} {result['risk_score']:<8} {result['action_id']:<12} "
                  f"{str(result['alert_created']):<8} {str(result['expected']):<10} {status:<10}")

        print("-" * 80)
        print(f"\nTotal: {len(results)} tests | Passed: {passed_count} | Failed: {len(results) - passed_count}\n")

        # Final verdict
        if passed_count == len(results):
            print("✅ ALL RISK CATEGORIES HANDLED CORRECTLY")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_all_risk_categories()
    exit(0 if success else 1)
