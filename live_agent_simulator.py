#!/usr/bin/env python3
"""
LIVE AGENT SIMULATOR - Real-Time Platform Testing
===================================================

This script simulates real AI agents performing actions and triggering
your platform's monitoring and authorization systems in REAL-TIME.

Watch your platform:
- Catch agent actions as they happen
- Generate alerts for high-risk operations
- Update dashboards in real-time
- Trigger authorization workflows

Usage:
    python3 live_agent_simulator.py --email admin@owkai.com --password your_password

Features:
- Simulates realistic AI agent behavior
- Sends actions every 5-30 seconds
- Varied risk levels (low, medium, high, critical)
- Auto-generates alerts for high-risk actions
- Real-time console output
- Production database updates
"""

import sys
import time
import random
import requests
import json
from datetime import datetime, UTC
from typing import Dict, List

# Configuration
BASE_URL = "https://pilot.owkai.app"

# Color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# HIGH-RISK FOCUSED SCENARIOS - For testing alerts and authorization
AGENT_SCENARIOS = [
    # CRITICAL RISK - Very common for testing (50% of actions)
    {
        "agent_id": "payment-processor",
        "action_type": "api_call",
        "description": "Processing customer payment via Stripe API",
        "tool_name": "stripe_api",
        "risk_level": "critical",
        "risk_score": lambda: random.randint(80, 95),
        "frequency": "common"  # CHANGED: Now very common for testing
    },
    {
        "agent_id": "user-provisioning",
        "action_type": "system_modification",
        "description": "Creating new user account with admin privileges",
        "tool_name": "identity_manager",
        "risk_level": "critical",
        "risk_score": lambda: random.randint(85, 99),
        "frequency": "common"  # CHANGED: Now common for testing
    },
    {
        "agent_id": "firewall-manager",
        "action_type": "system_modification",
        "description": "Updating production firewall rules",
        "tool_name": "cloud_security",
        "risk_level": "critical",
        "risk_score": lambda: random.randint(82, 98),
        "frequency": "common"  # CHANGED: Now common for testing
    },
    {
        "agent_id": "data-export-agent",
        "action_type": "data_export",
        "description": "Exporting customer PII data to external system",
        "tool_name": "data_pipeline",
        "risk_level": "critical",
        "risk_score": lambda: random.randint(81, 95),
        "frequency": "common"  # CHANGED: Now common for testing
    },
    {
        "agent_id": "database-admin",
        "action_type": "database_write",
        "description": "Executing production database schema changes",
        "tool_name": "postgresql_admin",
        "risk_level": "critical",
        "risk_score": lambda: random.randint(83, 97),
        "frequency": "common"  # CHANGED: Now common for testing
    },

    # HIGH RISK - Common (30% of actions)
    {
        "agent_id": "ml-model-updater",
        "action_type": "system_modification",
        "description": "Deploying updated ML model to production",
        "tool_name": "ml_pipeline",
        "risk_level": "high",
        "risk_score": lambda: random.randint(75, 89),
        "frequency": "rare"
    },
    {
        "agent_id": "api-key-manager",
        "action_type": "credentials_access",
        "description": "Rotating production API keys",
        "tool_name": "secrets_manager",
        "risk_level": "high",
        "risk_score": lambda: random.randint(76, 88),
        "frequency": "rare"
    },

    # MEDIUM/LOW RISK - Rare (20% of actions)
    {
        "agent_id": "data-sync-agent",
        "action_type": "database_write",
        "description": "Synchronizing customer data from Salesforce",
        "tool_name": "postgresql_connector",
        "risk_level": "medium",
        "risk_score": lambda: random.randint(50, 69),
        "frequency": "very_rare"
    },
    {
        "agent_id": "backup-automation",
        "action_type": "file_write",
        "description": "Creating automated database backup",
        "tool_name": "aws_s3",
        "risk_level": "low",
        "risk_score": lambda: random.randint(25, 45),
        "frequency": "very_rare"
    },
    {
        "agent_id": "analytics-reporter",
        "action_type": "data_read",
        "description": "Generating weekly analytics report",
        "tool_name": "analytics_engine",
        "risk_level": "low",
        "risk_score": lambda: random.randint(15, 35),
        "frequency": "very_rare"
    }
]


class LiveAgentSimulator:
    """Simulates live AI agents interacting with the platform"""

    def __init__(self, email: str, password: str, interval: int = 10):
        self.email = email
        self.password = password
        self.interval = interval  # seconds between actions
        self.token = None
        self.csrf_token = None
        self.session = requests.Session()
        self.actions_sent = 0
        self.alerts_generated = 0
        self.running = True

    def print_header(self):
        """Print simulator header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'LIVE AGENT SIMULATOR - Real-Time Platform Testing'.center(80)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}\n")
        print(f"{Colors.BOLD}Platform:{Colors.END} {BASE_URL}")
        print(f"{Colors.BOLD}User:{Colors.END} {self.email}")
        print(f"{Colors.BOLD}Interval:{Colors.END} ~{self.interval} seconds between actions")
        print(f"{Colors.BOLD}Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def authenticate(self) -> bool:
        """Authenticate via API and get token"""
        print(f"{Colors.BLUE}🔐 Authenticating...{Colors.END}")

        try:
            # Login via API
            response = self.session.post(
                f"{BASE_URL}/api/auth/token",
                json={"email": self.email, "password": self.password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"{Colors.GREEN}✅ Authenticated successfully{Colors.END}")
                print(f"{Colors.CYAN}User: {self.email}{Colors.END}")
                print(f"{Colors.CYAN}Token: {self.token[:30]}...{Colors.END}\n")
                return True
            else:
                print(f"{Colors.RED}❌ Login failed: {response.status_code}{Colors.END}")
                print(f"{Colors.YELLOW}Response: {response.text[:200]}{Colors.END}")
                return False

        except Exception as e:
            print(f"{Colors.RED}❌ Authentication error: {e}{Colors.END}")
            return False

    def select_scenario(self) -> Dict:
        """Select agent scenario based on frequency weights"""
        # Weight scenarios by frequency
        weighted_scenarios = []
        for scenario in AGENT_SCENARIOS:
            freq = scenario["frequency"]
            weight = {
                "common": 10,
                "rare": 3,
                "very_rare": 1
            }.get(freq, 5)

            weighted_scenarios.extend([scenario] * weight)

        return random.choice(weighted_scenarios)

    def send_agent_action(self, scenario: Dict) -> bool:
        """Send RAW agent action - let platform calculate risk and apply policies"""

        # Add realistic variations to description
        descriptions = [
            scenario["description"],
            f"{scenario['description']} - Batch #{random.randint(1, 999)}",
            f"{scenario['description']} (scheduled task)",
            f"{scenario['description']} - Automated execution"
        ]

        # RAW agent action data - NO pre-calculated risk scores
        # Platform's policy engine will analyze and score this
        action_data = {
            "agent_id": scenario["agent_id"],
            "action_type": scenario["action_type"],
            "description": random.choice(descriptions),
            "tool_name": scenario["tool_name"],
            "target_system": f"prod-{random.choice(['db', 'api', 'web', 'cache'])}",
            # Optional compliance metadata
            "nist_control": random.choice(["AC-2", "AU-9", "SC-7", "IA-2"]),
            "mitre_tactic": random.choice(["TA0001", "TA0002", "TA0003"])
        }

        # Print action being sent (no risk score known yet)
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n{Colors.BOLD}[{timestamp}] Sending Agent Action #{self.actions_sent + 1}{Colors.END}")
        print(f"  Agent: {Colors.CYAN}{scenario['agent_id']}{Colors.END}")
        print(f"  Action: {scenario['action_type']}")
        print(f"  Tool: {scenario['tool_name']}")
        print(f"  Description: {action_data['description'][:70]}...")
        print(f"  {Colors.BLUE}⏳ Platform will assess risk and apply policies...{Colors.END}")

        try:
            # Use the API endpoint designed for agent clients
            response = self.session.post(
                f"{BASE_URL}/api/authorization/agent-action",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=action_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                result = response.json()
                action_id = result.get("id", "unknown")
                risk_score = result.get("risk_score", "unknown")

                # Color code based on platform's calculated risk
                if isinstance(risk_score, (int, float)):
                    risk_color = Colors.RED if risk_score >= 80 else Colors.YELLOW if risk_score >= 60 else Colors.GREEN
                    risk_display = f"{risk_color}{risk_score}{Colors.END}"
                else:
                    risk_display = "unknown"

                print(f"  {Colors.GREEN}✅ Action processed (ID: {action_id}){Colors.END}")
                print(f"  📊 Platform Risk Score: {risk_display}")
                print(f"  📋 Status: {result.get('status', 'unknown')}")

                # Check if platform required approval
                if result.get("requires_approval"):
                    print(f"  {Colors.YELLOW}⚠️  Platform requires approval - Check Authorization Center{Colors.END}")

                # Check if platform triggered alert
                if result.get("alert_triggered"):
                    self.alerts_generated += 1
                    print(f"  {Colors.RED}🚨 PLATFORM TRIGGERED ALERT - Check AI Alert Management{Colors.END}")

                self.actions_sent += 1
                return True
            else:
                print(f"  {Colors.RED}❌ API Error: {response.status_code}{Colors.END}")
                print(f"  {Colors.YELLOW}Response: {response.text[:200]}{Colors.END}")
                return False

        except Exception as e:
            print(f"  {Colors.RED}❌ Error sending action: {e}{Colors.END}")
            return False

    def print_stats(self):
        """Print current statistics"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        actions_per_min = (self.actions_sent / runtime * 60) if runtime > 0 else 0

        print(f"\n{Colors.CYAN}{Colors.BOLD}{'─'*80}{Colors.END}")
        print(f"{Colors.BOLD}Statistics:{Colors.END}")
        print(f"  Actions Sent: {Colors.GREEN}{self.actions_sent}{Colors.END}")
        print(f"  Alerts Generated: {Colors.YELLOW}{self.alerts_generated}{Colors.END}")
        print(f"  Rate: {actions_per_min:.1f} actions/minute")
        print(f"  Runtime: {int(runtime)} seconds")
        print(f"{Colors.CYAN}{Colors.BOLD}{'─'*80}{Colors.END}")

    def run(self):
        """Run the live simulator"""
        self.print_header()

        # Authenticate
        if not self.authenticate():
            print(f"\n{Colors.RED}❌ Cannot start simulator - authentication failed{Colors.END}")
            return

        self.start_time = datetime.now()

        print(f"{Colors.GREEN}{Colors.BOLD}🚀 SIMULATOR STARTED{Colors.END}")
        print(f"{Colors.CYAN}Sending realistic agent actions every ~{self.interval} seconds...{Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.END}\n")
        print(f"{Colors.BOLD}Watch your platform at: {BASE_URL}{Colors.END}")
        print(f"  - Authorization Center: See pending actions appear")
        print(f"  - AI Alert Management: See alerts trigger")
        print(f"  - Dashboard: Watch metrics update")
        print(f"  - Activity Feed: See live agent activity\n")

        try:
            while self.running:
                # Select and send action
                scenario = self.select_scenario()
                self.send_agent_action(scenario)

                # Random interval (simulate realistic timing)
                wait_time = random.randint(
                    max(3, self.interval - 5),
                    self.interval + 5
                )

                # Show stats every 5 actions
                if self.actions_sent % 5 == 0 and self.actions_sent > 0:
                    self.print_stats()

                # Wait before next action
                print(f"\n{Colors.BLUE}⏳ Next action in {wait_time} seconds...{Colors.END}")
                time.sleep(wait_time)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Simulator stopped by user{Colors.END}")
            self.print_stats()
            print(f"\n{Colors.GREEN}✅ Simulation complete{Colors.END}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Live Agent Simulator - Test platform in real-time")
    parser.add_argument("--email", required=True, help="User email for authentication")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between actions (default: 10)")

    args = parser.parse_args()

    simulator = LiveAgentSimulator(
        email=args.email,
        password=args.password,
        interval=args.interval
    )

    simulator.run()


if __name__ == "__main__":
    main()
