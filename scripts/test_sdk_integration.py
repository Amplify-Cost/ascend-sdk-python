#!/usr/bin/env python3
"""
ONBOARD-044: SDK/API Integration Test Script
Tests that customers can send agent actions to Ascend via API

Usage:
    python3 scripts/test_sdk_integration.py --api-key "YOUR_API_KEY"
    python3 scripts/test_sdk_integration.py --api-key "YOUR_API_KEY" --base-url "http://localhost:8000"

Full customer integration test sequence:
1. Health check (no auth required)
2. Register an agent (requires API key)
3. Submit agent action for governance (requires API key)
4. Check action status (requires API key)
5. List actions (requires API key)
"""

import argparse
import requests
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def log_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


class AscendIntegrationTester:
    """Test SDK/API integration for Ascend platform"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-API-Key": api_key,  # Dual header support
            "User-Agent": "Ascend-SDK-Test/1.0"
        }
        self.test_agent_id = f"test-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.created_action_id: Optional[int] = None
        self.results: Dict[str, Any] = {}

    def test_health(self) -> bool:
        """Test 1: Health check (no auth required)"""
        print("\n" + "=" * 60)
        print("TEST 1: HEALTH CHECK")
        print("=" * 60)

        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10
            )

            log_info(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                log_success(f"Health: {data.get('status', 'unknown')}")
                log_info(f"Environment: {data.get('environment', 'unknown')}")
                log_info(f"Database: {data.get('checks', {}).get('database', {}).get('status', 'unknown')}")
                self.results['health'] = True
                return True
            else:
                log_error(f"Health check failed: {response.text[:200]}")
                self.results['health'] = False
                return False

        except Exception as e:
            log_error(f"Health check error: {e}")
            self.results['health'] = False
            return False

    def test_register_agent(self) -> bool:
        """Test 2: Register an agent"""
        print("\n" + "=" * 60)
        print("TEST 2: REGISTER AGENT")
        print("=" * 60)

        payload = {
            "agent_id": self.test_agent_id,
            "agent_name": "SDK Integration Test Agent",
            "agent_type": "autonomous",
            "description": "Test agent created by integration test script",
            "environment": "development",
            "owner_email": "sdk-test@example.com",
            "risk_tolerance": "medium",
            "allowed_tools": ["database_read", "api_call", "file_read"],
            "data_access_level": "internal"
        }

        try:
            log_info(f"Registering agent: {self.test_agent_id}")

            response = requests.post(
                f"{self.base_url}/api/registry/agents",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            log_info(f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                log_success(f"Agent registered: {data.get('agent_id', self.test_agent_id)}")
                self.results['register_agent'] = True
                return True
            elif response.status_code == 409:
                log_warning("Agent already exists (this is OK for re-runs)")
                self.results['register_agent'] = True
                return True
            else:
                log_error(f"Register failed: {response.text[:300]}")
                self.results['register_agent'] = False
                return False

        except Exception as e:
            log_error(f"Register agent error: {e}")
            self.results['register_agent'] = False
            return False

    def test_submit_action(self) -> bool:
        """Test 3: Submit agent action for governance"""
        print("\n" + "=" * 60)
        print("TEST 3: SUBMIT AGENT ACTION")
        print("=" * 60)

        payload = {
            "agent_id": self.test_agent_id,
            "action_type": "database_read",
            "description": "SDK integration test - reading user metrics",
            "tool_name": "PostgreSQL Query",
            "target_system": "analytics-db",
            "environment": "development",
            "context": {
                "query_type": "SELECT",
                "table": "user_metrics",
                "timestamp": datetime.now().isoformat(),
                "source": "sdk_integration_test"
            }
        }

        try:
            log_info(f"Submitting action for agent: {self.test_agent_id}")

            response = requests.post(
                f"{self.base_url}/api/v1/actions/submit",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            log_info(f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                self.created_action_id = data.get('id')
                log_success(f"Action submitted successfully!")
                log_info(f"Action ID: {self.created_action_id}")
                log_info(f"Status: {data.get('status', 'unknown')}")
                log_info(f"Risk Score: {data.get('risk_score', 'N/A')}")
                log_info(f"Risk Level: {data.get('risk_level', 'N/A')}")
                log_info(f"Requires Approval: {data.get('requires_approval', 'N/A')}")
                self.results['submit_action'] = True
                return True
            else:
                log_error(f"Submit failed: {response.text[:300]}")
                self.results['submit_action'] = False
                return False

        except Exception as e:
            log_error(f"Submit action error: {e}")
            self.results['submit_action'] = False
            return False

    def test_get_action_status(self) -> bool:
        """Test 4: Get action status"""
        print("\n" + "=" * 60)
        print("TEST 4: GET ACTION STATUS")
        print("=" * 60)

        if not self.created_action_id:
            log_warning("Skipping - no action was created")
            self.results['get_status'] = None
            return True

        try:
            log_info(f"Getting status for action: {self.created_action_id}")

            response = requests.get(
                f"{self.base_url}/api/v1/actions/{self.created_action_id}/status",
                headers=self.headers,
                timeout=30
            )

            log_info(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                log_success(f"Action status retrieved")
                log_info(f"Current Status: {data.get('status', 'unknown')}")
                log_info(f"Policy Decision: {data.get('policy_decision', 'N/A')}")
                self.results['get_status'] = True
                return True
            else:
                log_error(f"Get status failed: {response.text[:300]}")
                self.results['get_status'] = False
                return False

        except Exception as e:
            log_error(f"Get status error: {e}")
            self.results['get_status'] = False
            return False

    def test_list_actions(self) -> bool:
        """Test 5: List actions"""
        print("\n" + "=" * 60)
        print("TEST 5: LIST ACTIONS")
        print("=" * 60)

        try:
            log_info("Listing recent actions...")

            response = requests.get(
                f"{self.base_url}/api/v1/actions",
                headers=self.headers,
                params={"limit": 5},
                timeout=30
            )

            log_info(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    log_success(f"Retrieved {len(data)} actions")
                    for action in data[:3]:
                        log_info(f"  - ID: {action.get('id')}, Type: {action.get('action_type')}, Status: {action.get('status')}")
                else:
                    log_success(f"Actions retrieved: {data.get('total', len(data.get('items', [])))}")
                self.results['list_actions'] = True
                return True
            else:
                log_error(f"List failed: {response.text[:300]}")
                self.results['list_actions'] = False
                return False

        except Exception as e:
            log_error(f"List actions error: {e}")
            self.results['list_actions'] = False
            return False

    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}ASCEND SDK/API INTEGRATION TEST{Colors.END}")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {self.api_key[:20]}...")
        print(f"Test Agent ID: {self.test_agent_id}")

        # Run tests in sequence
        self.test_health()
        self.test_register_agent()
        self.test_submit_action()
        self.test_get_action_status()
        self.test_list_actions()

        # Print summary
        self.print_summary()

        # Return True if all tests passed
        return all(v is True or v is None for v in self.results.values())

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print("=" * 60)

        passed = 0
        failed = 0
        skipped = 0

        test_names = {
            'health': 'Health Check',
            'register_agent': 'Register Agent',
            'submit_action': 'Submit Action',
            'get_status': 'Get Action Status',
            'list_actions': 'List Actions'
        }

        for key, name in test_names.items():
            result = self.results.get(key)
            if result is True:
                print(f"  {Colors.GREEN}✅ PASS{Colors.END}: {name}")
                passed += 1
            elif result is False:
                print(f"  {Colors.RED}❌ FAIL{Colors.END}: {name}")
                failed += 1
            else:
                print(f"  {Colors.YELLOW}⏭️  SKIP{Colors.END}: {name}")
                skipped += 1

        print()
        print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED - SDK INTEGRATION VERIFIED{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED - CHECK CONFIGURATION{Colors.END}")


def main():
    parser = argparse.ArgumentParser(
        description="Test Ascend SDK/API Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test against production
  python3 scripts/test_sdk_integration.py --api-key "ask_xxxxxxxxxxxxx"

  # Test against local development
  python3 scripts/test_sdk_integration.py --api-key "ask_xxxxxxxxxxxxx" --base-url "http://localhost:8000"

  # Test against staging
  python3 scripts/test_sdk_integration.py --api-key "ask_xxxxxxxxxxxxx" --base-url "https://staging.owkai.app"
        """
    )

    parser.add_argument(
        "--api-key", "-k",
        required=True,
        help="API key for authentication (from API Keys tab in settings)"
    )

    parser.add_argument(
        "--base-url", "-u",
        default="https://pilot.owkai.app",
        help="Base URL for the API (default: https://pilot.owkai.app)"
    )

    args = parser.parse_args()

    # Validate API key format
    if not args.api_key.startswith(("ask_", "owkai_", "ascend_")):
        log_warning("API key doesn't start with expected prefix (ask_, owkai_, ascend_)")
        log_info("Continuing anyway...")

    # Run tests
    tester = AscendIntegrationTester(args.base_url, args.api_key)
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
