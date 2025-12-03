#!/usr/bin/env python3
"""
ASCEND SDK v2.0 - Basic Agent Integration
==========================================

This example demonstrates the core SDK v2.0 features:
1. Agent registration
2. Action evaluation with fail mode
3. Completion/failure logging
4. Circuit breaker pattern

Prerequisites:
- Python 3.8+
- pip install ascend-sdk

Usage:
    export ASCEND_API_KEY="owkai_your_key"
    python 07_basic_agent_v2.py

Security: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.2, NIST AI RMF

Author: Ascend Engineering Team
"""

import os
import time
import logging
from datetime import datetime

from owkai_sdk import AscendClient, FailMode, Decision
from owkai_sdk.exceptions import (
    AuthorizationError,
    CircuitBreakerOpen,
    TimeoutError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main agent workflow demonstration."""

    # ============================================================
    # 1. Initialize Client with Fail Mode
    # ============================================================

    client = AscendClient(
        api_key=os.getenv("ASCEND_API_KEY"),
        api_url=os.getenv("ASCEND_API_URL", "https://pilot.owkai.app"),
        agent_id="demo-agent-001",
        agent_name="Demo Financial Agent",
        environment="development",

        # Fail Mode: CLOSED = block if ASCEND unreachable (recommended)
        #            OPEN = allow if ASCEND unreachable (use with caution)
        fail_mode=FailMode.CLOSED,

        # Circuit Breaker: Auto-open after failures
        enable_circuit_breaker=True,
        circuit_breaker_threshold=5,  # Open after 5 failures
        circuit_breaker_timeout=60,   # Try again after 60 seconds

        # Logging
        debug=True,
    )

    logger.info("ASCEND Client initialized")

    # ============================================================
    # 2. Register Agent
    # ============================================================

    try:
        registration = client.register(
            capabilities=["financial.transfer", "database.query", "email.send"],
            allowed_resources=["stripe_api", "production_db", "smtp_server"],
            metadata={
                "version": "1.0.0",
                "team": "payments",
            }
        )
        logger.info(f"Agent registered: {registration}")
    except Exception as e:
        logger.warning(f"Registration failed (continuing): {e}")

    # ============================================================
    # 3. Evaluate Actions
    # ============================================================

    # Example 1: Low-risk action (should be allowed)
    logger.info("\n--- Example 1: Low-risk database query ---")
    try:
        decision = client.evaluate_action(
            action_type="database.query",
            resource="analytics_db",
            parameters={
                "query": "SELECT COUNT(*) FROM users",
                "read_only": True,
            },
            context={
                "user_id": "user-123",
                "session_id": "sess-abc",
            }
        )

        logger.info(f"Decision: {decision.decision.value}")
        logger.info(f"Risk Score: {decision.risk_score}")
        logger.info(f"Action ID: {decision.action_id}")

        if decision.decision == Decision.ALLOWED:
            # Execute the action
            result = {"rows": 1000}  # Simulated result

            # Log completion
            client.log_action_completed(
                action_id=decision.action_id,
                result=result,
                duration_ms=150,
            )
            logger.info("Action completed successfully")

    except AuthorizationError as e:
        logger.error(f"Action denied: {e.message}")
        logger.error(f"Policy violations: {e.policy_violations}")

    # Example 2: High-risk action (may require approval)
    logger.info("\n--- Example 2: High-risk financial transfer ---")
    try:
        decision = client.evaluate_action(
            action_type="financial.transfer",
            resource="stripe_api",
            parameters={
                "amount": 50000,
                "currency": "USD",
                "destination": "acct_external",
            },
            context={
                "risk_level": "high",
                "require_human_approval": True,
            },
            wait_for_decision=True,  # Wait for approval if pending
            timeout=30,  # Max 30 seconds
        )

        logger.info(f"Decision: {decision.decision.value}")
        logger.info(f"Risk Score: {decision.risk_score}")

        if decision.decision == Decision.ALLOWED:
            # Execute transfer
            result = {"transfer_id": "tr_123"}
            client.log_action_completed(
                action_id=decision.action_id,
                result=result,
                duration_ms=2500,
            )
            logger.info("Transfer completed")

        elif decision.decision == Decision.DENIED:
            logger.warning(f"Transfer denied: {decision.reason}")

        elif decision.decision == Decision.PENDING:
            logger.info(f"Transfer pending approval: {decision.approval_request_id}")

    except AuthorizationError as e:
        logger.error(f"Transfer denied: {e}")

    except TimeoutError as e:
        logger.warning(f"Approval timeout: {e}")

    # Example 3: Action that fails during execution
    logger.info("\n--- Example 3: Failed action ---")
    try:
        decision = client.evaluate_action(
            action_type="email.send",
            resource="smtp_server",
            parameters={
                "to": "customer@example.com",
                "subject": "Order Confirmation",
            }
        )

        if decision.decision == Decision.ALLOWED:
            # Simulate failure during execution
            try:
                raise ConnectionError("SMTP server unavailable")
            except Exception as exec_error:
                # Log the failure
                client.log_action_failed(
                    action_id=decision.action_id,
                    error=str(exec_error),
                    duration_ms=500,
                )
                logger.error(f"Action failed: {exec_error}")

    except AuthorizationError as e:
        logger.error(f"Email denied: {e}")

    # ============================================================
    # 4. Circuit Breaker Demonstration
    # ============================================================

    logger.info("\n--- Circuit Breaker Status ---")
    # The circuit breaker state is internal to the client
    # It will automatically open after consecutive failures
    # and close again after the recovery timeout

    logger.info("Circuit breaker is monitoring for failures")
    logger.info("After 5 consecutive failures, it will open for 60 seconds")

    # ============================================================
    # 5. Configure Webhook (Optional)
    # ============================================================

    logger.info("\n--- Webhook Configuration ---")
    try:
        webhook = client.configure_webhook(
            url="https://your-server.com/webhooks/ascend",
            events=["action.approved", "action.denied"],
            secret="your-webhook-secret",
        )
        logger.info(f"Webhook configured: {webhook}")
    except Exception as e:
        logger.warning(f"Webhook config failed (optional): {e}")

    logger.info("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
