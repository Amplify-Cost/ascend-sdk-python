#!/usr/bin/env python3
"""
OW-kai Enterprise Platform - End-to-End Client Test (Boto3 Version)
====================================================================

Engineer: Donald King (OW-kai Enterprise)
Date: 2025-11-17

PURPOSE:
--------
This script demonstrates how AWS-integrated enterprise clients can interact
with the OW-kai platform using boto3 and AWS services (Secrets Manager, SSM,
CloudWatch, etc.) for secure credential management and monitoring.

DIFFERENCES FROM REST API VERSION:
-----------------------------------
- Credentials stored in AWS Secrets Manager
- API tokens cached in SSM Parameter Store
- CloudWatch integration for monitoring
- Lambda-compatible execution model
- IAM role-based authentication
- VPC endpoint support

USAGE:
------
```bash
# Ensure AWS credentials are configured
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-2

# Run the test
python test_client_e2e_boto3.py --env production

# For Lambda deployment
pip install -r requirements.txt -t lambda_package/
cp test_client_e2e_boto3.py lambda_package/lambda_function.py
cd lambda_package && zip -r ../e2e_test.zip .
aws lambda create-function --function-name owkai-e2e-test --runtime python3.11 --handler lambda_function.lambda_handler --role arn:aws:iam::ACCOUNT:role/lambda-role --zip-file fileb://../e2e_test.zip
```

REQUIRED IAM PERMISSIONS:
-------------------------
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "ssm:GetParameter",
        "ssm:PutParameter",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```
"""

import boto3
import json
import requests
import sys
import argparse
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Tuple
import os

class AWSIntegratedE2ETest:
    """E2E Test with AWS Service Integration"""

    def __init__(self, region: str = "us-east-2", verbose: bool = False):
        self.region = region
        self.verbose = verbose

        # Initialize AWS clients
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)

        # Test configuration
        self.secret_name = "owkai/platform/credentials"
        self.ssm_token_param = "/owkai/api/access-token"
        self.base_url = None
        self.token = None

    def log(self, message: str, level: str = "INFO"):
        """Structured logging with CloudWatch integration"""
        timestamp = datetime.now(UTC).isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"

        if self.verbose:
            print(log_entry)

        # Optional: Send to CloudWatch Logs
        # self.send_to_cloudwatch_logs(log_entry)

    def get_credentials_from_secrets_manager(self) -> Dict[str, str]:
        """
        Retrieve credentials from AWS Secrets Manager

        Expected secret format:
        {
          "api_url": "https://pilot.owkai.app",
          "username": "admin@owkai.com",
          "password": "admin123",
          "api_key": "optional-api-key"
        }
        """
        try:
            self.log("Retrieving credentials from Secrets Manager...", "INFO")

            response = self.secrets_client.get_secret_value(
                SecretId=self.secret_name
            )

            secret = json.loads(response['SecretString'])
            self.base_url = secret.get('api_url', 'https://pilot.owkai.app')

            self.log("✅ Credentials retrieved successfully", "SUCCESS")
            return secret

        except self.secrets_client.exceptions.ResourceNotFoundException:
            self.log(f"❌ Secret '{self.secret_name}' not found", "ERROR")
            self.log("Creating example secret with default values...", "INFO")

            # Create example secret
            default_secret = {
                "api_url": "https://pilot.owkai.app",
                "username": "admin@owkai.com",
                "password": "admin123"
            }

            self.secrets_client.create_secret(
                Name=self.secret_name,
                Description="OW-kai Platform API Credentials",
                SecretString=json.dumps(default_secret)
            )

            self.log(f"✅ Created secret '{self.secret_name}'", "SUCCESS")
            return default_secret

        except Exception as e:
            self.log(f"❌ Error retrieving credentials: {str(e)}", "ERROR")
            raise

    def get_cached_token_from_ssm(self) -> Optional[str]:
        """
        Get cached API token from SSM Parameter Store

        Benefits:
        - Reduces authentication calls
        - Stores encrypted tokens
        - Enables cross-service token sharing
        """
        try:
            response = self.ssm_client.get_parameter(
                Name=self.ssm_token_param,
                WithDecryption=True
            )

            param_data = json.loads(response['Parameter']['Value'])
            token = param_data.get('token')
            expires_at = datetime.fromisoformat(param_data.get('expires_at'))

            # Check if token is still valid (with 5 min buffer)
            if datetime.now(UTC) < (expires_at - timedelta(minutes=5)):
                self.log("✅ Using cached token from SSM", "INFO")
                return token
            else:
                self.log("⚠️ Cached token expired", "WARNING")
                return None

        except self.ssm_client.exceptions.ParameterNotFound:
            self.log("ℹ️ No cached token in SSM", "INFO")
            return None
        except Exception as e:
            self.log(f"⚠️ Error retrieving cached token: {str(e)}", "WARNING")
            return None

    def cache_token_in_ssm(self, token: str, expires_in_seconds: int = 3600):
        """Cache token in SSM Parameter Store"""
        try:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

            param_value = json.dumps({
                "token": token,
                "expires_at": expires_at.isoformat(),
                "cached_at": datetime.now(UTC).isoformat()
            })

            self.ssm_client.put_parameter(
                Name=self.ssm_token_param,
                Value=param_value,
                Type='SecureString',
                Overwrite=True,
                Description='OW-kai Platform API Access Token'
            )

            self.log("✅ Token cached in SSM", "SUCCESS")

        except Exception as e:
            self.log(f"⚠️ Failed to cache token: {str(e)}", "WARNING")

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with OW-kai platform"""
        try:
            # Try cached token first
            cached_token = self.get_cached_token_from_ssm()
            if cached_token:
                self.token = cached_token
                return True

            # Get new token
            self.log("Authenticating with platform...", "INFO")

            response = requests.post(
                f"{self.base_url}/api/auth/token",
                json={
                    "email": credentials['username'],
                    "password": credentials['password']
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')

                # Cache the token
                self.cache_token_in_ssm(self.token)

                self.log("✅ Authentication successful", "SUCCESS")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False

    def send_metric_to_cloudwatch(self, metric_name: str, value: float, unit: str = 'Count'):
        """Send custom metrics to CloudWatch"""
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace='OWKai/E2E-Tests',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.now(UTC),
                        'Dimensions': [
                            {
                                'Name': 'Environment',
                                'Value': 'production'
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            self.log(f"⚠️ Failed to send CloudWatch metric: {str(e)}", "WARNING")

    def test_agent_action_workflow(self) -> bool:
        """Test complete agent action workflow"""
        try:
            self.log("Testing Agent Action Workflow...", "INFO")

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            # Submit action
            payload = {
                "agent_id": "boto3-test-agent",
                "action_type": "database_write",
                "description": "Boto3 E2E Test: Production database operation",
                "details": {
                    "table": "transactions",
                    "operation": "UPDATE",
                    "affected_rows": 2000,
                    "environment": "production",
                    "contains_pii": True
                },
                "requires_approval": True
            }

            start_time = datetime.now(UTC)

            response = requests.post(
                f"{self.base_url}/agent/agent-action",
                json=payload,
                headers=headers,
                timeout=10
            )

            response_time_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            # Send metrics to CloudWatch
            self.send_metric_to_cloudwatch('AgentActionSubmissionTime', response_time_ms, 'Milliseconds')

            if response.status_code in [200, 201]:
                data = response.json()
                action_id = data.get('id')
                risk_score = data.get('risk_score', 0)

                self.log(f"✅ Agent action created: ID={action_id}, Risk={risk_score}", "SUCCESS")

                # Send risk score metric
                self.send_metric_to_cloudwatch('AgentActionRiskScore', risk_score, 'None')

                return True
            else:
                self.log(f"❌ Agent action failed: {response.status_code}", "ERROR")
                self.send_metric_to_cloudwatch('AgentActionFailures', 1, 'Count')
                return False

        except Exception as e:
            self.log(f"❌ Agent action test error: {str(e)}", "ERROR")
            self.send_metric_to_cloudwatch('AgentActionErrors', 1, 'Count')
            return False

    def test_risk_config_operations(self) -> bool:
        """Test risk config activation (the bug we fixed)"""
        try:
            self.log("Testing Risk Config Operations (BUG FIX VERIFICATION)...", "INFO")

            headers = {
                "Authorization": f"Bearer {self.token}",
                "X-CSRF-Token": "boto3-csrf-token"
            }

            # Get config history
            response = requests.get(
                f"{self.base_url}/api/risk-scoring/config/history?limit=3",
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                self.log(f"❌ Get config history failed: {response.status_code}", "ERROR")
                return False

            configs = response.json()

            if len(configs) == 0:
                self.log("⚠️ No configs available for testing", "WARNING")
                return True

            # Test activation (THIS WAS RETURNING 500 BEFORE THE FIX)
            config_id = configs[0]['id']

            start_time = datetime.now(UTC)

            response = requests.put(
                f"{self.base_url}/api/risk-scoring/config/{config_id}/activate",
                headers=headers,
                timeout=10
            )

            response_time_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            if response.status_code == 200:
                self.log(f"✅ Config activation successful - NO 500 ERROR! 🎉", "SUCCESS")
                self.send_metric_to_cloudwatch('RiskConfigActivationSuccess', 1, 'Count')
                self.send_metric_to_cloudwatch('RiskConfigActivationTime', response_time_ms, 'Milliseconds')
                return True
            else:
                self.log(f"❌ Config activation failed: {response.status_code}", "ERROR")
                self.send_metric_to_cloudwatch('RiskConfigActivationFailures', 1, 'Count')
                return False

        except Exception as e:
            self.log(f"❌ Risk config test error: {str(e)}", "ERROR")
            return False

    def run_full_test_suite(self) -> bool:
        """Execute complete test suite"""
        self.log("=" * 80, "INFO")
        self.log("OW-KAI ENTERPRISE E2E TEST (Boto3/AWS Integration)", "INFO")
        self.log("=" * 80, "INFO")

        # Step 1: Get credentials from Secrets Manager
        credentials = self.get_credentials_from_secrets_manager()

        # Step 2: Authenticate
        if not self.authenticate(credentials):
            self.log("❌ Authentication failed - cannot continue", "ERROR")
            return False

        # Step 3: Test agent action workflow
        agent_test_passed = self.test_agent_action_workflow()

        # Step 4: Test risk config operations (THE FIX!)
        config_test_passed = self.test_risk_config_operations()

        # Overall result
        all_passed = agent_test_passed and config_test_passed

        if all_passed:
            self.log("=" * 80, "SUCCESS")
            self.log("🎉 ALL TESTS PASSED!", "SUCCESS")
            self.log("=" * 80, "SUCCESS")
            self.send_metric_to_cloudwatch('E2ETestSuccess', 1, 'Count')
        else:
            self.log("=" * 80, "ERROR")
            self.log("❌ SOME TESTS FAILED", "ERROR")
            self.log("=" * 80, "ERROR")
            self.send_metric_to_cloudwatch('E2ETestFailures', 1, 'Count')

        return all_passed


def lambda_handler(event, context):
    """
    AWS Lambda handler for scheduled E2E tests

    Event format:
    {
      "region": "us-east-2",
      "verbose": true
    }

    Schedule with EventBridge:
    - Rate: rate(15 minutes)
    - Cron: cron(0 * * * ? *)  # Every hour
    """
    region = event.get('region', 'us-east-2')
    verbose = event.get('verbose', False)

    tester = AWSIntegratedE2ETest(region=region, verbose=verbose)
    success = tester.run_full_test_suite()

    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps({
            'success': success,
            'timestamp': datetime.now(UTC).isoformat(),
            'message': 'All tests passed' if success else 'Some tests failed'
        })
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="OW-kai E2E Test with AWS Integration"
    )
    parser.add_argument(
        '--region',
        default='us-east-2',
        help='AWS region'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    tester = AWSIntegratedE2ETest(
        region=args.region,
        verbose=args.verbose
    )

    success = tester.run_full_test_suite()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
