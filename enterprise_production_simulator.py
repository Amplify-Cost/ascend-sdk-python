#!/usr/bin/env python3
"""
OW-kai Enterprise Production Simulator
=======================================

Simulates real-world enterprise customer usage patterns by continuously
sending agent actions and MCP server requests to the platform.

🏢 ENTERPRISE DESIGN PRINCIPLE:
Simulator sends ONLY raw action data (agent_id, action_type, description, details).
The APPLICATION decides EVERYTHING:
- Risk scores (via CVSS v3.1 calculator)
- Approval requirements (based on risk thresholds)
- NIST control mappings (via auto-mapper)
- MITRE tactic mappings (via enrichment service)
- Workflow routing (based on enterprise policy engine)

This script mimics how actual enterprise customers would use the platform:
- Multiple AI agents performing various operations
- MCP servers requesting tool executions
- Realistic timing and patterns
- Various environments (dev, staging, production)
- Different data sensitivity levels
- NO pre-populated risk assessments or approval hints

Engineer: Donald King (OW-kai Enterprise)
Date: 2025-11-19 (Updated)
"""

import requests
import json
import time
import random
import argparse
from datetime import datetime, UTC
from typing import Dict, List, Optional
import sys
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# COLOR OUTPUT
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ============================================================================
# ENTERPRISE SIMULATION DATA
# ============================================================================

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SimulationStats:
    total_actions: int = 0
    agent_actions: int = 0
    mcp_actions: int = 0
    low_risk: int = 0
    medium_risk: int = 0
    high_risk: int = 0
    critical_risk: int = 0
    approved: int = 0
    denied: int = 0
    pending: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None

# Realistic enterprise agent scenarios
ENTERPRISE_SCENARIOS = {
    "data_analytics": {
        "agents": ["data-pipeline-agent", "analytics-etl-agent", "reporting-agent"],
        "actions": [
            {
                "action_type": "database_read",
                "description": "Query customer analytics data",
                "risk": RiskLevel.LOW,
                "details": {
                    "database": "analytics_db",
                    "query_type": "SELECT",
                    "table": "customer_analytics",
                    "row_count": 10000
                }
            },
            {
                "action_type": "database_write",
                "description": "Update aggregated metrics",
                "risk": RiskLevel.MEDIUM,
                "details": {
                    "database": "analytics_db",
                    "operation": "INSERT",
                    "table": "daily_metrics",
                    "row_count": 500
                }
            }
        ]
    },
    "financial_processing": {
        "agents": ["payment-processor-agent", "fraud-detection-agent", "reconciliation-agent"],
        "actions": [
            {
                "action_type": "database_read",
                "description": "Retrieve transaction history",
                "risk": RiskLevel.MEDIUM,
                "details": {
                    "database": "transactions_db",
                    "query_type": "SELECT",
                    "table": "payment_transactions",
                    "contains_pii": True,
                    "row_count": 5000
                }
            },
            {
                "action_type": "database_write",
                "description": "Process batch payments",
                "risk": RiskLevel.HIGH,
                "details": {
                    "database": "transactions_db",
                    "operation": "UPDATE",
                    "table": "payment_transactions",
                    "contains_pii": True,
                    "row_count": 1500,
                    "environment": "production"
                }
            },
            {
                "action_type": "api_call",
                "description": "Submit payment to processor",
                "risk": RiskLevel.HIGH,
                "details": {
                    "endpoint": "https://api.payment-processor.com/submit",
                    "method": "POST",
                    "contains_pii": True,
                    "amount_usd": 125000
                }
            }
        ]
    },
    "healthcare_records": {
        "agents": ["ehr-integration-agent", "patient-data-agent", "compliance-agent"],
        "actions": [
            {
                "action_type": "database_read",
                "description": "Access patient medical records",
                "risk": RiskLevel.HIGH,
                "details": {
                    "database": "patient_records_db",
                    "query_type": "SELECT",
                    "table": "medical_history",
                    "contains_pii": True,
                    "hipaa_protected": True,
                    "row_count": 250
                }
            },
            {
                "action_type": "database_write",
                "description": "Update patient diagnosis codes",
                "risk": RiskLevel.CRITICAL,
                "details": {
                    "database": "patient_records_db",
                    "operation": "UPDATE",
                    "table": "diagnosis_codes",
                    "contains_pii": True,
                    "hipaa_protected": True,
                    "row_count": 50,
                    "environment": "production"
                }
            }
        ]
    },
    "infrastructure_management": {
        "agents": ["infrastructure-agent", "deployment-agent", "monitoring-agent"],
        "actions": [
            {
                "action_type": "aws_action",
                "description": "List EC2 instances",
                "risk": RiskLevel.LOW,
                "details": {
                    "service": "ec2",
                    "action": "describe_instances",
                    "region": "us-east-2"
                }
            },
            {
                "action_type": "aws_action",
                "description": "Terminate staging instances",
                "risk": RiskLevel.MEDIUM,
                "details": {
                    "service": "ec2",
                    "action": "terminate_instances",
                    "region": "us-east-2",
                    "environment": "staging",
                    "instance_count": 3
                }
            },
            {
                "action_type": "aws_action",
                "description": "Modify production RDS instance",
                "risk": RiskLevel.HIGH,
                "details": {
                    "service": "rds",
                    "action": "modify_db_instance",
                    "region": "us-east-2",
                    "environment": "production",
                    "instance_class": "db.r6g.xlarge"
                }
            }
        ]
    },
    "customer_service": {
        "agents": ["support-ticket-agent", "customer-lookup-agent", "refund-agent"],
        "actions": [
            {
                "action_type": "database_read",
                "description": "Lookup customer account details",
                "risk": RiskLevel.MEDIUM,
                "details": {
                    "database": "customer_db",
                    "query_type": "SELECT",
                    "table": "customer_accounts",
                    "contains_pii": True,
                    "row_count": 10
                }
            },
            {
                "action_type": "database_write",
                "description": "Process customer refund",
                "risk": RiskLevel.HIGH,
                "details": {
                    "database": "customer_db",
                    "operation": "INSERT",
                    "table": "refund_transactions",
                    "contains_pii": True,
                    "amount_usd": 5000,
                    "environment": "production"
                }
            }
        ]
    }
}

# MCP Server scenarios (simulating MCP servers making tool requests)
MCP_SERVER_SCENARIOS = [
    {
        "server_name": "filesystem-server",
        "tool": "read_file",
        "risk": RiskLevel.LOW,
        "args": {
            "path": "/home/user/documents/report.pdf"
        }
    },
    {
        "server_name": "filesystem-server",
        "tool": "write_file",
        "risk": RiskLevel.MEDIUM,
        "args": {
            "path": "/var/www/html/config.json",
            "content": "configuration data"
        }
    },
    {
        "server_name": "filesystem-server",
        "tool": "write_file",
        "risk": RiskLevel.HIGH,
        "args": {
            "path": "/etc/production/database.conf",
            "content": "db_password=secret123"
        }
    },
    {
        "server_name": "database-mcp-server",
        "tool": "execute_query",
        "risk": RiskLevel.MEDIUM,
        "args": {
            "database": "customers",
            "query": "SELECT * FROM orders WHERE customer_id = 12345"
        }
    },
    {
        "server_name": "database-mcp-server",
        "tool": "execute_query",
        "risk": RiskLevel.HIGH,
        "args": {
            "database": "customers",
            "query": "DELETE FROM orders WHERE status = 'cancelled'"
        }
    },
    {
        "server_name": "aws-mcp-server",
        "tool": "s3_upload",
        "risk": RiskLevel.MEDIUM,
        "args": {
            "bucket": "company-backups",
            "key": "database/backup-2024.sql.gz",
            "data_size_mb": 500
        }
    },
    {
        "server_name": "slack-mcp-server",
        "tool": "send_message",
        "risk": RiskLevel.LOW,
        "args": {
            "channel": "#alerts",
            "message": "System health check: All services operational"
        }
    }
]

# ============================================================================
# ENTERPRISE SIMULATOR
# ============================================================================

class EnterpriseProductionSimulator:
    """Simulates real-world enterprise customer usage"""

    def __init__(self, base_url: str, mode: str = "continuous", duration: int = 60):
        self.base_url = base_url.rstrip('/')
        self.mode = mode
        self.duration = duration
        self.token = None
        self.stats = SimulationStats()
        self.running = True

    def log(self, message: str, level: str = "INFO"):
        """Structured logging with colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.OKCYAN,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER,
            "STATS": Colors.OKBLUE
        }.get(level, Colors.ENDC)

        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")

    def authenticate(self) -> bool:
        """Authenticate and get token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/token",
                json={
                    "email": "admin@owkai.com",
                    "password": "admin123"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log(f"✅ Authenticated successfully", "SUCCESS")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False

    def submit_agent_action(self, scenario_name: str, action_config: dict) -> Optional[dict]:
        """Submit an agent action"""
        try:
            # Select random agent from scenario
            scenario = ENTERPRISE_SCENARIOS[scenario_name]
            agent_id = random.choice(scenario['agents'])

            # 🏢 ENTERPRISE FIX (2025-11-19): Simulator sends ONLY raw action data
            # Application decides EVERYTHING: risk scores, approval requirements, NIST/MITRE mappings
            # Simulator does NOT pre-populate any risk assessment or approval decisions
            payload = {
                "agent_id": agent_id,
                "action_type": action_config['action_type'],
                "description": action_config['description'],
                "details": action_config['details']
                # Removed: requires_approval (let application decide based on CVSS risk scoring)
            }

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            # Note: The endpoint requires CSRF token in production
            headers["X-CSRF-Token"] = "simulator-csrf-token"

            response = requests.post(
                f"{self.base_url}/api/agent-action",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.stats.agent_actions += 1
                self.stats.total_actions += 1

                risk_score = data.get('risk_score', 0)
                status = data.get('status', 'unknown')
                action_id = data.get('id', 'unknown')

                # Update risk stats
                if risk_score < 30:
                    self.stats.low_risk += 1
                    risk_label = "LOW"
                    risk_color = Colors.OKGREEN
                elif risk_score < 60:
                    self.stats.medium_risk += 1
                    risk_label = "MEDIUM"
                    risk_color = Colors.OKCYAN
                elif risk_score < 80:
                    self.stats.high_risk += 1
                    risk_label = "HIGH"
                    risk_color = Colors.WARNING
                else:
                    self.stats.critical_risk += 1
                    risk_label = "CRITICAL"
                    risk_color = Colors.FAIL

                # Update status stats
                if status == "approved":
                    self.stats.approved += 1
                elif status in ["pending_approval", "pending_stage_1", "pending_stage_2"]:
                    self.stats.pending += 1
                elif status == "denied":
                    self.stats.denied += 1

                self.log(
                    f"🤖 AGENT ACTION #{action_id} | {agent_id[:20]} | "
                    f"{risk_color}{risk_label} (Score: {risk_score}){Colors.ENDC} | "
                    f"Status: {status} | {action_config['description'][:50]}",
                    "INFO"
                )

                return data
            else:
                self.stats.errors += 1
                self.log(
                    f"❌ Agent action failed: HTTP {response.status_code} | "
                    f"{scenario_name} | {action_config['description'][:40]}",
                    "ERROR"
                )
                return None

        except Exception as e:
            self.stats.errors += 1
            self.log(f"❌ Agent action error: {str(e)}", "ERROR")
            return None

    def submit_mcp_action(self, mcp_config: dict) -> Optional[dict]:
        """Submit an MCP server action"""
        try:
            # 🏢 ENTERPRISE FIX (2025-11-18): Use UNIFIED endpoint (same as agent actions)
            # This ensures MCP actions are created with correct status (pending/approved)
            # Previous endpoint was for approval workflows, not initial submission
            payload = {
                "action_source": "mcp",                       # Indicates this is an MCP action
                "mcp_server": mcp_config['server_name'],      # MCP server name
                "action_type": mcp_config['tool'],            # Tool being invoked
                "namespace": "mcp",                           # MCP namespace
                "verb": mcp_config['tool'],                   # MCP verb (e.g., "read_file")
                "resource": json.dumps(mcp_config['args']),   # Resource (arguments as JSON string)
                "context": {                                  # Additional context
                    "user_id": 7,  # Admin user
                    "session_id": f"sim-session-{int(time.time())}",
                    "simulator": True,
                    "description": f"MCP {mcp_config['tool']} on {mcp_config['server_name']}"
                }
            }

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            headers["X-CSRF-Token"] = "simulator-csrf-token"

            # 🏢 ENTERPRISE FIX: Use unified endpoint (handles both agent and MCP actions)
            response = requests.post(
                f"{self.base_url}/api/governance/unified/action",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.stats.mcp_actions += 1
                self.stats.total_actions += 1

                # Extract decision from unified response format
                action_id = data.get('action_id', 'unknown')
                status = data.get('status', 'unknown')

                # Map status to decision for display
                decision_map = {
                    'approved': 'approved',
                    'pending': 'pending',
                    'denied': 'denied',
                    'pending_approval': 'pending'
                }
                decision = decision_map.get(status, status)

                # Update status stats
                if status == "approved":
                    self.stats.approved += 1
                elif status in ["pending", "pending_approval", "pending_stage_1", "pending_stage_2"]:
                    self.stats.pending += 1
                elif status == "denied":
                    self.stats.denied += 1

                # Extract risk score from response
                risk_score = data.get('risk_score', 0)

                # Update risk stats based on risk score
                if risk_score < 30:
                    self.stats.low_risk += 1
                    risk_label = "LOW"
                    risk_color = Colors.OKGREEN
                elif risk_score < 60:
                    self.stats.medium_risk += 1
                    risk_label = "MEDIUM"
                    risk_color = Colors.OKCYAN
                elif risk_score < 80:
                    self.stats.high_risk += 1
                    risk_label = "HIGH"
                    risk_color = Colors.WARNING
                else:
                    self.stats.critical_risk += 1
                    risk_label = "CRITICAL"
                    risk_color = Colors.FAIL

                self.log(
                    f"🔧 MCP ACTION #{action_id} | {mcp_config['server_name']} | "
                    f"Tool: {mcp_config['tool']} | "
                    f"{risk_color}{risk_label} (Score: {risk_score}){Colors.ENDC} | "
                    f"Status: {status}",
                    "INFO"
                )

                return data
            else:
                self.stats.errors += 1
                self.log(
                    f"❌ MCP action failed: HTTP {response.status_code} | "
                    f"{mcp_config['server_name']} | {mcp_config['tool']}",
                    "ERROR"
                )
                return None

        except Exception as e:
            self.stats.errors += 1
            self.log(f"❌ MCP action error: {str(e)}", "ERROR")
            return None

    def print_stats(self):
        """Print current statistics"""
        elapsed = (datetime.now(UTC) - self.stats.start_time).total_seconds() if self.stats.start_time else 0
        rate = self.stats.total_actions / elapsed if elapsed > 0 else 0

        print()
        self.log("=" * 80, "HEADER")
        self.log("📊 SIMULATION STATISTICS", "HEADER")
        self.log("=" * 80, "HEADER")
        self.log(f"⏱️  Runtime: {int(elapsed)}s | Rate: {rate:.2f} actions/sec", "STATS")
        self.log(f"📈 Total Actions: {self.stats.total_actions}", "STATS")
        self.log(f"   🤖 Agent Actions: {self.stats.agent_actions}", "STATS")
        self.log(f"   🔧 MCP Actions: {self.stats.mcp_actions}", "STATS")
        print()
        self.log(f"🎯 Risk Distribution:", "STATS")
        self.log(f"   {Colors.OKGREEN}● LOW: {self.stats.low_risk}{Colors.ENDC}", "STATS")
        self.log(f"   {Colors.OKCYAN}● MEDIUM: {self.stats.medium_risk}{Colors.ENDC}", "STATS")
        self.log(f"   {Colors.WARNING}● HIGH: {self.stats.high_risk}{Colors.ENDC}", "STATS")
        self.log(f"   {Colors.FAIL}● CRITICAL: {self.stats.critical_risk}{Colors.ENDC}", "STATS")
        print()
        self.log(f"📋 Status:", "STATS")
        self.log(f"   ✅ Approved: {self.stats.approved}", "STATS")
        self.log(f"   ⏳ Pending: {self.stats.pending}", "STATS")
        self.log(f"   ❌ Denied: {self.stats.denied}", "STATS")
        self.log(f"   💥 Errors: {self.stats.errors}", "STATS")
        self.log("=" * 80, "HEADER")
        print()

    def run_burst_mode(self, count: int = 10):
        """Send a burst of actions"""
        self.log(f"🚀 BURST MODE: Sending {count} actions...", "HEADER")

        for i in range(count):
            # Alternate between agent and MCP actions
            if i % 2 == 0:
                # Agent action
                scenario = random.choice(list(ENTERPRISE_SCENARIOS.keys()))
                action = random.choice(ENTERPRISE_SCENARIOS[scenario]['actions'])
                self.submit_agent_action(scenario, action)
            else:
                # MCP action
                mcp_config = random.choice(MCP_SERVER_SCENARIOS)
                self.submit_mcp_action(mcp_config)

            # Small delay between burst actions
            time.sleep(0.5)

        self.print_stats()

    def run_continuous_mode(self):
        """Continuously simulate enterprise usage"""
        self.log(f"🔄 CONTINUOUS MODE: Simulating for {self.duration} seconds...", "HEADER")
        self.log(f"⌨️  Press Ctrl+C to stop early", "INFO")
        print()

        end_time = time.time() + self.duration
        stats_interval = 10  # Print stats every 10 seconds
        last_stats_print = time.time()

        try:
            while time.time() < end_time and self.running:
                # Randomly choose scenario type
                if random.random() < 0.6:  # 60% agent actions
                    scenario = random.choice(list(ENTERPRISE_SCENARIOS.keys()))
                    action = random.choice(ENTERPRISE_SCENARIOS[scenario]['actions'])
                    self.submit_agent_action(scenario, action)
                else:  # 40% MCP actions
                    mcp_config = random.choice(MCP_SERVER_SCENARIOS)
                    self.submit_mcp_action(mcp_config)

                # Print periodic stats
                if time.time() - last_stats_print >= stats_interval:
                    self.print_stats()
                    last_stats_print = time.time()

                # Realistic delay between actions (1-5 seconds)
                delay = random.uniform(1, 5)
                time.sleep(delay)

        except KeyboardInterrupt:
            self.log("\n⚠️  Simulation interrupted by user", "WARNING")

        # Final stats
        self.print_stats()

    def run_realistic_mode(self):
        """Simulate realistic enterprise patterns"""
        self.log(f"🏢 REALISTIC MODE: Simulating enterprise workday pattern...", "HEADER")
        self.log(f"⌨️  Press Ctrl+C to stop", "INFO")
        print()

        # Simulate different activity levels throughout the day
        patterns = {
            "morning_rush": {"delay_range": (2, 5), "agent_ratio": 0.7},
            "midday_steady": {"delay_range": (3, 8), "agent_ratio": 0.5},
            "afternoon_peak": {"delay_range": (1, 4), "agent_ratio": 0.8},
            "evening_quiet": {"delay_range": (5, 15), "agent_ratio": 0.3}
        }

        end_time = time.time() + self.duration
        stats_interval = 15
        last_stats_print = time.time()

        try:
            while time.time() < end_time and self.running:
                # Cycle through patterns
                pattern_duration = self.duration / 4
                elapsed = time.time() - (end_time - self.duration)
                pattern_index = int(elapsed / pattern_duration)
                pattern_name = list(patterns.keys())[pattern_index % 4]
                pattern = patterns[pattern_name]

                # Choose action type based on pattern
                if random.random() < pattern['agent_ratio']:
                    scenario = random.choice(list(ENTERPRISE_SCENARIOS.keys()))
                    action = random.choice(ENTERPRISE_SCENARIOS[scenario]['actions'])
                    self.submit_agent_action(scenario, action)
                else:
                    mcp_config = random.choice(MCP_SERVER_SCENARIOS)
                    self.submit_mcp_action(mcp_config)

                # Print periodic stats
                if time.time() - last_stats_print >= stats_interval:
                    self.log(f"📊 Current pattern: {pattern_name.replace('_', ' ').title()}", "STATS")
                    self.print_stats()
                    last_stats_print = time.time()

                # Pattern-based delay
                delay = random.uniform(*pattern['delay_range'])
                time.sleep(delay)

        except KeyboardInterrupt:
            self.log("\n⚠️  Simulation interrupted by user", "WARNING")

        # Final stats
        self.print_stats()

    def run(self):
        """Main entry point"""
        self.log("=" * 80, "HEADER")
        self.log("🏢 OW-KAI ENTERPRISE PRODUCTION SIMULATOR", "HEADER")
        self.log(f"🎯 Target: {self.base_url}", "HEADER")
        self.log(f"📊 Mode: {self.mode.upper()}", "HEADER")
        self.log("=" * 80, "HEADER")
        print()

        # Authenticate
        if not self.authenticate():
            self.log("❌ Cannot continue without authentication", "ERROR")
            return False

        print()
        self.stats.start_time = datetime.now(UTC)

        # Run simulation based on mode
        if self.mode == "burst":
            self.run_burst_mode(count=20)
        elif self.mode == "continuous":
            self.run_continuous_mode()
        elif self.mode == "realistic":
            self.run_realistic_mode()
        else:
            self.log(f"❌ Unknown mode: {self.mode}", "ERROR")
            return False

        return True


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="OW-kai Enterprise Production Simulator - Simulate real customer usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Burst mode - send 20 actions quickly
  python enterprise_production_simulator.py --mode burst

  # Continuous mode - run for 5 minutes
  python enterprise_production_simulator.py --mode continuous --duration 300

  # Realistic mode - simulate workday pattern for 10 minutes
  python enterprise_production_simulator.py --mode realistic --duration 600

  # Target different environment
  python enterprise_production_simulator.py --url http://localhost:8000 --mode burst
        """
    )
    parser.add_argument(
        '--url',
        default='https://pilot.owkai.app',
        help='Base URL of the platform (default: https://pilot.owkai.app)'
    )
    parser.add_argument(
        '--mode',
        choices=['burst', 'continuous', 'realistic'],
        default='continuous',
        help='Simulation mode (default: continuous)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration in seconds for continuous/realistic modes (default: 60)'
    )

    args = parser.parse_args()

    simulator = EnterpriseProductionSimulator(
        base_url=args.url,
        mode=args.mode,
        duration=args.duration
    )

    success = simulator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
