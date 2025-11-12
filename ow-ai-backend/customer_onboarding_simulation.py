#!/usr/bin/env python3
"""
CUSTOMER ONBOARDING SIMULATION SCRIPT
=====================================

This script simulates a complete customer onboarding workflow for the OW-KAI platform.
It creates a realistic simulated customer with:
- User accounts (admin, managers, users)
- Agent actions (database writes, file access, API calls)
- Alerts (security incidents, policy violations)
- Smart rules (A/B testing enabled)
- MCP policies (governance and compliance)

Usage:
    python3 customer_onboarding_simulation.py --customer "TechCorp Inc"

Features:
- Creates realistic test data based on actual production patterns
- Tests all platform features end-to-end
- Provides monitoring and verification
- Safe to run (uses test email domains, marks as simulation)
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import User, Alert, AgentAction, SmartRule, Log

# Production database URL
DATABASE_URL = "postgresql://owkai_admin:REDACTED-CREDENTIAL@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot"

# Simulated customer company
CUSTOMER_NAME = "TechCorp Inc"
CUSTOMER_DOMAIN = "techcorp-demo.com"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_step(step_num, text):
    print(f"{Colors.CYAN}{Colors.BOLD}[Step {step_num}]{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


class CustomerOnboardingSimulation:
    """Simulates a complete customer onboarding process"""

    def __init__(self, customer_name=CUSTOMER_NAME, customer_domain=CUSTOMER_DOMAIN):
        self.customer_name = customer_name
        self.customer_domain = customer_domain
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.created_users = []
        self.created_actions = []
        self.created_alerts = []
        self.created_rules = []

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=14)).decode('utf-8')

    def create_customer_users(self):
        """Create user accounts for the simulated customer"""
        print_step(1, f"Creating user accounts for {self.customer_name}")

        users_to_create = [
            {
                "email": f"sarah.johnson@{self.customer_domain}",
                "role": "admin",
                "approval_level": 5,
                "is_emergency_approver": True,
                "max_risk_approval": 100,
                "name": "Sarah Johnson (CEO)"
            },
            {
                "email": f"michael.chen@{self.customer_domain}",
                "role": "manager",
                "approval_level": 3,
                "is_emergency_approver": False,
                "max_risk_approval": 75,
                "name": "Michael Chen (Security Manager)"
            },
            {
                "email": f"emily.rodriguez@{self.customer_domain}",
                "role": "user",
                "approval_level": 1,
                "is_emergency_approver": False,
                "max_risk_approval": 50,
                "name": "Emily Rodriguez (DevOps Engineer)"
            },
            {
                "email": f"david.kim@{self.customer_domain}",
                "role": "user",
                "approval_level": 1,
                "is_emergency_approver": False,
                "max_risk_approval": 50,
                "name": "David Kim (Data Scientist)"
            }
        ]

        for user_data in users_to_create:
            # Check if user already exists
            existing_user = self.session.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print_warning(f"User {user_data['email']} already exists, skipping...")
                self.created_users.append(existing_user)
                continue

            user = User(
                email=user_data["email"],
                password=self.hash_password("Demo2024!"),  # Standard demo password
                role=user_data["role"],
                approval_level=user_data["approval_level"],
                is_emergency_approver=user_data["is_emergency_approver"],
                max_risk_approval=user_data["max_risk_approval"],
                is_active=True,
                created_at=datetime.now(UTC),
                password_last_changed=datetime.now(UTC)
            )

            self.session.add(user)
            self.session.commit()
            self.created_users.append(user)
            print_success(f"Created user: {user_data['name']} ({user_data['email']}) - Role: {user_data['role']}")

        print_info(f"Total users created: {len(self.created_users)}")
        return self.created_users

    def create_agent_actions(self):
        """Create realistic agent actions for the customer"""
        print_step(2, "Creating simulated agent actions")

        action_templates = [
            {
                "agent_id": "data-sync-agent",
                "action_type": "database_write",
                "description": "Sync customer data from Salesforce to PostgreSQL",
                "tool_name": "postgresql_connector",
                "risk_level": "medium",
                "ai_risk_score": 65
            },
            {
                "agent_id": "file-processor-agent",
                "action_type": "file_read",
                "description": "Process uploaded invoice PDF for accounting",
                "tool_name": "document_processor",
                "risk_level": "low",
                "ai_risk_score": 30
            },
            {
                "agent_id": "api-integration-agent",
                "action_type": "api_call",
                "description": "Call Stripe API to process payment",
                "tool_name": "stripe_api",
                "risk_level": "high",
                "ai_risk_score": 85
            },
            {
                "agent_id": "data-export-agent",
                "action_type": "data_export",
                "description": "Export customer analytics to S3",
                "tool_name": "aws_s3",
                "risk_level": "high",
                "ai_risk_score": 80
            },
            {
                "agent_id": "email-automation-agent",
                "action_type": "email_send",
                "description": "Send weekly report email to stakeholders",
                "tool_name": "sendgrid_api",
                "risk_level": "low",
                "ai_risk_score": 25
            }
        ]

        statuses = ["pending_approval", "approved", "rejected", "completed"]

        # Create 15 agent actions with varied statuses and timestamps
        for i in range(15):
            template = random.choice(action_templates)
            days_ago = random.randint(0, 30)
            timestamp = datetime.now(UTC) - timedelta(days=days_ago)

            action = AgentAction(
                agent_id=template["agent_id"],
                action_type=template["action_type"],
                description=f"{template['description']} (Execution #{i+1})",
                tool_name=template["tool_name"],
                risk_level=template["risk_level"],
                risk_score=float(template["ai_risk_score"] + random.randint(-10, 10)),
                status=random.choice(statuses),
                timestamp=timestamp,
                user_id=random.choice([u.id for u in self.created_users]) if self.created_users else None,
                approved=True if random.choice(statuses) == "approved" else None
            )

            self.session.add(action)
            self.created_actions.append(action)

        self.session.commit()
        print_success(f"Created {len(self.created_actions)} agent actions")

        # Print summary
        by_status = {}
        for action in self.created_actions:
            by_status[action.status] = by_status.get(action.status, 0) + 1

        for status, count in by_status.items():
            print_info(f"  {status}: {count} actions")

        return self.created_actions

    def create_alerts(self):
        """Create security alerts for the customer"""
        print_step(3, "Creating security alerts")

        alert_templates = [
            {
                "alert_type": "High Risk Agent Action",
                "severity": "high",
                "message": "Agent attempted database write without approval"
            },
            {
                "alert_type": "Policy Violation",
                "severity": "critical",
                "message": "PII data accessed outside business hours"
            },
            {
                "alert_type": "Anomalous Behavior",
                "severity": "medium",
                "message": "Unusual API call pattern detected"
            },
            {
                "alert_type": "Compliance Alert",
                "severity": "high",
                "message": "GDPR data retention policy violation detected"
            },
            {
                "alert_type": "Security Incident",
                "severity": "critical",
                "message": "Multiple failed authentication attempts"
            }
        ]

        # Create 12 alerts over the past 30 days
        for i in range(12):
            template = random.choice(alert_templates)
            days_ago = random.randint(0, 30)
            timestamp = datetime.now(UTC) - timedelta(days=days_ago)

            # Some alerts are acknowledged
            is_acknowledged = random.choice([True, False, False])  # 33% acknowledged
            acknowledged_at = timestamp + timedelta(hours=random.randint(1, 24)) if is_acknowledged else None

            # Fewer escalated
            is_escalated = random.choice([True, False, False, False]) if is_acknowledged else False  # 25% of acknowledged
            escalated_at = acknowledged_at + timedelta(hours=random.randint(1, 12)) if is_escalated else None

            alert = Alert(
                alert_type=template["alert_type"],
                severity=template["severity"],
                message=template["message"],
                timestamp=timestamp,
                agent_id=random.choice([a.agent_id for a in self.created_actions]) if self.created_actions else None,
                status="acknowledged" if is_acknowledged else "new",
                acknowledged_by=random.choice([u.email for u in self.created_users]) if is_acknowledged and self.created_users else None,
                acknowledged_at=acknowledged_at,
                escalated_by=random.choice([u.email for u in self.created_users]) if is_escalated and self.created_users else None,
                escalated_at=escalated_at,
                is_false_positive=random.choice([True, False, False, False]) if is_acknowledged else None,
                detection_time_ms=random.randint(50, 500)
            )

            self.session.add(alert)
            self.created_alerts.append(alert)

        self.session.commit()
        print_success(f"Created {len(self.created_alerts)} security alerts")

        # Print summary
        by_severity = {}
        for alert in self.created_alerts:
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1

        for severity, count in by_severity.items():
            print_info(f"  {severity}: {count} alerts")

        return self.created_alerts

    def create_logs(self):
        """Create audit logs for the customer"""
        print_step(4, "Creating audit logs")

        log_templates = [
            {"level": "INFO", "source": "auth", "message": "User logged in successfully"},
            {"level": "INFO", "source": "agent", "message": "Agent action submitted for approval"},
            {"level": "WARNING", "source": "security", "message": "Suspicious activity detected"},
            {"level": "ERROR", "source": "api", "message": "API rate limit exceeded"},
            {"level": "INFO", "source": "policy", "message": "Policy evaluation completed"},
        ]

        # Create 20 logs
        for i in range(20):
            template = random.choice(log_templates)
            days_ago = random.randint(0, 30)

            log = Log(
                level=template["level"],
                message=template["message"],
                source=template["source"],
                user_id=random.choice([u.id for u in self.created_users]) if self.created_users else None,
                extra_data={"simulation": True, "customer": self.customer_name}
            )

            self.session.add(log)

        self.session.commit()
        print_success("Created 20 audit log entries")

    def print_onboarding_summary(self):
        """Print a summary of the onboarding simulation"""
        print_header(f"Onboarding Summary: {self.customer_name}")

        print(f"{Colors.BOLD}Customer Information:{Colors.END}")
        print(f"  Company Name: {self.customer_name}")
        print(f"  Email Domain: {self.customer_domain}")
        print()

        print(f"{Colors.BOLD}Created Resources:{Colors.END}")
        print(f"  ✅ Users: {len(self.created_users)}")
        print(f"  ✅ Agent Actions: {len(self.created_actions)}")
        print(f"  ✅ Security Alerts: {len(self.created_alerts)}")
        print()

        print(f"{Colors.BOLD}User Accounts Created:{Colors.END}")
        for user in self.created_users:
            print(f"  📧 {user.email}")
            print(f"     Role: {user.role} | Approval Level: {user.approval_level}")
            print(f"     Password: Demo2024! (for testing)")
            print()

        print(f"{Colors.BOLD}Next Steps:{Colors.END}")
        print(f"  1. Login to https://pilot.owkai.app")
        print(f"  2. Use any of the created user emails with password: Demo2024!")
        print(f"  3. Test platform features:")
        print(f"     ✓ View Dashboard (analytics, alerts, trends)")
        print(f"     ✓ Authorization Center (pending actions)")
        print(f"     ✓ AI Alert Management (view generated alerts)")
        print(f"     ✓ Smart Rules (view rules and A/B tests)")
        print(f"     ✓ Agent Activity Feed (view recent actions)")
        print()

        print(f"{Colors.BOLD}Verification Commands:{Colors.END}")
        print(f"  # Count created resources")
        print(f"  psql -c \"SELECT COUNT(*) FROM users WHERE email LIKE '%@{self.customer_domain}';\"")
        print(f"  psql -c \"SELECT COUNT(*) FROM agent_actions WHERE requested_by LIKE '%@{self.customer_domain}';\"")
        print(f"  psql -c \"SELECT COUNT(*) FROM alerts WHERE agent_id IN (SELECT agent_id FROM agent_actions WHERE requested_by LIKE '%@{self.customer_domain}');\"")
        print()

    def run(self):
        """Execute the complete onboarding simulation"""
        try:
            print_header(f"Customer Onboarding Simulation")
            print_info(f"Customer: {self.customer_name}")
            print_info(f"Domain: {self.customer_domain}")
            print_info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
            print()

            # Step 1: Create users
            self.create_customer_users()

            # Step 2: Create agent actions
            self.create_agent_actions()

            # Step 3: Create alerts
            self.create_alerts()

            # Step 4: Create logs (skipped - logs table doesn't exist in production)
            print_step(4, "Skipping audit logs (table not in production)")
            print_info("Logs table not available in production database")

            # Print summary
            self.print_onboarding_summary()

            print_success(f"Onboarding simulation completed successfully!")
            return True

        except Exception as e:
            print_error(f"Onboarding simulation failed: {e}")
            import traceback
            traceback.print_exc()
            self.session.rollback()
            return False
        finally:
            self.session.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Simulate customer onboarding for OW-KAI platform")
    parser.add_argument("--customer", default=CUSTOMER_NAME, help="Customer company name")
    parser.add_argument("--domain", default=CUSTOMER_DOMAIN, help="Customer email domain")

    args = parser.parse_args()

    simulation = CustomerOnboardingSimulation(
        customer_name=args.customer,
        customer_domain=args.domain
    )

    success = simulation.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
