#!/usr/bin/env python3
"""OW-KAI Authentication Testing - Uses /auth/token endpoint"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_REDACTED-CREDENTIAL = os.getenv("ADMIN_REDACTED-CREDENTIAL")

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_pass(msg):
    print(f"  {GREEN}✅ PASS: {msg}{RESET}")

def print_fail(msg):
    print(f"  {RED}❌ FAIL: {msg}{RESET}")

def print_info(msg):
    print(f"  {BLUE}ℹ️  {msg}{RESET}")

class AuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def test_login(self):
        print(f"\n{BLUE}🧪 TEST: Admin Login (/auth/token){RESET}")
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/token",
                headers={"Content-Type": "application/json"},
                json={"email": ADMIN_EMAIL, "password": ADMIN_REDACTED-CREDENTIAL}
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                user = data.get("user", {})
                print_pass("Login successful")
                print_info(f"User: {user.get('email')}")
                print_info(f"Role: {user.get('role')}")
                print_info(f"Token: {self.access_token[:30]}...")
                self.tests_passed += 1
                return True
            else:
                print_fail(f"Login failed: {response.status_code}")
                print_fail(f"Response: {response.text}")
                self.tests_failed += 1
                return False
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def test_pending_actions(self):
        print(f"\n{BLUE}🧪 TEST: Pending Actions{RESET}")
        if not self.access_token:
            print_fail("No token")
            self.tests_failed += 1
            return False
        try:
            response = self.session.get(
                f"{API_BASE_URL}/agent-control/pending-actions",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if response.status_code == 200:
                data = response.json()
                print_pass("Endpoint accessible")
                print_info(f"Pending actions: {len(data)}")
                self.tests_passed += 1
                return True
            else:
                print_fail(f"Failed: {response.status_code}")
                self.tests_failed += 1
                return False
        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            self.tests_failed += 1
            return False
    
    def run_all_tests(self):
        print(f"\n{BLUE}{'='*60}")
        print("OW-KAI AUTHENTICATION TEST SUITE")
        print(f"{'='*60}{RESET}\n")
        print_info(f"API: {API_BASE_URL}")
        print_info(f"User: {ADMIN_EMAIL}")
        
        if self.test_login():
            self.test_pending_actions()
        
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
    tester = AuthTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
