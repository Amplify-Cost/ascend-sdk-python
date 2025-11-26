#!/usr/bin/env python3
"""
OW-AI Integration Example 2: AWS Lambda with Governed boto3

USE CASE: Serverless functions that perform AWS operations (S3, EC2, RDS, IAM)
          with transparent governance - no code changes to existing boto3 calls.

This example shows how to:
1. Enable transparent boto3 governance with one line
2. Auto-approve low-risk operations (read operations)
3. Block/approve high-risk operations (delete, modify IAM, etc.)
4. Handle governance decisions in Lambda context

ARCHITECTURE:
    Lambda Trigger → Lambda Function → boto3 (patched)
                                            ↓
                                    OW-AI Governance Layer
                                            ↓
                                    Risk Assessment → Decision
                                            ↓
                                    AWS API (if approved)

RISK LEVELS BY OPERATION:
    ┌─────────────────────────────────────────────────────────┐
    │ CRITICAL (90-100): delete_bucket, terminate_instances,  │
    │                    delete_user, attach_role_policy      │
    │ HIGH (70-89):      delete_objects, modify_instance,     │
    │                    update_function_code                 │
    │ MEDIUM (40-69):    put_object, run_instances,          │
    │                    create_bucket                        │
    │ LOW (0-39):        list_*, get_*, describe_*           │
    └─────────────────────────────────────────────────────────┘

Engineer: OW-AI Enterprise
"""

import os
import json
import logging
from typing import Any, Dict
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================
# OW-AI GOVERNANCE SETUP
# ============================================

# IMPORTANT: Import and enable governance BEFORE importing boto3
from owkai.boto3_patch import enable_governance, disable_governance

# Enable governance with configuration
OWAI_API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
OWAI_BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")

enable_governance(
    api_key=OWAI_API_KEY,
    base_url=OWAI_BASE_URL,
    risk_threshold=70,        # Require approval for risk >= 70
    auto_approve_below=30,    # Auto-approve risk < 30
    bypass_read_only=True,    # Skip governance for read operations (faster)
    approval_timeout=60,      # Lambda timeout consideration (shorter)
    agent_id="aws-lambda-agent"
)

# Now import boto3 - all calls will be governed
import boto3


# ============================================
# LAMBDA HANDLER
# ============================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler with OW-AI governed boto3 operations.

    This handler demonstrates various AWS operations that are
    automatically governed by OW-AI based on risk level.

    Event Structure:
    {
        "operation": "list_buckets" | "put_object" | "delete_object" | etc.,
        "parameters": { ... operation-specific parameters ... }
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    operation = event.get("operation", "list_buckets")
    parameters = event.get("parameters", {})

    try:
        # Route to appropriate operation
        if operation == "list_buckets":
            result = operation_list_buckets()

        elif operation == "get_object":
            result = operation_get_object(
                bucket=parameters.get("bucket"),
                key=parameters.get("key")
            )

        elif operation == "put_object":
            result = operation_put_object(
                bucket=parameters.get("bucket"),
                key=parameters.get("key"),
                body=parameters.get("body", "")
            )

        elif operation == "delete_object":
            result = operation_delete_object(
                bucket=parameters.get("bucket"),
                key=parameters.get("key")
            )

        elif operation == "delete_bucket":
            result = operation_delete_bucket(
                bucket=parameters.get("bucket")
            )

        elif operation == "describe_instances":
            result = operation_describe_instances()

        elif operation == "terminate_instances":
            result = operation_terminate_instances(
                instance_ids=parameters.get("instance_ids", [])
            )

        else:
            result = {"error": f"Unknown operation: {operation}"}

        return {
            "statusCode": 200,
            "body": json.dumps(result, default=str)
        }

    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")

        # Check if this was a governance rejection
        error_message = str(e)
        if "rejected" in error_message.lower() or "approval" in error_message.lower():
            return {
                "statusCode": 403,
                "body": json.dumps({
                    "error": "Action blocked by OW-AI governance",
                    "details": error_message
                })
            }

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Operation failed",
                "details": error_message
            })
        }


# ============================================
# S3 OPERATIONS
# ============================================

def operation_list_buckets() -> Dict[str, Any]:
    """
    List S3 buckets - LOW RISK (auto-approved).

    Risk Score: ~15
    Governance: Bypassed (read-only) or auto-approved
    """
    logger.info("📋 Listing S3 buckets (low risk - auto-approved)")

    s3 = boto3.client("s3")
    response = s3.list_buckets()

    buckets = [
        {
            "name": bucket["Name"],
            "created": bucket["CreationDate"]
        }
        for bucket in response.get("Buckets", [])
    ]

    return {
        "operation": "list_buckets",
        "risk_level": "LOW",
        "governance": "auto-approved",
        "buckets": buckets
    }


def operation_get_object(bucket: str, key: str) -> Dict[str, Any]:
    """
    Get object from S3 - LOW RISK (auto-approved).

    Risk Score: ~25
    Governance: Bypassed (read-only) or auto-approved
    """
    logger.info(f"📥 Getting object s3://{bucket}/{key} (low risk)")

    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)

    return {
        "operation": "get_object",
        "risk_level": "LOW",
        "governance": "auto-approved",
        "bucket": bucket,
        "key": key,
        "content_type": response.get("ContentType"),
        "content_length": response.get("ContentLength"),
        "last_modified": response.get("LastModified")
    }


def operation_put_object(bucket: str, key: str, body: str) -> Dict[str, Any]:
    """
    Put object to S3 - MEDIUM RISK (may require approval).

    Risk Score: ~55
    Governance: Evaluated based on context
    """
    logger.info(f"📤 Putting object to s3://{bucket}/{key} (medium risk)")

    s3 = boto3.client("s3")
    response = s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="text/plain"
    )

    return {
        "operation": "put_object",
        "risk_level": "MEDIUM",
        "governance": "evaluated",
        "bucket": bucket,
        "key": key,
        "etag": response.get("ETag"),
        "version_id": response.get("VersionId")
    }


def operation_delete_object(bucket: str, key: str) -> Dict[str, Any]:
    """
    Delete object from S3 - HIGH RISK (requires approval).

    Risk Score: ~75
    Governance: Requires manual approval
    """
    logger.info(f"🗑️ Deleting object s3://{bucket}/{key} (high risk - requires approval)")

    s3 = boto3.client("s3")

    # This call will block until approved or timeout
    response = s3.delete_object(Bucket=bucket, Key=key)

    return {
        "operation": "delete_object",
        "risk_level": "HIGH",
        "governance": "approved",
        "bucket": bucket,
        "key": key,
        "deleted": True
    }


def operation_delete_bucket(bucket: str) -> Dict[str, Any]:
    """
    Delete S3 bucket - CRITICAL RISK (requires executive approval).

    Risk Score: ~95
    Governance: Requires L3 executive approval
    """
    logger.info(f"🚨 Deleting bucket {bucket} (CRITICAL risk - requires executive approval)")

    s3 = boto3.client("s3")

    # This call will block until approved or timeout
    # For CRITICAL operations, timeout may need to be longer
    response = s3.delete_bucket(Bucket=bucket)

    return {
        "operation": "delete_bucket",
        "risk_level": "CRITICAL",
        "governance": "approved (executive)",
        "bucket": bucket,
        "deleted": True
    }


# ============================================
# EC2 OPERATIONS
# ============================================

def operation_describe_instances() -> Dict[str, Any]:
    """
    Describe EC2 instances - LOW RISK (auto-approved).

    Risk Score: ~20
    Governance: Bypassed (read-only) or auto-approved
    """
    logger.info("📋 Describing EC2 instances (low risk)")

    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()

    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instances.append({
                "instance_id": instance["InstanceId"],
                "state": instance["State"]["Name"],
                "type": instance.get("InstanceType"),
                "launch_time": instance.get("LaunchTime")
            })

    return {
        "operation": "describe_instances",
        "risk_level": "LOW",
        "governance": "auto-approved",
        "instances": instances
    }


def operation_terminate_instances(instance_ids: list) -> Dict[str, Any]:
    """
    Terminate EC2 instances - CRITICAL RISK (requires executive approval).

    Risk Score: ~95
    Governance: Requires L3 executive approval
    """
    logger.info(f"🚨 Terminating instances {instance_ids} (CRITICAL risk)")

    if not instance_ids:
        return {"error": "No instance IDs provided"}

    ec2 = boto3.client("ec2")

    # This call will block until approved or timeout
    response = ec2.terminate_instances(InstanceIds=instance_ids)

    terminated = [
        {
            "instance_id": inst["InstanceId"],
            "previous_state": inst["PreviousState"]["Name"],
            "current_state": inst["CurrentState"]["Name"]
        }
        for inst in response.get("TerminatingInstances", [])
    ]

    return {
        "operation": "terminate_instances",
        "risk_level": "CRITICAL",
        "governance": "approved (executive)",
        "terminated_instances": terminated
    }


# ============================================
# GOVERNANCE CONTEXT HELPERS
# ============================================

def with_governance_context(operation_name: str, risk_override: str = None):
    """
    Decorator to add governance context to operations.

    Usage:
        @with_governance_context("custom_operation", risk_override="high")
        def my_operation():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"[OW-AI] Starting governed operation: {operation_name}")

            try:
                result = func(*args, **kwargs)
                logger.info(f"[OW-AI] Operation {operation_name} completed successfully")
                return result

            except Exception as e:
                if "rejected" in str(e).lower():
                    logger.warning(f"[OW-AI] Operation {operation_name} was rejected")
                raise

        return wrapper
    return decorator


# ============================================
# LOCAL TESTING
# ============================================

def test_locally():
    """Test the Lambda handler locally."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OW-AI Integration Example: AWS Lambda with boto3          ║
║                                                               ║
║     This example demonstrates transparent governance          ║
║     of all boto3 AWS API calls in Lambda functions.          ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Test 1: Low-risk operation (list buckets)
    print("\n" + "=" * 60)
    print("Test 1: List S3 Buckets (LOW RISK - Auto-approved)")
    print("=" * 60)

    event = {"operation": "list_buckets"}
    result = lambda_handler(event, None)
    print(f"Result: {json.dumps(json.loads(result['body']), indent=2)}")

    # Test 2: Medium-risk operation (put object)
    print("\n" + "=" * 60)
    print("Test 2: Put S3 Object (MEDIUM RISK - Evaluated)")
    print("=" * 60)

    event = {
        "operation": "put_object",
        "parameters": {
            "bucket": "my-test-bucket",
            "key": "test/file.txt",
            "body": "Hello, World!"
        }
    }
    result = lambda_handler(event, None)
    print(f"Result: {json.dumps(json.loads(result['body']), indent=2)}")

    # Test 3: High-risk operation (delete object)
    print("\n" + "=" * 60)
    print("Test 3: Delete S3 Object (HIGH RISK - Requires Approval)")
    print("=" * 60)

    event = {
        "operation": "delete_object",
        "parameters": {
            "bucket": "production-backup",
            "key": "critical-data.csv"
        }
    }
    result = lambda_handler(event, None)
    print(f"Result: {json.dumps(json.loads(result['body']), indent=2)}")

    # Test 4: Critical-risk operation (delete bucket)
    print("\n" + "=" * 60)
    print("Test 4: Delete S3 Bucket (CRITICAL RISK - Executive Approval)")
    print("=" * 60)

    event = {
        "operation": "delete_bucket",
        "parameters": {
            "bucket": "production-data"
        }
    }
    result = lambda_handler(event, None)
    print(f"Result: {json.dumps(json.loads(result['body']), indent=2)}")


if __name__ == "__main__":
    test_locally()
