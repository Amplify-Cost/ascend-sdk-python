"""
Tests for AWS Operation Risk Classifier
========================================

P0.4: Launch Critical - Boto3 Wrapper Tests

Tests the risk classification logic for AWS operations.
"""

import pytest
from ascend_boto3.risk_classifier import (
    classify_operation_risk,
    RiskLevel,
    AWS_OPERATION_RISKS,
    get_risk_description,
)


class TestRiskClassifier:
    """Test risk classification for AWS operations."""

    def test_s3_list_buckets_low_risk(self):
        """Test list_buckets is classified as low risk."""
        score, level = classify_operation_risk("s3", "list_buckets")
        assert level == RiskLevel.LOW
        assert score <= 44

    def test_s3_delete_bucket_critical_risk(self):
        """Test delete_bucket is classified as critical risk."""
        score, level = classify_operation_risk("s3", "delete_bucket")
        assert level == RiskLevel.CRITICAL
        assert score >= 85

    def test_s3_put_object_medium_risk(self):
        """Test put_object is classified as medium risk."""
        score, level = classify_operation_risk("s3", "put_object")
        assert level == RiskLevel.MEDIUM
        assert 45 <= score <= 69

    def test_ec2_describe_instances_low_risk(self):
        """Test describe_instances is classified as low risk."""
        score, level = classify_operation_risk("ec2", "describe_instances")
        assert level == RiskLevel.LOW

    def test_ec2_terminate_instances_critical_risk(self):
        """Test terminate_instances is classified as critical risk."""
        score, level = classify_operation_risk("ec2", "terminate_instances")
        assert level == RiskLevel.CRITICAL

    def test_iam_create_user_high_risk(self):
        """Test IAM create_user is classified as high risk."""
        score, level = classify_operation_risk("iam", "create_user")
        assert level == RiskLevel.HIGH

    def test_iam_attach_user_policy_critical_risk(self):
        """Test IAM policy attachment is critical risk."""
        score, level = classify_operation_risk("iam", "attach_user_policy")
        assert level == RiskLevel.CRITICAL

    def test_unknown_operation_default_medium(self):
        """Test unknown operations default to medium risk."""
        score, level = classify_operation_risk("unknown_service", "unknown_operation")
        assert level == RiskLevel.MEDIUM

    def test_pattern_matching_list_prefix(self):
        """Test pattern matching for list_ prefix."""
        score, level = classify_operation_risk("unknown", "list_something")
        assert level == RiskLevel.LOW

    def test_pattern_matching_delete_prefix(self):
        """Test pattern matching for delete_ prefix."""
        score, level = classify_operation_risk("unknown", "delete_something")
        assert level == RiskLevel.HIGH

    def test_case_insensitive_service(self):
        """Test service name is case-insensitive."""
        score1, level1 = classify_operation_risk("S3", "list_buckets")
        score2, level2 = classify_operation_risk("s3", "list_buckets")
        assert level1 == level2

    def test_case_insensitive_operation(self):
        """Test operation name is case-insensitive."""
        score1, level1 = classify_operation_risk("s3", "LIST_BUCKETS")
        score2, level2 = classify_operation_risk("s3", "list_buckets")
        assert level1 == level2


class TestRiskDescriptions:
    """Test risk level descriptions."""

    def test_low_risk_description(self):
        """Test low risk description."""
        desc = get_risk_description(RiskLevel.LOW)
        assert "read-only" in desc.lower()

    def test_critical_risk_description(self):
        """Test critical risk description."""
        desc = get_risk_description(RiskLevel.CRITICAL)
        assert "administrative" in desc.lower() or "wide impact" in desc.lower()


class TestAllMappedOperations:
    """Verify all mapped operations have valid risk scores."""

    def test_all_operations_have_valid_scores(self):
        """Test all mapped operations have scores in valid range."""
        for service, operations in AWS_OPERATION_RISKS.items():
            for operation, (score, level) in operations.items():
                assert 0 <= score <= 100, f"{service}.{operation} has invalid score {score}"

    def test_all_operations_have_valid_levels(self):
        """Test all mapped operations have valid risk levels."""
        for service, operations in AWS_OPERATION_RISKS.items():
            for operation, (score, level) in operations.items():
                assert level in RiskLevel, f"{service}.{operation} has invalid level {level}"

    def test_score_matches_level(self):
        """Test score ranges match risk levels."""
        level_ranges = {
            RiskLevel.LOW: (0, 44),
            RiskLevel.MEDIUM: (45, 69),
            RiskLevel.HIGH: (70, 84),
            RiskLevel.CRITICAL: (85, 100),
        }

        for service, operations in AWS_OPERATION_RISKS.items():
            for operation, (score, level) in operations.items():
                min_score, max_score = level_ranges[level]
                assert min_score <= score <= max_score, (
                    f"{service}.{operation}: score {score} doesn't match level {level} "
                    f"(expected {min_score}-{max_score})"
                )
