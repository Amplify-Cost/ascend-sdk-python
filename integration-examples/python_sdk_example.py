#!/usr/bin/env python3
"""
OW-AI Enterprise SDK Integration Example
=========================================

This example demonstrates how to integrate OW-AI Authorization Center
into your AI agent infrastructure for enterprise-grade governance.

Prerequisites:
- Python 3.8+
- pip install requests python-dotenv

Environment Variables:
- OWKAI_API_URL: API endpoint (default: https://pilot.owkai.app)
- OWKAI_API_KEY: Your organization's API key
- OWKAI_ORG_SLUG: Your organization slug

Usage:
    python python_sdk_example.py

Security Standards:
- SOC 2 Type II Compliant
- PCI-DSS 8.3 (MFA)
- HIPAA 164.312 (Audit)
- NIST 800-63B (Authentication)

Author: OW-AI Enterprise
Date: 2025-11-30
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('owkai-sdk')


class ActionType(Enum):
    """Supported action types for agent authorization"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION = "transaction"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    SYSTEM_OPERATION = "system_operation"


class DecisionStatus(Enum):
    """Authorization decision statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_MODIFICATION = "requires_modification"
    TIMEOUT = "timeout"


@dataclass
class AgentAction:
    """Represents an agent action requiring authorization"""
    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    resource_id: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    risk_indicators: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to API-compatible dictionary"""
        data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "resource": self.resource,
        }
        if self.resource_id:
            data["resource_id"] = self.resource_id
        if self.action_details:
            data["action_details"] = self.action_details
        if self.context:
            data["context"] = self.context
        if self.risk_indicators:
            data["risk_indicators"] = self.risk_indicators
        return data


class OWKAIClient:
    """
    OW-AI Authorization Center SDK Client

    Enterprise-grade client for submitting agent actions
    for authorization and policy enforcement.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_slug: Optional[str] = None,
        timeout: int = 30,
        debug: bool = False
    ):
        """
        Initialize the OW-AI client.

        Args:
            api_url: API endpoint URL
            api_key: Organization API key
            organization_slug: Organization identifier
            timeout: Request timeout in seconds
            debug: Enable debug logging
        """
        self.api_url = api_url or os.getenv('OWKAI_API_URL', 'https://pilot.owkai.app')
        self.api_key = api_key or os.getenv('OWKAI_API_KEY')
        self.organization_slug = organization_slug or os.getenv('OWKAI_ORG_SLUG')
        self.timeout = timeout

        if debug:
            logger.setLevel(logging.DEBUG)

        if not self.api_key:
            raise ValueError("API key is required. Set OWKAI_API_KEY environment variable.")

        # SEC-033: Support both X-API-Key header and Authorization Bearer
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "OWKAIClient/2.0 Python"
        }

        logger.info(f"OW-AI Client initialized for {self.api_url}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make authenticated request to API"""
        url = f"{self.api_url}{endpoint}"

        logger.debug(f"{method} {url}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)

            logger.error(f"API Error: {error_detail}")
            raise Exception(f"API Error: {error_detail}")

        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise TimeoutError("API request timed out")

        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            raise ConnectionError("Failed to connect to OW-AI API")

    def test_connection(self) -> Dict:
        """Test API connectivity and authentication"""
        try:
            # Use health endpoint first
            health = self._request("GET", "/health")

            # Then verify authentication
            deployment = self._request("GET", "/api/deployment-info")

            return {
                "status": "connected",
                "api_version": deployment.get("version", "unknown"),
                "server_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def submit_action(self, action: AgentAction) -> Dict:
        """
        Submit an agent action for authorization.

        Args:
            action: AgentAction object describing the action

        Returns:
            Authorization response with action_id and initial status
        """
        logger.info(f"Submitting action: {action.action_type} on {action.resource}")

        response = self._request(
            "POST",
            "/api/authorization/agent-action",
            data=action.to_dict()
        )

        logger.info(f"Action submitted: {response.get('action_id')} - Status: {response.get('status')}")
        return response

    def get_action_status(self, action_id: str) -> Dict:
        """
        Get the current status of an action.

        Args:
            action_id: The action ID returned from submit_action

        Returns:
            Current status and decision information
        """
        return self._request(
            "GET",
            f"/api/agent-action/status/{action_id}"
        )

    def wait_for_decision(
        self,
        action_id: str,
        timeout: int = 60,
        poll_interval: float = 2.0
    ) -> Dict:
        """
        Wait for an authorization decision.

        Args:
            action_id: The action ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks

        Returns:
            Final decision status
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_action_status(action_id)

            if status.get('decision') != 'pending':
                return status

            logger.debug(f"Action {action_id} still pending...")
            time.sleep(poll_interval)

        return {
            "action_id": action_id,
            "decision": "timeout",
            "error": f"Decision not received within {timeout} seconds"
        }

    def list_actions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict:
        """
        List recent agent actions for this organization.

        Args:
            limit: Maximum number of actions to return
            offset: Pagination offset
            status: Filter by status

        Returns:
            List of actions with pagination info
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        return self._request(
            "GET",
            "/api/agent-activity",
            params=params
        )

    def get_action_details(self, action_id: str) -> Dict:
        """
        Get detailed information about an action.

        Args:
            action_id: The action ID

        Returns:
            Full action details including audit trail
        """
        return self._request(
            "GET",
            f"/api/agent-action/{action_id}"
        )


class AuthorizedAgent:
    """
    Wrapper for AI agents that require OW-AI authorization.

    This class wraps your AI agent and automatically submits
    actions for authorization before execution.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        client: Optional[OWKAIClient] = None
    ):
        """
        Initialize an authorized agent.

        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable agent name
            client: OWKAIClient instance (creates new if not provided)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.client = client or OWKAIClient()

    def request_authorization(
        self,
        action_type: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
        risk_indicators: Optional[Dict] = None,
        wait_for_decision: bool = True,
        timeout: int = 60
    ) -> Dict:
        """
        Request authorization for an action.

        Args:
            action_type: Type of action (data_access, transaction, etc.)
            resource: Resource being accessed
            resource_id: Specific resource identifier
            details: Additional action details
            context: Contextual information
            risk_indicators: Risk assessment data
            wait_for_decision: Whether to wait for decision
            timeout: Decision timeout in seconds

        Returns:
            Authorization decision
        """
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            action_details=details,
            context=context,
            risk_indicators=risk_indicators
        )

        response = self.client.submit_action(action)

        if wait_for_decision and response.get('decision') == 'pending':
            return self.client.wait_for_decision(
                response['action_id'],
                timeout=timeout
            )

        return response

    def execute_if_authorized(
        self,
        action_type: str,
        resource: str,
        execute_fn: callable,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
        risk_indicators: Optional[Dict] = None,
        timeout: int = 60
    ) -> Any:
        """
        Execute a function only if authorized.

        Args:
            action_type: Type of action
            resource: Resource being accessed
            execute_fn: Function to execute if authorized
            resource_id: Specific resource identifier
            details: Additional action details
            context: Contextual information
            risk_indicators: Risk assessment data
            timeout: Decision timeout

        Returns:
            Result of execute_fn if authorized

        Raises:
            PermissionError: If action is denied
            TimeoutError: If decision times out
        """
        decision = self.request_authorization(
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            details=details,
            context=context,
            risk_indicators=risk_indicators,
            wait_for_decision=True,
            timeout=timeout
        )

        status = decision.get('decision', decision.get('status'))

        if status == 'approved':
            logger.info(f"Action authorized, executing...")
            return execute_fn()

        elif status == 'denied':
            reason = decision.get('reason', 'No reason provided')
            raise PermissionError(f"Action denied: {reason}")

        elif status == 'timeout':
            raise TimeoutError("Authorization decision timed out")

        else:
            raise Exception(f"Unexpected authorization status: {status}")


# =============================================================================
# Example Usage
# =============================================================================

def example_financial_advisor_agent():
    """Example: Financial Advisor AI Agent"""

    print("\n" + "="*60)
    print("OW-AI SDK Example: Financial Advisor Agent")
    print("="*60 + "\n")

    # Initialize client
    try:
        client = OWKAIClient()

        # Test connection
        print("Testing connection...")
        conn_status = client.test_connection()
        print(f"Connection: {conn_status['status']}")

        if conn_status['status'] != 'connected':
            print(f"Error: {conn_status.get('error')}")
            return

    except Exception as e:
        print(f"Failed to initialize client: {e}")
        print("\nMake sure OWKAI_API_KEY is set in your environment.")
        return

    # Create authorized agent
    agent = AuthorizedAgent(
        agent_id="financial-advisor-001",
        agent_name="Financial Advisor AI",
        client=client
    )

    # Example 1: Low-risk action (should auto-approve)
    print("\n--- Example 1: Low-Risk Query ---")
    try:
        decision = agent.request_authorization(
            action_type="query",
            resource="market_data",
            details={
                "operation": "read",
                "data_type": "public_prices"
            },
            risk_indicators={
                "pii_involved": False,
                "financial_data": False
            }
        )
        print(f"Decision: {decision.get('decision', decision.get('status'))}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Medium-risk action (may require review)
    print("\n--- Example 2: Customer Data Access ---")
    try:
        decision = agent.request_authorization(
            action_type="data_access",
            resource="customer_portfolio",
            resource_id="CUST-12345",
            details={
                "operation": "read",
                "fields": ["balance", "holdings"]
            },
            context={
                "user_request": "Show my portfolio",
                "session_id": "sess_abc123"
            },
            risk_indicators={
                "pii_involved": True,
                "financial_data": True,
                "data_sensitivity": "medium"
            }
        )
        print(f"Decision: {decision.get('decision', decision.get('status'))}")
        print(f"Risk Score: {decision.get('risk_score', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: High-risk action (likely requires approval)
    print("\n--- Example 3: High-Value Transaction ---")
    try:
        decision = agent.request_authorization(
            action_type="transaction",
            resource="customer_account",
            resource_id="ACC-98765",
            details={
                "operation": "transfer",
                "amount": 50000,
                "currency": "USD",
                "destination": "external_account"
            },
            context={
                "user_request": "Transfer $50,000 to my savings",
                "ip_address": "192.168.1.100"
            },
            risk_indicators={
                "amount_threshold": "exceeded",
                "external_transfer": True,
                "data_sensitivity": "critical"
            },
            timeout=30  # Shorter timeout for demo
        )
        print(f"Decision: {decision.get('decision', decision.get('status'))}")

        if decision.get('decision') == 'pending':
            print("Action requires manual review by compliance officer")

    except PermissionError as e:
        print(f"Action denied: {e}")
    except TimeoutError:
        print("Decision pending - requires manual approval")
    except Exception as e:
        print(f"Error: {e}")

    # Example 4: Execute with authorization
    print("\n--- Example 4: Conditional Execution ---")

    def get_portfolio_data():
        """Simulated function to get portfolio data"""
        return {
            "balance": 125000.00,
            "holdings": ["AAPL", "GOOGL", "MSFT"],
            "last_updated": datetime.now().isoformat()
        }

    try:
        result = agent.execute_if_authorized(
            action_type="data_access",
            resource="portfolio_summary",
            execute_fn=get_portfolio_data,
            details={"operation": "read"},
            risk_indicators={"pii_involved": False}
        )
        print(f"Authorized result: {result}")

    except PermissionError as e:
        print(f"Not authorized: {e}")
    except Exception as e:
        print(f"Error: {e}")

    # List recent actions
    print("\n--- Recent Actions ---")
    try:
        actions = client.list_actions(limit=5)
        for action in actions.get('actions', []):
            print(f"  - {action.get('action_id')}: {action.get('action_type')} -> {action.get('status')}")
    except Exception as e:
        print(f"Error listing actions: {e}")

    print("\n" + "="*60)
    print("Example Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    example_financial_advisor_agent()
