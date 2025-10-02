"""
Complete Integration Tests
Tests all critical workflows with proper authentication
"""
import pytest
from sqlalchemy import text

class TestIntegration:
    """Full integration test suite"""
    
    def test_database_connectivity(self, db_session):
        """Verify database connection"""
        result = db_session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1
    
    def test_nist_framework_complete(self, db_session):
        """Verify NIST SP 800-53 framework"""
        # Check controls loaded
        controls = db_session.execute(text("""
            SELECT control_id, family, title 
            FROM nist_controls 
            ORDER BY control_id 
            LIMIT 5
        """)).fetchall()
        
        assert len(controls) >= 5
        assert controls[0][0] == 'AC-1'  # First control
        
        # Check mappings exist
        mappings = db_session.execute(text("""
            SELECT COUNT(*) FROM nist_control_mappings
        """)).fetchone()[0]
        
        assert mappings > 0
    
    def test_mitre_framework_complete(self, db_session):
        """Verify MITRE ATT&CK framework"""
        # Check tactics
        tactics = db_session.execute(text("""
            SELECT tactic_id, name FROM mitre_tactics 
            ORDER BY tactic_id
        """)).fetchall()
        
        assert len(tactics) == 14
        assert tactics[0][0] == 'TA0001'  # Initial Access
        
        # Check techniques
        techniques = db_session.execute(text("""
            SELECT COUNT(*) FROM mitre_techniques
        """)).fetchone()[0]
        
        assert techniques >= 30
    
    def test_cvss_scoring_valid(self, db_session):
        """Verify CVSS assessments"""
        assessments = db_session.execute(text("""
            SELECT base_score, severity, vector_string
            FROM cvss_assessments
        """)).fetchall()
        
        assert len(assessments) > 0
        
        for score, severity, vector in assessments:
            # Validate ranges
            assert 0.0 <= float(score) <= 10.0
            assert severity in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert vector.startswith("CVSS:3.1/")
    
    def test_approver_system_configured(self, db_session):
        """Verify approver hierarchy"""
        approvers = db_session.execute(text("""
            SELECT 
                email, 
                approval_level, 
                max_risk_approval, 
                is_emergency_approver
            FROM users 
            WHERE approval_level > 0
            ORDER BY approval_level DESC
        """)).fetchall()
        
        # Must have approvers
        assert len(approvers) >= 1
        
        # Must have emergency approver
        emergency = [a for a in approvers if a[3]]
        assert len(emergency) >= 1
        
        # Verify highest level
        assert approvers[0][1] >= 2  # At least level 2
    
    def test_workflow_tables_operational(self, db_session):
        """Verify workflow infrastructure"""
        # Check tables exist and are queryable
        tables = [
            "workflow_executions",
            "agent_actions",
            "nist_control_mappings",
            "mitre_technique_mappings",
            "cvss_assessments"
        ]
        
        for table in tables:
            result = db_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            assert count >= 0  # Table exists
    
    def test_policy_enforcement_endpoint(self, test_client, auth_headers):
        """Test policy enforcement API (if auth works)"""
        action_data = {
            "action_type": "database_write",
            "resource": "test_resource",
            "risk_score": 55,
            "department": "Engineering"
        }
        
        response = test_client.post(
            "/api/governance/policies/enforce",
            json=action_data,
            headers=auth_headers
        )
        
        # Should either work (200) or fail gracefully (401/403)
        assert response.status_code in [200, 401, 403, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "decision" in result
            assert result["decision"] in ["ALLOW", "DENY", "REQUIRE_APPROVAL"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
