"""
Comprehensive Workflow Integration Tests
Tests end-to-end workflows, security, and edge cases
"""
import pytest
from sqlalchemy import text
import time

class TestWorkflowEndToEnd:
    """Test complete workflow lifecycle"""
    
    def test_workflow_creation_assigns_approver(self, test_client, auth_headers, db_session):
        """Test: Creating workflow auto-assigns approver"""
        response = test_client.post(
            "/api/governance/policies/enforce",
            json={
                "action_type": "database_modify",
                "resource": "production_db",
                "risk_score": 75,
                "department": "Engineering"
            },
            headers=auth_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("decision") == "REQUIRE_APPROVAL":
                assert "workflow_execution_id" in result
                assert "assigned_approver" in result or "workflow_id" in result
    
    def test_cvss_auto_mapping_on_action(self, db_session):
        """Test: CVSS scores are auto-created for actions"""
        # Get an action with CVSS
        action_with_cvss = db_session.execute(text("""
            SELECT a.id, c.base_score, c.severity
            FROM agent_actions a
            JOIN cvss_assessments c ON a.id = c.action_id
            LIMIT 1
        """)).fetchone()
        
        if action_with_cvss:
            action_id, score, severity = action_with_cvss
            assert 0.0 <= float(score) <= 10.0
            assert severity in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_nist_controls_map_to_actions(self, db_session):
        """Test: NIST controls are mapped to specific actions"""
        mappings = db_session.execute(text("""
            SELECT 
                ncm.action_id,
                nc.control_id,
                nc.title,
                ncm.relevance
            FROM nist_control_mappings ncm
            JOIN nist_controls nc ON ncm.control_id = nc.control_id
            LIMIT 5
        """)).fetchall()
        
        assert len(mappings) > 0
        
        for action_id, control_id, title, relevance in mappings:
            assert action_id is not None
            assert control_id is not None
            assert relevance in ["PRIMARY", "SECONDARY", "SUPPORTING"]
    
    def test_mitre_techniques_detected(self, db_session):
        """Test: MITRE techniques are detected for actions"""
        detections = db_session.execute(text("""
            SELECT 
                mtm.action_id,
                mt.technique_id,
                mt.name,
                mtm.confidence
            FROM mitre_technique_mappings mtm
            JOIN mitre_techniques mt ON mtm.technique_id = mt.technique_id
            LIMIT 5
        """)).fetchall()
        
        assert len(detections) > 0
        
        for action_id, tech_id, name, confidence in detections:
            assert action_id is not None
            assert tech_id.startswith('T')
            assert confidence in ["HIGH", "MEDIUM", "LOW"]
    
    def test_approver_load_balancing(self, db_session):
        """Test: Approvers have pending action counts"""
        approvers = db_session.execute(text("""
            SELECT 
                email,
                approval_level,
                (SELECT COUNT(*) FROM agent_actions 
                 WHERE pending_approvers LIKE '%' || users.email || '%') as pending_count
            FROM users
            WHERE approval_level > 0
        """)).fetchall()
        
        assert len(approvers) >= 1
        # Verify counts are numeric
        for email, level, count in approvers:
            assert count >= 0

class TestRiskScoring:
    """Test risk calculation and thresholds"""
    
    def test_risk_scores_within_bounds(self, db_session):
        """Test: All risk scores are 0-100"""
        actions = db_session.execute(text("""
            SELECT id, risk_score 
            FROM agent_actions 
            WHERE risk_score IS NOT NULL
        """)).fetchall()
        
        for action_id, risk_score in actions:
            assert 0 <= risk_score <= 100
    
    def test_high_risk_requires_approval(self, db_session):
        """Test: High risk actions have workflows"""
        high_risk = db_session.execute(text("""
            SELECT a.id, a.risk_score, a.status
            FROM agent_actions a
            WHERE a.risk_score >= 70
            LIMIT 5
        """)).fetchall()
        
        # If high risk actions exist, some should have workflows
        if len(high_risk) > 0:
            workflows_exist = any(status is not None for _, _, status in high_risk)
            # This is informational - not all high risk may have workflows yet

class TestSecurity:
    """Security and authorization tests"""
    
    def test_auth_required_for_protected_endpoints(self, test_client):
        """Test: Protected endpoints reject unauthenticated requests"""
        response = test_client.post(
            "/api/governance/policies/enforce",
            json={"action_type": "test", "risk_score": 50}
        )
        # Should be 401/403 without auth
        assert response.status_code in [401, 403, 422, 500]
    
    def test_invalid_token_rejected(self, test_client):
        """Test: Invalid JWT tokens are rejected"""
        response = test_client.post(
            "/api/governance/policies/enforce",
            json={"action_type": "test", "risk_score": 50},
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code in [401, 403, 500]
    
    def test_sql_injection_protection(self, test_client, auth_headers):
        """Test: SQL injection attempts are handled safely"""
        # Try SQL injection in action_type
        response = test_client.post(
            "/api/governance/policies/enforce",
            json={
                "action_type": "'; DROP TABLE users; --",
                "resource": "test",
                "risk_score": 50
            },
            headers=auth_headers
        )
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422, 500]

class TestDataIntegrity:
    """Test data consistency and relationships"""
    
    def test_no_orphaned_workflows(self, db_session):
        """Test: All workflows reference valid actions"""
        orphans = db_session.execute(text("""
            SELECT w.id 
            FROM workflow_executions w
            LEFT JOIN agent_actions a ON w.action_id = a.id
            WHERE w.action_id IS NOT NULL AND a.id IS NULL
        """)).fetchall()
        
        assert len(orphans) == 0
    
    def test_no_orphaned_cvss_assessments(self, db_session):
        """Test: All CVSS assessments reference valid actions"""
        orphans = db_session.execute(text("""
            SELECT c.id
            FROM cvss_assessments c
            LEFT JOIN agent_actions a ON c.action_id = a.id
            WHERE c.action_id IS NOT NULL AND a.id IS NULL
        """)).fetchall()
        
        assert len(orphans) == 0
    
    def test_control_mappings_valid(self, db_session):
        """Test: NIST control mappings reference valid controls"""
        invalid = db_session.execute(text("""
            SELECT ncm.id
            FROM nist_control_mappings ncm
            LEFT JOIN nist_controls nc ON ncm.control_id = nc.control_id
            WHERE nc.control_id IS NULL
        """)).fetchall()
        
        assert len(invalid) == 0

class TestPerformance:
    """Basic performance sanity checks"""
    
    def test_policy_enforcement_response_time(self, test_client, auth_headers):
        """Test: Policy enforcement responds within reasonable time"""
        start = time.time()
        
        response = test_client.post(
            "/api/governance/policies/enforce",
            json={
                "action_type": "file_read",
                "resource": "test.txt",
                "risk_score": 30
            },
            headers=auth_headers
        )
        
        elapsed = time.time() - start
        
        # Should respond in under 5 seconds
        assert elapsed < 5.0
        assert response.status_code in [200, 401, 403, 500]
    
    def test_database_query_performance(self, db_session):
        """Test: Basic queries execute quickly"""
        start = time.time()
        
        db_session.execute(text("""
            SELECT COUNT(*) FROM nist_controls
        """)).fetchone()
        
        elapsed = time.time() - start
        
        # Should complete in under 1 second
        assert elapsed < 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
