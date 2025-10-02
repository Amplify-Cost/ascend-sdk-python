"""
Critical Path Integration Tests
Tests core platform functionality without mocking
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from main import app
from database import SQLALCHEMY_DATABASE_URL
import os

os.environ['DATABASE_URL'] = SQLALCHEMY_DATABASE_URL

client = TestClient(app)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class TestCriticalWorkflows:
    """Critical path tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers with correct password"""
        response = client.post("/auth/token", json={
            "email": "admin@owkai.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Auth failed: {response.text}"
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_database_connectivity(self):
        """Test: Database is accessible"""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1
        finally:
            db.close()
    
    def test_nist_controls_loaded(self):
        """Test: NIST controls exist and are properly structured"""
        db = SessionLocal()
        try:
            control_count = db.execute(text(
                "SELECT COUNT(*) FROM nist_controls"
            )).fetchone()[0]
            
            assert control_count >= 40, f"Expected 40+ NIST controls, found {control_count}"
            
            # Verify critical controls exist
            critical = db.execute(text("""
                SELECT control_id FROM nist_controls 
                WHERE control_id IN ('AC-1', 'AU-2', 'SI-4')
            """)).fetchall()
            
            assert len(critical) == 3, "Missing critical NIST controls"
            
        finally:
            db.close()
    
    def test_mitre_framework_loaded(self):
        """Test: MITRE ATT&CK data is complete"""
        db = SessionLocal()
        try:
            # Check tactics
            tactic_count = db.execute(text(
                "SELECT COUNT(*) FROM mitre_tactics"
            )).fetchone()[0]
            assert tactic_count == 14
            
            # Check techniques
            technique_count = db.execute(text(
                "SELECT COUNT(*) FROM mitre_techniques"
            )).fetchone()[0]
            assert technique_count >= 30
            
            # Verify critical tactics exist
            critical_tactics = db.execute(text("""
                SELECT tactic_id FROM mitre_tactics 
                WHERE tactic_id IN ('TA0001', 'TA0010', 'TA0040')
            """)).fetchall()
            assert len(critical_tactics) == 3
            
        finally:
            db.close()
    
    def test_cvss_assessments_valid(self):
        """Test: CVSS assessments have valid scores"""
        db = SessionLocal()
        try:
            assessments = db.execute(text("""
                SELECT base_score, severity, vector_string 
                FROM cvss_assessments
            """)).fetchall()
            
            assert len(assessments) > 0, "No CVSS assessments found"
            
            for assessment in assessments:
                score, severity, vector = assessment
                # Validate score range
                assert 0.0 <= score <= 10.0
                # Validate severity
                assert severity in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
                # Validate vector format
                assert vector.startswith("CVSS:3.1/")
                
        finally:
            db.close()
    
    def test_approver_hierarchy(self):
        """Test: Approver hierarchy is properly configured"""
        db = SessionLocal()
        try:
            approvers = db.execute(text("""
                SELECT email, approval_level, max_risk_approval, is_emergency_approver
                FROM users 
                WHERE approval_level > 0
                ORDER BY approval_level DESC
            """)).fetchall()
            
            assert len(approvers) >= 1, "Need at least 1 approver"
            
            # Find emergency approver
            emergency_approvers = [a for a in approvers if a[3]]
            assert len(emergency_approvers) >= 1, "Need emergency approver"
            
            # Verify approval levels are valid
            for approver in approvers:
                assert 1 <= approver[1] <= 5
                assert approver[2] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                
        finally:
            db.close()
    
    def test_workflow_infrastructure(self):
        """Test: Workflow tables exist and are queryable"""
        db = SessionLocal()
        try:
            # Test workflow_executions
            db.execute(text("SELECT id FROM workflow_executions LIMIT 1"))
            
            # Test agent_actions
            db.execute(text("SELECT id FROM agent_actions LIMIT 1"))
            
            # Test control mappings
            nist_mappings = db.execute(text(
                "SELECT COUNT(*) FROM nist_control_mappings"
            )).fetchone()[0]
            
            mitre_mappings = db.execute(text(
                "SELECT COUNT(*) FROM mitre_technique_mappings"
            )).fetchone()[0]
            
            assert nist_mappings > 0, "Need NIST control mappings"
            assert mitre_mappings > 0, "Need MITRE technique mappings"
            
        finally:
            db.close()
    
    def test_policy_enforcement_endpoint(self, auth_headers):
        """Test: Policy enforcement API works end-to-end"""
        action_data = {
            "action_type": "database_write",
            "resource": "users_table",
            "risk_score": 65,
            "department": "Engineering"
        }
        
        response = client.post(
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
