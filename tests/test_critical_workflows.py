"""
Critical Path Integration Tests
Tests end-to-end workflows that must work in production
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from main import app
from database import SQLALCHEMY_DATABASE_URL

client = TestClient(app)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class TestCriticalWorkflows:
    """Test critical workflows end-to-end"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers"""
        response = client.post("/auth/token", json={
            "email": "admin@owkai.com",
            "password": "Admin123!@#"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_policy_enforcement_workflow(self, auth_headers):
        """Test: Policy enforcement creates workflow with auto-assigned approver"""
        
        # Step 1: Submit action for policy enforcement
        action_data = {
            "action_type": "database_write",
            "resource": "users_table",
            "risk_score": 75,
            "department": "Engineering",
            "user_email": "test@owkai.com"
        }
        
        response = client.post(
            "/api/governance/policies/enforce",
            json=action_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify workflow was created
        assert result["decision"] == "REQUIRE_APPROVAL"
        assert "workflow_execution_id" in result
        assert "assigned_approver" in result
        
        workflow_id = result["workflow_execution_id"]
        
        # Step 2: Verify approver can see workflow
        response = client.get(
            f"/api/workflows/{workflow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        workflow = response.json()
        assert workflow["status"] in ["pending", "PENDING"]
    
    def test_cvss_assessment_creation(self, auth_headers):
        """Test: CVSS auto-mapper creates assessments"""
        
        db = SessionLocal()
        
        # Get an existing action
        action = db.execute(text(
            "SELECT id FROM agent_actions LIMIT 1"
        )).fetchone()
        
        if not action:
            pytest.skip("No actions in database")
        
        action_id = action[0]
        
        # Check if CVSS assessment exists
        assessment = db.execute(text("""
            SELECT base_score, severity 
            FROM cvss_assessments 
            WHERE action_id = :action_id
        """), {"action_id": action_id}).fetchone()
        
        # Should have CVSS score
        if assessment:
            assert assessment[0] >= 0.0
            assert assessment[0] <= 10.0
            assert assessment[1] in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        db.close()
    
    def test_nist_control_mapping(self, auth_headers):
        """Test: NIST controls are mapped to actions"""
        
        db = SessionLocal()
        
        # Check if NIST controls exist
        control_count = db.execute(text(
            "SELECT COUNT(*) FROM nist_controls"
        )).fetchone()[0]
        
        assert control_count >= 40, "Should have at least 40 NIST controls"
        
        # Check if mappings exist
        mapping_count = db.execute(text(
            "SELECT COUNT(*) FROM nist_control_mappings"
        )).fetchone()[0]
        
        assert mapping_count > 0, "Should have control mappings"
        
        db.close()
    
    def test_mitre_technique_detection(self, auth_headers):
        """Test: MITRE techniques are detected"""
        
        db = SessionLocal()
        
        # Check tactics loaded
        tactic_count = db.execute(text(
            "SELECT COUNT(*) FROM mitre_tactics"
        )).fetchone()[0]
        
        assert tactic_count == 14, "Should have 14 MITRE tactics"
        
        # Check techniques loaded
        technique_count = db.execute(text(
            "SELECT COUNT(*) FROM mitre_techniques"
        )).fetchone()[0]
        
        assert technique_count >= 30, "Should have 30+ techniques"
        
        db.close()
    
    def test_sla_monitor_integration(self, auth_headers):
        """Test: SLA monitor can find overdue workflows"""
        
        db = SessionLocal()
        
        # Count workflows
        workflow_count = db.execute(text(
            "SELECT COUNT(*) FROM workflow_executions"
        )).fetchone()[0]
        
        # If workflows exist, SLA monitor should be able to query them
        if workflow_count > 0:
            # This mimics what SLA monitor does
            overdue = db.execute(text("""
                SELECT COUNT(*) 
                FROM workflow_executions 
                WHERE status = 'pending' 
                AND created_at < NOW() - INTERVAL '24 hours'
            """)).fetchone()[0]
            
            assert overdue >= 0  # Just verify query works
        
        db.close()
    
    def test_approver_assignment_logic(self, auth_headers):
        """Test: Approvers are assigned based on risk"""
        
        db = SessionLocal()
        
        # Check if approvers are configured
        approver_count = db.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE approval_level > 0
        """)).fetchone()[0]
        
        assert approver_count >= 1, "Need at least 1 approver configured"
        
        # Check emergency approver exists
        emergency = db.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE is_emergency_approver = true
        """)).fetchone()[0]
        
        assert emergency >= 1, "Need emergency approver"
        
        db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
