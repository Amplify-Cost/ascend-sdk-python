#!/usr/bin/env python3
"""
Ascend SDK - Financial Advisor AI Agent Example
================================================

This example demonstrates a financial advisor AI agent that uses
Ascend for governance of sensitive financial operations.

Use cases:
- Portfolio data access
- Transaction execution
- Financial recommendations
- Customer data queries

Prerequisites:
    pip install ascend-ai-sdk

Environment:
    export ASCEND_API_KEY="ascend_prod_your_key_here"

Run:
    python examples/financial_advisor.py
"""

from ascend import AuthorizedAgent, AuthorizationDeniedError
from datetime import datetime


class FinancialAdvisorAgent:
    """Financial advisor AI agent with Ascend governance"""

    def __init__(self):
        self.agent = AuthorizedAgent(
            agent_id="financial-advisor-001",
            agent_name="AI Financial Advisor"
        )

    def get_portfolio(self, customer_id: str):
        """Get customer portfolio (requires authorization)"""
        print(f"\n📊 Requesting portfolio data for customer {customer_id}")

        def fetch_portfolio():
            # Simulated portfolio data
            return {
                "customer_id": customer_id,
                "total_value": 125000.00,
                "holdings": [
                    {"symbol": "AAPL", "shares": 100, "value": 17500.00},
                    {"symbol": "GOOGL", "shares": 50, "value": 7500.00},
                    {"symbol": "MSFT", "shares": 200, "value": 75000.00},
                ],
                "cash": 25000.00,
                "last_updated": datetime.now().isoformat()
            }

        try:
            portfolio = self.agent.execute_if_authorized(
                action_type="data_access",
                resource="customer_portfolio",
                resource_id=customer_id,
                execute_fn=fetch_portfolio,
                details={
                    "operation": "read",
                    "fields": ["holdings", "balance", "cash"]
                },
                risk_indicators={
                    "pii_involved": True,
                    "financial_data": True,
                    "data_sensitivity": "medium"
                }
            )

            print("✅ Portfolio data authorized and retrieved")
            print(f"   Total Value: ${portfolio['total_value']:,.2f}")
            print(f"   Holdings: {len(portfolio['holdings'])} positions")
            print(f"   Cash: ${portfolio['cash']:,.2f}")
            return portfolio

        except AuthorizationDeniedError as e:
            print(f"❌ Portfolio access denied: {e.message}")
            return None

    def execute_trade(self, customer_id: str, symbol: str, shares: int, action: str):
        """Execute a stock trade (requires authorization)"""
        print(f"\n💹 Requesting trade: {action} {shares} shares of {symbol}")

        def process_trade():
            # Simulated trade execution
            return {
                "trade_id": "TRD-789",
                "status": "executed",
                "symbol": symbol,
                "shares": shares,
                "action": action,
                "price": 175.00,  # Simulated price
                "total": 175.00 * shares,
                "timestamp": datetime.now().isoformat()
            }

        try:
            trade_result = self.agent.execute_if_authorized(
                action_type="transaction",
                resource="trading_platform",
                resource_id=f"{customer_id}_{symbol}",
                execute_fn=process_trade,
                details={
                    "customer_id": customer_id,
                    "symbol": symbol,
                    "shares": shares,
                    "action": action,
                    "estimated_value": 175.00 * shares
                },
                context={
                    "market_hours": True,
                    "account_verified": True
                },
                risk_indicators={
                    "transaction_value": 175.00 * shares,
                    "high_value": (175.00 * shares) > 10000,
                    "data_sensitivity": "critical"
                }
            )

            print("✅ Trade authorized and executed")
            print(f"   Trade ID: {trade_result['trade_id']}")
            print(f"   {action.upper()} {shares} shares @ ${trade_result['price']:.2f}")
            print(f"   Total: ${trade_result['total']:,.2f}")
            return trade_result

        except AuthorizationDeniedError as e:
            print(f"❌ Trade denied: {e.message}")
            return None

    def transfer_funds(self, customer_id: str, amount: float, destination: str):
        """Transfer funds (requires authorization)"""
        print(f"\n💸 Requesting funds transfer: ${amount:,.2f} to {destination}")

        def process_transfer():
            # Simulated transfer
            return {
                "transfer_id": "TXN-456",
                "status": "completed",
                "amount": amount,
                "destination": destination,
                "timestamp": datetime.now().isoformat()
            }

        try:
            transfer_result = self.agent.execute_if_authorized(
                action_type="transaction",
                resource="customer_account",
                resource_id=customer_id,
                execute_fn=process_transfer,
                details={
                    "operation": "transfer",
                    "amount": amount,
                    "currency": "USD",
                    "destination": destination,
                    "destination_type": "external_account"
                },
                context={
                    "verified_destination": False,  # New destination
                    "ip_address": "192.168.1.100"
                },
                risk_indicators={
                    "amount_threshold": "exceeded" if amount > 10000 else "normal",
                    "external_transfer": True,
                    "data_sensitivity": "critical",
                    "new_destination": True
                }
            )

            print("✅ Transfer authorized and completed")
            print(f"   Transfer ID: {transfer_result['transfer_id']}")
            print(f"   Amount: ${transfer_result['amount']:,.2f}")
            return transfer_result

        except AuthorizationDeniedError as e:
            print(f"❌ Transfer denied: {e.message}")
            print("   Large transfers to new destinations require manual approval")
            return None

    def get_recommendations(self, customer_id: str):
        """Get investment recommendations (low risk)"""
        print(f"\n💡 Generating investment recommendations for {customer_id}")

        def generate_recommendations():
            # Simulated AI recommendations
            return {
                "recommendations": [
                    {
                        "type": "diversification",
                        "message": "Consider diversifying into bonds (20% allocation)",
                        "confidence": 0.85
                    },
                    {
                        "type": "rebalancing",
                        "message": "Reduce tech exposure from 70% to 50%",
                        "confidence": 0.78
                    }
                ],
                "risk_score": 6.5,
                "timestamp": datetime.now().isoformat()
            }

        try:
            recommendations = self.agent.execute_if_authorized(
                action_type="recommendation",
                resource="investment_advice",
                resource_id=customer_id,
                execute_fn=generate_recommendations,
                details={
                    "recommendation_type": "portfolio_optimization"
                },
                risk_indicators={
                    "pii_involved": False,
                    "financial_data": True,
                    "data_sensitivity": "low"
                }
            )

            print("✅ Recommendations generated")
            for rec in recommendations['recommendations']:
                print(f"   - {rec['message']} (confidence: {rec['confidence']:.0%})")
            return recommendations

        except AuthorizationDeniedError as e:
            print(f"❌ Recommendations denied: {e.message}")
            return None


def main():
    """Run financial advisor agent demo"""
    print("="*70)
    print("ASCEND SDK - FINANCIAL ADVISOR AI AGENT DEMO")
    print("="*70)

    advisor = FinancialAdvisorAgent()
    customer_id = "CUST-12345"

    # Scenario 1: View portfolio (medium risk - should auto-approve)
    advisor.get_portfolio(customer_id)

    # Scenario 2: Generate recommendations (low risk - should auto-approve)
    advisor.get_recommendations(customer_id)

    # Scenario 3: Execute small trade (medium risk - may auto-approve)
    advisor.execute_trade(customer_id, "AAPL", 10, "buy")

    # Scenario 4: Execute large trade (high risk - may require approval)
    advisor.execute_trade(customer_id, "TSLA", 100, "buy")

    # Scenario 5: Large transfer to new account (critical risk - requires approval)
    advisor.transfer_funds(customer_id, 50000, "external_account_789")

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nKey Observations:")
    print("  - Low/medium risk actions auto-approved")
    print("  - High-value transactions require manual review")
    print("  - All actions logged for audit trail")
    print("  - Policies enforce financial compliance\n")


if __name__ == "__main__":
    main()
