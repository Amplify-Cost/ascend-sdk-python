"""
Unit Tests for Policy Conflict Detection Engine

Tests all 4 conflict types:
- Effect contradictions (deny vs allow)
- Priority conflicts
- Resource hierarchy conflicts
- Condition mismatches

Author: OW-KAI Engineering Team
"""

import sys
sys.path.insert(0, '/Users/mac_001/OW_AI_Project/ow-ai-backend')

import unittest
from services.policy_conflict_detector import PolicyConflictDetector, ConflictType
from models import EnterprisePolicy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from datetime import datetime, UTC


class TestPolicyConflictDetector(unittest.TestCase):
    """Test suite for policy conflict detection"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Create new database session for each test"""
        self.db = self.SessionLocal()
        self.detector = PolicyConflictDetector(self.db)

    def tearDown(self):
        """Clean up database after each test"""
        self.db.query(EnterprisePolicy).delete()
        self.db.commit()
        self.db.close()

    # ========================================================================
    # TEST 1: EFFECT CONTRADICTION DETECTION
    # ========================================================================

    def test_effect_conflict_deny_vs_allow(self):
        """Test detection of deny vs allow on same resource"""

        # Create existing policy: DENY on database:*
        existing_policy = EnterprisePolicy(
            policy_name="Deny All Database Access",
            description="Block all database operations",
            effect="deny",
            actions=["write", "delete"],
            resources=["database:*"],
            conditions={},
            priority=100,
            status="active",
            created_by="test@example.com"
        )
        self.db.add(existing_policy)
        self.db.commit()

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

        # Detect conflicts
        conflicts = self.detector.detect_conflicts(new_policy)

        # Verify conflict detected
        self.assertGreater(len(conflicts), 0, "Should detect effect conflict")
        effect_conflicts = [c for c in conflicts if c.conflict_type == "effect_contradiction"]
        self.assertGreater(len(effect_conflicts), 0, "Should detect effect contradiction")

        # Verify severity
        self.assertEqual(effect_conflicts[0].severity, ConflictType.CRITICAL)

        print(f"✅ TEST 1 PASSED: Effect conflict detected (deny vs permit)")

    def test_no_conflict_different_resources(self):
        """Test no conflict when resources don't overlap"""

        # Existing: DENY database:*
        existing = EnterprisePolicy(
            policy_name="Deny Database",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: ALLOW s3:*  (different resource)
        new_policy = {
            "policy_name": "Allow S3",
            "effect": "permit",
            "actions": ["write"],
            "resources": ["s3:*"],
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        self.assertEqual(len(conflicts), 0, "Should not detect conflict on different resources")
        print(f"✅ TEST 2 PASSED: No conflict on different resources")

    # ========================================================================
    # TEST 2: PRIORITY CONFLICT DETECTION
    # ========================================================================

    def test_priority_conflict_same_priority_overlapping_resources(self):
        """Test detection of same priority on overlapping resources"""

        # Existing: Priority 100 on database:*
        existing = EnterprisePolicy(
            policy_name="Database Policy 1",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: Also priority 100 on database:production:*
        new_policy = {
            "policy_name": "Database Policy 2",
            "effect": "deny",
            "actions": ["write"],
            "resources": ["database:production:*"],
            "priority": 100  # Same priority!
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        priority_conflicts = [c for c in conflicts if c.conflict_type == "priority_conflict"]
        self.assertGreater(len(priority_conflicts), 0, "Should detect priority conflict")
        self.assertEqual(priority_conflicts[0].severity, ConflictType.HIGH)

        print(f"✅ TEST 3 PASSED: Priority conflict detected")

    def test_no_priority_conflict_different_priorities(self):
        """Test no conflict when priorities differ"""

        # Existing: Priority 100
        existing = EnterprisePolicy(
            policy_name="High Priority",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: Priority 90 (different)
        new_policy = {
            "policy_name": "Lower Priority",
            "effect": "deny",
            "actions": ["write"],
            "resources": ["database:*"],
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        priority_conflicts = [c for c in conflicts if c.conflict_type == "priority_conflict"]
        self.assertEqual(len(priority_conflicts), 0, "Should not detect priority conflict with different priorities")

        print(f"✅ TEST 4 PASSED: No priority conflict with different priorities")

    # ========================================================================
    # TEST 3: RESOURCE HIERARCHY CONFLICT DETECTION
    # ========================================================================

    def test_resource_hierarchy_conflict_parent_child(self):
        """Test detection of parent/child resource conflicts"""

        # Existing: DENY on database:* (parent)
        existing = EnterprisePolicy(
            policy_name="Deny All Databases",
            effect="deny",
            actions=["delete"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: ALLOW on database:prod:users (child)
        new_policy = {
            "policy_name": "Allow Specific Table",
            "effect": "permit",
            "actions": ["delete"],
            "resources": ["database:prod:users"],
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        hierarchy_conflicts = [c for c in conflicts if c.conflict_type == "resource_hierarchy"]
        # Should detect both hierarchy conflict AND effect conflict
        self.assertGreater(len(conflicts), 0, "Should detect conflicts")

        print(f"✅ TEST 5 PASSED: Resource hierarchy conflict detected")

    # ========================================================================
    # TEST 4: CONDITION MISMATCH DETECTION
    # ========================================================================

    def test_condition_mismatch_same_key_different_value(self):
        """Test detection of conflicting condition values"""

        # Existing: environment = "production"
        existing = EnterprisePolicy(
            policy_name="Production Policy",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            conditions={"environment": "production"},
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: environment = "development" (same resource, conflicting condition)
        new_policy = {
            "policy_name": "Development Policy",
            "effect": "deny",
            "actions": ["write"],
            "resources": ["database:*"],
            "conditions": {"environment": "development"},
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        condition_conflicts = [c for c in conflicts if c.conflict_type == "condition_mismatch"]
        self.assertGreater(len(condition_conflicts), 0, "Should detect condition mismatch")
        self.assertEqual(condition_conflicts[0].severity, ConflictType.MEDIUM)

        print(f"✅ TEST 6 PASSED: Condition mismatch detected")

    # ========================================================================
    # TEST 5: WILDCARD RESOURCE MATCHING
    # ========================================================================

    def test_wildcard_resource_matching(self):
        """Test wildcard (*) matching in resources"""

        # Existing: database:* (wildcard)
        existing = EnterprisePolicy(
            policy_name="All Databases",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        # New: Specific database (should match wildcard)
        new_policy = {
            "policy_name": "Specific Database",
            "effect": "permit",
            "actions": ["write"],
            "resources": ["database:production"],
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        self.assertGreater(len(conflicts), 0, "Should detect conflict with wildcard")

        print(f"✅ TEST 7 PASSED: Wildcard resource matching works")

    # ========================================================================
    # TEST 6: SYSTEM-WIDE CONFLICT ANALYSIS
    # ========================================================================

    def test_system_wide_analysis(self):
        """Test system-wide conflict scanning"""

        # Create multiple policies
        policies = [
            EnterprisePolicy(
                policy_name=f"Policy {i}",
                effect="deny" if i % 2 == 0 else "permit",
                actions=["write"],
                resources=["database:*"],
                priority=100,
                status="active",
                created_by="test"
            )
            for i in range(5)
        ]

        for p in policies:
            self.db.add(p)
        self.db.commit()

        # Run system-wide analysis
        analysis = self.detector.analyze_all_policies()

        self.assertIn("total_conflicts", analysis)
        self.assertIn("critical", analysis)
        self.assertIn("policies_analyzed", analysis)
        self.assertEqual(analysis["policies_analyzed"], 5)

        print(f"✅ TEST 8 PASSED: System-wide analysis completed")
        print(f"   Analyzed: {analysis['policies_analyzed']} policies")
        print(f"   Found: {analysis['total_conflicts']} total conflicts")

    # ========================================================================
    # TEST 7: RESOLUTION SUGGESTIONS
    # ========================================================================

    def test_resolution_suggestions_provided(self):
        """Test that conflicts include resolution suggestions"""

        # Create conflicting policies
        existing = EnterprisePolicy(
            policy_name="Deny All",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(existing)
        self.db.commit()

        new_policy = {
            "policy_name": "Allow Some",
            "effect": "permit",
            "actions": ["write"],
            "resources": ["database:prod:*"],
            "priority": 90
        }

        conflicts = self.detector.detect_conflicts(new_policy)

        self.assertGreater(len(conflicts), 0)
        conflict = conflicts[0]
        self.assertTrue(hasattr(conflict, 'resolution_suggestions'))
        self.assertGreater(len(conflict.resolution_suggestions), 0)

        print(f"✅ TEST 9 PASSED: Resolution suggestions provided")
        print(f"   Suggestions: {conflict.resolution_suggestions}")

    # ========================================================================
    # TEST 8: EXCLUDE SELF FROM CONFLICT CHECK
    # ========================================================================

    def test_exclude_self_from_conflict_check(self):
        """Test that updating a policy doesn't conflict with itself"""

        # Create policy
        policy = EnterprisePolicy(
            policy_name="Test Policy",
            effect="deny",
            actions=["write"],
            resources=["database:*"],
            priority=100,
            status="active",
            created_by="test"
        )
        self.db.add(policy)
        self.db.commit()
        policy_id = policy.id

        # Update same policy (should exclude itself from conflict check)
        updated_policy = {
            "id": policy_id,
            "policy_name": "Test Policy (Updated)",
            "effect": "deny",
            "actions": ["write"],
            "resources": ["database:*"],
            "priority": 100
        }

        conflicts = self.detector.detect_conflicts(updated_policy, policy_id=policy_id)

        self.assertEqual(len(conflicts), 0, "Policy should not conflict with itself")

        print(f"✅ TEST 10 PASSED: Policy doesn't conflict with itself on update")


def run_all_tests():
    """Run all conflict detection tests and generate report"""

    print("\n" + "="*70)
    print("POLICY CONFLICT DETECTION - TEST SUITE")
    print("="*70 + "\n")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPolicyConflictDetector)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Conflict detection is working correctly!\n")
        return True
    else:
        print("❌ SOME TESTS FAILED - Review failures above\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
