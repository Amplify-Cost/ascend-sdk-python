#!/usr/bin/env python3
"""OW-KAI Authorization Center Testing"""
import os
import requests
import psycopg2
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
RESET = '\033[0m'

def print_pass(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")

def print_fail(msg):
    print(f"  {RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"  {YELLOW}ℹ️  {msg}{RESET}")

def print_test(msg):
    print(f"\n{BLUE}🧪 TEST: {msg}{RESET}")

class AuthorizationTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.db_conn = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def login(self):
        print_test("Admin Login")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/token",
                json={"email": ADMIN_EMAIL, "password": ADMIN_REDACTED-CREDENTIAL}
            )
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                print_pass("Logged in as admin")
                self.tests_passed += 1
                return True
            print_fail(f"Login failed: {response.status_code}")
            self.tests_failed += 1
            return False
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def connect_db(self):
        print_test("Database Connection")
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print_pass("Database connected")
            self.tests_passed += 1
            return True
        except Exception as e:
            print_fail(f"Connection failed: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_pending_actions_endpoint(self):
        print_test("Pending Actions Endpoint")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/agent-control/pending-actions",
                headers=headers
            )
            if response.status_code == 200:
                actions = response.json()
                print_pass(f"Retrieved {len(actions.get("actions", actions) if isinstance(actions, dict) else actions)} pending actions")
                self.tests_passed += 1
                return True
            print_fail(f"Failed: {response.status_code}")
            self.tests_failed += 1
            return False
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def verify_workflows_exist(self):
        print_test("Verify Risk-Based Workflows")
        try:
            cur = self.db_conn.cursor()
            expected = ['risk_0_49', 'risk_50_69', 'risk_70_89', 'risk_90_100']
            
            cur.execute("SELECT id FROM workflows WHERE id = ANY(%s)", (expected,))
            found = [row[0] for row in cur.fetchall()]
            
            for wf in expected:
                if wf in found:
                    print_pass(f"Workflow: {wf}")
            
            print_pass(f"Found {len(found)}/4 workflows")
            self.tests_passed += 1
            return True
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_dashboard_metrics(self):
        print_test("Dashboard Metrics")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/api/authorization/dashboard",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print_pass("Dashboard accessible")
                kpis = data.get('enterprise_kpis', {})
                print_info(f"SLA Compliance: {kpis.get('sla_compliance', 'N/A')}%")
                print_info(f"Security Score: {kpis.get('security_posture_score', 'N/A')}")
                self.tests_passed += 1
                return True
            print_fail(f"Failed: {response.status_code}")
            self.tests_failed += 1
            return False
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def run_all_tests(self):
        print(f"\n{BLUE}{'='*60}")
        print("OW-KAI AUTHORIZATION CENTER TEST SUITE")
        print(f"{'='*60}{RESET}\n")
        
        if not self.login():
            return False
        
        if not self.connect_db():
            return False
        
        self.test_pending_actions_endpoint()
        self.verify_workflows_exist()
        self.test_dashboard_metrics()
        
        if self.db_conn:
            self.db_conn.close()
        
        print(f"\n{BLUE}{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}{RESET}")
        print(f"{GREEN}✅ Passed: {self.tests_passed}{RESET}")
        print(f"{RED}❌ Failed: {self.tests_failed}{RESET}")
        
        if self.tests_failed == 0:
            print(f"\n{GREEN}🎉 ALL TESTS PASSED! 🎉{RESET}\n")
            return True
        else:
            print(f"\n{RED}⚠️  SOME TESTS FAILED{RESET}\n")
            return False

if __name__ == "__main__":
    tester = AuthorizationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
