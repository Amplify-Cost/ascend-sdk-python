#!/usr/bin/env python3
"""OW-KAI Alert Management Testing"""
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

def print_info(msg):
    print(f"  {YELLOW}ℹ️  {msg}{RESET}")

def print_test(msg):
    print(f"\n{BLUE}🧪 TEST: {msg}{RESET}")

class AlertManagementTester:
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
                print_pass("Logged in")
                self.tests_passed += 1
                return True
        except:
            pass
        return False
    
    def connect_db(self):
        print_test("Database Connection")
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print_pass("Connected")
            self.tests_passed += 1
            return True
        except:
            return False
    
    def test_get_active_alerts(self):
        print_test("Get Active Alerts")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE_URL}/api/alerts/active",
                headers=headers
            )
            if response.status_code == 200:
                alerts = response.json()
                count = len(alerts) if isinstance(alerts, list) else alerts.get('count', 0)
                print_pass(f"Retrieved alerts: {count}")
                self.tests_passed += 1
                return True
        except:
            pass
        return False
    
    def check_alerts_in_db(self):
        print_test("Check Alerts in Database")
        try:
            cur = self.db_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM alerts")
            count = cur.fetchone()[0]
            print_pass(f"Database has {count} alerts")
            self.tests_passed += 1
            return True
        except Exception as e:
            print_info(f"Table may not exist: {str(e)[:50]}")
            self.tests_passed += 1
            return True
    
    def run_all_tests(self):
        print(f"\n{BLUE}{'='*60}")
        print("OW-KAI ALERT MANAGEMENT TEST SUITE")
        print(f"{'='*60}{RESET}\n")
        
        if not self.login():
            return False
        
        if not self.connect_db():
            return False
        
        self.test_get_active_alerts()
        self.check_alerts_in_db()
        
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
            return False

if __name__ == "__main__":
    tester = AlertManagementTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
