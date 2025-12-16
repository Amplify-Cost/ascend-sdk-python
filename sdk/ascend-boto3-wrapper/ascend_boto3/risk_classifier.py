"""
AWS Operation Risk Classifier
==============================

Classifies AWS API operations by risk level for governance decisions.

This module provides risk scoring for AWS SDK operations based on:
- Operation type (read, write, delete, admin)
- Service category (compute, storage, IAM, etc.)
- Potential impact (reversibility, blast radius)

Risk Levels:
    LOW (0-44):      Read-only operations, no state changes
    MEDIUM (45-69):  Write operations, reversible changes
    HIGH (70-84):    Destructive operations, difficult to reverse
    CRITICAL (85-100): Administrative operations, wide impact

Created: 2025-12-09
"""

from enum import Enum
from typing import Dict, Tuple, Optional
import re


class RiskLevel(str, Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# AWS operation risk mappings by service and operation pattern
# Format: (risk_score, risk_level)
AWS_OPERATION_RISKS: Dict[str, Dict[str, Tuple[int, RiskLevel]]] = {
    # S3 Operations
    "s3": {
        "list_buckets": (15, RiskLevel.LOW),
        "list_objects": (15, RiskLevel.LOW),
        "list_objects_v2": (15, RiskLevel.LOW),
        "head_bucket": (10, RiskLevel.LOW),
        "head_object": (10, RiskLevel.LOW),
        "get_object": (20, RiskLevel.LOW),
        "get_bucket_location": (15, RiskLevel.LOW),
        "get_bucket_acl": (20, RiskLevel.LOW),
        "put_object": (45, RiskLevel.MEDIUM),
        "copy_object": (45, RiskLevel.MEDIUM),
        "create_bucket": (55, RiskLevel.MEDIUM),
        "put_bucket_acl": (70, RiskLevel.HIGH),
        "put_bucket_policy": (75, RiskLevel.HIGH),
        "delete_object": (65, RiskLevel.MEDIUM),
        "delete_objects": (75, RiskLevel.HIGH),
        "delete_bucket": (95, RiskLevel.CRITICAL),
        "delete_bucket_policy": (80, RiskLevel.HIGH),
    },

    # EC2 Operations
    "ec2": {
        "describe_instances": (15, RiskLevel.LOW),
        "describe_vpcs": (15, RiskLevel.LOW),
        "describe_security_groups": (15, RiskLevel.LOW),
        "describe_subnets": (15, RiskLevel.LOW),
        "describe_volumes": (15, RiskLevel.LOW),
        "run_instances": (60, RiskLevel.MEDIUM),
        "start_instances": (50, RiskLevel.MEDIUM),
        "stop_instances": (55, RiskLevel.MEDIUM),
        "reboot_instances": (50, RiskLevel.MEDIUM),
        "create_security_group": (65, RiskLevel.MEDIUM),
        "authorize_security_group_ingress": (75, RiskLevel.HIGH),
        "authorize_security_group_egress": (75, RiskLevel.HIGH),
        "revoke_security_group_ingress": (70, RiskLevel.HIGH),
        "terminate_instances": (90, RiskLevel.CRITICAL),
        "delete_security_group": (80, RiskLevel.HIGH),
        "delete_vpc": (90, RiskLevel.CRITICAL),
    },

    # IAM Operations (highest risk)
    "iam": {
        "list_users": (20, RiskLevel.LOW),
        "list_roles": (20, RiskLevel.LOW),
        "list_policies": (20, RiskLevel.LOW),
        "get_user": (20, RiskLevel.LOW),
        "get_role": (20, RiskLevel.LOW),
        "get_policy": (20, RiskLevel.LOW),
        "create_user": (80, RiskLevel.HIGH),
        "create_role": (80, RiskLevel.HIGH),
        "create_policy": (75, RiskLevel.HIGH),
        "attach_user_policy": (85, RiskLevel.CRITICAL),
        "attach_role_policy": (85, RiskLevel.CRITICAL),
        "put_user_policy": (85, RiskLevel.CRITICAL),
        "put_role_policy": (85, RiskLevel.CRITICAL),
        "create_access_key": (90, RiskLevel.CRITICAL),
        "delete_user": (95, RiskLevel.CRITICAL),
        "delete_role": (95, RiskLevel.CRITICAL),
        "update_assume_role_policy": (90, RiskLevel.CRITICAL),
    },

    # RDS Operations
    "rds": {
        "describe_db_instances": (15, RiskLevel.LOW),
        "describe_db_clusters": (15, RiskLevel.LOW),
        "describe_db_snapshots": (15, RiskLevel.LOW),
        "create_db_instance": (65, RiskLevel.MEDIUM),
        "create_db_cluster": (65, RiskLevel.MEDIUM),
        "modify_db_instance": (70, RiskLevel.HIGH),
        "start_db_instance": (50, RiskLevel.MEDIUM),
        "stop_db_instance": (55, RiskLevel.MEDIUM),
        "reboot_db_instance": (55, RiskLevel.MEDIUM),
        "delete_db_instance": (90, RiskLevel.CRITICAL),
        "delete_db_cluster": (95, RiskLevel.CRITICAL),
        "delete_db_snapshot": (75, RiskLevel.HIGH),
    },

    # Lambda Operations
    "lambda": {
        "list_functions": (15, RiskLevel.LOW),
        "get_function": (20, RiskLevel.LOW),
        "get_function_configuration": (20, RiskLevel.LOW),
        "invoke": (45, RiskLevel.MEDIUM),
        "create_function": (60, RiskLevel.MEDIUM),
        "update_function_code": (70, RiskLevel.HIGH),
        "update_function_configuration": (65, RiskLevel.MEDIUM),
        "delete_function": (80, RiskLevel.HIGH),
        "add_permission": (75, RiskLevel.HIGH),
    },

    # DynamoDB Operations
    "dynamodb": {
        "list_tables": (15, RiskLevel.LOW),
        "describe_table": (15, RiskLevel.LOW),
        "get_item": (20, RiskLevel.LOW),
        "query": (25, RiskLevel.LOW),
        "scan": (30, RiskLevel.LOW),
        "put_item": (45, RiskLevel.MEDIUM),
        "update_item": (50, RiskLevel.MEDIUM),
        "batch_write_item": (60, RiskLevel.MEDIUM),
        "delete_item": (55, RiskLevel.MEDIUM),
        "create_table": (60, RiskLevel.MEDIUM),
        "delete_table": (90, RiskLevel.CRITICAL),
    },

    # SQS Operations
    "sqs": {
        "list_queues": (15, RiskLevel.LOW),
        "get_queue_url": (15, RiskLevel.LOW),
        "get_queue_attributes": (15, RiskLevel.LOW),
        "receive_message": (25, RiskLevel.LOW),
        "send_message": (40, RiskLevel.LOW),
        "send_message_batch": (45, RiskLevel.MEDIUM),
        "delete_message": (45, RiskLevel.MEDIUM),
        "purge_queue": (70, RiskLevel.HIGH),
        "create_queue": (50, RiskLevel.MEDIUM),
        "delete_queue": (75, RiskLevel.HIGH),
    },

    # SNS Operations
    "sns": {
        "list_topics": (15, RiskLevel.LOW),
        "list_subscriptions": (15, RiskLevel.LOW),
        "get_topic_attributes": (15, RiskLevel.LOW),
        "publish": (40, RiskLevel.LOW),
        "create_topic": (50, RiskLevel.MEDIUM),
        "subscribe": (50, RiskLevel.MEDIUM),
        "unsubscribe": (45, RiskLevel.MEDIUM),
        "delete_topic": (70, RiskLevel.HIGH),
    },

    # CloudFormation Operations
    "cloudformation": {
        "list_stacks": (15, RiskLevel.LOW),
        "describe_stacks": (15, RiskLevel.LOW),
        "describe_stack_resources": (15, RiskLevel.LOW),
        "get_template": (20, RiskLevel.LOW),
        "create_stack": (75, RiskLevel.HIGH),
        "update_stack": (80, RiskLevel.HIGH),
        "delete_stack": (95, RiskLevel.CRITICAL),
    },

    # Secrets Manager Operations
    "secretsmanager": {
        "list_secrets": (25, RiskLevel.LOW),
        "describe_secret": (25, RiskLevel.LOW),
        "get_secret_value": (45, RiskLevel.MEDIUM),
        "create_secret": (60, RiskLevel.MEDIUM),
        "put_secret_value": (70, RiskLevel.HIGH),
        "update_secret": (70, RiskLevel.HIGH),
        "delete_secret": (85, RiskLevel.CRITICAL),
        "restore_secret": (65, RiskLevel.MEDIUM),
    },

    # KMS Operations
    "kms": {
        "list_keys": (20, RiskLevel.LOW),
        "describe_key": (20, RiskLevel.LOW),
        "encrypt": (35, RiskLevel.LOW),
        "decrypt": (45, RiskLevel.MEDIUM),
        "generate_data_key": (45, RiskLevel.MEDIUM),
        "create_key": (70, RiskLevel.HIGH),
        "enable_key": (60, RiskLevel.MEDIUM),
        "disable_key": (75, RiskLevel.HIGH),
        "schedule_key_deletion": (95, RiskLevel.CRITICAL),
    },
}

# Default risk patterns for operations not explicitly mapped
DEFAULT_PATTERNS: Dict[str, Tuple[int, RiskLevel]] = {
    r"^list_": (15, RiskLevel.LOW),
    r"^get_": (20, RiskLevel.LOW),
    r"^describe_": (15, RiskLevel.LOW),
    r"^head_": (10, RiskLevel.LOW),
    r"^put_": (50, RiskLevel.MEDIUM),
    r"^create_": (55, RiskLevel.MEDIUM),
    r"^update_": (60, RiskLevel.MEDIUM),
    r"^modify_": (65, RiskLevel.MEDIUM),
    r"^start_": (50, RiskLevel.MEDIUM),
    r"^stop_": (55, RiskLevel.MEDIUM),
    r"^reboot_": (50, RiskLevel.MEDIUM),
    r"^delete_": (75, RiskLevel.HIGH),
    r"^remove_": (70, RiskLevel.HIGH),
    r"^terminate_": (85, RiskLevel.CRITICAL),
    r"^revoke_": (70, RiskLevel.HIGH),
    r"^attach_": (70, RiskLevel.HIGH),
    r"^detach_": (65, RiskLevel.MEDIUM),
}


def classify_operation_risk(
    service: str,
    operation: str,
    params: Optional[Dict] = None
) -> Tuple[int, RiskLevel]:
    """
    Classify the risk level of an AWS operation.

    Args:
        service: AWS service name (e.g., 's3', 'ec2', 'iam')
        operation: Operation name (e.g., 'delete_bucket', 'list_objects')
        params: Operation parameters (optional, for context-aware scoring)

    Returns:
        Tuple of (risk_score, risk_level)

    Example:
        >>> classify_operation_risk('s3', 'delete_bucket')
        (95, RiskLevel.CRITICAL)
        >>> classify_operation_risk('s3', 'list_objects')
        (15, RiskLevel.LOW)
    """
    service = service.lower()
    operation = operation.lower()

    # Check explicit mappings first
    if service in AWS_OPERATION_RISKS:
        if operation in AWS_OPERATION_RISKS[service]:
            return AWS_OPERATION_RISKS[service][operation]

    # Fall back to pattern matching
    for pattern, risk in DEFAULT_PATTERNS.items():
        if re.match(pattern, operation):
            return risk

    # Default to medium risk for unknown operations
    return (50, RiskLevel.MEDIUM)


def get_risk_description(risk_level: RiskLevel) -> str:
    """Get human-readable description of risk level."""
    descriptions = {
        RiskLevel.LOW: "Read-only operation, no state changes",
        RiskLevel.MEDIUM: "Write operation, reversible changes",
        RiskLevel.HIGH: "Destructive operation, difficult to reverse",
        RiskLevel.CRITICAL: "Administrative operation, wide impact potential",
    }
    return descriptions.get(risk_level, "Unknown risk level")
