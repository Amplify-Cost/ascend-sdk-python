#!/usr/bin/env python3
"""
OW-kai Enterprise Agent Simulation
===================================

Production test script demonstrating real-world agent governance integration.

This simulates how a customer's AI agents would integrate with OW-kai for:
- Action submission and approval workflow
- Risk-based auto-approval
- Human-in-the-loop for high-risk actions
- Audit trail and compliance logging

Usage:
    # Set your API key first
    export OWKAI_API_KEY="owkai_live_xxx"

    # Run the simulation
    python enterprise_agent_simulation.py

    # Or with inline API key
    python enterprise_agent_simulation.py --api-key "owkai_live_xxx"

Prerequisites:
    1. Register an agent in the UI (Agent Registry)
    2. Generate an API key (Settings > API Keys)
    3. Configure the agent's allowed actions

Author: OW-kai Enterprise
Version: 1.0.0
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
DEFAULT_BASE_URL = "https://pilot.owkai.app"

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print simulation banner."""
    print(f"""
{Colors.CYAN}{'='*70}
   ____  _    __     _  __    _    ___    _____ _
  / __ \| |  / /    | |/ /   / \  |_ _|  / ____(_)
 | |  | | | / /_____| ' /   / _ \  | |  | (___  _ _ __ ___
 | |  | | |/ /______| <    / ___ \ | |   \___ \| | '_ ` _ \
 | |__| |   <       | . \ /_/   \_\___|  ____) | | | | | | |
  \____/|_|\_\      |_|\_\            |_|_____/|_|_| |_| |_|

  Enterprise Agent Governance Simulation
{'='*70}{Colors.ENDC}
""")

class EnterpriseAgentSimulator:
    """
    Simulates an enterprise AI agent integrating with OW-kai governance.

    This demonstrates the complete flow:
    1. Agent submits action request
    2. OW-kai evaluates risk and policies
    3. Action is approved, denied, or held for human review
    4. Agent receives decision and proceeds accordingly
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OWkai-Enterprise-Agent/1.0"
        })
        self.agent_id = None
        self.action_history = []

    def log(self, level: str, message: str):
        """Log with timestamp and color."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "ACTION": Colors.CYAN
        }
        color = colors.get(level, Colors.ENDC)
        print(f"{Colors.BOLD}[{timestamp}]{Colors.ENDC} {color}[{level}]{Colors.ENDC} {message}")

    def register_agent(
        self,
        agent_id: str,
        display_name: str,
        agent_type: str = "supervised",
        allowed_actions: list = None,
        auto_approve_below: int = 30,
        max_risk_threshold: int = 80
    ) -> bool:
        """
        Register the agent with OW-kai governance platform.

        This is typically done once during agent deployment.
        """
        self.agent_id = agent_id
        self.log("INFO", f"Registering agent: {display_name} ({agent_id})")

        payload = {
            "agent_id": agent_id,
            "display_name": display_name,
            "description": f"Enterprise simulation agent - {display_name}",
            "agent_type": agent_type,
            "auto_approve_below": auto_approve_below,
            "max_risk_threshold": max_risk_threshold,
            "allowed_action_types": allowed_actions or [],
            "alert_on_high_risk": True,
            "tags": ["simulation", "enterprise", "test"]
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/registry/agents",
                json=payload
            )

            if response.status_code == 200:
                self.log("SUCCESS", f"Agent registered successfully")
                return True
            elif response.status_code == 409:
                self.log("WARNING", "Agent already registered (continuing with existing)")
                return True
            else:
                self.log("ERROR", f"Registration failed: {response.text}")
                return False
        except Exception as e:
            self.log("ERROR", f"Registration error: {str(e)}")
            return False

    def submit_action(
        self,
        action_type: str,
        description: str,
        tool_name: str = "enterprise_tool",
        risk_score: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Submit an action for governance evaluation.

        This is called BEFORE the agent executes any sensitive operation.
        The action is evaluated against policies and risk thresholds.

        Returns:
            {
                "action_id": 123,
                "status": "approved" | "pending_approval" | "rejected",
                "risk_score": 75,
                "risk_level": "high",
                "can_proceed": True/False,
                "nist_controls": ["AC-3", "AU-12"],
                "mitre_tactics": ["TA0006"]
            }
        """
        self.log("ACTION", f"Submitting: {action_type} - {description[:50]}...")

        payload = {
            "agent_id": self.agent_id,
            "action_type": action_type,
            "description": description,
            "tool_name": tool_name
        }

        if risk_score is not None:
            payload["risk_score"] = risk_score
        if metadata:
            payload["metadata"] = metadata

        try:
            response = self.session.post(
                f"{self.base_url}/api/sdk/agent-action",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                self._log_action_result(result)
                self.action_history.append(result)
                return result
            else:
                error = response.json() if response.text else {"detail": "Unknown error"}
                self.log("ERROR", f"Action submission failed: {error}")
                return {"status": "error", "error": error}

        except Exception as e:
            self.log("ERROR", f"Action error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _log_action_result(self, result: Dict[str, Any]):
        """Log the action result with visual formatting."""
        status = result.get("status", "unknown")
        risk_score = result.get("risk_score", 0)
        risk_level = result.get("risk_level", "unknown")
        action_id = result.get("action_id", "N/A")

        # Status color
        if status == "approved":
            status_display = f"{Colors.GREEN}APPROVED{Colors.ENDC}"
        elif status == "pending_approval":
            status_display = f"{Colors.YELLOW}PENDING APPROVAL{Colors.ENDC}"
        elif status == "rejected":
            status_display = f"{Colors.RED}REJECTED{Colors.ENDC}"
        else:
            status_display = f"{Colors.YELLOW}{status}{Colors.ENDC}"

        # Risk level color
        risk_colors = {
            "critical": Colors.RED,
            "high": Colors.YELLOW,
            "medium": Colors.CYAN,
            "low": Colors.GREEN
        }
        risk_color = risk_colors.get(risk_level, Colors.ENDC)

        print(f"""
    {Colors.BOLD}Action Result:{Colors.ENDC}
    ├── ID: {action_id}
    ├── Status: {status_display}
    ├── Risk Score: {risk_color}{risk_score}/100{Colors.ENDC}
    ├── Risk Level: {risk_color}{risk_level.upper()}{Colors.ENDC}
    ├── NIST Controls: {result.get('nist_controls', [])}
    └── MITRE Tactics: {result.get('mitre_tactics', [])}
""")

    def wait_for_approval(self, action_id: int, timeout: int = 60) -> bool:
        """
        Wait for human approval of a pending action.

        In production, you might:
        - Poll periodically
        - Use webhooks for immediate notification
        - Implement async callbacks
        """
        self.log("INFO", f"Waiting for approval of action {action_id} (timeout: {timeout}s)")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/agent-action/status/{action_id}"
                )
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")

                    if status == "approved":
                        self.log("SUCCESS", f"Action {action_id} was APPROVED")
                        return True
                    elif status == "rejected":
                        self.log("ERROR", f"Action {action_id} was REJECTED")
                        return False
                    elif status != "pending_approval":
                        self.log("WARNING", f"Unexpected status: {status}")
                        return False

                    # Still pending, wait and retry
                    remaining = int(timeout - (time.time() - start_time))
                    print(f"\r    Waiting for approval... ({remaining}s remaining)", end="")
                    time.sleep(2)
                else:
                    self.log("ERROR", f"Failed to check status: {response.text}")
                    return False
            except Exception as e:
                self.log("ERROR", f"Error checking status: {str(e)}")
                return False

        print()  # Newline after countdown
        self.log("WARNING", f"Timeout waiting for approval of action {action_id}")
        return False

    def run_simulation(self, scenarios: list = None):
        """
        Run a complete governance simulation with various action types.

        Demonstrates:
        - Low-risk actions (auto-approved)
        - Medium-risk actions (logged, may require review)
        - High-risk actions (requires human approval)
        - Critical-risk actions (blocked or requires MFA)
        """
        if scenarios is None:
            scenarios = self._get_default_scenarios()

        print(f"\n{Colors.BOLD}Starting Enterprise Governance Simulation{Colors.ENDC}")
        print(f"Agent: {self.agent_id}")
        print(f"API: {self.base_url}")
        print(f"Scenarios: {len(scenarios)}")
        print("-" * 50)

        results_summary = {"approved": 0, "pending": 0, "rejected": 0, "error": 0}

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{Colors.BOLD}[Scenario {i}/{len(scenarios)}]{Colors.ENDC} {scenario.get('name', 'Unnamed')}")

            result = self.submit_action(
                action_type=scenario["action_type"],
                description=scenario["description"],
                tool_name=scenario.get("tool_name", "enterprise_tool"),
                risk_score=scenario.get("risk_score"),
                metadata=scenario.get("metadata")
            )

            status = result.get("status", "error")
            if status == "approved":
                results_summary["approved"] += 1
            elif status == "pending_approval":
                results_summary["pending"] += 1
                # Option to wait for approval
                if scenario.get("wait_for_approval"):
                    self.wait_for_approval(result.get("action_id"), timeout=30)
            elif status == "rejected":
                results_summary["rejected"] += 1
            else:
                results_summary["error"] += 1

            time.sleep(1)  # Brief pause between actions

        # Print summary
        self._print_summary(results_summary)
        return results_summary

    def _get_default_scenarios(self) -> list:
        """Default test scenarios covering all risk levels."""
        return [
            {
                "name": "LLM Call (Low Risk)",
                "action_type": "llm_call",
                "description": "Generate customer response using GPT-4",
                "tool_name": "openai_gpt4",
                "metadata": {"model": "gpt-4", "tokens": 500}
            },
            {
                "name": "Cache Read (Low Risk)",
                "action_type": "cache_read",
                "description": "Read user preferences from Redis cache",
                "tool_name": "redis_cache"
            },
            {
                "name": "Database Query (Medium Risk)",
                "action_type": "database_query",
                "description": "SELECT customer_name, email FROM customers WHERE id = 12345",
                "tool_name": "postgresql",
                "metadata": {"table": "customers", "operation": "SELECT"}
            },
            {
                "name": "API Integration (Medium Risk)",
                "action_type": "external_api_call",
                "description": "Fetch account balance from banking API",
                "tool_name": "banking_api",
                "metadata": {"endpoint": "/accounts/balance", "method": "GET"}
            },
            {
                "name": "File Read (Medium Risk)",
                "action_type": "file_read",
                "description": "Read configuration file /etc/app/config.yaml",
                "tool_name": "filesystem",
                "metadata": {"path": "/etc/app/config.yaml"}
            },
            {
                "name": "Data Export (High Risk)",
                "action_type": "data_export",
                "description": "Export customer records to CSV for compliance audit",
                "tool_name": "data_exporter",
                "risk_score": 75,
                "metadata": {"format": "CSV", "records": 10000}
            },
            {
                "name": "Database Write (Critical Risk)",
                "action_type": "database_write",
                "description": "UPDATE accounts SET balance = balance - 5000 WHERE account_id = 'A123'",
                "tool_name": "postgresql",
                "risk_score": 90,
                "metadata": {"table": "accounts", "operation": "UPDATE", "amount": 5000}
            },
            {
                "name": "Admin Action (Critical Risk)",
                "action_type": "admin_action",
                "description": "Grant admin privileges to user john.doe@company.com",
                "tool_name": "iam_system",
                "risk_score": 95,
                "metadata": {"user": "john.doe@company.com", "role": "admin"}
            }
        ]

    def _print_summary(self, results: Dict[str, int]):
        """Print simulation summary."""
        total = sum(results.values())
        print(f"""
{Colors.BOLD}{'='*50}
SIMULATION SUMMARY
{'='*50}{Colors.ENDC}

Total Actions: {total}

{Colors.GREEN}Approved:{Colors.ENDC}      {results['approved']:3d} ({results['approved']/total*100:.1f}%)
{Colors.YELLOW}Pending:{Colors.ENDC}       {results['pending']:3d} ({results['pending']/total*100:.1f}%)
{Colors.RED}Rejected:{Colors.ENDC}      {results['rejected']:3d} ({results['rejected']/total*100:.1f}%)
{Colors.RED}Errors:{Colors.ENDC}        {results['error']:3d} ({results['error']/total*100:.1f}%)

{Colors.CYAN}Actions requiring human approval are visible in:{Colors.ENDC}
  {self.base_url} > Authorization Dashboard > Pending Actions

{Colors.BOLD}{'='*50}{Colors.ENDC}
""")


def main():
    """Main entry point for the simulation."""
    parser = argparse.ArgumentParser(
        description="OW-kai Enterprise Agent Governance Simulation"
    )
    parser.add_argument(
        "--api-key",
        help="OW-kai API key (or set OWKAI_API_KEY env var)"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OW-kai API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--agent-id",
        default="enterprise-simulation-agent",
        help="Agent ID to use for simulation"
    )
    parser.add_argument(
        "--agent-name",
        default="Enterprise Simulation Agent",
        help="Display name for the agent"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("OWKAI_API_KEY")
    if not api_key:
        print(f"{Colors.RED}Error: API key required{Colors.ENDC}")
        print("Set OWKAI_API_KEY environment variable or use --api-key flag")
        print("\nTo get an API key:")
        print(f"  1. Go to {args.base_url}")
        print("  2. Navigate to Settings > API Keys")
        print("  3. Generate a new key")
        sys.exit(1)

    print_banner()

    # Initialize simulator
    simulator = EnterpriseAgentSimulator(
        api_key=api_key,
        base_url=args.base_url
    )

    # Register the agent
    registered = simulator.register_agent(
        agent_id=args.agent_id,
        display_name=args.agent_name,
        allowed_actions=[
            "llm_call", "cache_read", "cache_write",
            "database_query", "database_read", "database_write",
            "file_read", "file_write",
            "external_api_call", "data_export", "admin_action"
        ]
    )

    if not registered:
        print(f"{Colors.YELLOW}Continuing with simulation despite registration issue...{Colors.ENDC}")

    # Run the simulation
    try:
        results = simulator.run_simulation()

        # Exit with error code if all actions failed
        if results["error"] == sum(results.values()):
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Simulation interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Simulation error: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
