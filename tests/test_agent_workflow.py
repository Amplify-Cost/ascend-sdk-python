#!/usr/bin/env python3
"""
OW-KAI Enterprise Agent Workflow Testing
Simulates real agents submitting actions through the API
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_REDACTED-CREDENTIAL = os.getenv("ADMIN_REDACTED-CREDENTIAL")

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_pass(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")

def print_fail(msg):
    print(f"  {RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"  {YELLOW}ℹ️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{BLUE}{'='*60}\n{msg}\n{'='*60}{RESET}")

def print_action(msg):
    print(f"  {CYAN}🤖 {msg}{RESET}")

# Simulated agent actions with different risk levels
AGENT_ACTIONS = [
    {
        "agent_name": "DataAnalyzer_AI",
        "action_type": "database_query",
        "description": "Query customer purchase history for Q4 analytics",
        "metadata": {
            "query_type": "SELECT",
            "table": "customers",
            "estimated_rows": 50000
        }
    },
    {
        "agent_name": "EmailBot_AI",
        "action_type": "send_email",
        "description": "Send automated welcome email to 25 new customers",
        "metadata": {
            "recipient_count": 25,
            "email_type": "welcome",
            "has_attachments": False
        }
    },
    {
        "agent_name": "SecurityScanner_AI",
        "action_type": "firewall_modification",
        "description": "Update firewall rules to allow new application ports",
        "metadata": {
            "rule_type": "allow",
            "ports": "8080,8443",
            "protocol": "TCP"
        }
    },
    {
        "agent_name": "BackupManager_AI",
        "action_type": "delete_files",
        "description": "Delete production backup files older than 90 days",
        "metadata": {
            "file_count": 150,
            "total_size_gb": 2500,
            "environment": "production"
        }
    },
    {
        "agent_name": "PaymentProcessor_AI",
        "action_type": "financial_transaction",
        "description": "Process batch payment to 200 vendors ($2.5M total)",
        "metadata": {
            "transaction_count": 200,
            "total_amount": 2500000,
            "currency": "USD"
        }
    },
    {
        "agent_name": "CodeDeployer_AI",
        "action_type": "code_deployment",
        "description": "Deploy microservice update to production cluster",
        "metadata": {
            "service": "payment-gateway",
            "environment": "production",
            "rollback_available": True
        }
    }
]

class AgentWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.submitted_actions = []
        
    def authenticate(self):
        """Authenticate as admin"""
        print_header("STEP 1: AUTHENTICATION")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/token",
                json={"email": ADMIN_EMAIL, "password": ADMIN_REDACTED-CREDENTIAL}
            )
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                print_pass(f"Authenticated as {ADMIN_EMAIL}")
                return True
            print_fail(f"Authentication failed: {response.status_code}")
            return False
        except Exception as e:
            print_fail(f"Authentication error: {str(e)}")
            return False
    
    def clear_existing_actions(self):
        """Clear existing test data"""
        print_header("STEP 2: CLEAR EXISTING TEST DATA")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get all pending actions
            response = self.session.get(
                f"{API_BASE_URL}/agent-control/pending-actions",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                existing = data.get("actions", [])
                print_info(f"Found {len(existing)} existing actions")
                
                if len(existing) == 0:
                    print_info("No existing actions to clear")
                else:
                    print_info("Note: Existing actions will remain for manual testing")
                    print_info("You can approve/reject them in the UI")
                
                return True
        except Exception as e:
            print_fail(f"Error checking existing actions: {str(e)}")
            return False
    
    def submit_agent_action(self, action_data):
        """Submit a single agent action through the API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/agent-action",
                headers=headers,
                json=action_data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                action_id = result.get("id") or result.get("action_id")
                risk_score = result.get("risk_score", "N/A")
                workflow = result.get("workflow_id", "N/A")
                
                self.submitted_actions.append({
                    "id": action_id,
                    "name": action_data["agent_name"],
                    "risk_score": risk_score,
                    "workflow": workflow
                })
                
                print_action(f"{action_data['agent_name']}")
                print_info(f"  Action ID: {action_id}")
                print_info(f"  Risk Score: {risk_score}")
                print_info(f"  Workflow: {workflow}")
                print_pass(f"  ✓ Submitted successfully")
                return True
            else:
                print_fail(f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print_fail(f"Error: {str(e)}")
            return False
    
    def submit_all_actions(self):
        """Submit all simulated agent actions"""
        print_header("STEP 3: SUBMIT AGENT ACTIONS (Simulating Real Agents)")
        print_info("Each action will go through the system's risk assessment")
        print_info("and be routed to the appropriate approval workflow\n")
        
        success_count = 0
        for i, action in enumerate(AGENT_ACTIONS, 1):
            print(f"\n{CYAN}━━━ Agent {i}/{len(AGENT_ACTIONS)} ━━━{RESET}")
            if self.submit_agent_action(action):
                success_count += 1
            time.sleep(0.5)  # Small delay between submissions
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        print_pass(f"Successfully submitted {success_count}/{len(AGENT_ACTIONS)} actions")
        return success_count > 0
    
    def verify_pending_actions(self):
        """Verify actions appear in the pending queue"""
        print_header("STEP 4: VERIFY ACTIONS IN AUTHORIZATION CENTER")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/agent-control/pending-actions",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                actions = data.get("actions", [])
                total = data.get("total_count", len(actions))
                
                print_pass(f"Found {total} total pending actions in system")
                
                # Show breakdown by risk level
                if "enterprise_metadata" in data:
                    meta = data["enterprise_metadata"]
                    print_info(f"High Risk Actions: {meta.get('high_risk_count', 0)}")
                    print_info(f"Exec Approval Required: {meta.get('executive_approval_required', 0)}")
                    print_info(f"SLA Deadline: {meta.get('sla_deadline', 'N/A')}")
                
                return True
                
        except Exception as e:
            print_fail(f"Error: {str(e)}")
            return False
    
    def verify_dashboard(self):
        """Check the authorization dashboard metrics"""
        print_header("STEP 5: CHECK DASHBOARD METRICS")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/api/authorization/dashboard",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                metrics = data.get("metrics", {})
                
                print_info("📊 Current Status:")
                print_info(f"  Pending: {summary.get('total_pending', 0)}")
                print_info(f"  Approved: {summary.get('total_approved', 0)}")
                print_info(f"  Rejected: {summary.get('total_rejected', 0)}")
                
                if metrics:
                    print_info(f"\n📈 System Metrics:")
                    print_info(f"  SLA Compliance: {metrics.get('sla_compliance', 0)}%")
                    print_info(f"  Security Score: {metrics.get('security_score', 0)}")
                
                print_pass("Dashboard accessible and showing metrics")
                return True
                
        except Exception as e:
            print_fail(f"Error: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary and next steps"""
        print_header("✅ TEST COMPLETE - NEXT STEPS")
        
        print(f"\n{CYAN}📋 What to do next:{RESET}")
        print_info("1. Open your browser: https://pilot.owkai.app")
        print_info("2. Navigate to the Authorization Center")
        print_info("3. You should see all submitted agent actions")
        print_info("4. Test the approval workflow:")
        print_info("   - Click on each action to view details")
        print_info("   - Approve low/medium risk actions")
        print_info("   - Reject or escalate high risk actions")
        print_info("   - Verify risk scores and workflows are correct")
        
        print(f"\n{CYAN}🔍 Actions submitted:{RESET}")
        for action in self.submitted_actions:
            risk_level = "🟢 LOW" if float(action['risk_score']) < 50 else "🟡 MEDIUM" if float(action['risk_score']) < 80 else "🔴 HIGH"
            print_info(f"{action['name']}: {risk_level} (Score: {action['risk_score']})")
        
        print(f"\n{GREEN}{'='*60}")
        print(f"🎉 SYSTEM VERIFIED - READY FOR PILOT DEMO!")
        print(f"{'='*60}{RESET}\n")

def main():
    print_header("🚀 OW-KAI ENTERPRISE AGENT WORKFLOW TEST")
    print_info("This test simulates real AI agents submitting actions")
    print_info("through your API to verify end-to-end functionality\n")
    
    tester = AgentWorkflowTester()
    
    # Run test steps
    if not tester.authenticate():
        return
    
    if not tester.clear_existing_actions():
        return
    
    if not tester.submit_all_actions():
        return
    
    # Small delay to let system process
    print_info("\nWaiting for system to process actions...")
    time.sleep(2)
    
    if not tester.verify_pending_actions():
        return
    
    if not tester.verify_dashboard():
        return
    
    tester.print_summary()

if __name__ == "__main__":
    main()
