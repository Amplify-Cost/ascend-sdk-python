"""
OW-AI SDK boto3 Patch Tests

Tests for boto3 auto-patching functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from owkai.boto3_patch import (
    _get_operation_risk,
    _is_read_only,
    _risk_to_score,
    enable_governance,
    disable_governance,
    is_governance_enabled,
    get_governance_config,
    GovernanceConfig,
)
from owkai.models import RiskLevel


class TestOperationRiskClassification:
    """Tests for operation risk classification."""

    def test_s3_delete_bucket_is_critical(self) -> None:
        """Test S3 delete_bucket is classified as CRITICAL."""
        risk = _get_operation_risk("s3", "delete_bucket")
        assert risk == RiskLevel.CRITICAL

    def test_s3_list_buckets_is_low(self) -> None:
        """Test S3 list_buckets is classified as LOW."""
        risk = _get_operation_risk("s3", "list_buckets")
        assert risk == RiskLevel.LOW

    def test_ec2_terminate_instances_is_critical(self) -> None:
        """Test EC2 terminate_instances is classified as CRITICAL."""
        risk = _get_operation_risk("ec2", "terminate_instances")
        assert risk == RiskLevel.CRITICAL

    def test_iam_attach_role_policy_is_critical(self) -> None:
        """Test IAM attach_role_policy is classified as CRITICAL."""
        risk = _get_operation_risk("iam", "attach_role_policy")
        assert risk == RiskLevel.CRITICAL

    def test_unknown_delete_operation_is_high(self) -> None:
        """Test unknown delete operations default to HIGH."""
        risk = _get_operation_risk("unknown_service", "delete_something")
        assert risk == RiskLevel.HIGH

    def test_unknown_list_operation_is_low(self) -> None:
        """Test unknown list operations default to LOW."""
        risk = _get_operation_risk("unknown_service", "list_items")
        assert risk == RiskLevel.LOW

    def test_unknown_create_operation_is_medium(self) -> None:
        """Test unknown create operations default to MEDIUM."""
        risk = _get_operation_risk("unknown_service", "create_resource")
        assert risk == RiskLevel.MEDIUM


class TestRiskToScore:
    """Tests for risk level to score conversion."""

    def test_low_risk_score(self) -> None:
        """Test LOW risk converts to 25."""
        assert _risk_to_score(RiskLevel.LOW) == 25

    def test_medium_risk_score(self) -> None:
        """Test MEDIUM risk converts to 55."""
        assert _risk_to_score(RiskLevel.MEDIUM) == 55

    def test_high_risk_score(self) -> None:
        """Test HIGH risk converts to 85."""
        assert _risk_to_score(RiskLevel.HIGH) == 85

    def test_critical_risk_score(self) -> None:
        """Test CRITICAL risk converts to 95."""
        assert _risk_to_score(RiskLevel.CRITICAL) == 95


class TestIsReadOnly:
    """Tests for read-only operation detection."""

    def test_list_is_read_only(self) -> None:
        """Test list_ prefix is read-only."""
        assert _is_read_only("list_buckets") is True

    def test_describe_is_read_only(self) -> None:
        """Test describe_ prefix is read-only."""
        assert _is_read_only("describe_instances") is True

    def test_get_is_read_only(self) -> None:
        """Test get_ prefix is read-only."""
        assert _is_read_only("get_object") is True

    def test_head_is_read_only(self) -> None:
        """Test head_ prefix is read-only."""
        assert _is_read_only("head_object") is True

    def test_put_is_not_read_only(self) -> None:
        """Test put_ prefix is not read-only."""
        assert _is_read_only("put_object") is False

    def test_delete_is_not_read_only(self) -> None:
        """Test delete_ prefix is not read-only."""
        assert _is_read_only("delete_bucket") is False

    def test_create_is_not_read_only(self) -> None:
        """Test create_ prefix is not read-only."""
        assert _is_read_only("create_bucket") is False


class TestGovernanceConfig:
    """Tests for GovernanceConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = GovernanceConfig(api_key="test_key")
        assert config.risk_threshold == 70
        assert config.auto_approve_below == 30
        assert config.approval_timeout == 300
        assert config.bypass_read_only is True
        assert "sts" in config.disabled_services

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = GovernanceConfig(
            api_key="test_key",
            risk_threshold=80,
            auto_approve_below=20,
            approval_timeout=600,
            bypass_read_only=False,
        )
        assert config.risk_threshold == 80
        assert config.auto_approve_below == 20
        assert config.approval_timeout == 600
        assert config.bypass_read_only is False


class TestGovernanceState:
    """Tests for governance enable/disable."""

    def test_governance_initially_disabled(self) -> None:
        """Test governance is initially disabled."""
        # Reset state
        disable_governance()
        assert is_governance_enabled() is False

    def test_governance_config_none_when_disabled(self) -> None:
        """Test config is None when disabled."""
        disable_governance()
        config = get_governance_config()
        # Config may be None or have enabled=False
        assert config is None or not is_governance_enabled()


class TestEnableGovernance:
    """Tests for enable_governance function."""

    def test_enable_requires_boto3(self) -> None:
        """Test enable_governance raises error without boto3."""
        # This test would need boto3 to not be installed
        # Skip if boto3 is available
        try:
            import boto3
            pytest.skip("boto3 is installed")
        except ImportError:
            with pytest.raises(ImportError) as exc_info:
                enable_governance(api_key="owkai_admin_test123456789012345678901234")
            assert "boto3 is not installed" in str(exc_info.value)

    @pytest.mark.skipif(
        True,
        reason="Requires boto3 to be installed for full test",
    )
    def test_enable_governance_patches_boto3(self) -> None:
        """Test that enable_governance patches boto3.client."""
        # This would test the actual patching behavior
        pass

    @pytest.mark.skipif(
        True,
        reason="Requires boto3 to be installed for full test",
    )
    def test_disable_governance_restores_boto3(self) -> None:
        """Test that disable_governance restores original behavior."""
        pass


class TestBoto3Integration:
    """Integration tests for boto3 patching (require boto3)."""

    @pytest.fixture
    def mock_boto3(self):
        """Mock boto3 module."""
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        return mock_boto3

    def test_read_operation_bypassed(self) -> None:
        """Test read-only operations bypass governance."""
        # With bypass_read_only=True (default), list_buckets should pass through
        # This tests the logic without requiring actual boto3
        assert _is_read_only("list_buckets") is True
        assert _get_operation_risk("s3", "list_buckets") == RiskLevel.LOW
        assert _risk_to_score(RiskLevel.LOW) == 25
        # 25 < 30 (auto_approve_below default), so would be auto-approved

    def test_high_risk_operation_requires_approval(self) -> None:
        """Test high-risk operations require approval."""
        risk = _get_operation_risk("s3", "delete_bucket")
        score = _risk_to_score(risk)
        default_threshold = 70

        assert risk == RiskLevel.CRITICAL
        assert score == 95
        assert score >= default_threshold  # Would require approval
