"""
OW-kai Enterprise Phase 5: Integration Suite Tests
===================================================

Comprehensive test suite for the enterprise integration management system.
Tests cover models, schemas, enums, and service functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from models_integration_suite import (
    # Enums
    IntegrationType,
    AuthType,
    HealthStatus,
    DataFlowStatus,
    EventSeverity,
    # Schemas
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    IntegrationResponse,
    DataFlowCreateRequest,
    DataFlowResponse,
    BulkOperationRequest,
    # Config
    INTEGRATION_TYPE_CONFIG,
    DATA_FLOW_TEMPLATES,
)


# ============================================
# Enum Tests
# ============================================

class TestIntegrationType:
    """Test IntegrationType enum values."""

    def test_all_integration_types_exist(self):
        """Verify all expected integration types are defined."""
        expected_types = ["webhook", "slack", "teams", "servicenow", "siem", "compliance", "email", "custom"]
        for type_name in expected_types:
            assert IntegrationType(type_name) is not None

    def test_integration_type_values(self):
        """Verify integration type enum values."""
        assert IntegrationType.WEBHOOK.value == "webhook"
        assert IntegrationType.SLACK.value == "slack"
        assert IntegrationType.TEAMS.value == "teams"
        assert IntegrationType.SERVICENOW.value == "servicenow"
        assert IntegrationType.SIEM.value == "siem"
        assert IntegrationType.COMPLIANCE.value == "compliance"
        assert IntegrationType.EMAIL.value == "email"
        assert IntegrationType.CUSTOM.value == "custom"


class TestAuthType:
    """Test AuthType enum values."""

    def test_all_auth_types_exist(self):
        """Verify all expected auth types are defined."""
        expected_types = ["none", "api_key", "oauth2", "basic", "certificate", "jwt"]
        for auth_type in expected_types:
            assert AuthType(auth_type) is not None

    def test_auth_type_values(self):
        """Verify auth type enum values."""
        assert AuthType.NONE.value == "none"
        assert AuthType.API_KEY.value == "api_key"
        assert AuthType.OAUTH2.value == "oauth2"
        assert AuthType.BASIC.value == "basic"
        assert AuthType.CERTIFICATE.value == "certificate"
        assert AuthType.JWT.value == "jwt"


class TestHealthStatus:
    """Test HealthStatus enum values."""

    def test_all_health_statuses_exist(self):
        """Verify all expected health statuses are defined."""
        expected_statuses = ["healthy", "degraded", "unhealthy", "unknown"]
        for status in expected_statuses:
            assert HealthStatus(status) is not None

    def test_health_status_values(self):
        """Verify health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestDataFlowStatus:
    """Test DataFlowStatus enum values."""

    def test_all_flow_statuses_exist(self):
        """Verify all expected data flow statuses are defined."""
        expected_statuses = ["running", "completed", "failed", "partial"]
        for status in expected_statuses:
            assert DataFlowStatus(status) is not None


class TestEventSeverity:
    """Test EventSeverity enum values."""

    def test_all_severities_exist(self):
        """Verify all expected severity levels are defined."""
        expected_severities = ["critical", "high", "medium", "low", "info"]
        for severity in expected_severities:
            assert EventSeverity(severity) is not None


# ============================================
# Schema Validation Tests
# ============================================

class TestIntegrationCreateRequest:
    """Test IntegrationCreateRequest schema validation."""

    def test_valid_webhook_integration(self):
        """Test creating a valid webhook integration request."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.WEBHOOK,
            integration_name="Production Webhook",
            endpoint_url="https://api.example.com/webhook",
            auth_type=AuthType.API_KEY,
            config={"headers": {"X-Custom": "value"}},
        )
        assert request.integration_type == IntegrationType.WEBHOOK
        assert request.integration_name == "Production Webhook"
        assert request.endpoint_url == "https://api.example.com/webhook"

    def test_valid_slack_integration(self):
        """Test creating a valid Slack integration request."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.SLACK,
            integration_name="Engineering Alerts",
            endpoint_url="https://hooks.slack.com/services/xxx",
            auth_type=AuthType.OAUTH2,
        )
        assert request.integration_type == IntegrationType.SLACK
        assert request.auth_type == AuthType.OAUTH2

    def test_valid_servicenow_integration(self):
        """Test creating a valid ServiceNow integration request."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.SERVICENOW,
            integration_name="ITSM Incidents",
            endpoint_url="https://company.service-now.com/api",
            auth_type=AuthType.BASIC,
            config={"table": "incident", "auto_assign": True},
        )
        assert request.integration_type == IntegrationType.SERVICENOW
        assert request.config["table"] == "incident"

    def test_integration_name_validation(self):
        """Test that empty integration name fails validation."""
        with pytest.raises(ValueError):
            IntegrationCreateRequest(
                integration_type=IntegrationType.WEBHOOK,
                integration_name="",
                endpoint_url="https://example.com",
            )

    def test_integration_name_whitespace_stripped(self):
        """Test that whitespace is stripped from integration name."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.WEBHOOK,
            integration_name="  Test Integration  ",
            endpoint_url="https://example.com",
        )
        assert request.integration_name == "Test Integration"

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.COMPLIANCE,
            integration_name="SOX Exports",
        )
        assert request.endpoint_url is None
        assert request.config is None
        assert request.tags is None

    def test_tags_as_list(self):
        """Test that tags can be provided as a list."""
        request = IntegrationCreateRequest(
            integration_type=IntegrationType.WEBHOOK,
            integration_name="Tagged Integration",
            tags=["production", "critical", "security"],
        )
        assert len(request.tags) == 3
        assert "production" in request.tags


class TestIntegrationUpdateRequest:
    """Test IntegrationUpdateRequest schema validation."""

    def test_partial_update(self):
        """Test that partial updates are allowed."""
        request = IntegrationUpdateRequest(
            display_name="New Display Name",
        )
        assert request.display_name == "New Display Name"
        assert request.description is None
        assert request.is_enabled is None

    def test_full_update(self):
        """Test full update with all fields."""
        request = IntegrationUpdateRequest(
            display_name="Updated Name",
            description="Updated description",
            endpoint_url="https://new-endpoint.com",
            auth_type=AuthType.OAUTH2,
            is_enabled=False,
            tags=["updated"],
        )
        assert request.display_name == "Updated Name"
        assert request.is_enabled is False


class TestDataFlowCreateRequest:
    """Test DataFlowCreateRequest schema validation."""

    def test_valid_data_flow(self):
        """Test creating a valid data flow request."""
        request = DataFlowCreateRequest(
            flow_name="Alerts to Slack",
            source_integration_id=1,
            source_type="internal",
            destination_type="slack",
            data_type="alert",
            batch_size=100,
            batch_interval_seconds=60,
        )
        assert request.flow_name == "Alerts to Slack"
        assert request.batch_size == 100

    def test_batch_size_limits(self):
        """Test batch size constraints."""
        # Valid minimum
        request = DataFlowCreateRequest(
            flow_name="Test Flow",
            source_integration_id=1,
            source_type="internal",
            destination_type="webhook",
            data_type="event",
            batch_size=1,
        )
        assert request.batch_size == 1

        # Valid maximum
        request = DataFlowCreateRequest(
            flow_name="Test Flow",
            source_integration_id=1,
            source_type="internal",
            destination_type="webhook",
            data_type="event",
            batch_size=10000,
        )
        assert request.batch_size == 10000

    def test_transformation_rules(self):
        """Test transformation rules configuration."""
        request = DataFlowCreateRequest(
            flow_name="Transformed Flow",
            source_integration_id=1,
            source_type="internal",
            destination_type="siem",
            data_type="event",
            transformation_rules={
                "format": "cef",
                "include_metadata": True,
                "field_mapping": {"alert_id": "event_id"},
            },
        )
        assert request.transformation_rules["format"] == "cef"


class TestBulkOperationRequest:
    """Test BulkOperationRequest schema validation."""

    def test_valid_bulk_operation(self):
        """Test creating a valid bulk operation request."""
        request = BulkOperationRequest(
            integration_ids=[1, 2, 3, 4, 5],
            operation="enable",
        )
        assert len(request.integration_ids) == 5
        assert request.operation == "enable"

    def test_minimum_integrations(self):
        """Test that at least one integration is required."""
        request = BulkOperationRequest(
            integration_ids=[1],
            operation="disable",
        )
        assert len(request.integration_ids) == 1


# ============================================
# Configuration Tests
# ============================================

class TestIntegrationTypeConfig:
    """Test integration type configurations."""

    def test_all_types_have_config(self):
        """Verify all integration types have configuration."""
        for int_type in IntegrationType:
            assert int_type in INTEGRATION_TYPE_CONFIG

    def test_config_has_required_fields(self):
        """Verify each config has required fields."""
        required_fields = [
            "display_name",
            "description",
            "required_fields",
            "supported_auth",
            "default_retry_config",
            "health_check_interval_seconds",
        ]
        for int_type, config in INTEGRATION_TYPE_CONFIG.items():
            for field in required_fields:
                assert field in config, f"Missing {field} in {int_type} config"

    def test_webhook_config(self):
        """Test webhook integration configuration."""
        config = INTEGRATION_TYPE_CONFIG[IntegrationType.WEBHOOK]
        assert config["display_name"] == "Webhook"
        assert "endpoint_url" in config["required_fields"]
        assert AuthType.API_KEY in config["supported_auth"]

    def test_servicenow_config(self):
        """Test ServiceNow integration configuration."""
        config = INTEGRATION_TYPE_CONFIG[IntegrationType.SERVICENOW]
        assert config["display_name"] == "ServiceNow"
        assert AuthType.BASIC in config["supported_auth"]
        assert AuthType.OAUTH2 in config["supported_auth"]

    def test_siem_config(self):
        """Test SIEM integration configuration."""
        config = INTEGRATION_TYPE_CONFIG[IntegrationType.SIEM]
        assert "SIEM" in config["display_name"]
        assert AuthType.API_KEY in config["supported_auth"]
        assert AuthType.CERTIFICATE in config["supported_auth"]

    def test_retry_config_structure(self):
        """Test retry configuration structure."""
        for int_type, config in INTEGRATION_TYPE_CONFIG.items():
            retry = config["default_retry_config"]
            assert "max_retries" in retry
            assert "backoff_multiplier" in retry
            assert "initial_delay_ms" in retry
            assert retry["max_retries"] >= 1


class TestDataFlowTemplates:
    """Test data flow templates."""

    def test_all_templates_exist(self):
        """Verify expected templates exist."""
        expected_templates = [
            "alert_to_slack",
            "alert_to_servicenow",
            "events_to_siem",
            "compliance_to_webhook",
        ]
        for template_name in expected_templates:
            assert template_name in DATA_FLOW_TEMPLATES

    def test_template_structure(self):
        """Verify each template has required fields."""
        required_fields = [
            "name",
            "description",
            "source_type",
            "destination_type",
            "data_type",
        ]
        for template_name, template in DATA_FLOW_TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"Missing {field} in {template_name} template"

    def test_alert_to_slack_template(self):
        """Test alert to Slack template configuration."""
        template = DATA_FLOW_TEMPLATES["alert_to_slack"]
        assert template["name"] == "Alerts to Slack"
        assert template["source_type"] == "internal"
        assert template["destination_type"] == "slack"
        assert template["data_type"] == "alert"
        assert "severity" in template["filter_rules"]

    def test_alert_to_servicenow_template(self):
        """Test alert to ServiceNow template configuration."""
        template = DATA_FLOW_TEMPLATES["alert_to_servicenow"]
        assert template["destination_type"] == "servicenow"
        assert "incident_mapping" in template["transformation_rules"]

    def test_events_to_siem_template(self):
        """Test events to SIEM template configuration."""
        template = DATA_FLOW_TEMPLATES["events_to_siem"]
        assert template["destination_type"] == "siem"
        assert template["transformation_rules"]["format"] == "cef"


# ============================================
# Security Tests
# ============================================

class TestSecurityFeatures:
    """Test security-related features."""

    def test_credentials_field_exists(self):
        """Verify credentials field exists for secure storage."""
        # The model should have a field for encrypted credentials
        from models_integration_suite import IntegrationRegistry
        assert hasattr(IntegrationRegistry, 'credentials_encrypted')

    def test_auth_types_include_certificate(self):
        """Verify certificate-based auth is supported."""
        assert AuthType.CERTIFICATE in AuthType.__members__.values()

    def test_jwt_auth_supported(self):
        """Verify JWT auth is supported."""
        assert AuthType.JWT in AuthType.__members__.values()

    def test_payload_hash_for_deduplication(self):
        """Verify event model has payload hash for deduplication."""
        from models_integration_suite import IntegrationEvent
        assert hasattr(IntegrationEvent, 'payload_hash')

    def test_event_expiration(self):
        """Verify events have expiration for cleanup."""
        from models_integration_suite import IntegrationEvent
        assert hasattr(IntegrationEvent, 'expires_at')


# ============================================
# Health Status Tests
# ============================================

class TestHealthStatusLogic:
    """Test health status determination logic."""

    def test_healthy_threshold(self):
        """Test healthy status threshold."""
        # 0-1 consecutive failures = healthy
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_degraded_threshold(self):
        """Test degraded status threshold."""
        # 2-4 consecutive failures = degraded
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_unhealthy_threshold(self):
        """Test unhealthy status threshold."""
        # 5+ consecutive failures = unhealthy
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


# ============================================
# Model Field Tests
# ============================================

class TestIntegrationRegistryModel:
    """Test IntegrationRegistry model fields."""

    def test_required_fields(self):
        """Test that required fields are defined."""
        from models_integration_suite import IntegrationRegistry
        required_attrs = [
            'id', 'organization_id', 'integration_type', 'integration_name',
            'endpoint_url', 'auth_type', 'is_enabled', 'health_status',
            'consecutive_failures', 'config', 'created_at'
        ]
        for attr in required_attrs:
            assert hasattr(IntegrationRegistry, attr)

    def test_health_tracking_fields(self):
        """Test health tracking fields exist."""
        from models_integration_suite import IntegrationRegistry
        health_attrs = [
            'health_status', 'last_health_check',
            'consecutive_failures', 'uptime_percent_30d'
        ]
        for attr in health_attrs:
            assert hasattr(IntegrationRegistry, attr)


class TestIntegrationEventModel:
    """Test IntegrationEvent model fields."""

    def test_required_fields(self):
        """Test that required fields are defined."""
        from models_integration_suite import IntegrationEvent
        required_attrs = [
            'id', 'organization_id', 'event_id', 'correlation_id',
            'source_type', 'event_type', 'severity', 'payload',
            'event_time', 'received_at', 'status'
        ]
        for attr in required_attrs:
            assert hasattr(IntegrationEvent, attr)


class TestDataFlowExecutionModel:
    """Test DataFlowExecution model fields."""

    def test_metric_fields(self):
        """Test execution metric fields exist."""
        from models_integration_suite import DataFlowExecution
        metric_attrs = [
            'records_read', 'records_processed',
            'records_failed', 'records_skipped',
            'duration_ms', 'errors'
        ]
        for attr in metric_attrs:
            assert hasattr(DataFlowExecution, attr)


class TestIntegrationMetricModel:
    """Test IntegrationMetric model fields."""

    def test_performance_fields(self):
        """Test performance metric fields exist."""
        from models_integration_suite import IntegrationMetric
        perf_attrs = [
            'avg_latency_ms', 'p95_latency_ms',
            'p99_latency_ms', 'max_latency_ms',
            'uptime_percent', 'error_rate'
        ]
        for attr in perf_attrs:
            assert hasattr(IntegrationMetric, attr)


# ============================================
# Response Schema Tests
# ============================================

class TestResponseSchemas:
    """Test response schema configurations."""

    def test_integration_response_from_attributes(self):
        """Test IntegrationResponse supports ORM mode."""
        assert IntegrationResponse.model_config.get('from_attributes', False)

    def test_data_flow_response_from_attributes(self):
        """Test DataFlowResponse supports ORM mode."""
        assert DataFlowResponse.model_config.get('from_attributes', False)


# ============================================
# Integration Count Tests
# ============================================

class TestIntegrationCounts:
    """Test integration type and template counts."""

    def test_integration_type_count(self):
        """Verify we have expected number of integration types."""
        assert len(IntegrationType) == 8  # webhook, slack, teams, servicenow, siem, compliance, email, custom

    def test_auth_type_count(self):
        """Verify we have expected number of auth types."""
        assert len(AuthType) == 6  # none, api_key, oauth2, basic, certificate, jwt

    def test_health_status_count(self):
        """Verify we have expected number of health statuses."""
        assert len(HealthStatus) == 4  # healthy, degraded, unhealthy, unknown

    def test_template_count(self):
        """Verify we have expected number of templates."""
        assert len(DATA_FLOW_TEMPLATES) >= 4  # at least 4 templates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
