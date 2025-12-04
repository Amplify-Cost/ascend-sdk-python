"""
SEC-064: Enterprise Risk Pipeline Unit Tests

Comprehensive test suite for the unified enterprise risk assessment pipeline.
These tests ensure regression-free updates and validate compliance requirements.

Compliance:
- SOC 2 CC8.1: Testing requirements for change management
- PCI-DSS 6.5: Secure development testing
- NIST 800-53 SA-11: Developer Security Testing

Document ID: SEC-064-TESTS
Publisher: OW-kai Corporation
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, UTC
from dataclasses import asdict

# Import the module under test
from services.enterprise_risk_pipeline import (
    EnterpriseRiskPipeline,
    EnterpriseRiskResult,
    CVSSResult,
    ComplianceMapping,
    PolicyEvaluation,
    RiskFusion,
    AutomationResult,
    get_enterprise_risk_pipeline
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.flush = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_action():
    """Create a mock AgentAction."""
    action = Mock()
    action.id = 12345
    action.agent_id = "test-agent-001"
    action.action_type = "database_query"
    action.description = "Test action description"
    action.tool_name = "sql_executor"
    action.risk_score = 50
    action.risk_level = "medium"
    action.requires_approval = False
    action.status = "pending"
    action.approved = False
    action.timestamp = datetime.now(UTC)
    action.cvss_score = None
    action.cvss_severity = None
    action.mitre_tactic = None
    action.mitre_technique = None
    action.nist_control = None
    action.nist_description = None
    action.policy_evaluated = False
    action.policy_decision = None
    action.policy_risk_score = None
    return action


@pytest.fixture
def valid_data():
    """Create valid request data."""
    return {
        "agent_id": "test-agent-001",
        "action_type": "database_query",
        "description": "Execute SELECT query on users table",
        "tool_name": "sql_executor",
        "environment": "production",
        "target_system": "users_db",
        "contains_pii": False
    }


@pytest.fixture
def mock_current_user():
    """Create a mock current user context."""
    return {
        "user_id": "user-123",
        "email": "test@example.com",
        "role": "admin",
        "auth_method": "api_key"
    }


@pytest.fixture
def pipeline(mock_db):
    """Create a pipeline instance with mocked dependencies."""
    return EnterpriseRiskPipeline(mock_db)


# =============================================================================
# TEST: INPUT VALIDATION
# Compliance: PCI-DSS 6.5.1, NIST 800-53 SI-10
# =============================================================================

class TestInputValidation:
    """Tests for _validate_input() method."""

    def test_validate_input_with_valid_data(self, pipeline, valid_data):
        """Test that valid data passes validation."""
        # Should not raise
        pipeline._validate_input(valid_data)

    def test_validate_input_missing_agent_id(self, pipeline, valid_data):
        """Test that missing agent_id raises ValueError."""
        del valid_data["agent_id"]
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(valid_data)
        assert "agent_id" in str(exc_info.value)

    def test_validate_input_missing_action_type(self, pipeline, valid_data):
        """Test that missing action_type raises ValueError."""
        del valid_data["action_type"]
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(valid_data)
        assert "action_type" in str(exc_info.value)

    def test_validate_input_missing_description(self, pipeline, valid_data):
        """Test that missing description raises ValueError."""
        del valid_data["description"]
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(valid_data)
        assert "description" in str(exc_info.value)

    def test_validate_input_missing_tool_name(self, pipeline, valid_data):
        """Test that missing tool_name raises ValueError."""
        del valid_data["tool_name"]
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(valid_data)
        assert "tool_name" in str(exc_info.value)

    def test_validate_input_empty_agent_id(self, pipeline, valid_data):
        """Test that empty agent_id raises ValueError."""
        valid_data["agent_id"] = ""
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(valid_data)
        assert "agent_id" in str(exc_info.value)

    def test_validate_input_multiple_missing_fields(self, pipeline):
        """Test that multiple missing fields are all reported."""
        data = {"environment": "production"}
        with pytest.raises(ValueError) as exc_info:
            pipeline._validate_input(data)
        error_msg = str(exc_info.value)
        assert "agent_id" in error_msg
        assert "action_type" in error_msg
        assert "description" in error_msg
        assert "tool_name" in error_msg


# =============================================================================
# TEST: RISK FUSION CALCULATION
# Compliance: SOC 2 CC3.2, NIST 800-30
# =============================================================================

class TestRiskFusion:
    """Tests for risk fusion calculation (80% Policy + 20% Hybrid)."""

    @pytest.mark.asyncio
    async def test_risk_fusion_calculation(self, pipeline, mock_action):
        """Test that risk fusion correctly applies 80/20 weighting."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.policy.evaluated = True
        result.fusion.policy_risk = 80
        result.fusion.hybrid_risk = 40

        await pipeline._stage_risk_fusion(mock_action, result)

        # Expected: (80 * 0.8) + (40 * 0.2) = 64 + 8 = 72
        assert result.fusion.fused_score == 72
        assert result.fusion.fusion_applied is True
        assert "80" in result.fusion.formula
        assert "40" in result.fusion.formula

    @pytest.mark.asyncio
    async def test_risk_fusion_without_policy(self, pipeline, mock_action):
        """Test fusion falls back to hybrid when policy not evaluated."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.policy.evaluated = False
        result.fusion.hybrid_risk = 60

        await pipeline._stage_risk_fusion(mock_action, result)

        assert result.fusion.fused_score == 60
        assert result.fusion.fusion_applied is False


# =============================================================================
# TEST: SAFETY RULES
# Compliance: SOC 2 CC7.1, PCI-DSS 12.10
# =============================================================================

class TestSafetyRules:
    """Tests for safety rules that override calculated scores."""

    @pytest.mark.asyncio
    async def test_safety_rule_critical_cvss_floor(self, pipeline, mock_action, valid_data):
        """Test CRITICAL CVSS sets minimum floor of 85."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.cvss = CVSSResult(base_score=9.8, severity="CRITICAL")
        result.fusion.fused_score = 50  # Below floor

        await pipeline._stage_safety_rules(mock_action, valid_data, result)

        assert result.risk_score >= 85
        assert "CRITICAL_CVSS_FLOOR_85" in result.fusion.safety_rules_applied

    @pytest.mark.asyncio
    async def test_safety_rule_policy_deny_override(self, pipeline, mock_action, valid_data):
        """Test Policy DENY sets score to 100."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.policy.decision = "deny"
        result.fusion.fused_score = 30

        await pipeline._stage_safety_rules(mock_action, valid_data, result)

        assert result.risk_score == 100
        assert "POLICY_DENY_OVERRIDE_100" in result.fusion.safety_rules_applied

    @pytest.mark.asyncio
    async def test_safety_rule_pii_production_floor(self, pipeline, mock_action):
        """Test PII in production sets minimum floor of 70."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.fusion.fused_score = 40  # Below floor

        data = {
            "agent_id": "test",
            "action_type": "data_export",
            "description": "Export PII customer data",
            "tool_name": "exporter",
            "environment": "production",
            "contains_pii": True
        }

        await pipeline._stage_safety_rules(mock_action, data, result)

        assert result.risk_score >= 70
        assert "PII_PRODUCTION_FLOOR_70" in result.fusion.safety_rules_applied

    @pytest.mark.asyncio
    async def test_no_safety_rules_when_not_needed(self, pipeline, mock_action, valid_data):
        """Test no safety rules applied when thresholds not met."""
        result = EnterpriseRiskResult(
            risk_score=0,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )
        result.fusion.fused_score = 90  # Already high

        await pipeline._stage_safety_rules(mock_action, valid_data, result)

        assert result.risk_score == 90
        assert len(result.fusion.safety_rules_applied) == 0


# =============================================================================
# TEST: RISK LEVEL DETERMINATION
# Compliance: NIST 800-30, SOC 2 CC3.2
# =============================================================================

class TestRiskLevelDetermination:
    """Tests for risk level thresholds."""

    def test_critical_risk_level(self, pipeline, mock_action):
        """Test score >= 85 is CRITICAL."""
        result = EnterpriseRiskResult(
            risk_score=90,
            risk_level="",
            requires_approval=False,
            status="pending",
            approved=False
        )

        pipeline._update_action(mock_action, result)

        assert result.risk_level == "critical"
        assert result.requires_approval is True

    def test_high_risk_level(self, pipeline, mock_action):
        """Test score >= 70 and < 85 is HIGH."""
        result = EnterpriseRiskResult(
            risk_score=75,
            risk_level="",
            requires_approval=False,
            status="pending",
            approved=False
        )

        pipeline._update_action(mock_action, result)

        assert result.risk_level == "high"
        assert result.requires_approval is True

    def test_medium_risk_level(self, pipeline, mock_action):
        """Test score >= 45 and < 70 is MEDIUM."""
        result = EnterpriseRiskResult(
            risk_score=55,
            risk_level="",
            requires_approval=False,
            status="pending",
            approved=False
        )

        pipeline._update_action(mock_action, result)

        assert result.risk_level == "medium"
        assert result.requires_approval is True

    def test_low_risk_level(self, pipeline, mock_action):
        """Test score < 45 is LOW."""
        result = EnterpriseRiskResult(
            risk_score=30,
            risk_level="",
            requires_approval=False,
            status="pending",
            approved=False
        )

        pipeline._update_action(mock_action, result)

        assert result.risk_level == "low"
        assert result.requires_approval is False
        assert result.approved is True


# =============================================================================
# TEST: GRACEFUL DEGRADATION
# Compliance: SOC 2 CC7.2, NIST 800-53 SI-17
# =============================================================================

class TestGracefulDegradation:
    """Tests for graceful degradation when services fail."""

    @pytest.mark.asyncio
    async def test_cvss_failure_continues_pipeline(self, pipeline, mock_action, valid_data):
        """Test pipeline continues when CVSS service fails."""
        result = EnterpriseRiskResult(
            risk_score=50,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )

        with patch('services.enterprise_risk_pipeline.cvss_calculator') as mock_cvss:
            mock_cvss.calculate_base_score.side_effect = Exception("CVSS service unavailable")

            cvss_result = await pipeline._stage_cvss(mock_action, valid_data, result)

            assert cvss_result is None
            assert "cvss" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_policy_failure_continues_pipeline(self, pipeline, mock_action, valid_data, mock_current_user):
        """Test pipeline continues when policy engine fails."""
        result = EnterpriseRiskResult(
            risk_score=50,
            risk_level="medium",
            requires_approval=False,
            status="pending",
            approved=False
        )

        with patch('services.enterprise_risk_pipeline.create_policy_engine') as mock_policy:
            mock_policy.side_effect = Exception("Policy engine unavailable")

            await pipeline._stage_policy(mock_action, valid_data, mock_current_user, result)

            assert result.policy.evaluated is False
            assert any("policy" in err.lower() for err in result.errors)


# =============================================================================
# TEST: DATABASE ROLLBACK ON ERROR
# Compliance: SOC 2 CC8.1, PCI-DSS 6.5.5
# =============================================================================

class TestDatabaseRollback:
    """Tests for explicit database rollback on exception."""

    @pytest.mark.asyncio
    async def test_rollback_called_on_exception(self, mock_db, mock_action, valid_data, mock_current_user):
        """Test that db.rollback() is called when pipeline fails."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        # Make commit raise an exception
        mock_db.commit.side_effect = Exception("Database commit failed")

        result = await pipeline.evaluate_action(
            action=mock_action,
            data=valid_data,
            current_user=mock_current_user,
            organization_id=1,
            source="test"
        )

        # Verify rollback was called
        mock_db.rollback.assert_called_once()
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_pipeline_returns_partial_result_on_error(self, mock_db, mock_action, valid_data, mock_current_user):
        """Test pipeline returns partial result on error instead of raising."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        # Make flush raise an exception mid-pipeline
        mock_db.flush.side_effect = Exception("Database flush failed")

        result = await pipeline.evaluate_action(
            action=mock_action,
            data=valid_data,
            current_user=mock_current_user,
            organization_id=1,
            source="test"
        )

        # Should return result, not raise
        assert isinstance(result, EnterpriseRiskResult)
        assert len(result.errors) > 0


# =============================================================================
# TEST: ALERT GENERATION
# Compliance: SOC 2 CC7.2, PCI-DSS 12.10, NIST 800-53 IR-6
# =============================================================================

class TestAlertGeneration:
    """Tests for alert generation on high-risk actions."""

    @pytest.mark.asyncio
    async def test_alert_created_for_high_risk(self, mock_db, mock_action, valid_data):
        """Test alert is created for high-risk actions."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        result = EnterpriseRiskResult(
            risk_score=80,
            risk_level="high",
            requires_approval=True,
            status="pending",
            approved=False
        )

        # Mock no existing alert
        mock_db.query.return_value.filter.return_value.first.return_value = None

        await pipeline._stage_alert_generation(mock_action, valid_data, organization_id=1, result=result)

        # Verify alert was added
        mock_db.add.assert_called()
        assert result.automation.alert_created is True

    @pytest.mark.asyncio
    async def test_alert_created_for_critical_risk(self, mock_db, mock_action, valid_data):
        """Test alert is created for critical-risk actions."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        result = EnterpriseRiskResult(
            risk_score=95,
            risk_level="critical",
            requires_approval=True,
            status="pending",
            approved=False
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        await pipeline._stage_alert_generation(mock_action, valid_data, organization_id=1, result=result)

        assert result.automation.alert_created is True

    @pytest.mark.asyncio
    async def test_no_alert_for_low_risk(self, mock_db, mock_action, valid_data):
        """Test no alert created for low-risk actions."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        result = EnterpriseRiskResult(
            risk_score=30,
            risk_level="low",
            requires_approval=False,
            status="approved",
            approved=True
        )

        await pipeline._stage_alert_generation(mock_action, valid_data, organization_id=1, result=result)

        # Alert should not be created
        assert result.automation.alert_created is False

    @pytest.mark.asyncio
    async def test_alert_deduplication(self, mock_db, mock_action, valid_data):
        """Test existing alert is reused (no duplicate)."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        result = EnterpriseRiskResult(
            risk_score=85,
            risk_level="critical",
            requires_approval=True,
            status="pending",
            approved=False
        )

        # Mock existing alert
        existing_alert = Mock()
        existing_alert.id = 999
        mock_db.query.return_value.filter.return_value.first.return_value = existing_alert

        await pipeline._stage_alert_generation(mock_action, valid_data, organization_id=1, result=result)

        # Should use existing alert, not create new
        assert result.automation.alert_id == 999
        assert result.automation.alert_created is True


# =============================================================================
# TEST: ORGANIZATION ISOLATION
# Compliance: SOC 2 CC6.1, PCI-DSS 7.1, NIST 800-53 AC-3
# =============================================================================

class TestOrganizationIsolation:
    """Tests for multi-tenant data isolation."""

    @pytest.mark.asyncio
    async def test_alert_includes_organization_id(self, mock_db, mock_action, valid_data):
        """Test alert is created with correct organization_id."""
        pipeline = EnterpriseRiskPipeline(mock_db)

        result = EnterpriseRiskResult(
            risk_score=85,
            risk_level="critical",
            requires_approval=True,
            status="pending",
            approved=False
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Capture the Alert object passed to db.add()
        captured_alert = None
        def capture_add(obj):
            nonlocal captured_alert
            captured_alert = obj
        mock_db.add.side_effect = capture_add

        await pipeline._stage_alert_generation(mock_action, valid_data, organization_id=42, result=result)

        # Verify organization_id is set correctly
        assert captured_alert is not None
        assert captured_alert.organization_id == 42


# =============================================================================
# TEST: RESPONSE SERIALIZATION
# Compliance: API contract validation
# =============================================================================

class TestResponseSerialization:
    """Tests for EnterpriseRiskResult.to_response_dict()."""

    def test_to_response_dict_structure(self):
        """Test response dictionary has correct structure."""
        result = EnterpriseRiskResult(
            risk_score=75,
            risk_level="high",
            requires_approval=True,
            status="pending",
            approved=False
        )
        result.cvss = CVSSResult(base_score=7.5, severity="HIGH")
        result.compliance.mitre_tactic = "Execution"
        result.compliance.mitre_technique = "T1059"
        result.compliance.nist_control = "AC-3"
        result.stages_completed = ["cvss", "mitre", "nist"]
        result.processing_time_ms = 150.5

        response = result.to_response_dict()

        # Verify top-level keys
        assert response["risk_score"] == 75
        assert response["risk_level"] == "high"
        assert response["requires_approval"] is True
        assert response["status"] == "pending"
        assert response["approved"] is False

        # Verify compliance section
        assert response["compliance"]["cvss_score"] == 7.5
        assert response["compliance"]["cvss_severity"] == "HIGH"
        assert response["compliance"]["mitre_tactic"] == "Execution"
        assert response["compliance"]["nist_control"] == "AC-3"

        # Verify metadata
        assert response["meta"]["processing_time_ms"] == 150.5
        assert len(response["meta"]["stages_completed"]) == 3

    def test_to_response_dict_handles_none_cvss(self):
        """Test response handles missing CVSS data."""
        result = EnterpriseRiskResult(
            risk_score=50,
            risk_level="medium",
            requires_approval=True,
            status="pending",
            approved=False
        )

        response = result.to_response_dict()

        assert response["compliance"]["cvss_score"] is None
        assert response["compliance"]["cvss_severity"] is None


# =============================================================================
# TEST: FACTORY FUNCTION
# =============================================================================

class TestFactoryFunction:
    """Tests for get_enterprise_risk_pipeline factory."""

    def test_factory_creates_pipeline(self, mock_db):
        """Test factory returns EnterpriseRiskPipeline instance."""
        pipeline = get_enterprise_risk_pipeline(mock_db)

        assert isinstance(pipeline, EnterpriseRiskPipeline)
        assert pipeline.db == mock_db


# =============================================================================
# TEST: CONSTANTS AND THRESHOLDS
# =============================================================================

class TestConstants:
    """Tests for pipeline constants."""

    def test_threshold_values(self):
        """Verify threshold constants are correct."""
        assert EnterpriseRiskPipeline.THRESHOLD_CRITICAL == 85
        assert EnterpriseRiskPipeline.THRESHOLD_HIGH == 70
        assert EnterpriseRiskPipeline.THRESHOLD_MEDIUM == 45

    def test_safety_rule_floors(self):
        """Verify safety rule floor values."""
        assert EnterpriseRiskPipeline.SAFETY_CVSS_CRITICAL_FLOOR == 85
        assert EnterpriseRiskPipeline.SAFETY_POLICY_DENY_SCORE == 100
        assert EnterpriseRiskPipeline.SAFETY_PII_PRODUCTION_FLOOR == 70

    def test_fusion_weights(self):
        """Verify risk fusion weights sum to 1.0."""
        assert EnterpriseRiskPipeline.POLICY_WEIGHT == 0.8
        assert EnterpriseRiskPipeline.HYBRID_WEIGHT == 0.2
        assert EnterpriseRiskPipeline.POLICY_WEIGHT + EnterpriseRiskPipeline.HYBRID_WEIGHT == 1.0

    def test_pipeline_version(self):
        """Verify pipeline version is set."""
        assert EnterpriseRiskPipeline.PIPELINE_VERSION == "1.0.0"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
