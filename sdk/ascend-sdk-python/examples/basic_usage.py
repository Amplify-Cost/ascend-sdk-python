#!/usr/bin/env python3
"""
Ascend SDK - Basic Usage Example
=================================

This example demonstrates basic usage of the Ascend AI SDK.

Prerequisites:
    pip install ascend-ai-sdk

Environment:
    export ASCEND_API_KEY="ascend_prod_your_key_here"
    export ASCEND_API_URL="https://pilot.owkai.app"  # Optional

Run:
    python examples/basic_usage.py
"""

from ascend import AscendClient, AgentAction, AuthorizedAgent
from ascend import AuthorizationDeniedError, ValidationError


def example_1_simple_submission():
    """Example 1: Simple action submission"""
    print("\n" + "="*60)
    print("Example 1: Simple Action Submission")
    print("="*60)

    # Initialize client
    client = AscendClient()

    # Create action
    action = AgentAction(
        agent_id="demo-bot-001",
        agent_name="Demo Bot",
        action_type="query",
        resource="public_database",
    )

    # Submit action
    result = client.submit_action(action)

    print(f"Action ID: {result.action_id}")
    print(f"Status: {result.status}")
    print(f"Risk Level: {result.risk_level}")

    if result.is_approved():
        print("✅ Action approved - you can execute it now")
    elif result.is_denied():
        print(f"❌ Action denied: {result.reason}")
    else:
        print("⏳ Action pending manual review")


def example_2_authorized_execution():
    """Example 2: Conditional execution with AuthorizedAgent"""
    print("\n" + "="*60)
    print("Example 2: Conditional Execution")
    print("="*60)

    # Initialize agent
    agent = AuthorizedAgent(
        agent_id="customer-bot-001",
        agent_name="Customer Service Bot"
    )

    # Define function to execute if authorized
    def fetch_customer_data():
        # Simulated data fetch
        return {
            "customer_id": "CUST-123",
            "name": "John Doe",
            "balance": 5000.00
        }

    try:
        # Execute only if authorized
        data = agent.execute_if_authorized(
            action_type="data_access",
            resource="customer_profile",
            resource_id="CUST-123",
            execute_fn=fetch_customer_data,
            risk_indicators={"pii_involved": True}
        )

        print("✅ Data fetched successfully:")
        print(f"   Customer: {data['name']}")
        print(f"   Balance: ${data['balance']:.2f}")

    except AuthorizationDeniedError as e:
        print(f"❌ Access denied: {e.message}")


def example_3_high_risk_transaction():
    """Example 3: High-risk transaction with details"""
    print("\n" + "="*60)
    print("Example 3: High-Risk Transaction")
    print("="*60)

    agent = AuthorizedAgent(
        agent_id="payment-bot-001",
        agent_name="Payment Bot"
    )

    def process_payment(amount, recipient):
        # Simulated payment processing
        return {
            "transaction_id": "TXN-456",
            "status": "success",
            "amount": amount,
            "recipient": recipient
        }

    try:
        result = agent.execute_if_authorized(
            action_type="transaction",
            resource="payment_gateway",
            resource_id="external_account_789",
            execute_fn=lambda: process_payment(50000, "external_account_789"),
            details={
                "amount": 50000,
                "currency": "USD",
                "destination_type": "external"
            },
            context={
                "session_id": "sess_abc123",
                "ip_address": "192.168.1.100"
            },
            risk_indicators={
                "amount_threshold": "exceeded",
                "external_transfer": True,
                "data_sensitivity": "critical"
            }
        )

        print("✅ Payment processed:")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Amount: ${result['amount']:,}")

    except AuthorizationDeniedError as e:
        print(f"❌ Payment blocked: {e.message}")
        print("   This high-value transaction requires manual approval")


def example_4_connection_test():
    """Example 4: Test API connection"""
    print("\n" + "="*60)
    print("Example 4: Connection Test")
    print("="*60)

    client = AscendClient()

    # Test connection
    status = client.test_connection()

    if status.is_connected():
        print("✅ Connected to Ascend API")
        print(f"   API Version: {status.api_version}")
        print(f"   Latency: {status.latency_ms:.0f}ms")
        print(f"   Server Time: {status.server_time}")
    else:
        print("❌ Connection failed")
        print(f"   Error: {status.error}")


def example_5_list_actions():
    """Example 5: List recent actions"""
    print("\n" + "="*60)
    print("Example 5: List Recent Actions")
    print("="*60)

    client = AscendClient()

    # List all actions
    result = client.list_actions(limit=5)

    print(f"Total actions: {result.total}")
    print(f"Showing: {len(result.actions)} actions\n")

    for action in result.actions:
        metadata = action.metadata
        print(f"  - ID: {action.action_id}")
        print(f"    Type: {metadata.get('action_type', 'unknown')}")
        print(f"    Status: {action.status}")
        print(f"    Risk: {action.risk_level or 'N/A'}")
        print()


def example_6_error_handling():
    """Example 6: Error handling"""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)

    try:
        # Invalid action (missing required fields)
        action = AgentAction(
            agent_id="",  # Empty agent_id - invalid!
            agent_name="Test",
            action_type="query",
            resource="database"
        )

        client = AscendClient()
        client.submit_action(action)

    except ValidationError as e:
        print(f"✅ Validation error caught correctly:")
        print(f"   {e.message}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("ASCEND AI SDK - USAGE EXAMPLES")
    print("="*70)

    try:
        example_4_connection_test()  # Test connection first
        example_1_simple_submission()
        example_2_authorized_execution()
        example_3_high_risk_transaction()
        example_5_list_actions()
        example_6_error_handling()

        print("\n" + "="*70)
        print("EXAMPLES COMPLETE")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set ASCEND_API_KEY environment variable:")
        print("  export ASCEND_API_KEY='ascend_prod_your_key_here'")


if __name__ == "__main__":
    main()
