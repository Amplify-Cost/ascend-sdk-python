"""
Tests for Boto3 Governance Wrapper
===================================

P0.4: Launch Critical - Boto3 Wrapper Tests

Tests the governance wrapper functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from ascend_boto3.wrapper import (
    GovernanceConfig,
    enable_governance,
    disable_governance,
    is_governance_enabled,
    _should_bypass,
    _sanitize_params,
    _extract_resource_id,
)
from ascend_boto3.risk_classifier import RiskLevel


class TestGovernanceConfig:
    """Test GovernanceConfig dataclass."""

    def test_config_with_defaults(self):
        """Test config creation with defaults."""
        config = GovernanceConfig(api_key="ascend_test_key")
        assert config.api_key == "ascend_test_key"
        assert config.base_url == "https://pilot.owkai.app"
        assert config.auto_approve_low_risk is True
        assert config.auto_approve_medium_risk is False
        assert config.agent_id is not None  # Auto-generated

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = GovernanceConfig(
            api_key="ascend_test_key",
            agent_id="custom-agent",
            agent_name="Custom Agent",
            auto_approve_medium_risk=True,
            bypass_services={"cloudwatch", "logs"}
        )
        assert config.agent_id == "custom-agent"
        assert config.agent_name == "Custom Agent"
        assert config.auto_approve_medium_risk is True
        assert "cloudwatch" in config.bypass_services

    def test_config_normalizes_bypass_sets(self):
        """Test bypass sets are normalized to lowercase."""
        config = GovernanceConfig(
            api_key="test",
            bypass_services={"CloudWatch", "LOGS"},
            bypass_operations={"S3.List_Buckets"}
        )
        assert "cloudwatch" in config.bypass_services
        assert "logs" in config.bypass_services
        assert "s3.list_buckets" in config.bypass_operations


class TestBypassLogic:
    """Test bypass logic for governance."""

    def test_bypass_by_service(self):
        """Test bypassing by service name."""
        config = GovernanceConfig(
            api_key="test",
            bypass_services={"cloudwatch"}
        )
        assert _should_bypass("cloudwatch", "put_metric_data", config) is True
        assert _should_bypass("s3", "put_object", config) is False

    def test_bypass_by_operation(self):
        """Test bypassing by specific operation."""
        config = GovernanceConfig(
            api_key="test",
            bypass_operations={"s3.list_buckets"}
        )
        assert _should_bypass("s3", "list_buckets", config) is True
        assert _should_bypass("s3", "delete_bucket", config) is False


class TestParamSanitization:
    """Test parameter sanitization for logging."""

    def test_redacts_sensitive_keys(self):
        """Test sensitive keys are redacted."""
        params = {
            "Bucket": "my-bucket",
            "Password": "secret123",
            "AccessKey": "AKIAIOSFODNN7EXAMPLE"
        }
        sanitized = _sanitize_params(params)

        assert sanitized["Bucket"] == "my-bucket"
        assert sanitized["Password"] == "[REDACTED]"
        assert sanitized["AccessKey"] == "[REDACTED]"

    def test_handles_nested_dicts(self):
        """Test nested dictionaries are sanitized."""
        params = {
            "Config": {
                "Username": "user",
                "Password": "secret"
            }
        }
        sanitized = _sanitize_params(params)

        assert sanitized["Config"]["Username"] == "user"
        assert sanitized["Config"]["Password"] == "[REDACTED]"

    def test_preserves_non_sensitive_data(self):
        """Test non-sensitive data is preserved."""
        params = {
            "Bucket": "my-bucket",
            "Key": "my-file.txt",  # 'Key' is common but not always sensitive
            "ContentType": "text/plain"
        }
        sanitized = _sanitize_params(params)

        # Note: Key might be redacted depending on implementation
        assert sanitized["Bucket"] == "my-bucket"
        assert sanitized["ContentType"] == "text/plain"


class TestResourceIdExtraction:
    """Test resource ID extraction from parameters."""

    def test_extracts_bucket_name(self):
        """Test extraction of S3 bucket name."""
        params = {"Bucket": "my-bucket", "Key": "file.txt"}
        resource_id = _extract_resource_id("s3", "get_object", params)
        assert resource_id == "my-bucket"

    def test_extracts_instance_ids(self):
        """Test extraction of EC2 instance IDs."""
        params = {"InstanceIds": ["i-1234", "i-5678"]}
        resource_id = _extract_resource_id("ec2", "terminate_instances", params)
        assert "i-1234" in resource_id
        assert "i-5678" in resource_id

    def test_extracts_table_name(self):
        """Test extraction of DynamoDB table name."""
        params = {"TableName": "my-table"}
        resource_id = _extract_resource_id("dynamodb", "delete_table", params)
        assert resource_id == "my-table"

    def test_returns_none_for_unknown_params(self):
        """Test returns None when no recognizable ID parameter."""
        params = {"SomeOtherParam": "value"}
        resource_id = _extract_resource_id("unknown", "unknown_op", params)
        assert resource_id is None


class TestGovernanceEnableDisable:
    """Test enable/disable governance functionality."""

    def test_is_governance_enabled_default_false(self):
        """Test governance is disabled by default."""
        # Ensure clean state
        disable_governance()
        assert is_governance_enabled() is False

    def test_enable_requires_api_key(self):
        """Test enable_governance requires API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                enable_governance()
            assert "API key required" in str(exc_info.value)

    def test_enable_accepts_env_api_key(self):
        """Test enable_governance accepts API key from environment."""
        with patch.dict(os.environ, {"ASCEND_API_KEY": "ascend_test_xxx_abc123"}):
            with patch("boto3.client"):
                with patch("botocore.client.ClientCreator.create_client"):
                    try:
                        enable_governance()
                        assert is_governance_enabled() is True
                    finally:
                        disable_governance()


class TestDryRunMode:
    """Test dry run mode functionality."""

    def test_dry_run_config(self):
        """Test dry run configuration."""
        config = GovernanceConfig(api_key="test", dry_run=True)
        assert config.dry_run is True

    def test_dry_run_default_false(self):
        """Test dry run defaults to False."""
        config = GovernanceConfig(api_key="test")
        assert config.dry_run is False
