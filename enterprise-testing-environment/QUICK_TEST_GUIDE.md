# OW-KAI Platform - Quick Enterprise Testing Guide

**Purpose**: Execute complete end-to-end testing without persistent infrastructure
**Duration**: 2-3 hours
**Cost**: $0 (uses existing pilot.owkai.app platform)

---

## Overview

This guide provides a **complete, runnable test** of the OW-KAI AI Governance Platform that simulates enterprise usage without requiring AWS infrastructure. Perfect for:

- ✅ Validating platform capabilities
- ✅ Training team members
- ✅ Demonstrating to stakeholders
- ✅ POC/pilot evaluation
- ✅ Integration testing

---

## Quick Start (5 Minutes)

### Prerequisites

```bash
# Required tools
python --version  # Requires 3.9+
pip install requests pyjwt

# Optional (for advanced testing)
pip install pytest locust websockets
```

### Step 1: Get Credentials

Contact the OW-KAI team or use demo credentials:
- **Email**: `admin@owkai.com`
- **Password**: `admin123` (demo environment)
- **Platform URL**: `https://pilot.owkai.app`

### Step 2: Run Quick Test

```bash
# Download test script
curl -O https://raw.githubusercontent.com/ow-kai/quick-test/main/quick_test.py

# Run test
python quick_test.py
```

**Expected Output**:
```
✅ Authentication successful
✅ Health check passed
✅ Model registered (action_id: 1234)
✅ Risk score calculated: 67
✅ MCP action evaluated: PENDING_APPROVAL
✅ All tests passed!
```

---

## Complete Test Script

Save this as `owkai_complete_test.py`:

```python
#!/usr/bin/env python3
"""
OW-KAI Platform - Complete Enterprise Test Suite

Tests all major platform capabilities:
1. Authentication
2. Health checks
3. Model registration
4. Governance workflows
5. MCP evaluation
6. Risk assessment
7. Policy evaluation
8. Audit trail

Duration: ~5 minutes
Requirements: Python 3.9+, requests library
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class OWKAITester:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")

    def authenticate(self) -> bool:
        """Test 1: Authentication"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_test("Authentication", "PASS", f"Token received")
                return True
            else:
                self.log_test("Authentication", "FAIL", f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Authentication", "FAIL", str(e))
            return False

    def test_health(self) -> bool:
        """Test 2: Health Check"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                enterprise = data.get('enterprise_grade')

                self.log_test("Health Check", "PASS",
                             f"Status={status}, Enterprise={enterprise}")
                return True
            else:
                self.log_test("Health Check", "FAIL", f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Health Check", "FAIL", str(e))
            return False

    def test_model_registration(self) -> Dict[str, Any]:
        """Test 3: Model Registration"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            model_data = {
                "action_type": "model_deployment",
                "action_source": "agent",
                "model_name": f"test-model-{int(time.time())}",
                "risk_level": "medium",
                "metadata": {
                    "test_run": True,
                    "deployed_by": "automated-test",
                    "model_type": "RandomForest"
                }
            }

            response = self.session.post(
                f"{self.base_url}/api/governance/unified/action",
                json=model_data,
                headers=headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                action_id = data.get('action_id')
                risk_score = data.get('risk_score')
                status = data.get('status')

                self.log_test("Model Registration", "PASS",
                             f"ID={action_id}, Risk={risk_score}, Status={status}")
                return data
            else:
                self.log_test("Model Registration", "FAIL",
                             f"Status: {response.status_code}, {response.text[:200]}")
                return {}

        except Exception as e:
            self.log_test("Model Registration", "FAIL", str(e))
            return {}

    def test_mcp_evaluation(self) -> Dict[str, Any]:
        """Test 4: MCP Action Evaluation"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            mcp_request = {
                "server_id": "test-server-1",
                "namespace": "filesystem",
                "verb": "read_file",
                "resource": "/tmp/test.txt",
                "session_id": f"session-{int(time.time())}",
                "client_id": "automated-test",
                "parameters": {"encoding": "utf-8"}
            }

            response = self.session.post(
                f"{self.base_url}/mcp/evaluate",
                json=mcp_request,
                headers=headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                decision = data.get('decision')
                risk_score = data.get('risk_score')
                requires_approval = data.get('requires_approval')

                self.log_test("MCP Evaluation", "PASS",
                             f"Decision={decision}, Risk={risk_score}, "
                             f"Approval={requires_approval}")
                return data
            else:
                self.log_test("MCP Evaluation", "FAIL",
                             f"Status: {response.status_code}, {response.text[:200]}")
                return {}

        except Exception as e:
            self.log_test("MCP Evaluation", "FAIL", str(e))
            return {}

    def test_list_pending_actions(self) -> List[Dict]:
        """Test 5: List Pending Actions"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            response = self.session.get(
                f"{self.base_url}/api/governance/pending-actions",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 0

                self.log_test("List Pending Actions", "PASS", f"Found {count} pending actions")
                return data if isinstance(data, list) else []
            else:
                self.log_test("List Pending Actions", "FAIL",
                             f"Status: {response.status_code}")
                return []

        except Exception as e:
            self.log_test("List Pending Actions", "FAIL", str(e))
            return []

    def test_workflow_configs(self) -> Dict[str, Any]:
        """Test 6: Workflow Configurations"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            response = self.session.get(
                f"{self.base_url}/api/authorization/workflow-config",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                workflows = data.get('workflows', {})
                count = len(workflows)

                self.log_test("Workflow Configs", "PASS", f"Found {count} workflows")
                return data
            else:
                self.log_test("Workflow Configs", "FAIL",
                             f"Status: {response.status_code}")
                return {}

        except Exception as e:
            self.log_test("Workflow Configs", "FAIL", str(e))
            return {}

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 70)
        print("TEST REPORT")
        print("=" * 70)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        print("\nDetailed Results:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result['details']:
                print(f"   {result['details']}")

        print("\n" + "=" * 70)

        return passed == total


def main():
    print("=" * 70)
    print("OW-KAI PLATFORM - ENTERPRISE TEST SUITE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print()

    # Configuration
    BASE_URL = "https://pilot.owkai.app"
    EMAIL = "admin@owkai.com"
    REDACTED-CREDENTIAL = "admin123"  # Demo credentials

    # Initialize tester
    tester = OWKAITester(BASE_URL, EMAIL, REDACTED-CREDENTIAL)

    # Run test suite
    print("Running tests...\n")

    # Test 1: Authentication
    if not tester.authenticate():
        print("\n❌ Authentication failed. Aborting remaining tests.")
        return False

    # Test 2: Health Check
    tester.test_health()

    # Test 3: Model Registration
    tester.test_model_registration()

    # Test 4: MCP Evaluation
    tester.test_mcp_evaluation()

    # Test 5: List Pending Actions
    tester.test_list_pending_actions()

    # Test 6: Workflow Configurations
    tester.test_workflow_configs()

    # Generate report
    all_passed = tester.generate_report()

    print(f"\nEnd Time: {datetime.now().isoformat()}")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

---

## Running the Test

### Option 1: Direct Python Execution

```bash
# Save the script
cat > owkai_test.py << 'EOF'
# [Paste complete script above]
EOF

# Run
python3 owkai_test.py
```

### Option 2: Using Docker (Isolated Environment)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests pyjwt

COPY owkai_test.py .

CMD ["python", "owkai_test.py"]
EOF

# Build and run
docker build -t owkai-test .
docker run --rm owkai-test
```

### Option 3: Pytest Integration

```bash
# Install pytest
pip install pytest requests

# Create pytest test file
cat > test_owkai_platform.py << 'EOF'
import pytest
import requests
from owkai_test import OWKAITester

@pytest.fixture
def tester():
    return OWKAITester(
        base_url="https://pilot.owkai.app",
        email="admin@owkai.com",
        password="admin123"
    )

def test_authentication(tester):
    assert tester.authenticate() == True

def test_health_check(tester):
    tester.authenticate()
    assert tester.test_health() == True

def test_model_registration(tester):
    tester.authenticate()
    result = tester.test_model_registration()
    assert 'action_id' in result

def test_mcp_evaluation(tester):
    tester.authenticate()
    result = tester.test_mcp_evaluation()
    assert 'decision' in result

def test_workflow_configs(tester):
    tester.authenticate()
    result = tester.test_workflow_configs()
    assert 'workflows' in result
EOF

# Run pytest
pytest test_owkai_platform.py -v
```

---

## Expected Results

### Successful Test Output

```
======================================================================
OW-KAI PLATFORM - ENTERPRISE TEST SUITE
======================================================================
Start Time: 2025-11-19T14:30:00

Running tests...

✅ Authentication: PASS
   Token received
✅ Health Check: PASS
   Status=healthy, Enterprise=True
✅ Model Registration: PASS
   ID=1234, Risk=45, Status=pending_approval
✅ MCP Evaluation: PASS
   Decision=EVALUATE, Risk=55, Approval=True
✅ List Pending Actions: PASS
   Found 3 pending actions
✅ Workflow Configs: PASS
   Found 4 workflows

======================================================================
TEST REPORT
======================================================================
Total Tests: 6
Passed: 6 ✅
Failed: 0 ❌
Success Rate: 100.0%

Detailed Results:
✅ Authentication: PASS
   Token received
✅ Health Check: PASS
   Status=healthy, Enterprise=True
✅ Model Registration: PASS
   ID=1234, Risk=45, Status=pending_approval
✅ MCP Evaluation: PASS
   Decision=EVALUATE, Risk=55, Approval=True
✅ List Pending Actions: PASS
   Found 3 pending actions
✅ Workflow Configs: PASS
   Found 4 workflows

======================================================================

End Time: 2025-11-19T14:35:23
```

---

## Advanced Testing Scenarios

### Scenario 1: High-Risk Model Deployment

```python
def test_high_risk_deployment():
    """Test high-risk model requiring multi-level approval"""

    tester = OWKAITester("https://pilot.owkai.app", "admin@owkai.com", "admin123")
    tester.authenticate()

    # Register high-risk model
    result = tester.session.post(
        f"{tester.base_url}/api/governance/unified/action",
        json={
            "action_type": "model_deployment",
            "action_source": "agent",
            "model_name": "fraud-detection-critical",
            "risk_level": "critical",
            "metadata": {
                "environment": "production",
                "data_sensitivity": "PII",
                "regulatory_impact": "SOX"
            }
        },
        headers={'Authorization': f'Bearer {tester.token}'}
    ).json()

    # Verify approval requirements
    assert result['requires_approval'] == True
    assert result['approval_level'] >= 3  # Should require Level 3+ approval
    assert result['risk_score'] >= 70  # High risk score

    print(f"✅ High-risk deployment correctly flagged for approval")
    print(f"   Risk Score: {result['risk_score']}")
    print(f"   Approval Level: {result['approval_level']}")
```

### Scenario 2: MCP Server Action Governance

```python
def test_mcp_dangerous_action():
    """Test MCP action that should be denied or require approval"""

    tester = OWKAITester("https://pilot.owkai.app", "admin@owkai.com", "admin123")
    tester.authenticate()

    # Attempt dangerous database operation
    result = tester.session.post(
        f"{tester.base_url}/mcp/evaluate",
        json={
            "server_id": "database-server",
            "namespace": "database",
            "verb": "execute_query",
            "resource": "production_db",
            "session_id": "test-session",
            "client_id": "test-client",
            "parameters": {
                "query": "DROP TABLE users;"
            }
        },
        headers={'Authorization': f'Bearer {tester.token}'}
    ).json()

    # Verify it's blocked or requires approval
    assert result['decision'] in ['DENY', 'EVALUATE']
    if result['decision'] == 'EVALUATE':
        assert result['requires_approval'] == True

    print(f"✅ Dangerous MCP action correctly handled")
    print(f"   Decision: {result['decision']}")
    print(f"   Risk Score: {result['risk_score']}")
```

### Scenario 3: Compliance Monitoring

```python
def test_compliance_evaluation():
    """Test compliance policy evaluation"""

    tester = OWKAITester("https://pilot.owkai.app", "admin@owkai.com", "admin123")
    tester.authenticate()

    # Register model with PII handling
    result = tester.session.post(
        f"{tester.base_url}/api/governance/unified/action",
        json={
            "action_type": "model_deployment",
            "action_source": "agent",
            "model_name": "customer-segmentation",
            "risk_level": "medium",
            "metadata": {
                "handles_pii": True,
                "data_region": "EU",
                "compliance_requirements": ["GDPR", "SOC2"]
            }
        },
        headers={'Authorization': f'Bearer {tester.token}'}
    ).json()

    # Verify compliance checks were performed
    assert 'policy_results' in result or 'compliance_score' in result

    print(f"✅ Compliance evaluation completed")
    print(f"   Action ID: {result.get('action_id')}")
```

---

## Cleanup

Since no infrastructure was deployed, cleanup is automatic. However, you may want to:

```python
def cleanup_test_data():
    """Optional: Clean up test actions (if implemented in platform)"""

    tester = OWKAITester("https://pilot.owkai.app", "admin@owkai.com", "admin123")
    tester.authenticate()

    # Get all test actions
    actions = tester.session.get(
        f"{tester.base_url}/api/governance/unified-actions",
        params={"created_by": "automated-test"},
        headers={'Authorization': f'Bearer {tester.token}'}
    ).json()

    print(f"Found {len(actions)} test actions")

    # Note: Actual cleanup would require a delete endpoint
    # This is typically not needed as test data is isolated
```

---

## Troubleshooting

### Issue: Authentication Fails

```
❌ Authentication: FAIL
   Status: 401
```

**Solution**:
1. Verify credentials are correct
2. Check platform URL is accessible
3. Ensure no network/firewall blocking HTTPS

### Issue: Token Expired

```
❌ Model Registration: FAIL
   Status: 401 - Token expired
```

**Solution**:
Re-authenticate before each major test section:

```python
tester.authenticate()  # Refresh token
result = tester.test_model_registration()
```

### Issue: Timeout

```
❌ Health Check: FAIL
   Request timeout
```

**Solution**:
1. Check internet connectivity
2. Verify pilot.owkai.app is accessible
3. Increase timeout in requests

---

## Performance Benchmarks

Expected performance (from automated test runs):

| Test | Expected Duration | Acceptable Range |
|------|------------------|------------------|
| Authentication | <1s | <2s |
| Health Check | <500ms | <1s |
| Model Registration | <2s | <5s |
| MCP Evaluation | <2s | <5s |
| List Actions | <1s | <3s |
| **Total Suite** | **~5-10s** | **<30s** |

---

## Next Steps

After successful testing:

1. **Integration**: Use the OWKAIClient library for production integration
2. **Customization**: Adapt test scenarios to your use cases
3. **Automation**: Integrate into CI/CD pipeline
4. **Monitoring**: Set up continuous testing
5. **Documentation**: Document your specific integration patterns

---

## Support

For issues or questions:
- **Email**: support@ow-kai.com
- **Platform**: https://pilot.owkai.app
- **Documentation**: See ENTERPRISE_ONBOARDING_GUIDE.md

---

**Document Version**: 1.0
**Last Updated**: November 19, 2025
**Tested On**: pilot.owkai.app (production)
