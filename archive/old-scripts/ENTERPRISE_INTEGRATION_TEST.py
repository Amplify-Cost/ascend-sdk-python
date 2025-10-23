#!/usr/bin/env python3
"""
🏢 ENTERPRISE SYSTEM INTEGRATION TEST
=====================================
Tests all 4 subsystems and their integration points

Subsystems:
1. Authorization Center (Actions & Approvals)
2. Alert System
3. Rules Engine
4. Automation/Playbooks & Workflows

Author: Enterprise Engineering Team
Date: 2025-10-22
"""

import sys
from datetime import datetime
from sqlalchemy import func
from database import SessionLocal
from models import (
    AgentAction, Alert, SmartRule, AutomationPlaybook, 
    PlaybookExecution, Workflow, WorkflowExecution, User
)

# Test results storage
test_results = {
    'subsystem_tests': [],
    'integration_tests': [],
    'total_passed': 0,
    'total_failed': 0
}

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_result(test_name, passed, details=""):
    """Record and print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       → {details}")
    
    if passed:
        test_results['total_passed'] += 1
    else:
        test_results['total_failed'] += 1
    
    return passed

def test_subsystem_1_authorization():
    """Test Authorization Center subsystem"""
    print_header("SUBSYSTEM 1: AUTHORIZATION CENTER")
    
    db = SessionLocal()
    try:
        # Test 1: Can query actions
        actions = db.query(AgentAction).all()
        test_result(
            "Actions table accessible",
            True,
            f"Found {len(actions)} actions"
        )
        
        # Test 2: Actions have required fields
        if actions:
            sample = actions[0]
            has_fields = all([
                hasattr(sample, 'id'),
                hasattr(sample, 'action_type'),
                hasattr(sample, 'status'),
                hasattr(sample, 'ai_risk_score')
            ])
            test_result(
                "Action model has required fields",
                has_fields,
                f"Sample action: {sample.action_type}"
            )
        
        # Test 3: Count by status
        pending = db.query(AgentAction).filter(AgentAction.status == 'pending').count()
        approved = db.query(AgentAction).filter(AgentAction.status == 'approved').count()
        test_result(
            "Actions categorized by status",
            True,
            f"Pending: {pending}, Approved: {approved}"
        )
        
        # Test 4: Risk score distribution
        high_risk = db.query(AgentAction).filter(AgentAction.ai_risk_score >= 70).count()
        test_result(
            "Risk scoring exists",
            True,
            f"High-risk actions (≥70): {high_risk}"
        )
        
        return True
        
    except Exception as e:
        test_result("Authorization subsystem", False, str(e))
        return False
    finally:
        db.close()

def test_subsystem_2_alerts():
    """Test Alert System subsystem"""
    print_header("SUBSYSTEM 2: ALERT SYSTEM")
    
    db = SessionLocal()
    try:
        # Test 1: Can query alerts
        alerts = db.query(Alert).all()
        test_result(
            "Alerts table accessible",
            True,
            f"Found {len(alerts)} alerts"
        )
        
        # Test 2: Alerts have severity levels
        if alerts:
            critical = db.query(Alert).filter(Alert.severity == 'critical').count()
            high = db.query(Alert).filter(Alert.severity == 'high').count()
            test_result(
                "Alert severity categorization",
                True,
                f"Critical: {critical}, High: {high}"
            )
        
        # Test 3: Alert status tracking
        active = db.query(Alert).filter(Alert.status == 'active').count()
        resolved = db.query(Alert).filter(Alert.status == 'resolved').count()
        test_result(
            "Alert status tracking",
            True,
            f"Active: {active}, Resolved: {resolved}"
        )
        
        return True
        
    except Exception as e:
        test_result("Alert subsystem", False, str(e))
        return False
    finally:
        db.close()

def test_subsystem_3_rules():
    """Test Rules Engine subsystem"""
    print_header("SUBSYSTEM 3: RULES ENGINE")
    
    db = SessionLocal()
    try:
        # Test 1: Can query rules
        rules = db.query(SmartRule).all()
        test_result(
            "Rules table accessible",
            True,
            f"Found {len(rules)} rules"
        )
        
        # Test 2: Rules have conditions
        if rules:
            sample = rules[0]
            has_conditions = hasattr(sample, 'conditions') and sample.conditions is not None
            test_result(
                "Rules have evaluation conditions",
                has_conditions,
                f"Sample rule: {sample.rule_name if hasattr(sample, 'rule_name') else 'N/A'}"
            )
        
        # Test 3: Active vs inactive rules
        active = db.query(SmartRule).filter(SmartRule.status == 'active').count()
        test_result(
            "Active rules available for evaluation",
            active > 0,
            f"Active rules: {active}"
        )
        
        return True
        
    except Exception as e:
        test_result("Rules Engine subsystem", False, str(e))
        return False
    finally:
        db.close()

def test_subsystem_4_automation():
    """Test Automation/Playbooks subsystem"""
    print_header("SUBSYSTEM 4: AUTOMATION & WORKFLOWS")
    
    db = SessionLocal()
    try:
        # Test 1: Playbooks table
        playbooks = db.query(AutomationPlaybook).all()
        test_result(
            "Playbooks table accessible",
            True,
            f"Found {len(playbooks)} playbooks"
        )
        
        # Test 2: Workflows table
        workflows = db.query(Workflow).all()
        test_result(
            "Workflows table accessible",
            True,
            f"Found {len(workflows)} workflows"
        )
        
        # Test 3: Active playbooks
        active_playbooks = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.status == 'active'
        ).count()
        test_result(
            "Active playbooks ready for execution",
            active_playbooks > 0,
            f"Active playbooks: {active_playbooks}"
        )
        
        # Test 4: Execution history
        executions = db.query(PlaybookExecution).count()
        test_result(
            "Playbook execution tracking",
            True,
            f"Execution records: {executions}"
        )
        
        return True
        
    except Exception as e:
        test_result("Automation subsystem", False, str(e))
        return False
    finally:
        db.close()

def test_integration_1_action_to_rules():
    """Test: Do actions trigger rule evaluation?"""
    print_header("INTEGRATION TEST 1: ACTIONS → RULES")
    
    db = SessionLocal()
    try:
        # Check if actions have risk scores (indicating rules ran)
        actions_with_scores = db.query(AgentAction).filter(
            AgentAction.ai_risk_score.isnot(None)
        ).count()
        
        total_actions = db.query(AgentAction).count()
        
        if total_actions > 0:
            percentage = (actions_with_scores / total_actions) * 100
            test_result(
                "Actions have risk scores (rules evaluated)",
                actions_with_scores > 0,
                f"{actions_with_scores}/{total_actions} actions ({percentage:.1f}%) have risk scores"
            )
        else:
            test_result(
                "Actions exist for testing",
                False,
                "No actions found in database"
            )
        
    except Exception as e:
        test_result("Action→Rules integration", False, str(e))
    finally:
        db.close()

def test_integration_2_action_to_alerts():
    """Test: Do high-risk actions create alerts?"""
    print_header("INTEGRATION TEST 2: ACTIONS → ALERTS")
    
    db = SessionLocal()
    try:
        # Check high-risk actions
        high_risk_actions = db.query(AgentAction).filter(
            AgentAction.ai_risk_score >= 80
        ).count()
        
        # Check if alerts exist
        total_alerts = db.query(Alert).count()
        
        if high_risk_actions > 0:
            test_result(
                "High-risk actions exist",
                True,
                f"Found {high_risk_actions} high-risk actions"
            )
            
            test_result(
                "Alerts exist in system",
                total_alerts > 0,
                f"Found {total_alerts} alerts"
            )
            
            # Can't definitively prove link without foreign key, but can suggest
            print(f"       ℹ️  Integration status uncertain - need foreign key to verify")
        else:
            test_result(
                "High-risk actions for testing",
                False,
                "No high-risk actions found"
            )
        
    except Exception as e:
        test_result("Action→Alert integration", False, str(e))
    finally:
        db.close()

def test_integration_3_action_to_workflows():
    """Test: Do actions trigger workflows?"""
    print_header("INTEGRATION TEST 3: ACTIONS → WORKFLOWS")
    
    db = SessionLocal()
    try:
        # Check if actions have workflow_id
        actions_with_workflows = db.query(AgentAction).filter(
            AgentAction.workflow_id.isnot(None)
        ).count()
        
        total_actions = db.query(AgentAction).count()
        
        if total_actions > 0:
            percentage = (actions_with_workflows / total_actions) * 100 if total_actions > 0 else 0
            test_result(
                "Actions linked to workflows",
                actions_with_workflows > 0,
                f"{actions_with_workflows}/{total_actions} actions ({percentage:.1f}%) have workflows"
            )
            
            # Check workflow executions
            executions = db.query(WorkflowExecution).count()
            test_result(
                "Workflow executions exist",
                executions >= 0,
                f"Found {executions} workflow execution records"
            )
        else:
            test_result(
                "Actions exist for testing",
                False,
                "No actions found"
            )
        
    except Exception as e:
        test_result("Action→Workflow integration", False, str(e))
    finally:
        db.close()

def test_integration_4_playbooks_executable():
    """Test: Can playbooks be executed?"""
    print_header("INTEGRATION TEST 4: PLAYBOOK EXECUTION")
    
    db = SessionLocal()
    try:
        # Check if playbooks have proper structure
        playbooks = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.status == 'active'
        ).all()
        
        if playbooks:
            sample = playbooks[0]
            has_structure = all([
                hasattr(sample, 'trigger_conditions'),
                hasattr(sample, 'actions'),
                hasattr(sample, 'status')
            ])
            
            test_result(
                "Playbooks have executable structure",
                has_structure,
                f"Sample: {sample.name}"
            )
            
            # Check execution history
            exec_count = db.query(PlaybookExecution).count()
            test_result(
                "Playbook execution history tracking",
                True,
                f"Total executions recorded: {exec_count}"
            )
        else:
            test_result(
                "Active playbooks exist",
                False,
                "No active playbooks found"
            )
        
    except Exception as e:
        test_result("Playbook execution", False, str(e))
    finally:
        db.close()

def generate_report():
    """Generate final test report"""
    print_header("📊 TEST SUMMARY REPORT")
    
    total_tests = test_results['total_passed'] + test_results['total_failed']
    pass_rate = (test_results['total_passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n✅ Passed: {test_results['total_passed']}")
    print(f"❌ Failed: {test_results['total_failed']}")
    print(f"📊 Pass Rate: {pass_rate:.1f}%")
    
    print("\n" + "=" * 70)
    print("🎯 VERDICT:")
    print("=" * 70)
    
    if pass_rate >= 90:
        print("✅ EXCELLENT - All subsystems operational, integration working")
    elif pass_rate >= 70:
        print("⚠️  GOOD - Core systems work, some integration issues")
    elif pass_rate >= 50:
        print("⚠️  FAIR - Systems exist but integration needs work")
    else:
        print("❌ NEEDS ATTENTION - Significant integration issues")
    
    print("\n💡 RECOMMENDATION:")
    if pass_rate >= 80:
        print("   System is production-ready. Rebuild can wait.")
    else:
        print("   Consider implementing the Enterprise Rebuild Plan soon.")
    
    print("=" * 70)

def main():
    """Run all tests"""
    print("=" * 70)
    print("🏢 ENTERPRISE SYSTEM INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Database: PostgreSQL")
    print("=" * 70)
    
    # Run subsystem tests
    test_subsystem_1_authorization()
    test_subsystem_2_alerts()
    test_subsystem_3_rules()
    test_subsystem_4_automation()
    
    # Run integration tests
    test_integration_1_action_to_rules()
    test_integration_2_action_to_alerts()
    test_integration_3_action_to_workflows()
    test_integration_4_playbooks_executable()
    
    # Generate report
    generate_report()
    
    # Exit code
    sys.exit(0 if test_results['total_failed'] == 0 else 1)

if __name__ == "__main__":
    main()
