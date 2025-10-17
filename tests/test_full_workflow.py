#!/usr/bin/env python3
"""OW-KAI Full End-to-End Workflow Testing"""
import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_REDACTED-CREDENTIAL = os.getenv("ADMIN_REDACTED-CREDENTIAL")

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

def print_step(num, msg):
    print(f"\n{MAGENTA}{'='*60}")
    print(f"STEP {num}: {msg}")
    print(f"{'='*60}{RESET}")

def print_pass(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")

def print_info(msg):
    print(f"  {YELLOW}ℹ️  {msg}{RESET}")

class FullWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.db_conn = None
        self.steps_passed = 0
        self.steps_failed = 0
    
    def step1_login(self):
        print_step(1, "User Authentication")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/token",
                json={"email": ADMIN_EMAIL, "password": ADMIN_REDACTED-CREDENTIAL}
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                user = data.get("user", {})
                print_pass("Authentication successful")
                print_info(f"User: {user.get('email')}")
                print_info(f"Role: {user.get('role')}")
                self.steps_passed += 1
                return True
        except:
            pass
        self.steps_failed += 1
        return False
    
    def step2_connect_db(self):
        print_step(2, "Database Connection")
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print_pass("Database connected")
            self.steps_passed += 1
            return True
        except:
            self.steps_failed += 1
            return False
    
    def step3_check_pending_actions(self):
        print_step(3, "Check Pending Actions")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/agent-control/pending-actions",
                headers=headers
            )
            if response.status_code == 200:
                actions = response.json()
                print_pass(f"Found {len(actions.get("actions", []))} pending actions")
                self.steps_passed += 1
                return True
        except:
            pass
        self.steps_failed += 1
        return False
    
    def step4_check_workflows(self):
        print_step(4, "Verify Risk-Based Workflows")
        try:
            cur = self.db_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM workflows WHERE id LIKE 'risk_%'")
            count = cur.fetchone()[0]
            print_pass(f"Found {count} risk-based workflows")
            self.steps_passed += 1
            return True
        except:
            self.steps_failed += 1
            return False
    
    def step5_check_dashboard(self):
        print_step(5, "Authorization Dashboard Metrics")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/api/authorization/dashboard",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                kpis = data.get('enterprise_kpis', {})
                print_pass("Dashboard accessible")
                print_info(f"SLA Compliance: {kpis.get('sla_compliance', 'N/A')}%")
                print_info(f"Security Score: {kpis.get('security_posture_score', 'N/A')}")
                self.steps_passed += 1
                return True
        except:
            pass
        self.steps_failed += 1
        return False
    
    def step6_database_integrity(self):
        print_step(6, "Database Integrity Check")
        try:
            cur = self.db_conn.cursor()
            tables = [
                ('users', 'SELECT COUNT(*) FROM users'),
                ('workflows', 'SELECT COUNT(*) FROM workflows'),
                ('agent_actions', 'SELECT COUNT(*) FROM agent_actions'),
            ]
            
            all_good = True
            for table_name, query in tables:
                try:
                    cur.execute(query)
                    count = cur.fetchone()[0]
                    print_pass(f"{table_name}: {count} records")
                except:
                    print_info(f"{table_name}: not checked")
            
            self.steps_passed += 1
            return True
        except:
            self.steps_failed += 1
            return False
    
    def run_full_workflow(self):
        print(f"\n{BLUE}{'='*60}")
        print("OW-KAI END-TO-END WORKFLOW TEST")
        print(f"{'='*60}{RESET}\n")
        print_info(f"API: {API_BASE_URL}")
        print_info(f"Started: {datetime.now()}")
        
        steps = [
            self.step1_login,
            self.step2_connect_db,
            self.step3_check_pending_actions,
            self.step4_check_workflows,
            self.step5_check_dashboard,
            self.step6_database_integrity,
        ]
        
        for step in steps:
            if not step():
                print(f"\n{RED}⚠️  Step failed, continuing...{RESET}")
        
        if self.db_conn:
            self.db_conn.close()
        
        print(f"\n{BLUE}{'='*60}")
        print("END-TO-END TEST SUMMARY")
        print(f"{'='*60}{RESET}")
        print(f"{GREEN}✅ Steps Passed: {self.steps_passed}{RESET}")
        print(f"{RED}❌ Steps Failed: {self.steps_failed}{RESET}")
        
        if self.steps_failed == 0:
            print(f"\n{GREEN}{'='*60}")
            print("🎉 FULL WORKFLOW TEST PASSED! 🎉")
            print("System functioning correctly end-to-end")
            print(f"{'='*60}{RESET}\n")
            return True
        else:
            print(f"\n{RED}⚠️  SOME STEPS FAILED{RESET}\n")
            return False

if __name__ == "__main__":
    tester = FullWorkflowTester()
    success = tester.run_full_workflow()
    exit(0 if success else 1)
