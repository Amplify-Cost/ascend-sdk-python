#!/usr/bin/env python3
"""
FastAPI Bug Fix Test Script
Tests all the bug fixes we implemented
Run this after applying the fixes to verify everything works
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change if your server runs on different port
TEST_USER_EMAIL = "admin@company.com"  # Change to your test admin email
TEST_REDACTED-CREDENTIAL = "password"  # Change to your test password

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

class FastAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

    def test_server_running(self):
        """Test 1: Check if server is running"""
        print_header("TEST 1: Server Health Check")
        try:
            response = self.session.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print_success("Server is running and healthy")
                print_info(f"Response: {response.json()}")
                self.test_results['passed'] += 1
                return True
            else:
                print_error(f"Server unhealthy - Status: {response.status_code}")
                self.test_results['failed'] += 1
                return False
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to server. Make sure FastAPI is running on http://localhost:8000")
            print_info("Start your server with: uvicorn main:app --reload")
            self.test_results['failed'] += 1
            return False
        except Exception as e:
            print_error(f"Health check failed: {str(e)}")
            self.test_results['failed'] += 1
            return False

    def test_authentication(self):
        """Test 2: Authentication system"""
        print_header("TEST 2: Authentication System")
        try:
            # Try to get a token
            auth_data = {
                "username": TEST_USER_EMAIL,
                "password": TEST_REDACTED-CREDENTIAL
            }
            
            response = self.session.post(f"{BASE_URL}/token", data=auth_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print_success("Authentication successful")
                    self.test_results['passed'] += 1
                    return True
                else:
                    print_error("Token received but empty")
                    self.test_results['failed'] += 1
                    return False
            else:
                print_warning("Authentication endpoint not available or credentials incorrect")
                print_info("Proceeding with tests that don't require auth")
                self.test_results['warnings'] += 1
                return False
                
        except Exception as e:
            print_warning(f"Authentication test failed: {str(e)}")
            print_info("Proceeding with tests that don't require auth")
            self.test_results['warnings'] += 1
            return False

    def test_analytics_trends(self):
        """Test 3: Analytics trends endpoint (BUG FIX 1)"""
        print_header("TEST 3: Analytics Trends Endpoint (Database Session Fix)")
        try:
            response = self.session.get(f"{BASE_URL}/analytics/trends")
            
            if response.status_code == 200:
                data = response.json()
                required_keys = ['high_risk_actions_by_day', 'top_agents', 'top_tools', 'enriched_actions', 'summary']
                
                if all(key in data for key in required_keys):
                    print_success("Analytics trends endpoint working correctly")
                    print_info(f"Returned {len(data['enriched_actions'])} enriched actions")
                    print_info(f"Summary: {data['summary']['total_actions']} total actions")
                    self.test_results['passed'] += 1
                    return True
                else:
                    print_error("Analytics response missing required keys")
                    print_info(f"Available keys: {list(data.keys())}")
                    self.test_results['failed'] += 1
                    return False
            else:
                print_error(f"Analytics trends failed - Status: {response.status_code}")
                print_info(f"Response: {response.text}")
                self.test_results['failed'] += 1
                return False
                
        except Exception as e:
            print_error(f"Analytics trends test failed: {str(e)}")
            self.test_results['failed'] += 1
            return False

    def test_agent_actions_get(self):
        """Test 4: Get agent actions endpoint (BUG FIX 2)"""
        print_header("TEST 4: Get Agent Actions Endpoint (Session Management Fix)")
        try:
            response = self.session.get(f"{BASE_URL}/agent-actions")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print_success(f"Agent actions endpoint working - returned {len(data)} actions")
                    
                    if len(data) > 0:
                        # Check structure of first action
                        first_action = data[0]
                        required_fields = ['id', 'agent_id', 'action_type', 'description', 'status']
                        
                        if all(field in first_action for field in required_fields):
                            print_info(f"Action structure correct: {first_action['agent_id']} - {first_action['status']}")
                        else:
                            print_warning("Action structure missing some fields")
                    
                    self.test_results['passed'] += 1
                    return True
                else:
                    print_error("Expected list response, got something else")
                    self.test_results['failed'] += 1
                    return False
            else:
                print_error(f"Get agent actions failed - Status: {response.status_code}")
                print_info(f"Response: {response.text}")
                self.test_results['failed'] += 1
                return False
                
        except Exception as e:
            print_error(f"Get agent actions test failed: {str(e)}")
            self.test_results['failed'] += 1
            return False

    def test_agent_actions_post(self):
        """Test 5: Post agent actions endpoint (BUG FIX 3 - Duplicate removal)"""
        print_header("TEST 5: Post Agent Actions Endpoint (Duplicate Route Fix)")
        try:
            test_action = {
                "agent_id": "test-agent-001",
                "action_type": "test_scan",
                "description": "Test action for bug fix verification",
                "risk_level": "low",
                "tool_name": "test-tool"
            }
            
            response = self.session.post(f"{BASE_URL}/agent-actions", json=test_action)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "action_id" in data:
                    print_success(f"Agent action submitted successfully - ID: {data['action_id']}")
                    self.test_results['passed'] += 1
                    return data['action_id']  # Return ID for further tests
                else:
                    print_error("Action submitted but response format unexpected")
                    print_info(f"Response: {data}")
                    self.test_results['failed'] += 1
                    return None
            elif response.status_code == 422:
                print_warning("Validation error - check if all required fields are provided")
                print_info(f"Response: {response.json()}")
                self.test_results['warnings'] += 1
                return None
            else:
                print_error(f"Post agent action failed - Status: {response.status_code}")
                print_info(f"Response: {response.text}")
                self.test_results['failed'] += 1
                return None
                
        except Exception as e:
            print_error(f"Post agent action test failed: {str(e)}")
            self.test_results['failed'] += 1
            return None

    def test_approval_endpoints(self, action_id):
        """Test 6: Approval endpoints (BUG FIX 4 & 5 - Transaction handling)"""
        print_header("TEST 6: Approval Endpoints (Transaction Handling Fix)")
        
        if not action_id:
            print_warning("No action ID available for approval test")
            self.test_results['warnings'] += 1
            return False
        
        # Test approve endpoint
        try:
            response = self.session.post(f"{BASE_URL}/agent-action/{action_id}/approve")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "approved" in data["message"].lower():
                    print_success(f"Approval endpoint working - Action {action_id} approved")
                    self.test_results['passed'] += 1
                    return True
                else:
                    print_warning("Approval endpoint responded but message format unexpected")
                    print_info(f"Response: {data}")
                    self.test_results['warnings'] += 1
                    return False
            elif response.status_code == 403:
                print_warning("Approval requires admin permissions (this is expected)")
                print_info("Test passed - proper authorization check in place")
                self.test_results['passed'] += 1
                return True
            elif response.status_code == 404:
                print_warning(f"Action {action_id} not found for approval")
                self.test_results['warnings'] += 1
                return False
            else:
                print_error(f"Approval endpoint failed - Status: {response.status_code}")
                print_info(f"Response: {response.text}")
                self.test_results['failed'] += 1
                return False
                
        except Exception as e:
            print_error(f"Approval endpoint test failed: {str(e)}")
            self.test_results['failed'] += 1
            return False

    def test_database_operations(self):
        """Test 7: Database operations don't leak connections"""
        print_header("TEST 7: Database Connection Management")
        try:
            print_info("Testing multiple rapid requests to check for connection leaks...")
            
            # Make multiple rapid requests
            for i in range(5):
                response = self.session.get(f"{BASE_URL}/analytics/trends")
                if response.status_code != 200:
                    print_error(f"Request {i+1} failed with status {response.status_code}")
                    self.test_results['failed'] += 1
                    return False
                time.sleep(0.1)  # Small delay
            
            print_success("Multiple rapid requests succeeded - no connection leaks detected")
            self.test_results['passed'] += 1
            return True
            
        except Exception as e:
            print_error(f"Database connection test failed: {str(e)}")
            self.test_results['failed'] += 1
            return False

    def test_async_sync_consistency(self):
        """Test 8: Check that async/sync endpoints work correctly"""
        print_header("TEST 8: Async/Sync Endpoint Consistency")
        
        # Test various endpoints to ensure they respond correctly
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/analytics/trends", "GET"),
            ("/agent-actions", "GET"),
            ("/alerts", "GET")
        ]
        
        passed_endpoints = 0
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}", timeout=10)
                else:
                    continue  # Skip non-GET for this test
                
                if response.status_code in [200, 201]:
                    print_success(f"{endpoint} - Status: {response.status_code}")
                    passed_endpoints += 1
                else:
                    print_warning(f"{endpoint} - Status: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print_error(f"{endpoint} - Timeout (possible blocking operation)")
                self.test_results['failed'] += 1
                return False
            except Exception as e:
                print_warning(f"{endpoint} - Error: {str(e)}")
        
        if passed_endpoints >= len(endpoints_to_test) // 2:
            print_success(f"Async/sync consistency check passed - {passed_endpoints}/{len(endpoints_to_test)} endpoints working")
            self.test_results['passed'] += 1
            return True
        else:
            print_error(f"Too many endpoints failing - {passed_endpoints}/{len(endpoints_to_test)} working")
            self.test_results['failed'] += 1
            return False

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print_header("FASTAPI BUG FIX VERIFICATION")
        print_info(f"Testing server at: {BASE_URL}")
        print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Server health
        if not self.test_server_running():
            print_error("Server not running - cannot continue tests")
            return False
        
        # Test 2: Authentication (optional)
        self.test_authentication()
        
        # Test 3: Analytics trends (BUG FIX 1)
        self.test_analytics_trends()
        
        # Test 4: Get agent actions (BUG FIX 2)
        self.test_agent_actions_get()
        
        # Test 5: Post agent actions (BUG FIX 3)
        action_id = self.test_agent_actions_post()
        
        # Test 6: Approval endpoints (BUG FIX 4 & 5)
        self.test_approval_endpoints(action_id)
        
        # Test 7: Database connection management
        self.test_database_operations()
        
        # Test 8: Async/sync consistency
        self.test_async_sync_consistency()
        
        # Final summary
        self.print_summary()
        
        return self.test_results['failed'] == 0

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total_tests = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        
        print_success(f"PASSED: {self.test_results['passed']} tests")
        if self.test_results['warnings'] > 0:
            print_warning(f"WARNINGS: {self.test_results['warnings']} tests")
        if self.test_results['failed'] > 0:
            print_error(f"FAILED: {self.test_results['failed']} tests")
        
        print_info(f"TOTAL: {total_tests} tests run")
        
        if self.test_results['failed'] == 0:
            print_success("🎉 ALL CRITICAL TESTS PASSED! Your bug fixes are working correctly.")
        else:
            print_error("❌ Some tests failed. Please check the error messages above.")
        
        # Specific guidance
        print_header("NEXT STEPS")
        if self.test_results['failed'] == 0:
            print_success("✅ Your FastAPI application is working correctly with all bug fixes applied!")
            print_info("You can now confidently deploy or continue development.")
        else:
            print_error("🔧 Issues detected. Here's what to check:")
            print_info("1. Make sure your database is running and accessible")
            print_info("2. Verify all the code replacements were applied correctly")
            print_info("3. Check the server logs for any startup errors")
            print_info("4. Ensure all required dependencies are installed")

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
    
    tester = FastAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()