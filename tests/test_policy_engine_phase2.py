"""
Phase 2 Policy Engine Tests - Validation & Error Handling
"""
import pytest
from services.cedar_enforcement_service import (
    PolicyCompiler, 
    PolicyValidationError,
    EnforcementEngine,
    CedarStylePolicy
)

class TestPolicyValidation:
    """Test input validation"""
    
    def test_empty_policy_rejected(self):
        """Empty policy should raise error"""
        with pytest.raises(PolicyValidationError):
            PolicyCompiler.compile("")
    
    def test_whitespace_only_rejected(self):
        """Whitespace-only policy should raise error"""
        with pytest.raises(PolicyValidationError):
            PolicyCompiler.compile("   \n  \t  ")
    
    def test_too_short_rejected(self):
        """Policy under 10 chars should raise error"""
        with pytest.raises(PolicyValidationError):
            PolicyCompiler.compile("deny all")
    
    def test_no_action_keyword_rejected(self):
        """Policy without action should raise error"""
        with pytest.raises(PolicyValidationError):
            PolicyCompiler.compile("this is some random text about databases")
    
    def test_valid_deny_policy(self):
        """Valid deny policy should compile"""
        result = PolicyCompiler.compile("Deny delete access to production database")
        assert result["effect"] == "deny"
        assert "delete" in result["actions"]
    
    def test_valid_approval_policy(self):
        """Valid approval policy should compile"""
        result = PolicyCompiler.compile("Require manager approval for modifying customer data")
        assert result["effect"] == "require_approval"
        assert "modify" in result["actions"]
    
    def test_valid_permit_policy(self):
        """Valid permit policy should compile"""
        result = PolicyCompiler.compile("Allow read access to public documentation files")
        assert result["effect"] == "permit"
        assert "read" in result["actions"]

class TestErrorHandling:
    """Test error handling in enforcement engine"""
    
    def test_evaluate_with_empty_principal(self):
        """Empty principal should fail closed (deny)"""
        engine = EnforcementEngine()
        result = engine.evaluate("", "read", "database")
        assert result["decision"] == "DENY"
        assert "error" in result
    
    def test_evaluate_with_empty_action(self):
        """Empty action should fail closed"""
        engine = EnforcementEngine()
        result = engine.evaluate("user:123", "", "database")
        assert result["decision"] == "DENY"
    
    def test_evaluate_with_empty_resource(self):
        """Empty resource should fail closed"""
        engine = EnforcementEngine()
        result = engine.evaluate("user:123", "read", "")
        assert result["decision"] == "DENY"
    
    def test_evaluate_with_malformed_policy(self):
        """Engine should handle malformed policies gracefully"""
        engine = EnforcementEngine()
        
        # Load a policy with missing fields
        malformed_policy = {
            "id": "test-1",
            "effect": "deny",
            # Missing actions and resources
        }
        engine.load_policies([malformed_policy])
        
        # Should not crash
        result = engine.evaluate("user:123", "read", "database")
        assert "decision" in result

class TestEdgeCases:
    """Test edge cases"""
    
    def test_compile_multiple_actions(self):
        """Should extract multiple action types"""
        result = PolicyCompiler.compile(
            "Deny read, write, and delete access to financial data"
        )
        assert len(result["actions"]) >= 2
        assert "read" in result["actions"] or "delete" in result["actions"]
    
    def test_compile_multiple_resources(self):
        """Should extract multiple resource types"""
        result = PolicyCompiler.compile(
            "Block access to production database and S3 buckets"
        )
        assert len(result["resources"]) >= 1
    
    def test_evaluate_no_policies_loaded(self):
        """Evaluation with no policies should allow"""
        engine = EnforcementEngine()
        result = engine.evaluate("user:123", "read", "file")
        assert result["decision"] == "ALLOW"
    
    def test_evaluate_caching_works(self):
        """Repeated evaluations should use cache"""
        engine = EnforcementEngine()
        
        # First evaluation
        result1 = engine.evaluate("user:123", "read", "database")
        hits_before = engine.stats["cache_hits"]
        
        # Second evaluation (same inputs)
        result2 = engine.evaluate("user:123", "read", "database")
        hits_after = engine.stats["cache_hits"]
        
        assert hits_after > hits_before
        assert result1["decision"] == result2["decision"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
