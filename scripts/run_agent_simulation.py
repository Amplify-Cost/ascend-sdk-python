#!/usr/bin/env python3
"""
OW-AI Enterprise Agent Simulation
==================================

Simulates real AI agents operating in enterprise scenarios:
- Financial Advisor Agent (investment recommendations, transactions)
- Data Analyst Agent (customer data access, reporting)
- IT Operations Agent (system maintenance, security scans)
- Customer Service Agent (ticket resolution, communications)

This creates REAL agent actions in your production system that:
- Appear in the dashboard
- Require approval based on risk level
- Generate audit trails
- Demonstrate the full authorization flow

Usage:
    python scripts/run_agent_simulation.py

Environment:
    OWKAI_API_KEY - Your API key (or uses the one from Acme Corp)
    OWKAI_API_URL - API endpoint (default: https://pilot.owkai.app)
"""

import os
import sys
import time
import random
import requests
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

# Configuration
API_URL = os.getenv("OWKAI_API_URL", "https://pilot.owkai.app")
API_KEY = os.getenv("OWKAI_API_KEY", "owkai_admin_l21io8R4OAJttHsTD5Wzua28_rk0EXkR-Uryj81wFuI")

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class AgentSimulator:
    """Simulates real AI agents making authorization requests."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
        self.actions_created = []

    def submit_action(self, action: Dict[str, Any]) -> Optional[Dict]:
        """Submit an agent action to the API via SDK endpoint."""
        try:
            response = self.session.post(
                f"{self.api_url}/api/sdk/agent-action",
                json=action
            )
            if response.status_code in [200, 201]:
                result = response.json()
                self.actions_created.append(result)
                return result
            else:
                print(f"  {Colors.RED}Error: {response.status_code} - {response.text[:100]}{Colors.RESET}")
                return None
        except Exception as e:
            print(f"  {Colors.RED}Error: {e}{Colors.RESET}")
            return None


# ============================================================================
# AGENT DEFINITIONS - Real-world enterprise AI agents
# ============================================================================

AGENTS = {
    "financial-advisor-001": {
        "name": "Financial Advisor AI",
        "description": "AI agent providing investment recommendations and managing transactions",
        "icon": "💰",
        "scenarios": [
            {
                "action_type": "data_access",
                "description": "Accessing customer portfolio for quarterly review",
                "risk_score": 35,
                "resource": "customer_portfolio_db",
                "metadata": {
                    "customer_id": "CUST-2847",
                    "purpose": "quarterly_review",
                    "data_classification": "confidential"
                }
            },
            {
                "action_type": "recommendation",
                "description": "Generating investment recommendation based on market analysis",
                "risk_score": 45,
                "resource": "recommendation_engine",
                "metadata": {
                    "recommendation_type": "portfolio_rebalance",
                    "confidence_score": 0.87,
                    "market_conditions": "bullish"
                }
            },
            {
                "action_type": "transaction",
                "description": "Executing approved stock purchase order",
                "risk_score": 72,
                "resource": "trading_system",
                "metadata": {
                    "transaction_type": "buy",
                    "symbol": "AAPL",
                    "shares": 150,
                    "estimated_value": 28500.00,
                    "requires_approval": True
                }
            },
            {
                "action_type": "transaction",
                "description": "Processing high-value wire transfer request",
                "risk_score": 88,
                "resource": "payment_gateway",
                "metadata": {
                    "transaction_type": "wire_transfer",
                    "amount": 250000.00,
                    "currency": "USD",
                    "destination": "external_bank",
                    "requires_executive_approval": True
                }
            }
        ]
    },
    "data-analyst-002": {
        "name": "Data Analyst AI",
        "description": "AI agent analyzing customer data and generating insights",
        "icon": "📊",
        "scenarios": [
            {
                "action_type": "query",
                "description": "Running aggregate analytics query on sales data",
                "risk_score": 20,
                "resource": "analytics_warehouse",
                "metadata": {
                    "query_type": "aggregate",
                    "tables": ["sales_summary"],
                    "date_range": "last_90_days"
                }
            },
            {
                "action_type": "data_access",
                "description": "Accessing PII for customer segmentation analysis",
                "risk_score": 65,
                "resource": "customer_pii_table",
                "metadata": {
                    "pii_fields": ["email", "phone", "address"],
                    "purpose": "segmentation",
                    "data_minimization_applied": True
                }
            },
            {
                "action_type": "report_generation",
                "description": "Generating executive dashboard with revenue projections",
                "risk_score": 40,
                "resource": "reporting_engine",
                "metadata": {
                    "report_type": "executive_dashboard",
                    "includes_projections": True,
                    "distribution": ["c_suite", "board"]
                }
            },
            {
                "action_type": "data_export",
                "description": "Exporting customer list for marketing campaign",
                "risk_score": 75,
                "resource": "customer_database",
                "metadata": {
                    "export_format": "csv",
                    "record_count": 15000,
                    "destination": "marketing_platform",
                    "contains_pii": True
                }
            }
        ]
    },
    "it-ops-003": {
        "name": "IT Operations AI",
        "description": "AI agent managing infrastructure and security operations",
        "icon": "🔧",
        "scenarios": [
            {
                "action_type": "system_operation",
                "description": "Running scheduled database backup",
                "risk_score": 25,
                "resource": "backup_system",
                "metadata": {
                    "operation": "backup",
                    "database": "production_db",
                    "retention_days": 30
                }
            },
            {
                "action_type": "security_scan",
                "description": "Executing vulnerability scan on production servers",
                "risk_score": 35,
                "resource": "security_scanner",
                "metadata": {
                    "scan_type": "vulnerability",
                    "targets": ["web-prod-01", "web-prod-02", "api-prod-01"],
                    "severity_threshold": "medium"
                }
            },
            {
                "action_type": "system_operation",
                "description": "Applying security patches to production servers",
                "risk_score": 70,
                "resource": "patch_management",
                "metadata": {
                    "patch_type": "security",
                    "cve_ids": ["CVE-2024-1234", "CVE-2024-5678"],
                    "requires_restart": True,
                    "maintenance_window": "scheduled"
                }
            },
            {
                "action_type": "system_operation",
                "description": "Rotating database credentials across all services",
                "risk_score": 82,
                "resource": "secrets_manager",
                "metadata": {
                    "operation": "credential_rotation",
                    "scope": "all_databases",
                    "services_affected": 12,
                    "requires_coordination": True
                }
            }
        ]
    },
    "customer-service-004": {
        "name": "Customer Service AI",
        "description": "AI agent handling customer support and communications",
        "icon": "🎧",
        "scenarios": [
            {
                "action_type": "query",
                "description": "Looking up customer order history",
                "risk_score": 15,
                "resource": "order_database",
                "metadata": {
                    "customer_id": "CUST-9182",
                    "query_scope": "order_history",
                    "time_range": "last_12_months"
                }
            },
            {
                "action_type": "communication",
                "description": "Sending automated response to customer inquiry",
                "risk_score": 30,
                "resource": "email_system",
                "metadata": {
                    "channel": "email",
                    "template": "order_status_update",
                    "personalization_level": "high"
                }
            },
            {
                "action_type": "data_modification",
                "description": "Processing customer refund request",
                "risk_score": 55,
                "resource": "refund_system",
                "metadata": {
                    "refund_amount": 149.99,
                    "order_id": "ORD-28471",
                    "reason": "product_defect",
                    "auto_approved": False
                }
            },
            {
                "action_type": "data_modification",
                "description": "Updating customer account with new billing information",
                "risk_score": 60,
                "resource": "customer_accounts",
                "metadata": {
                    "update_type": "billing_info",
                    "verification_completed": True,
                    "pci_compliant": True
                }
            }
        ]
    }
}


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")


def print_agent_header(agent_id: str, agent_info: Dict):
    print(f"\n{Colors.BOLD}{agent_info['icon']} {agent_info['name']}{Colors.RESET}")
    print(f"   {Colors.CYAN}ID: {agent_id}{Colors.RESET}")
    print(f"   {agent_info['description']}")


def get_risk_color(risk_score: int) -> str:
    if risk_score < 30:
        return Colors.GREEN
    elif risk_score < 60:
        return Colors.YELLOW
    elif risk_score < 80:
        return Colors.MAGENTA
    else:
        return Colors.RED


def run_simulation(continuous: bool = False, interval: int = 30):
    """Run the agent simulation."""

    print_header("OW-AI Enterprise Agent Simulation")
    print(f"\n  API: {API_URL}")
    print(f"  Started: {datetime.now(UTC).isoformat()}")

    if continuous:
        print(f"  Mode: {Colors.YELLOW}CONTINUOUS{Colors.RESET} (interval: {interval}s)")
        print(f"  Press Ctrl+C to stop")
    else:
        print(f"  Mode: {Colors.GREEN}SINGLE RUN{Colors.RESET}")

    simulator = AgentSimulator(API_URL, API_KEY)

    # Test connection
    print(f"\n{Colors.BLUE}Testing API connection...{Colors.RESET}")
    try:
        response = simulator.session.get(f"{API_URL}/api/agent-activity")
        if response.status_code == 200:
            print(f"  {Colors.GREEN}Connected successfully{Colors.RESET}")
        else:
            print(f"  {Colors.RED}Connection failed: {response.status_code}{Colors.RESET}")
            return
    except Exception as e:
        print(f"  {Colors.RED}Connection error: {e}{Colors.RESET}")
        return

    iteration = 0

    try:
        while True:
            iteration += 1

            if continuous:
                print_header(f"Simulation Round {iteration}")

            # Run through each agent
            for agent_id, agent_info in AGENTS.items():
                print_agent_header(agent_id, agent_info)

                # Select 1-2 random scenarios for this round
                num_scenarios = random.randint(1, 2) if continuous else len(agent_info["scenarios"])
                scenarios = random.sample(agent_info["scenarios"], min(num_scenarios, len(agent_info["scenarios"])))

                for scenario in scenarios:
                    # Build the action payload
                    action = {
                        "agent_id": agent_id,
                        "action_type": scenario["action_type"],
                        "description": scenario["description"],
                        "risk_score": scenario["risk_score"],
                        "resource": scenario.get("resource", "unknown"),
                        "metadata": scenario.get("metadata", {}),
                        "status": "pending"
                    }

                    risk_color = get_risk_color(scenario["risk_score"])

                    print(f"\n   {Colors.BLUE}Submitting:{Colors.RESET} {scenario['description'][:50]}...")
                    print(f"   {Colors.CYAN}Type:{Colors.RESET} {scenario['action_type']}")
                    print(f"   {Colors.CYAN}Risk:{Colors.RESET} {risk_color}{scenario['risk_score']}/100{Colors.RESET}")

                    result = simulator.submit_action(action)

                    if result:
                        action_id = result.get("id") or result.get("action_id", "N/A")
                        status = result.get("status", "submitted")
                        print(f"   {Colors.GREEN}Created:{Colors.RESET} Action ID #{action_id} ({status})")

                    # Small delay between actions
                    time.sleep(0.5)

            if not continuous:
                break

            print(f"\n{Colors.YELLOW}Waiting {interval}s before next round...{Colors.RESET}")
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Simulation stopped by user{Colors.RESET}")

    # Summary
    print_header("Simulation Summary")
    print(f"\n  Total Actions Created: {Colors.GREEN}{len(simulator.actions_created)}{Colors.RESET}")
    print(f"  Agents Simulated: {len(AGENTS)}")
    print(f"\n  {Colors.CYAN}View in Dashboard:{Colors.RESET}")
    print(f"  {API_URL}/#org=acme-corp")
    print(f"\n  {Colors.CYAN}Query via API:{Colors.RESET}")
    print(f"  curl -H 'X-API-Key: {API_KEY[:20]}...' {API_URL}/api/agent-activity")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OW-AI Enterprise Agent Simulation")
    parser.add_argument("--continuous", "-c", action="store_true",
                        help="Run continuously (simulates ongoing agent activity)")
    parser.add_argument("--interval", "-i", type=int, default=30,
                        help="Interval between rounds in continuous mode (seconds)")

    args = parser.parse_args()

    run_simulation(continuous=args.continuous, interval=args.interval)


if __name__ == "__main__":
    main()
