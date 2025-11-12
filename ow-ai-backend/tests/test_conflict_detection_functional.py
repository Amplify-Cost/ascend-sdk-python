"""
Functional Tests for Policy Conflict Detection

Tests conflict detection with real scenarios using mock database.

Author: OW-KAI Engineering Team
"""

import sys
sys.path.insert(0, '/Users/mac_001/OW_AI_Project/ow-ai-backend')

from services.policy_conflict_detector import PolicyConflictDetector, ConflictType


class MockDB:
    """Mock database session for testing"""

    def __init__(self):
        self.policies = []

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.policies

    def add_policy(self, policy):
        self.policies.append(policy)


class MockPolicy:
    """Mock policy object"""

    def __init__(self, policy_id, policy_name, effect, actions, resources, conditions=None, priority=100):
        self.id = policy_id
        self.policy_name = policy_name
        self.effect = effect
        self.actions = actions
        self.resources = resources
        self.conditions = conditions or {}
        self.priority = priority
        self.status = "active"


def test_effect_conflict():
    """TEST 1: Effect Contradiction (CRITICAL)"""
    print("\n" + "="*70)
    print("TEST 1: Effect Contradiction Detection")
    print("="*70)

    db = MockDB()

    # Existing policy: DENY on database:*
    existing = MockPolicy(
        policy_id=1,
        policy_name="Deny All Database Access",
        effect="deny",
        actions=["write", "delete"],
        resources=["database:*"],
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    # New policy: ALLOW on database:production:*
    new_policy = {
        "id": 0,
        "policy_name": "Allow Production Database",
        "effect": "permit",
        "actions": ["write"],
        "resources": ["database:production:*"],
        "conditions": {},
        "priority": 90
    }

    conflicts = detector.detect_conflicts(new_policy)

    # Verify
    effect_conflicts = [c for c in conflicts if c.conflict_type == "effect_contradiction"]

    if len(effect_conflicts) > 0:
        print("✅ PASS: Effect conflict detected")
        print(f"   Severity: {effect_conflicts[0].severity}")
        print(f"   Description: {effect_conflicts[0].description}")
        print(f"   Suggestions: {effect_conflicts[0].resolution_suggestions[0]}")
        return True
    else:
        print("❌ FAIL: Effect conflict not detected")
        return False


def test_priority_conflict():
    """TEST 2: Priority Conflict (HIGH)"""
    print("\n" + "="*70)
    print("TEST 2: Priority Conflict Detection")
    print("="*70)

    db = MockDB()

    # Existing: Priority 100 on database:*
    existing = MockPolicy(
        policy_id=1,
        policy_name="Database Policy 1",
        effect="deny",
        actions=["write"],
        resources=["database:*"],
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    # New: Also priority 100 on overlapping resource
    new_policy = {
        "id": 0,
        "policy_name": "Database Policy 2",
        "effect": "deny",
        "actions": ["write"],
        "resources": ["database:production:*"],
        "priority": 100  # Same priority!
    }

    conflicts = detector.detect_conflicts(new_policy)
    priority_conflicts = [c for c in conflicts if c.conflict_type == "priority_conflict"]

    if len(priority_conflicts) > 0:
        print("✅ PASS: Priority conflict detected")
        print(f"   Severity: {priority_conflicts[0].severity}")
        print(f"   Description: {priority_conflicts[0].description}")
        return True
    else:
        print("❌ FAIL: Priority conflict not detected")
        return False


def test_wildcard_matching():
    """TEST 3: Wildcard Resource Matching"""
    print("\n" + "="*70)
    print("TEST 3: Wildcard Resource Matching")
    print("="*70)

    db = MockDB()

    # Existing: Wildcard resource
    existing = MockPolicy(
        policy_id=1,
        policy_name="All Databases",
        effect="deny",
        actions=["write"],
        resources=["*"],  # Matches everything
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    # New: Specific resource (should match wildcard)
    new_policy = {
        "id": 0,
        "policy_name": "Specific Database",
        "effect": "permit",
        "actions": ["write"],
        "resources": ["database:production"],
        "priority": 90
    }

    conflicts = detector.detect_conflicts(new_policy)

    if len(conflicts) > 0:
        print("✅ PASS: Wildcard matching works")
        print(f"   Found {len(conflicts)} conflicts")
        return True
    else:
        print("❌ FAIL: Wildcard matching failed")
        return False


def test_no_conflict_different_resources():
    """TEST 4: No False Positives"""
    print("\n" + "="*70)
    print("TEST 4: No False Positives (Different Resources)")
    print("="*70)

    db = MockDB()

    # Existing: DENY database:*
    existing = MockPolicy(
        policy_id=1,
        policy_name="Deny Database",
        effect="deny",
        actions=["write"],
        resources=["database:*"],
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    # New: ALLOW s3:* (completely different resource)
    new_policy = {
        "id": 0,
        "policy_name": "Allow S3",
        "effect": "permit",
        "actions": ["write"],
        "resources": ["s3:*"],
        "priority": 90
    }

    conflicts = detector.detect_conflicts(new_policy)

    if len(conflicts) == 0:
        print("✅ PASS: No false positive on different resources")
        return True
    else:
        print("❌ FAIL: False positive detected")
        print(f"   Unexpected conflicts: {len(conflicts)}")
        return False


def test_condition_mismatch():
    """TEST 5: Condition Mismatch Detection"""
    print("\n" + "="*70)
    print("TEST 5: Condition Mismatch Detection")
    print("="*70)

    db = MockDB()

    # Existing: environment = production
    existing = MockPolicy(
        policy_id=1,
        policy_name="Production Policy",
        effect="deny",
        actions=["write"],
        resources=["database:*"],
        conditions={"environment": "production"},
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    # New: environment = development (same resource, different condition)
    new_policy = {
        "id": 0,
        "policy_name": "Development Policy",
        "effect": "deny",
        "actions": ["write"],
        "resources": ["database:*"],
        "conditions": {"environment": "development"},
        "priority": 90
    }

    conflicts = detector.detect_conflicts(new_policy)
    condition_conflicts = [c for c in conflicts if c.conflict_type == "condition_mismatch"]

    if len(condition_conflicts) > 0:
        print("✅ PASS: Condition mismatch detected")
        print(f"   Severity: {condition_conflicts[0].severity}")
        return True
    else:
        print("❌ FAIL: Condition mismatch not detected")
        return False


def test_system_wide_analysis():
    """TEST 6: System-Wide Conflict Analysis"""
    print("\n" + "="*70)
    print("TEST 6: System-Wide Conflict Analysis")
    print("="*70)

    db = MockDB()

    # Create 5 policies with intentional conflicts
    policies = [
        MockPolicy(1, "Deny DB", "deny", ["write"], ["database:*"], {}, 100),
        MockPolicy(2, "Allow DB Prod", "permit", ["write"], ["database:prod:*"], {}, 100),  # Priority conflict + effect conflict
        MockPolicy(3, "Deny S3", "deny", ["write"], ["s3:*"], {}, 90),
        MockPolicy(4, "Allow S3 Public", "permit", ["write"], ["s3://public-*"], {}, 90),  # Effect conflict
        MockPolicy(5, "Deny All", "deny", ["*"], ["*"], {}, 50)  # Conflicts with everything
    ]

    for p in policies:
        db.add_policy(p)

    detector = PolicyConflictDetector(db)
    analysis = detector.analyze_all_policies()

    print(f"Policies Analyzed: {analysis['policies_analyzed']}")
    print(f"Total Conflicts: {analysis['total_conflicts']}")
    print(f"  - Critical: {analysis['critical']}")
    print(f"  - High: {analysis['high']}")
    print(f"  - Medium: {analysis['medium']}")
    print(f"  - Low: {analysis['low']}")

    if analysis['total_conflicts'] > 0:
        print("✅ PASS: System-wide analysis detected conflicts")
        return True
    else:
        print("❌ FAIL: System-wide analysis found no conflicts (expected some)")
        return False


def test_resolution_suggestions():
    """TEST 7: Resolution Suggestions Provided"""
    print("\n" + "="*70)
    print("TEST 7: Resolution Suggestions Provided")
    print("="*70)

    db = MockDB()

    existing = MockPolicy(
        policy_id=1,
        policy_name="Deny All",
        effect="deny",
        actions=["write"],
        resources=["database:*"],
        priority=100
    )
    db.add_policy(existing)

    detector = PolicyConflictDetector(db)

    new_policy = {
        "id": 0,
        "policy_name": "Allow Some",
        "effect": "permit",
        "actions": ["write"],
        "resources": ["database:prod:*"],
        "priority": 90
    }

    conflicts = detector.detect_conflicts(new_policy)

    if len(conflicts) > 0 and len(conflicts[0].resolution_suggestions) > 0:
        print("✅ PASS: Resolution suggestions provided")
        print(f"   Suggestions:")
        for i, suggestion in enumerate(conflicts[0].resolution_suggestions[:3], 1):
            print(f"     {i}. {suggestion}")
        return True
    else:
        print("❌ FAIL: No resolution suggestions")
        return False


def run_all_tests():
    """Run all functional tests"""

    print("\n" + "="*80)
    print("POLICY CONFLICT DETECTION - FUNCTIONAL TEST SUITE")
    print("="*80)

    tests = [
        ("Effect Contradiction", test_effect_conflict),
        ("Priority Conflict", test_priority_conflict),
        ("Wildcard Matching", test_wildcard_matching),
        ("No False Positives", test_no_conflict_different_resources),
        ("Condition Mismatch", test_condition_mismatch),
        ("System-Wide Analysis", test_system_wide_analysis),
        ("Resolution Suggestions", test_resolution_suggestions)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("="*80)
    print(f"Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("="*80 + "\n")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Conflict Detection is WORKING!\n")
        return True
    else:
        print(f"⚠️  {total-passed} test(s) failed - Review failures above\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
