"""
Critical Path Integration Tests - Final Version
Uses shared fixtures from conftest.py
"""
import pytest
from sqlalchemy import text

class TestCriticalWorkflows:
    """Critical path tests with proper fixtures"""
    
    def test_database_connectivity(self, db_session):
        """Test: Database is accessible"""
        result = db_session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1
    
    def test_nist_controls_loaded(self, db_session):
        """Test: NIST controls exist"""
        control_count = db_session.execute(text(
            "SELECT COUNT(*) FROM nist_controls"
        )).fetchone()[0]
        
        assert control_count >= 40
        
        # Verify critical controls
        critical = db_session.execute(text("""
            SELECT control_id FROM nist_controls 
            WHERE control_id IN ('AC-1', 'AU-2', 'SI-4')
        """)).fetchall()
        
        assert len(critical) == 3
    
    def test_mitre_framework_loaded(self, db_session):
        """Test: MITRE ATT&CK data is complete"""
        tactic_count = db_session.execute(text(
            "SELECT COUNT(*) FROM mitre_tactics"
        )).fetchone()[0]
        assert tactic_count == 14
        
        technique_count = db_session.execute(text(
            "SELECT COUNT(*) FROM mitre_techniques"
        )).fetchone()[0]
        assert technique_count >= 30
    
    def test_cvss_assessments_valid(self, db_session):
        """Test: CVSS assessments have valid scores (now with fix)"""
        assessments = db_session.execute(text("""
            SELECT base_score, severity, vector_string 
            FROM cvss_assessments
        """)).fetchall()
        
        assert len(assessments) > 0
        
        for assessment in assessments:
            score, severity, vector = assessment
            # With fix, all scores should be <= 10.0
            assert 0.0 <= float(score) <= 10.0, f"Invalid score: {score}"
            assert severity in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert vector.startswith("CVSS:3.1/")
    
    def test_approver_hierarchy(self, db_session):
        """Test: Approver hierarchy configured"""
        approvers = db_session.execute(text("""
            SELECT email, approval_level, is_emergency_approver
            FROM users 
            WHERE approval_level > 0
        """)).fetchall()
        
        assert len(approvers) >= 1
        
        emergency_approvers = [a for a in approvers if a[2]]
        assert len(emergency_approvers) >= 1
    
    def test_workflow_infrastructure(self, db_session):
        """Test: Workflow tables queryable"""
        db_session.execute(text("SELECT id FROM workflow_executions LIMIT 1"))
        db_session.execute(text("SELECT id FROM agent_actions LIMIT 1"))
        
        nist_mappings = db_session.execute(text(
            "SELECT COUNT(*) FROM nist_control_mappings"
        )).fetchone()[0]
        
        mitre_mappings = db_session.execute(text(
            "SELECT COUNT(*) FROM mitre_technique_mappings"
        )).fetchone()[0]
        
        assert nist_mappings > 0
        assert mitre_mappings > 0
    
    def test_policy_enforcement_endpoint(self, test_client, auth_headers):
        """Test: Policy enforcement API works"""
        action_data = {
            "action_type": "database_write",
            "resource": "users_table",
            "risk_score": 65,
            "department": "Engineering"
        }
        
        response = test_client.post(
            "/api/governance/policies/enforce",
            json=action_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "decision" in result
        assert result["decision"] in ["ALLOW", "DENY", "REQUIRE_APPROVAL"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
