# OW-AI Enterprise: End-to-End Customer Testing Guide

**Test as a New Customer - PRODUCTION ENVIRONMENT**

This guide walks you through testing the OW-AI platform exactly as a new customer would experience it - from onboarding to integrating agents and MCP servers.

**Environment: PRODUCTION (https://pilot.owkai.app)**

---

## Overview

You will simulate being "Acme Corp", a new pilot customer who wants to:
1. Get onboarded to the platform
2. Log in and explore the dashboard
3. Create governance policies
4. Integrate an AI agent with the SDK
5. Set up an MCP server for Claude Desktop
6. Test that actions are blocked/approved correctly

---

## Prerequisites

Before starting, ensure:

```bash
# 1. Production backend is accessible
curl -s https://pilot.owkai.app/health | jq

# 2. You have AWS credentials configured (for Cognito provisioning)
aws sts get-caller-identity

# 3. Database connection to production RDS
# (Only needed for onboarding script)
```

---

## PHASE 1: Customer Onboarding

### Step 1.1: Onboard as "Acme Corp"

```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

# First, do a dry run to see what will happen
python scripts/onboard_pilot_customer.py \
  --company "Acme Corp" \
  --email "admin@acmecorp.test" \
  --dry-run

# If it looks good, run for real
python scripts/onboard_pilot_customer.py \
  --company "Acme Corp" \
  --email "admin@acmecorp.test"
```

**What happens:**
- Organization "Acme Corp" is created with slug "acme-corp"
- AWS Cognito user pool is provisioned
- Admin user account is created
- You get a temporary password

**Save these values:**
```
Organization ID: ____
Organization Slug: acme-corp
Cognito Pool ID: ____
Temporary Password: ____
```

### Step 1.2: Log In to the Platform

1. Open browser: **https://pilot.owkai.app**
2. Enter email: `admin@acmecorp.test`
3. Enter temporary password from onboarding
4. Change password when prompted
5. (Optional) Set up MFA

**Verify:**
- [ ] Can log in successfully
- [ ] Dashboard loads
- [ ] Organization name shows "Acme Corp"

---

## PHASE 2: Create Governance Policies

### Step 2.1: Create a "Block Production Deletes" Policy

Navigate to: **Authorization Center > Policy Management**

Click "Create Policy" and enter:

```
Name: No Production DELETE Operations
Description: Block all DELETE operations on production databases

Conditions:
- action_type = "database_delete"
- target_system = "production"

Decision: DENY
```

### Step 2.2: Create a "Require Approval for High Risk" Policy

```
Name: High Risk Approval Required
Description: Actions with risk score 70+ require manager approval

Conditions:
- risk_score >= 70

Decision: REQUIRE_APPROVAL
Approvers: admin@acmecorp.test
```

### Step 2.3: Verify Policies via API

```bash
# Get a token first (replace with actual login)
TOKEN="your_jwt_token_here"

# List policies
curl -s https://pilot.owkai.app/api/governance/policies \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Verify:**
- [ ] Both policies are listed
- [ ] Policies show as "active"

---

## PHASE 3: Generate API Key for SDK

### Step 3.1: Create API Key

Navigate to: **Settings > API Keys**

Click "Generate New Key":
- Name: `acme-agent-key`
- Permissions: `agent:execute`, `governance:read`

**Save the API Key:**
```
OWKAI_API_KEY=owkai_admin_xxxxxxxxxxxxxxxxxxxx
```

### Step 3.2: Verify API Key Works

```bash
export OWKAI_API_KEY="owkai_admin_xxxxxxxxxxxxxxxxxxxx"
export OWKAI_BASE_URL="https://pilot.owkai.app"

# Test the key
curl -s "$OWKAI_BASE_URL/health" \
  -H "Authorization: Bearer $OWKAI_API_KEY" | jq

# Test authenticated endpoint
curl -s "$OWKAI_BASE_URL/api/governance/policies" \
  -H "Authorization: Bearer $OWKAI_API_KEY" | jq
```

---

## PHASE 4: Test SDK Integration (Agent)

### Step 4.1: Set Up Test Environment

```bash
# Create test directory
mkdir -p /tmp/owkai-test
cd /tmp/owkai-test

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install SDK (from local source)
pip install -e /Users/mac_001/OW_AI_Project/owkai-sdk

# Or install dependencies manually
pip install httpx
```

### Step 4.2: Create Test Agent Script

Create file: `/tmp/owkai-test/test_agent.py`

```python
#!/usr/bin/env python3
"""
Acme Corp Test Agent

This simulates an AI agent that needs to perform various operations,
some of which should be allowed and some blocked by governance.
"""

import os
import sys

# Add SDK to path if needed
sys.path.insert(0, "/Users/mac_001/OW_AI_Project/owkai-sdk")

from owkai.enforcement import (
    EnforcedClient,
    GovernanceBlockedError,
    ActionRejectedError,
    ApprovalTimeoutError,
    GovernanceUnavailableError,
)

# Configuration - PRODUCTION
API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")

def main():
    print("=" * 60)
    print("  ACME CORP - AI Agent Governance Test")
    print("=" * 60)

    # Initialize enforced client
    print("\n[1] Initializing EnforcedClient...")
    client = EnforcedClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        enforcement_mode="mandatory",
        fail_closed=True,
        approval_timeout=30,  # Short timeout for testing
        agent_id="acme-test-agent"
    )
    print("    ✅ Client initialized in MANDATORY mode")

    # Test 1: Low-risk read operation (should auto-approve)
    print("\n[2] Testing LOW-RISK read operation...")
    try:
        result = client.execute_governed(
            action=lambda: {"users": ["alice", "bob", "charlie"]},
            action_type="database_read",
            description="Fetch user list from staging database",
            tool_name="postgresql",
            target_system="staging",
            risk_context={"query_type": "SELECT", "table": "users"}
        )
        print(f"    ✅ AUTO-APPROVED! Result: {result}")
    except Exception as e:
        print(f"    ❌ Unexpected: {type(e).__name__}: {e}")

    # Test 2: High-risk delete on staging (should require approval)
    print("\n[3] Testing HIGH-RISK delete on STAGING...")
    try:
        result = client.execute_governed(
            action=lambda: {"deleted_count": 150},
            action_type="database_delete",
            description="Delete inactive user sessions",
            tool_name="postgresql",
            target_system="staging",
            risk_context={
                "query_type": "DELETE",
                "table": "sessions",
                "estimated_rows": 150
            }
        )
        print(f"    ✅ APPROVED! Result: {result}")
    except ApprovalTimeoutError as e:
        print(f"    ⏰ TIMEOUT (expected if no approver): {e.timeout_seconds}s")
        print(f"       Action ID: {e.action_id}")
        print(f"       Check dashboard to approve/reject")
    except GovernanceBlockedError as e:
        print(f"    🚫 BLOCKED by policy: {e.blocking_reason}")
    except ActionRejectedError as e:
        print(f"    ❌ REJECTED by {e.rejected_by}: {e.rejection_reason}")

    # Test 3: Production delete (should be BLOCKED by policy)
    print("\n[4] Testing PRODUCTION DELETE (should be blocked)...")
    try:
        result = client.execute_governed(
            action=lambda: {"deleted_count": 1000},
            action_type="database_delete",
            description="Delete old records from production users table",
            tool_name="postgresql",
            target_system="production",
            risk_context={
                "query_type": "DELETE",
                "table": "users",
                "estimated_rows": 1000
            }
        )
        print(f"    ⚠️ UNEXPECTED: Action was allowed! {result}")
    except GovernanceBlockedError as e:
        print(f"    ✅ CORRECTLY BLOCKED!")
        print(f"       Reason: {e.blocking_reason}")
        print(f"       Policy: {e.policy_name}")
        print(f"       Risk Score: {e.risk_score}")
    except ApprovalTimeoutError as e:
        print(f"    ⏰ Timeout (policy may not be configured)")
    except Exception as e:
        print(f"    ❌ Error: {type(e).__name__}: {e}")

    # Test 4: File system operation
    print("\n[5] Testing FILE SYSTEM operation...")
    try:
        result = client.execute_governed(
            action=lambda: {"files_backed_up": 25},
            action_type="file_write",
            description="Create backup of configuration files",
            tool_name="filesystem",
            target_system="staging",
            target_resource="/backups/config/",
            risk_context={"operation": "backup", "file_count": 25}
        )
        print(f"    ✅ Result: {result}")
    except GovernanceBlockedError as e:
        print(f"    🚫 BLOCKED: {e.blocking_reason}")
    except ApprovalTimeoutError as e:
        print(f"    ⏰ TIMEOUT waiting for approval")

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print("""
    Test 1 (Low-risk read):     Should AUTO-APPROVE
    Test 2 (High-risk staging): Should REQUIRE APPROVAL or TIMEOUT
    Test 3 (Production delete): Should be BLOCKED by policy
    Test 4 (File operation):    Depends on policy configuration

    Check the OW-AI dashboard for:
    - Action history
    - Pending approvals
    - Audit logs
    """)

    client.close()
    print("\n✅ Test agent completed!")

if __name__ == "__main__":
    main()
```

### Step 4.3: Run the Test Agent

```bash
cd /tmp/owkai-test
source venv/bin/activate

# Set environment variables - PRODUCTION
export OWKAI_API_KEY="owkai_admin_your_actual_key"
export OWKAI_BASE_URL="https://pilot.owkai.app"

# Run the test
python test_agent.py
```

**Expected Results:**

| Test | Expected Outcome |
|------|------------------|
| Low-risk read | AUTO-APPROVE (action executes) |
| High-risk staging delete | REQUIRE_APPROVAL or TIMEOUT |
| Production delete | BLOCKED by policy |
| File operation | Depends on policies |

### Step 4.4: Approve/Reject Pending Actions

1. Open dashboard: **https://pilot.owkai.app**
2. Navigate to **Authorization Center**
3. Find pending actions
4. Click "Approve" or "Reject"
5. Re-run the test agent to see different behavior

---

## PHASE 5: Test MCP Server Integration

### Step 5.1: Create MCP Server Script

Create file: `/tmp/owkai-test/acme_mcp_server.py`

```python
#!/usr/bin/env python3
"""
Acme Corp MCP Server

This MCP server provides governed tools for Claude Desktop.
All tool executions go through OW-AI governance.
"""

import asyncio
import os
import sys

# Add SDK to path
sys.path.insert(0, "/Users/mac_001/OW_AI_Project/owkai-sdk")

from owkai.mcp_enforced import EnforcedMCPServer

# Configuration - PRODUCTION
API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")

# Initialize server
server = EnforcedMCPServer(
    api_key=API_KEY,
    base_url=BASE_URL,
    server_name="Acme Corp Database Tools",
    enforcement_mode="mandatory",
    fail_closed=True,
    approval_timeout=60
)

# Simulated database
class MockDatabase:
    def __init__(self):
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@acme.com"},
            {"id": 2, "name": "Bob", "email": "bob@acme.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@acme.com"},
        ]

    async def query(self, sql: str):
        return f"Query executed: {sql}"

    async def get_users(self):
        return self.users

    async def delete_user(self, user_id: int):
        self.users = [u for u in self.users if u["id"] != user_id]
        return {"deleted": user_id}

db = MockDatabase()

# ============================================
# TOOL DEFINITIONS
# ============================================

@server.tool(
    name="list_users",
    description="List all users in the database (low risk)",
    namespace="database",
    verb="read",
    risk_hint="low"
)
async def list_users():
    """List all users - should auto-approve."""
    return await db.get_users()

@server.tool(
    name="query_database",
    description="Execute a read-only SQL query (medium risk)",
    namespace="database",
    verb="read",
    risk_hint="medium"
)
async def query_database(query: str, database: str = "staging"):
    """Execute SQL query - medium risk, may require approval."""
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries allowed")
    return await db.query(query)

@server.tool(
    name="delete_user",
    description="Delete a user from the database (high risk)",
    namespace="database",
    verb="delete",
    risk_hint="high"
)
async def delete_user(user_id: int, reason: str = ""):
    """Delete user - high risk, requires approval."""
    return await db.delete_user(user_id)

@server.tool(
    name="drop_table",
    description="Drop a database table (CRITICAL risk - production)",
    namespace="database",
    verb="delete",
    risk_hint="critical"
)
async def drop_table(table_name: str, confirm: bool = False):
    """Drop table - critical risk, should be blocked."""
    if not confirm:
        raise ValueError("Must confirm=true to drop table")
    return {"dropped": table_name}

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("Starting Acme Corp MCP Server...")
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Base URL: {BASE_URL}")
    print("Enforcement: MANDATORY (fail-closed)")
    print("\nAvailable tools:")
    print("  - list_users (low risk)")
    print("  - query_database (medium risk)")
    print("  - delete_user (high risk)")
    print("  - drop_table (critical risk)")
    print("\nWaiting for MCP requests on stdin...")

    asyncio.run(server.run_stdio())
```

### Step 5.2: Test MCP Server Manually

```bash
cd /tmp/owkai-test
source venv/bin/activate

# PRODUCTION environment
export OWKAI_API_KEY="owkai_admin_your_actual_key"
export OWKAI_BASE_URL="https://pilot.owkai.app"

# Test initialization
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python acme_mcp_server.py

# Test tools/list
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python acme_mcp_server.py

# Test low-risk tool (list_users)
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_users","arguments":{}}}' | python acme_mcp_server.py

# Test high-risk tool (delete_user)
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"delete_user","arguments":{"user_id":1,"reason":"test"}}}' | python acme_mcp_server.py
```

### Step 5.3: Configure Claude Desktop (Optional)

If you have Claude Desktop installed:

1. Open Claude Desktop config:
   ```bash
   # macOS
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add the MCP server:
   ```json
   {
     "mcpServers": {
       "acme-database": {
         "command": "python",
         "args": ["/tmp/owkai-test/acme_mcp_server.py"],
         "env": {
           "OWKAI_API_KEY": "owkai_admin_your_key_here",
           "OWKAI_BASE_URL": "https://pilot.owkai.app"
         }
       }
     }
   }
   ```

3. Restart Claude Desktop

4. Try asking Claude:
   - "List all users in the database" (should work)
   - "Delete user with ID 1" (should require approval or block)
   - "Drop the users table" (should be blocked)

---

## PHASE 6: Verify in Dashboard

Open: **https://pilot.owkai.app**

### Step 6.1: Check Action History

Navigate to: **Authorization Center > Activity Log**

Verify you see:
- [ ] Actions from test agent
- [ ] Actions from MCP server
- [ ] Correct decisions (ALLOW, DENY, REQUIRE_APPROVAL)
- [ ] Risk scores

### Step 6.2: Check Pending Approvals

Navigate to: **Authorization Center > Pending Actions**

If there are pending items:
1. Review the action details
2. Check risk assessment
3. Click Approve or Reject
4. Verify the agent/MCP server receives the decision

### Step 6.3: Review Audit Log

Navigate to: **Settings > Audit Log**

Verify:
- [ ] All actions are logged
- [ ] Timestamps are correct
- [ ] User/agent attribution is accurate

---

## PHASE 7: Test Error Scenarios

### Step 7.1: Test Network Failure (Fail-Closed)

```bash
# Point to invalid URL to simulate network failure
cd /tmp/owkai-test
export OWKAI_BASE_URL="https://invalid.owkai.app"
python test_agent.py

# Expected: GovernanceUnavailableError
# Actions should NOT execute (fail-closed)
```

### Step 7.2: Test Invalid API Key

```bash
export OWKAI_API_KEY="invalid_key_12345"
python test_agent.py

# Expected: Authentication error
```

### Step 7.3: Test Approval Timeout

1. Set short timeout in client: `approval_timeout=10`
2. Run action that requires approval
3. Do NOT approve in dashboard
4. Verify: ApprovalTimeoutError after 10 seconds
5. Verify: Action did NOT execute

---

## Summary Checklist

### Customer Onboarding
- [ ] Organization created successfully
- [ ] Cognito pool provisioned
- [ ] Admin user can log in
- [ ] Password change works

### Governance Configuration
- [ ] Can create policies via UI
- [ ] Policies apply correctly
- [ ] Can view policies via API

### SDK Integration
- [ ] API key generated
- [ ] EnforcedClient initializes
- [ ] Low-risk actions auto-approve
- [ ] High-risk actions require approval
- [ ] Policy-blocked actions are denied
- [ ] Fail-closed works (network errors block)

### MCP Server Integration
- [ ] Server starts without errors
- [ ] tools/list returns registered tools
- [ ] Low-risk tools execute
- [ ] High-risk tools go through governance
- [ ] Critical tools are blocked
- [ ] Claude Desktop integration (optional)

### Dashboard Verification
- [ ] Action history shows all actions
- [ ] Pending approvals are visible
- [ ] Approve/Reject works
- [ ] Audit log is complete

---

## Troubleshooting

### "Connection refused" Error
```bash
# Check production health
curl -s https://pilot.owkai.app/health | jq

# If production is down, check ECS service status
aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service
```

### "Authentication failed" Error
- Verify API key is correct
- Check API key has proper permissions
- Ensure key hasn't expired

### "Module not found" Error
```bash
# Ensure SDK is in path
export PYTHONPATH="/Users/mac_001/OW_AI_Project/owkai-sdk:$PYTHONPATH"
```

### Actions Not Being Blocked
- Check policies are active
- Verify policy conditions match action
- Review action details in dashboard

---

## Clean Up

After testing:

```bash
# Remove test files
rm -rf /tmp/owkai-test

# (Optional) Delete test organization from database
# Be careful with this in production!
```

---

**Happy Testing!**

If you encounter any issues, check:
1. Production logs: `aws logs tail /ecs/owkai-pilot-backend --follow`
2. Dashboard for error messages: https://pilot.owkai.app
3. Network tab in browser dev tools
4. ECS service status: `aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service`
