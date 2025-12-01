"""
OW-AI Enterprise E2E Comprehensive Test Suite
==============================================

Tests all major functionality against production/staging environment.

Usage:
    python tests/e2e_comprehensive_test.py --email admin@acme.com --password YOUR_PASSWORD

Or set environment variables:
    export OWKAI_TEST_EMAIL=admin@acme.com
    export OWKAI_TEST_PASSWORD=YOUR_PASSWORD
    python tests/e2e_comprehensive_test.py
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

# Test configuration
BASE_URL = os.getenv("OWKAI_API_URL", "https://pilot.owkai.app")
TEST_RESULTS: List[Dict[str, Any]] = []


class Colors:
    """Terminal colors for output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"  [{status}] {test_name}")
    if details and not passed:
        print(f"        {Colors.YELLOW}{details}{Colors.RESET}")
    TEST_RESULTS.append({
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })


class OWKAITestClient:
    """Test client for OW-AI API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_info: Optional[Dict] = None

    def login(self, email: str, password: str) -> bool:
        """Authenticate and get tokens."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/token",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                return True

            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated GET request."""
        return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated POST request."""
        return self.session.post(f"{self.base_url}{endpoint}", **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated PUT request."""
        return self.session.put(f"{self.base_url}{endpoint}", **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated DELETE request."""
        return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)


# =============================================================================
# Test Categories
# =============================================================================

def test_health_endpoints(client: OWKAITestClient):
    """Test health and system endpoints."""
    print(f"\n{Colors.BOLD}=== Health & System Tests ==={Colors.RESET}")

    # Health check
    try:
        r = client.get("/health")
        passed = r.status_code == 200 and r.json().get("status") == "healthy"
        log_result("Health endpoint", passed, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Health endpoint", False, str(e))

    # Deployment info
    try:
        r = client.get("/api/deployment-info")
        passed = r.status_code == 200 and "commit_sha" in r.json()
        log_result("Deployment info", passed)
    except Exception as e:
        log_result("Deployment info", False, str(e))

    # OpenAPI spec
    try:
        r = client.get("/openapi.json")
        passed = r.status_code == 200 and "paths" in r.json()
        log_result("OpenAPI spec available", passed)
    except Exception as e:
        log_result("OpenAPI spec available", False, str(e))


def test_authentication(client: OWKAITestClient, email: str, password: str):
    """Test authentication flows."""
    print(f"\n{Colors.BOLD}=== Authentication Tests ==={Colors.RESET}")

    # Login
    passed = client.login(email, password)
    log_result("Login with credentials", passed)

    if not passed:
        print(f"{Colors.RED}Cannot continue without authentication{Colors.RESET}")
        return False

    # Get current user
    try:
        r = client.get("/api/auth/me")
        passed = r.status_code == 200 and "email" in r.json()
        client.user_info = r.json() if passed else None
        log_result("Get current user", passed)
    except Exception as e:
        log_result("Get current user", False, str(e))

    # CSRF token
    try:
        r = client.get("/api/auth/csrf")
        passed = r.status_code == 200
        log_result("CSRF token endpoint", passed)
    except Exception as e:
        log_result("CSRF token endpoint", False, str(e))

    # Auth diagnostic
    try:
        r = client.get("/api/auth/diagnostic")
        passed = r.status_code == 200
        log_result("Auth diagnostic", passed)
    except Exception as e:
        log_result("Auth diagnostic", False, str(e))

    return True


def test_agent_actions(client: OWKAITestClient):
    """Test agent action submission and management."""
    print(f"\n{Colors.BOLD}=== Agent Action Tests ==={Colors.RESET}")

    # List agent actions
    try:
        r = client.get("/api/agent-activity")
        passed = r.status_code == 200
        data = r.json() if passed else {}
        log_result("List agent actions", passed, f"Count: {len(data) if isinstance(data, list) else 'N/A'}")
    except Exception as e:
        log_result("List agent actions", False, str(e))

    # Submit test action
    test_action = {
        "agent_id": "e2e-test-agent",
        "agent_name": "E2E Test Agent",
        "action_type": "data_access",
        "resource": "test_resource",
        "action_details": {
            "operation": "e2e_test",
            "timestamp": datetime.now().isoformat()
        }
    }

    action_id = None
    try:
        r = client.post("/api/authorization/agent-action", json=test_action)
        passed = r.status_code in [200, 201]
        if passed:
            data = r.json()
            action_id = data.get("action_id") or data.get("id")
        log_result("Submit agent action", passed, f"Action ID: {action_id}")
    except Exception as e:
        log_result("Submit agent action", False, str(e))

    # Get action status
    if action_id:
        try:
            r = client.get(f"/api/agent-action/status/{action_id}")
            passed = r.status_code == 200
            log_result("Get action status", passed)
        except Exception as e:
            log_result("Get action status", False, str(e))

    return action_id


def test_authorization(client: OWKAITestClient, action_id: Optional[str]):
    """Test authorization workflows."""
    print(f"\n{Colors.BOLD}=== Authorization Tests ==={Colors.RESET}")

    # List pending actions
    try:
        r = client.get("/api/authorization/pending")
        passed = r.status_code == 200
        log_result("List pending actions", passed)
    except Exception as e:
        log_result("List pending actions", False, str(e))

    # Authorization metrics
    try:
        r = client.get("/api/authorization/metrics")
        passed = r.status_code == 200
        log_result("Authorization metrics", passed)
    except Exception as e:
        log_result("Authorization metrics", False, str(e))

    # Authorize action (if we have one)
    if action_id:
        try:
            r = client.post(f"/api/authorization/authorize/{action_id}", json={
                "approved": True,
                "comments": "E2E test approval"
            })
            passed = r.status_code in [200, 400, 404]  # 400/404 acceptable if action already processed
            log_result("Authorize action", passed)
        except Exception as e:
            log_result("Authorize action", False, str(e))


def test_governance(client: OWKAITestClient):
    """Test governance and policy endpoints."""
    print(f"\n{Colors.BOLD}=== Governance Tests ==={Colors.RESET}")

    # List policies
    try:
        r = client.get("/api/governance/policies")
        passed = r.status_code == 200
        data = r.json() if passed else {}
        count = len(data.get("policies", data)) if isinstance(data, (dict, list)) else 0
        log_result("List governance policies", passed, f"Count: {count}")
    except Exception as e:
        log_result("List governance policies", False, str(e))

    # Policy templates
    try:
        r = client.get("/api/governance/policy-templates")
        passed = r.status_code == 200
        log_result("Get policy templates", passed)
    except Exception as e:
        log_result("Get policy templates", False, str(e))

    # Audit events
    try:
        r = client.get("/api/governance/audit-events")
        passed = r.status_code == 200
        log_result("Get audit events", passed)
    except Exception as e:
        log_result("Get audit events", False, str(e))


def test_alerts(client: OWKAITestClient):
    """Test alert management."""
    print(f"\n{Colors.BOLD}=== Alert Tests ==={Colors.RESET}")

    # List alerts
    try:
        r = client.get("/api/alerts")
        passed = r.status_code == 200
        log_result("List alerts", passed)
    except Exception as e:
        log_result("List alerts", False, str(e))

    # Alert statistics
    try:
        r = client.get("/api/alerts/statistics")
        passed = r.status_code == 200
        log_result("Alert statistics", passed)
    except Exception as e:
        log_result("Alert statistics", False, str(e))


def test_smart_rules(client: OWKAITestClient):
    """Test smart rules engine."""
    print(f"\n{Colors.BOLD}=== Smart Rules Tests ==={Colors.RESET}")

    # List smart rules
    try:
        r = client.get("/api/smart-rules")
        passed = r.status_code == 200
        log_result("List smart rules", passed)
    except Exception as e:
        log_result("List smart rules", False, str(e))

    # Rule templates
    try:
        r = client.get("/api/smart-rules/templates")
        passed = r.status_code == 200
        log_result("Get rule templates", passed)
    except Exception as e:
        log_result("Get rule templates", False, str(e))


def test_analytics(client: OWKAITestClient):
    """Test analytics endpoints."""
    print(f"\n{Colors.BOLD}=== Analytics Tests ==={Colors.RESET}")

    # Risk trends
    try:
        r = client.get("/api/analytics/risk-trends")
        passed = r.status_code == 200
        log_result("Risk trends", passed)
    except Exception as e:
        log_result("Risk trends", False, str(e))

    # Action trends
    try:
        r = client.get("/api/analytics/action-trends")
        passed = r.status_code == 200
        log_result("Action trends", passed)
    except Exception as e:
        log_result("Action trends", False, str(e))

    # AI insights
    try:
        r = client.get("/ai-insights")
        passed = r.status_code == 200
        log_result("AI insights", passed)
    except Exception as e:
        log_result("AI insights", False, str(e))


def test_enterprise_features(client: OWKAITestClient):
    """Test enterprise-specific features."""
    print(f"\n{Colors.BOLD}=== Enterprise Features Tests ==={Colors.RESET}")

    # Organization settings
    try:
        r = client.get("/api/organizations/current")
        passed = r.status_code == 200
        log_result("Get organization", passed)
    except Exception as e:
        log_result("Get organization", False, str(e))

    # Enterprise users
    try:
        r = client.get("/api/enterprise-users")
        passed = r.status_code == 200
        log_result("List enterprise users", passed)
    except Exception as e:
        log_result("List enterprise users", False, str(e))

    # Audit logs
    try:
        r = client.get("/api/audit/logs")
        passed = r.status_code == 200
        log_result("Audit logs", passed)
    except Exception as e:
        log_result("Audit logs", False, str(e))

    # Data retention
    try:
        r = client.get("/api/retention/policies")
        passed = r.status_code == 200
        log_result("Retention policies", passed)
    except Exception as e:
        log_result("Retention policies", False, str(e))


def test_integrations(client: OWKAITestClient):
    """Test integration endpoints."""
    print(f"\n{Colors.BOLD}=== Integration Tests ==={Colors.RESET}")

    # Webhooks
    try:
        r = client.get("/api/webhooks")
        passed = r.status_code == 200
        log_result("List webhooks", passed)
    except Exception as e:
        log_result("List webhooks", False, str(e))

    # Notifications
    try:
        r = client.get("/api/notifications/channels")
        passed = r.status_code == 200
        log_result("Notification channels", passed)
    except Exception as e:
        log_result("Notification channels", False, str(e))

    # Integration status
    try:
        r = client.get("/api/integrations/status")
        passed = r.status_code == 200
        log_result("Integration status", passed)
    except Exception as e:
        log_result("Integration status", False, str(e))


def test_api_keys(client: OWKAITestClient):
    """Test API key management."""
    print(f"\n{Colors.BOLD}=== API Key Tests ==={Colors.RESET}")

    # List API keys
    try:
        r = client.get("/api/keys")
        passed = r.status_code == 200
        log_result("List API keys", passed)
    except Exception as e:
        log_result("List API keys", False, str(e))


def test_security_headers(client: OWKAITestClient):
    """Test security headers are present."""
    print(f"\n{Colors.BOLD}=== Security Header Tests ==={Colors.RESET}")

    try:
        r = client.get("/health")
        headers = r.headers

        # X-Frame-Options
        passed = headers.get("X-Frame-Options") == "DENY"
        log_result("X-Frame-Options: DENY", passed, headers.get("X-Frame-Options", "missing"))

        # X-Content-Type-Options
        passed = headers.get("X-Content-Type-Options") == "nosniff"
        log_result("X-Content-Type-Options: nosniff", passed)

        # X-XSS-Protection
        passed = "1" in headers.get("X-XSS-Protection", "")
        log_result("X-XSS-Protection enabled", passed)

        # HSTS
        passed = "max-age" in headers.get("Strict-Transport-Security", "")
        log_result("HSTS enabled", passed, headers.get("Strict-Transport-Security", "missing")[:50])

    except Exception as e:
        log_result("Security headers check", False, str(e))


def print_summary():
    """Print test summary."""
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    failed = total - passed

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"Pass Rate: {passed/total*100:.1f}%")
    print(f"{'='*60}\n")

    if failed > 0:
        print(f"{Colors.YELLOW}Failed Tests:{Colors.RESET}")
        for r in TEST_RESULTS:
            if not r["passed"]:
                print(f"  - {r['test']}: {r['details']}")
        print()

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="OW-AI E2E Test Suite")
    parser.add_argument("--email", default=os.getenv("OWKAI_TEST_EMAIL"), help="Test user email")
    parser.add_argument("--password", default=os.getenv("OWKAI_TEST_PASSWORD"), help="Test user password")
    parser.add_argument("--url", default=BASE_URL, help="API base URL")
    args = parser.parse_args()

    if not args.email or not args.password:
        print(f"{Colors.RED}Error: Email and password required{Colors.RESET}")
        print("Usage: python e2e_comprehensive_test.py --email admin@acme.com --password YOUR_PASSWORD")
        print("Or set OWKAI_TEST_EMAIL and OWKAI_TEST_PASSWORD environment variables")
        sys.exit(1)

    print(f"\n{Colors.BOLD}OW-AI Enterprise E2E Test Suite{Colors.RESET}")
    print(f"API URL: {args.url}")
    print(f"Test User: {args.email}")
    print(f"Started: {datetime.now().isoformat()}")

    client = OWKAITestClient(args.url)

    # Run tests
    test_health_endpoints(client)

    if not test_authentication(client, args.email, args.password):
        print(f"\n{Colors.RED}Authentication failed - cannot run authenticated tests{Colors.RESET}")
        print_summary()
        sys.exit(1)

    action_id = test_agent_actions(client)
    test_authorization(client, action_id)
    test_governance(client)
    test_alerts(client)
    test_smart_rules(client)
    test_analytics(client)
    test_enterprise_features(client)
    test_integrations(client)
    test_api_keys(client)
    test_security_headers(client)

    # Summary
    success = print_summary()

    # Save results
    results_file = f"e2e_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump({
            "url": args.url,
            "timestamp": datetime.now().isoformat(),
            "results": TEST_RESULTS
        }, f, indent=2)
    print(f"Results saved to: {results_file}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
