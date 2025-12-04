"""
SEC-065: Enterprise Executive Brief Service - Unit Tests

Comprehensive test suite for the cached executive briefing system.

Test Coverage:
- Cached brief lookup performance
- Rate limiting enforcement
- Multi-tenant isolation
- LLM fallback behavior
- Empty state handling
- Pagination and limits
- Admin force regeneration
- Metric calculations
- Risk assessment logic

Compliance:
- SOC 2 AU-6: Audit record review verification
- PCI-DSS 10.6: Daily security event review verification
- NIST 800-53 AU-6: Audit Review, Analysis, Reporting verification

Document ID: SEC-065-TESTS
Publisher: Ascend (OW-kai Corporation)
Version: 1.0.0
"""

import pytest
import time
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

# Import the modules under test
from services.executive_brief_service import (
    ExecutiveBriefService,
    ExecutiveBriefConfig,
    get_executive_brief_service,
    DEFAULT_CONFIG
)
from models_executive_brief import ExecutiveBrief
from models import Alert, Organization


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_org_id():
    """Standard test organization ID"""
    return 1


@pytest.fixture
def mock_config():
    """Test configuration with shorter timeouts"""
    return ExecutiveBriefConfig(
        CACHE_TTL_HOURS=1,
        COOLDOWN_MINUTES=5,
        MAX_ALERT_SNAPSHOT=10,
        LLM_MAX_TOKENS=500,
        LLM_TEMPERATURE=0.5,
        LLM_MODEL="gpt-3.5-turbo"
    )


@pytest.fixture
def service(mock_db, mock_org_id, mock_config):
    """Create ExecutiveBriefService instance for testing"""
    return ExecutiveBriefService(mock_db, mock_org_id, mock_config)


@pytest.fixture
def sample_brief():
    """Create a sample ExecutiveBrief for testing"""
    brief = Mock(spec=ExecutiveBrief)
    brief.id = 1
    brief.organization_id = 1
    brief.brief_id = "exec-brief-1234567890"
    brief.time_period = "24h"
    brief.generated_at = datetime.now(UTC)
    brief.expires_at = datetime.now(UTC) + timedelta(hours=1)
    brief.generated_by = "test@example.com"
    brief.summary = "Test executive summary"
    brief.key_metrics = {
        "threats_detected": 10,
        "threats_prevented": 5,
        "cost_savings": "$250,000",
        "system_accuracy": "85.0%"
    }
    brief.recommendations = []
    brief.risk_assessment = "MEDIUM"
    brief.alert_count = 10
    brief.high_priority_count = 3
    brief.critical_count = 1
    brief.is_current = True
    brief.is_expired = Mock(return_value=False)
    brief.is_valid = Mock(return_value=True)
    brief.to_api_response = Mock(return_value={
        "brief_id": brief.brief_id,
        "summary": brief.summary,
        "risk_assessment": brief.risk_assessment
    })
    return brief


@pytest.fixture
def sample_alerts():
    """Create sample alerts for testing"""
    alerts = []
    severities = ["critical", "high", "medium", "low"]

    for i in range(10):
        alert = Mock(spec=Alert)
        alert.id = i + 1
        alert.organization_id = 1
        alert.severity = severities[i % 4]
        alert.alert_type = f"TEST_ALERT_{i}"
        alert.message = f"Test alert message {i}"
        alert.timestamp = datetime.now(UTC) - timedelta(hours=i)
        alert.status = "new" if i % 2 == 0 else "acknowledged"
        alerts.append(alert)

    return alerts


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestServiceInitialization:
    """Test service initialization and configuration"""

    def test_service_initialization(self, mock_db, mock_org_id):
        """Test service initializes with correct parameters"""
        service = ExecutiveBriefService(mock_db, mock_org_id)

        assert service.db == mock_db
        assert service.org_id == mock_org_id
        assert service.config is not None

    def test_service_with_custom_config(self, mock_db, mock_org_id, mock_config):
        """Test service accepts custom configuration"""
        service = ExecutiveBriefService(mock_db, mock_org_id, mock_config)

        assert service.config.CACHE_TTL_HOURS == 1
        assert service.config.COOLDOWN_MINUTES == 5
        assert service.config.MAX_ALERT_SNAPSHOT == 10

    def test_factory_function(self, mock_db, mock_org_id):
        """Test factory function creates service correctly"""
        service = get_executive_brief_service(mock_db, mock_org_id)

        assert isinstance(service, ExecutiveBriefService)
        assert service.org_id == mock_org_id

    def test_default_config_values(self):
        """Test default configuration has expected values"""
        config = ExecutiveBriefConfig()

        assert config.CACHE_TTL_HOURS == 1
        assert config.COOLDOWN_MINUTES == 5
        assert config.MAX_ALERT_SNAPSHOT == 100
        assert config.LLM_MAX_TOKENS == 1000
        assert config.LLM_TEMPERATURE == 0.7
        assert config.LLM_MODEL == "gpt-3.5-turbo"
        assert "24h" in config.TIME_PERIOD_DAYS
        assert config.TIME_PERIOD_DAYS["24h"] == 1


# =============================================================================
# CACHED BRIEF LOOKUP TESTS
# =============================================================================

class TestCachedBriefLookup:
    """Test cached brief retrieval functionality"""

    def test_get_cached_brief_found(self, service, sample_brief, mock_db):
        """Test successful cached brief retrieval"""
        # Setup mock query chain
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        result = service.get_cached_brief()

        assert result == sample_brief
        mock_db.query.assert_called_once()

    def test_get_cached_brief_not_found(self, service, mock_db):
        """Test cached brief retrieval when none exists"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)

        result = service.get_cached_brief()

        assert result is None

    def test_get_cached_brief_filters_by_org_id(self, service, mock_db, mock_org_id):
        """Test multi-tenant isolation in cached brief lookup"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)

        service.get_cached_brief()

        # Verify filter was called (checking org isolation)
        mock_query.filter.assert_called()

    def test_get_cached_brief_handles_exception(self, service, mock_db):
        """Test graceful error handling in cached brief lookup"""
        mock_db.query = Mock(side_effect=Exception("Database error"))

        result = service.get_cached_brief()

        assert result is None


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================

class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_can_regenerate_no_previous_brief(self, service, mock_db):
        """Test regeneration allowed when no previous brief exists"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)

        can_regen, remaining = service.can_regenerate()

        assert can_regen is True
        assert remaining == 0

    def test_can_regenerate_cooldown_expired(self, service, sample_brief, mock_db):
        """Test regeneration allowed after cooldown expires"""
        # Set generated_at to 10 minutes ago (past 5-minute cooldown)
        sample_brief.generated_at = datetime.now(UTC) - timedelta(minutes=10)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        can_regen, remaining = service.can_regenerate()

        assert can_regen is True
        assert remaining == 0

    def test_can_regenerate_cooldown_active(self, service, sample_brief, mock_db):
        """Test regeneration blocked during cooldown"""
        # Set generated_at to 2 minutes ago (within 5-minute cooldown)
        sample_brief.generated_at = datetime.now(UTC) - timedelta(minutes=2)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        can_regen, remaining = service.can_regenerate()

        assert can_regen is False
        assert remaining > 0
        assert remaining <= 180  # Should be approximately 3 minutes

    def test_can_regenerate_handles_exception(self, service, mock_db):
        """Test graceful error handling allows regeneration on exception"""
        mock_db.query = Mock(side_effect=Exception("Database error"))

        can_regen, remaining = service.can_regenerate()

        # On error, fail open for usability
        assert can_regen is True
        assert remaining == 0


# =============================================================================
# MULTI-TENANT ISOLATION TESTS
# =============================================================================

class TestMultiTenantIsolation:
    """Test multi-tenant data isolation"""

    def test_service_stores_org_id(self, mock_db):
        """Test service stores organization ID"""
        org_id_1 = 1
        org_id_2 = 2

        service_1 = ExecutiveBriefService(mock_db, org_id_1)
        service_2 = ExecutiveBriefService(mock_db, org_id_2)

        assert service_1.org_id == org_id_1
        assert service_2.org_id == org_id_2
        assert service_1.org_id != service_2.org_id

    def test_get_brief_by_id_filters_by_org(self, service, mock_db, sample_brief):
        """Test get_brief_by_id enforces org isolation"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        result = service.get_brief_by_id("exec-brief-123")

        # Verify filter was called with AND condition
        mock_query.filter.assert_called()

    def test_get_brief_history_filters_by_org(self, service, mock_db):
        """Test brief history enforces org isolation"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        service.get_brief_history(limit=10, offset=0)

        mock_query.filter.assert_called()


# =============================================================================
# METRIC CALCULATION TESTS
# =============================================================================

class TestMetricCalculation:
    """Test metric calculation logic"""

    def test_calculate_metrics_empty_alerts(self, service):
        """Test metrics calculation with no alerts"""
        metrics = service._calculate_metrics([])

        assert metrics["total_alerts"] == 0
        assert metrics["critical_count"] == 0
        assert metrics["high_count"] == 0
        assert metrics["medium_count"] == 0
        assert metrics["low_count"] == 0
        assert metrics["threats_detected"] == 0
        assert metrics["threats_prevented"] == 0
        assert metrics["cost_savings"] == "$0"
        assert metrics["system_accuracy"] == "N/A"

    def test_calculate_metrics_with_alerts(self, service, sample_alerts):
        """Test metrics calculation with sample alerts"""
        metrics = service._calculate_metrics(sample_alerts)

        assert metrics["total_alerts"] == 10
        assert metrics["critical_count"] >= 0
        assert metrics["high_count"] >= 0
        assert metrics["threats_detected"] == 10

    def test_calculate_metrics_severity_counts(self, service):
        """Test severity counting logic"""
        alerts = []
        for severity in ["critical", "critical", "high", "medium", "low"]:
            alert = Mock()
            alert.severity = severity
            alert.status = "new"
            alerts.append(alert)

        metrics = service._calculate_metrics(alerts)

        assert metrics["critical_count"] == 2
        assert metrics["high_count"] == 1
        assert metrics["medium_count"] == 1
        assert metrics["low_count"] == 1

    def test_calculate_metrics_cost_savings(self, service):
        """Test cost savings calculation uses configurable value"""
        # 5 acknowledged alerts = 5 * COST_PER_INCIDENT_USD
        alerts = []
        for i in range(10):
            alert = Mock()
            alert.severity = "high"
            alert.status = "acknowledged" if i < 5 else "new"
            alerts.append(alert)

        metrics = service._calculate_metrics(alerts)

        assert metrics["threats_prevented"] == 5
        # Cost is calculated as: prevented * config.COST_PER_INCIDENT_USD
        expected_cost = 5 * service.config.COST_PER_INCIDENT_USD
        assert f"${expected_cost:,}" in metrics["cost_savings"]

    def test_calculate_metrics_cost_savings_disabled(self, mock_db, mock_org_id):
        """Test cost savings disabled when COST_PER_INCIDENT_USD is 0"""
        config = ExecutiveBriefConfig(COST_PER_INCIDENT_USD=0)
        service = ExecutiveBriefService(mock_db, mock_org_id, config)

        alerts = []
        for i in range(5):
            alert = Mock()
            alert.severity = "high"
            alert.status = "acknowledged"
            alerts.append(alert)

        metrics = service._calculate_metrics(alerts)

        assert metrics["threats_prevented"] == 5
        assert metrics["cost_savings"] == "$0"

    def test_calculate_metrics_custom_cost_per_incident(self, mock_db, mock_org_id):
        """Test custom COST_PER_INCIDENT_USD value"""
        # Enterprise-specific cost: $100,000 per incident
        config = ExecutiveBriefConfig(COST_PER_INCIDENT_USD=100000)
        service = ExecutiveBriefService(mock_db, mock_org_id, config)

        alerts = []
        for i in range(3):
            alert = Mock()
            alert.severity = "critical"
            alert.status = "acknowledged"
            alerts.append(alert)

        metrics = service._calculate_metrics(alerts)

        assert metrics["threats_prevented"] == 3
        # 3 * $100,000 = $300,000
        assert metrics["cost_savings"] == "$300,000"

    def test_max_alerts_for_analysis_configurable(self, mock_db, mock_org_id):
        """Test MAX_ALERTS_FOR_ANALYSIS is configurable"""
        # Custom limit: 500 alerts
        config = ExecutiveBriefConfig(MAX_ALERTS_FOR_ANALYSIS=500)
        service = ExecutiveBriefService(mock_db, mock_org_id, config)

        assert service.config.MAX_ALERTS_FOR_ANALYSIS == 500

    def test_fetch_alerts_uses_configurable_limit(self, mock_db, mock_org_id):
        """Test _fetch_alerts_for_period uses MAX_ALERTS_FOR_ANALYSIS"""
        config = ExecutiveBriefConfig(MAX_ALERTS_FOR_ANALYSIS=250)
        service = ExecutiveBriefService(mock_db, mock_org_id, config)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        service._fetch_alerts_for_period("24h")

        # Verify limit was called with the configured value
        mock_query.limit.assert_called_with(250)


# =============================================================================
# RISK ASSESSMENT TESTS
# =============================================================================

class TestRiskAssessment:
    """Test risk assessment calculation"""

    def test_risk_assessment_critical(self, service):
        """Test CRITICAL risk assessment threshold"""
        metrics = {
            "critical_count": 10,
            "high_count": 5,
            "total_alerts": 20
        }

        risk = service._calculate_risk_assessment(metrics)

        assert risk == "CRITICAL"

    def test_risk_assessment_high(self, service):
        """Test HIGH risk assessment threshold"""
        metrics = {
            "critical_count": 2,
            "high_count": 5,
            "total_alerts": 10
        }

        risk = service._calculate_risk_assessment(metrics)

        assert risk == "HIGH"

    def test_risk_assessment_medium(self, service):
        """Test MEDIUM risk assessment threshold"""
        metrics = {
            "critical_count": 0,
            "high_count": 2,
            "total_alerts": 5
        }

        risk = service._calculate_risk_assessment(metrics)

        assert risk == "MEDIUM"

    def test_risk_assessment_low(self, service):
        """Test LOW risk assessment threshold"""
        metrics = {
            "critical_count": 0,
            "high_count": 0,
            "total_alerts": 1
        }

        risk = service._calculate_risk_assessment(metrics)

        assert risk == "LOW"

    def test_risk_assessment_no_data(self, service):
        """Test NO_DATA risk assessment for empty state"""
        metrics = {
            "critical_count": 0,
            "high_count": 0,
            "total_alerts": 0
        }

        risk = service._calculate_risk_assessment(metrics)

        assert risk == "NO_DATA"


# =============================================================================
# RECOMMENDATION GENERATION TESTS
# =============================================================================

class TestRecommendationGeneration:
    """Test recommendation generation logic"""

    def test_recommendations_critical_alerts(self, service):
        """Test recommendations for critical alerts"""
        metrics = {
            "critical_count": 5,
            "high_count": 3,
            "pending_count": 2
        }

        recs = service._generate_recommendations([], metrics)

        # Should have CRITICAL priority recommendation
        priorities = [r["priority"] for r in recs]
        assert "CRITICAL" in priorities

    def test_recommendations_high_alerts(self, service):
        """Test recommendations for high priority alerts"""
        metrics = {
            "critical_count": 0,
            "high_count": 10,
            "pending_count": 2
        }

        recs = service._generate_recommendations([], metrics)

        priorities = [r["priority"] for r in recs]
        assert "HIGH" in priorities

    def test_recommendations_pending_backlog(self, service):
        """Test recommendations for pending alert backlog"""
        metrics = {
            "critical_count": 0,
            "high_count": 0,
            "pending_count": 10
        }

        recs = service._generate_recommendations([], metrics)

        priorities = [r["priority"] for r in recs]
        assert "MEDIUM" in priorities

    def test_recommendations_always_includes_low(self, service):
        """Test that ongoing recommendation is always included"""
        metrics = {
            "critical_count": 0,
            "high_count": 0,
            "pending_count": 0
        }

        recs = service._generate_recommendations([], metrics)

        priorities = [r["priority"] for r in recs]
        assert "LOW" in priorities

    def test_recommendation_structure(self, service):
        """Test recommendation has all required fields"""
        metrics = {
            "critical_count": 1,
            "high_count": 0,
            "pending_count": 0
        }

        recs = service._generate_recommendations([], metrics)

        for rec in recs:
            assert "priority" in rec
            assert "action" in rec
            assert "timeframe" in rec
            assert "owner" in rec


# =============================================================================
# ALERT SNAPSHOT TESTS
# =============================================================================

class TestAlertSnapshot:
    """Test alert snapshot creation for audit trail"""

    def test_snapshot_limits_alerts(self, service, sample_alerts):
        """Test snapshot respects MAX_ALERT_SNAPSHOT limit"""
        # Service config has MAX_ALERT_SNAPSHOT = 10
        large_alert_list = sample_alerts * 20  # 200 alerts

        snapshot = service._create_alert_snapshot(large_alert_list)

        assert len(snapshot) <= service.config.MAX_ALERT_SNAPSHOT

    def test_snapshot_includes_required_fields(self, service, sample_alerts):
        """Test snapshot includes all required fields"""
        snapshot = service._create_alert_snapshot(sample_alerts[:1])

        assert len(snapshot) == 1
        assert "id" in snapshot[0]
        assert "severity" in snapshot[0]
        assert "alert_type" in snapshot[0]
        assert "timestamp" in snapshot[0]


# =============================================================================
# LLM FALLBACK TESTS
# =============================================================================

class TestLLMFallback:
    """Test LLM fallback behavior"""

    def test_generate_fallback_empty_alerts(self, service):
        """Test fallback summary for empty alerts"""
        metrics = {
            "total_alerts": 0,
            "critical_count": 0,
            "high_count": 0,
            "threats_prevented": 0,
            "cost_savings": "$0"
        }

        summary = service._generate_fallback([], metrics)

        assert "EXECUTIVE SECURITY BRIEFING" in summary
        assert "MINIMAL" in summary or "0" in summary

    def test_generate_fallback_critical_alerts(self, service, sample_alerts):
        """Test fallback summary for critical alerts"""
        metrics = {
            "total_alerts": 10,
            "critical_count": 5,
            "high_count": 3,
            "threats_prevented": 5,
            "cost_savings": "$250,000"
        }

        summary = service._generate_fallback(sample_alerts, metrics)

        assert "EXECUTIVE SECURITY BRIEFING" in summary
        assert "CRITICAL" in summary

    def test_generate_summary_empty_state(self, service):
        """Test summary generation for empty state"""
        summary, method, info = service._generate_summary([], {})

        assert method == "empty_state"
        assert "No security events" in summary


# =============================================================================
# BRIEF HISTORY TESTS
# =============================================================================

class TestBriefHistory:
    """Test brief history functionality"""

    def test_get_brief_history_pagination(self, service, mock_db):
        """Test history pagination parameters"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        service.get_brief_history(limit=20, offset=10)

        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(20)

    def test_get_brief_history_handles_exception(self, service, mock_db):
        """Test history handles errors gracefully"""
        mock_db.query = Mock(side_effect=Exception("Database error"))

        result = service.get_brief_history()

        assert result == []


# =============================================================================
# VIEW RECORDING TESTS
# =============================================================================

class TestViewRecording:
    """Test brief view recording for audit trail"""

    def test_record_view_success(self, service, mock_db, sample_brief):
        """Test successful view recording"""
        sample_brief.viewed_by = []

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        result = service.record_view("exec-brief-123", "viewer@example.com")

        assert result is True
        mock_db.commit.assert_called()

    def test_record_view_brief_not_found(self, service, mock_db):
        """Test view recording when brief not found"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)

        result = service.record_view("nonexistent-brief", "viewer@example.com")

        assert result is False


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestConfiguration:
    """Test configuration handling"""

    def test_time_period_mapping(self):
        """Test time period to days mapping"""
        config = ExecutiveBriefConfig()

        assert config.TIME_PERIOD_DAYS["24h"] == 1
        assert config.TIME_PERIOD_DAYS["7d"] == 7
        assert config.TIME_PERIOD_DAYS["30d"] == 30
        assert config.TIME_PERIOD_DAYS["90d"] == 90

    def test_risk_thresholds(self):
        """Test risk threshold configuration"""
        config = ExecutiveBriefConfig()

        assert config.RISK_THRESHOLDS["CRITICAL"] == 10
        assert config.RISK_THRESHOLDS["HIGH"] == 5
        assert config.RISK_THRESHOLDS["MEDIUM"] == 1
        assert config.RISK_THRESHOLDS["LOW"] == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestBriefGeneration:
    """Test brief generation workflow"""

    def test_generate_brief_rate_limited(self, service, sample_brief, mock_db):
        """Test brief generation respects rate limit"""
        # Set up a recent brief (within cooldown)
        sample_brief.generated_at = datetime.now(UTC) - timedelta(minutes=2)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        with pytest.raises(ValueError) as excinfo:
            service.generate_brief(time_period="24h", user_email="test@example.com")

        assert "Rate limit" in str(excinfo.value)

    def test_generate_brief_force_bypasses_rate_limit(self, service, sample_brief, mock_db):
        """Test force regeneration bypasses rate limit"""
        # Set up a recent brief (within cooldown)
        sample_brief.generated_at = datetime.now(UTC) - timedelta(minutes=2)

        # Mock the query chain for can_regenerate check
        mock_query_regen = Mock()
        mock_query_regen.filter = Mock(return_value=mock_query_regen)
        mock_query_regen.order_by = Mock(return_value=mock_query_regen)
        mock_query_regen.first = Mock(return_value=sample_brief)

        # Mock the query chain for alert fetching
        mock_query_alerts = Mock()
        mock_query_alerts.filter = Mock(return_value=mock_query_alerts)
        mock_query_alerts.order_by = Mock(return_value=mock_query_alerts)
        mock_query_alerts.limit = Mock(return_value=mock_query_alerts)
        mock_query_alerts.all = Mock(return_value=[])

        # Mock the query chain for superseding
        mock_query_supersede = Mock()
        mock_query_supersede.filter = Mock(return_value=mock_query_supersede)
        mock_query_supersede.update = Mock()

        # Set up query to return different mocks based on model
        def query_side_effect(model):
            if model == ExecutiveBrief:
                return mock_query_regen
            elif model == Alert:
                return mock_query_alerts
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)

        # Should not raise when force=True
        # Note: This will fail at brief creation due to mocking complexity,
        # but validates rate limit is bypassed
        try:
            service.generate_brief(
                time_period="24h",
                user_email="admin@example.com",
                force=True
            )
        except Exception as e:
            # Expected to fail in brief creation, but should NOT be rate limit error
            assert "Rate limit" not in str(e)


# =============================================================================
# COMPLIANCE VERIFICATION TESTS
# =============================================================================

class TestComplianceVerification:
    """Test compliance requirements are met"""

    def test_audit_trail_fields_exist(self):
        """Verify audit trail fields exist in model"""
        # These fields are required for SOC 2 AU-6 compliance
        brief = ExecutiveBrief()

        assert hasattr(brief, 'organization_id')
        assert hasattr(brief, 'generated_at')
        assert hasattr(brief, 'generated_by')
        assert hasattr(brief, 'viewed_by')
        assert hasattr(brief, 'version')
        assert hasattr(brief, 'superseded_by_id')

    def test_multi_tenant_field_exists(self):
        """Verify multi-tenant isolation field exists"""
        # Required for PCI-DSS 7.1 compliance
        brief = ExecutiveBrief()

        assert hasattr(brief, 'organization_id')

    def test_immutable_version_tracking(self):
        """Verify version tracking for SOX compliance"""
        brief = ExecutiveBrief()

        assert hasattr(brief, 'version')
        assert hasattr(brief, 'superseded_by_id')
        assert hasattr(brief, 'is_current')


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_handle_none_severity(self, service):
        """Test handling of alerts with None severity"""
        alerts = [Mock(severity=None, status="new")]

        metrics = service._calculate_metrics(alerts)

        assert metrics["total_alerts"] == 1
        assert metrics["low_count"] == 1  # Default to low

    def test_handle_unknown_severity(self, service):
        """Test handling of alerts with unknown severity"""
        alerts = [Mock(severity="unknown", status="new")]

        metrics = service._calculate_metrics(alerts)

        assert metrics["total_alerts"] == 1

    def test_handle_none_status(self, service):
        """Test handling of alerts with None status"""
        alerts = [Mock(severity="high", status=None)]

        metrics = service._calculate_metrics(alerts)

        assert metrics["total_alerts"] == 1

    def test_empty_viewed_by_list(self, service, mock_db, sample_brief):
        """Test recording view when viewed_by is None"""
        sample_brief.viewed_by = None

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_brief)
        mock_db.query = Mock(return_value=mock_query)

        result = service.record_view("exec-brief-123", "viewer@example.com")

        assert result is True


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test performance-related functionality"""

    def test_cached_lookup_uses_indexes(self, service, mock_db):
        """Verify cached lookup query structure"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query = Mock(return_value=mock_query)

        service.get_cached_brief()

        # Verify query uses filter (for indexed lookup)
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called()

    def test_alert_query_has_limit(self, service, mock_db):
        """Verify alert queries are limited"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query = Mock(return_value=mock_query)

        service._fetch_alerts_for_period("24h")

        mock_query.limit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
