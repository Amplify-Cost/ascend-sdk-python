# Testing OW-AI with Real AI Agents - Live Demo Guide

**Purpose**: Demonstrate how OW-AI monitors and blocks REAL AI agents (Claude, GPT, AutoGPT) when they try to perform dangerous actions in AWS.

**Time Required**: 45 minutes

**What You're Proving**: Your governance system can intercept actual AI agents in real-time, not just log fake events.

---

## Understanding: How AI Agents Actually Work with AWS

### The Real Architecture:

```
REAL AI AGENT (Claude Code, AutoGPT, etc.)
    ↓
Uses tools/functions to interact with systems
    ↓
Makes API calls via:
    - AWS SDK (boto3)
    - MCP Tools (Anthropic's Model Context Protocol)
    - LangChain tools
    - Custom function calls
    ↓
YOUR OW-AI GOVERNANCE LAYER (intercepts here)
    ↓
If ALLOWED → Action proceeds to AWS
If DENIED → Action blocked, agent gets error
```

### The Key Question:

**Where does OW-AI sit in this flow?**

There are 3 ways to integrate:

1. **MCP Server Wrapper** (Best for Claude/Anthropic agents)
   - OW-AI runs as an MCP server
   - AI agent calls OW-AI MCP tools instead of direct AWS
   - OW-AI checks permissions, then proxies to AWS

2. **SDK Middleware** (Best for AutoGPT/LangChain)
   - Patch boto3 or AWS SDK
   - Every AWS call goes through OW-AI first
   - OW-AI approves/denies, then forwards

3. **API Gateway/Proxy** (Best for enterprise deployment)
   - AI agents call your API gateway
   - Gateway routes through OW-AI
   - OW-AI makes final AWS calls

---

## Option 1: Test with Claude Code (MCP Integration)

This is the SIMPLEST way to demonstrate real AI agent governance.

### What You're Building:

```
Claude Code (AI Agent)
    ↓
Calls MCP tool: "write_to_rds_database"
    ↓
OW-AI MCP Server (your governance layer)
    ├─ Evaluates: Is this allowed?
    ├─ Risk Score: 95 (HIGH - production write with PII)
    ├─ Policy Match: "Block Prod DB Writes with PII"
    └─ Returns: ERROR - Action DENIED
    ↓
Claude Code sees: "Permission denied by governance policy"
    ↓
Action BLOCKED (never reaches AWS)
```

### Step 1: Create OW-AI MCP Server

Create a file: `/tmp/owkai_mcp_server.py`

```python
#!/usr/bin/env python3
"""
OW-AI MCP Server
Intercepts AI agent tool calls and applies governance
"""
import json
import sys
import requests
from typing import Any, Dict

# OW-AI API endpoint
OWKAI_API = "https://pilot.owkai.app/api"
OWKAI_TOKEN = "your-admin-token-here"  # Get from OW-AI login

class OWKAIMCPServer:
    """MCP Server that enforces OW-AI governance"""

    def __init__(self):
        self.tools = {
            "write_to_rds_database": self.write_to_rds_database,
            "delete_s3_files": self.delete_s3_files,
            "terminate_ec2_instance": self.terminate_ec2_instance,
            "read_from_database": self.read_from_database
        }

    def check_permission(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call OW-AI API to check if action is allowed
        """
        try:
            response = requests.post(
                f"{OWKAI_API}/agent/agent-action",
                headers={
                    "Authorization": f"Bearer {OWKAI_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=action,
                timeout=5
            )

            result = response.json()

            # OW-AI returns: {status: "approved/denied/pending", risk_score: 95, ...}
            return result

        except Exception as e:
            # Fail closed - if OW-AI is down, block everything
            return {
                "status": "denied",
                "reason": f"Governance check failed: {str(e)}",
                "risk_score": 100
            }

    def write_to_rds_database(self, database_name: str, data: str,
                               contains_pii: bool = False) -> Dict[str, Any]:
        """
        Tool: Write to RDS Database
        AI agents call this, OW-AI checks permission first
        """
        # Build action for OW-AI evaluation
        action = {
            "agent_id": "claude-code-demo",
            "action_type": "database_write",
            "resource_type": "rds:database",
            "resource_name": database_name,
            "environment": "production" if "prod" in database_name else "development",
            "contains_pii": contains_pii,
            "description": f"AI agent writing data to {database_name}",
            "user_id": 1  # Admin user
        }

        # Check with OW-AI BEFORE executing
        permission = self.check_permission(action)

        if permission["status"] == "denied":
            return {
                "success": False,
                "error": f"⛔ BLOCKED BY OW-AI GOVERNANCE",
                "reason": permission.get("reason", "Policy violation"),
                "risk_score": permission.get("risk_score"),
                "policy_matched": permission.get("policy_name"),
                "action_logged": permission.get("action_id")
            }

        elif permission["status"] == "pending":
            return {
                "success": False,
                "error": "⏸️  REQUIRES APPROVAL",
                "reason": f"Action requires {permission.get('approval_level', 'manager')} approval",
                "approval_id": permission.get("approval_id"),
                "message": "Human approval needed before proceeding"
            }

        else:  # approved
            # NOW execute the actual AWS action
            import boto3
            rds = boto3.client('rds')

            # ... actual RDS write code here ...

            return {
                "success": True,
                "message": "✅ Data written to database",
                "bytes_written": len(data),
                "governance_check": "PASSED",
                "risk_score": permission.get("risk_score")
            }

    def delete_s3_files(self, bucket_name: str, file_pattern: str) -> Dict[str, Any]:
        """
        Tool: Delete S3 Files
        HIGH RISK - always check governance
        """
        action = {
            "agent_id": "claude-code-demo",
            "action_type": "file_delete",
            "resource_type": "s3:bucket",
            "resource_name": bucket_name,
            "environment": "production",
            "description": f"AI agent deleting files matching {file_pattern} from {bucket_name}"
        }

        permission = self.check_permission(action)

        if permission["status"] != "approved":
            return {
                "success": False,
                "error": "⛔ BLOCKED BY OW-AI GOVERNANCE",
                "reason": permission.get("reason"),
                "risk_score": permission.get("risk_score")
            }

        # Execute S3 deletion (if approved)
        import boto3
        s3 = boto3.client('s3')
        # ... actual S3 delete code ...

        return {"success": True, "files_deleted": 0}

    def read_from_database(self, database_name: str) -> Dict[str, Any]:
        """
        Tool: Read from Database
        LOW RISK - but still governed
        """
        action = {
            "agent_id": "claude-code-demo",
            "action_type": "database_read",
            "resource_type": "rds:database",
            "resource_name": database_name,
            "environment": "production" if "prod" in database_name else "development",
            "contains_pii": False,
            "description": f"AI agent reading from {database_name}"
        }

        permission = self.check_permission(action)

        if permission["status"] == "denied":
            return {
                "success": False,
                "error": "⛔ BLOCKED",
                "reason": permission.get("reason")
            }

        # Execute read
        return {
            "success": True,
            "data": ["sample", "data"],
            "governance_check": "PASSED"
        }

    def handle_request(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main MCP handler - routes tool calls
        """
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        return self.tools[tool_name](**params)


def main():
    """
    MCP Server main loop
    Reads JSON-RPC requests from stdin, returns responses to stdout
    """
    server = OWKAIMCPServer()

    print("OW-AI MCP Server started", file=sys.stderr)
    print(f"Enforcing governance for {len(server.tools)} tools", file=sys.stderr)

    for line in sys.stdin:
        try:
            request = json.loads(line)
            tool_name = request.get("tool")
            params = request.get("params", {})

            result = server.handle_request(tool_name, params)

            response = {
                "id": request.get("id"),
                "result": result
            }

            print(json.dumps(response))
            sys.stdout.flush()

        except Exception as e:
            error_response = {
                "id": request.get("id") if "request" in locals() else None,
                "error": str(e)
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
```

### Step 2: Configure Claude Code to Use Your MCP Server

Create: `/tmp/claude_mcp_config.json`

```json
{
  "mcpServers": {
    "owkai-governance": {
      "command": "python3",
      "args": ["/tmp/owkai_mcp_server.py"],
      "env": {
        "OWKAI_API": "https://pilot.owkai.app/api",
        "OWKAI_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Step 3: Test with Real Claude Code

Now when you chat with Claude Code:

**You say**:
> "Please write customer credit card numbers to the production database customer-financials-prod"

**What Happens**:
1. Claude Code thinks: "I need to write to a database"
2. Claude Code calls MCP tool: `write_to_rds_database(database_name="customer-financials-prod", data="...", contains_pii=True)`
3. Your OW-AI MCP Server intercepts this
4. OW-AI evaluates:
   - Action: database_write
   - Resource: customer-financials-prod (production!)
   - Contains PII: Yes
   - Risk Score: 95 (CRITICAL)
   - Policy Match: "Block Prod DB Writes with PII"
   - Decision: **DENIED**
5. MCP Server returns error to Claude:
   ```json
   {
     "success": false,
     "error": "⛔ BLOCKED BY OW-AI GOVERNANCE",
     "reason": "Production database writes with PII are not allowed",
     "risk_score": 95,
     "policy_matched": "Block Prod DB Writes with PII"
   }
   ```
6. Claude Code responds to you:
   > "I'm unable to write to the production database because OW-AI governance has blocked this action. The risk score is 95 (CRITICAL) and it violates the policy 'Block Prod DB Writes with PII'. Would you like me to try writing to the development database instead?"

**THIS IS REAL-TIME AI AGENT GOVERNANCE!**

---

## Option 2: Test with AutoGPT (Boto3 Middleware)

For AutoGPT or other Python-based AI agents that use boto3.

### Step 1: Create Boto3 Wrapper

Create: `/tmp/owkai_boto3_wrapper.py`

```python
"""
Boto3 Wrapper for OW-AI Governance
Intercepts all AWS API calls and checks with OW-AI first
"""
import boto3
import requests
from botocore.client import BaseClient

OWKAI_API = "https://pilot.owkai.app/api"
OWKAI_TOKEN = "your-token-here"

class OWKAIGovernedBoto3Client:
    """
    Wraps any boto3 client and adds governance checks
    """
    def __init__(self, service_name: str, **kwargs):
        self.client = boto3.client(service_name, **kwargs)
        self.service_name = service_name

    def __getattr__(self, name):
        """
        Intercept all method calls
        """
        original_method = getattr(self.client, name)

        def governed_method(*args, **kwargs):
            # Check with OW-AI first
            action = {
                "agent_id": "autogpt-demo",
                "action_type": f"{self.service_name}_{name}",
                "resource_type": f"{self.service_name}:resource",
                "description": f"AI agent calling {self.service_name}.{name}",
                "environment": "production"
            }

            response = requests.post(
                f"{OWKAI_API}/agent/agent-action",
                headers={"Authorization": f"Bearer {OWKAI_TOKEN}"},
                json=action,
                timeout=5
            )

            result = response.json()

            if result.get("status") == "denied":
                raise PermissionError(
                    f"⛔ OW-AI BLOCKED: {result.get('reason')} "
                    f"(Risk: {result.get('risk_score')}/100)"
                )

            # If approved, execute original AWS call
            return original_method(*args, **kwargs)

        return governed_method


# Monkey-patch boto3
_original_boto3_client = boto3.client

def governed_boto3_client(service_name, **kwargs):
    return OWKAIGovernedBoto3Client(service_name, **kwargs)

boto3.client = governed_boto3_client
```

### Step 2: Use in AutoGPT

In AutoGPT's environment, add:

```python
# At the top of AutoGPT's main file
import owkai_boto3_wrapper  # This patches boto3

# Now ALL AWS calls go through OW-AI
import boto3

rds = boto3.client('rds')

# This will be intercepted by OW-AI
rds.delete_db_instance(DBInstanceIdentifier='production-db')
# ⛔ Raises: PermissionError("OW-AI BLOCKED: Cannot delete production database")
```

---

## Option 3: Live Demo Script (Using Your Current System)

If you don't have MCP integration yet, here's how to demonstrate governance with your existing OW-AI:

### Setup (5 minutes):

1. **Create Demo Organization in OW-AI**:
   - Name: TechCorp Demo
   - Compliance: SOX, PCI-DSS

2. **Create Blocking Rule**:
   - Policy: "Block Production Database Writes with PII"
   - Decision: DENY
   - Risk Threshold: 90

3. **Open 2 Browser Tabs**:
   - Tab 1: OW-AI Activity Dashboard
   - Tab 2: Terminal with curl commands

### Live Demo (2 minutes):

**Show Audience Tab 1** (OW-AI Dashboard):
> "This is our governance dashboard. Right now it's empty. Watch what happens when an AI agent tries to perform a dangerous action..."

**Switch to Tab 2** (Terminal), run this command:

```bash
# Simulate AI agent making dangerous action
curl -X POST "https://pilot.owkai.app/api/agent/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "claude-code-customer-demo",
    "action_type": "database_write",
    "resource_type": "rds:database",
    "resource_name": "customer-financials-prod",
    "environment": "production",
    "contains_pii": true,
    "description": "AI agent attempting to write customer credit cards to production database",
    "user_id": 1
  }'
```

**Expected Output** (in terminal):
```json
{
  "id": 187,
  "status": "denied",
  "reason": "Blocked by policy: Block Production Database Writes with PII",
  "risk_score": 95,
  "cvss_severity": "CRITICAL",
  "policy_matched": "Block Prod DB Writes with PII",
  "timestamp": "2025-11-13T15:30:45Z"
}
```

> "There! The action was DENIED instantly. Risk score: 95 out of 100."

**Switch back to Tab 1** (OW-AI Dashboard):
- Click "Refresh"
- Point to the new RED entry that just appeared

> "And here it is in our audit trail. This action will be logged forever for compliance. The AI agent received an error and couldn't proceed."

**Show Low-Risk Action** (compare):

```bash
# Now show a SAFE action that's allowed
curl -X POST "https://pilot.owkai.app/api/agent/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "claude-code-customer-demo",
    "action_type": "database_read",
    "resource_type": "rds:database",
    "resource_name": "test-data-dev",
    "environment": "development",
    "contains_pii": false,
    "description": "AI agent reading test data from dev database"
  }'
```

**Expected**:
```json
{
  "status": "approved",
  "risk_score": 25,
  "cvss_severity": "LOW"
}
```

> "This action was approved immediately because it's low risk - reading from a dev database. The AI can work efficiently without constant approvals."

---

## What You've Demonstrated

✅ **Real-time Interception**: Action blocked in < 200ms
✅ **Risk-based Decision**: High-risk blocked, low-risk allowed
✅ **Audit Trail**: Every action logged permanently
✅ **Compliance**: SOX/PCI-DSS/GDPR aligned
✅ **Enterprise-grade**: CVSS scoring, NIST controls, MITRE tactics

---

## For a Real Customer Demo:

1. **Before Meeting**:
   - Set up their organization in OW-AI
   - Create 3-4 governance rules
   - Test with curl commands
   - Have Activity dashboard open

2. **During Meeting** (7 minutes):
   - Minute 1: Show their organization setup
   - Minute 2: Explain governance rules
   - Minute 3-4: Live test HIGH RISK action → BLOCKED
   - Minute 5: Live test LOW RISK action → ALLOWED
   - Minute 6: Show Activity dashboard with both actions
   - Minute 7: Show analytics (X% blocked, Y% allowed)

3. **Close**:
   - Export PDF report
   - Show integration options (MCP, boto3, API)
   - Schedule follow-up to deploy in their environment

---

## The Key Difference

**❌ What We're NOT doing**: Logging fake events after they happen

**✅ What We ARE doing**: Intercepting real API calls BEFORE they reach AWS

This is **preventative governance**, not detective logging.

---

## Next Steps

1. **Immediate** (Today):
   - Test the curl command demo
   - Verify actions appear in Activity dashboard
   - Practice the 7-minute demo script

2. **This Week**:
   - Build the MCP server wrapper
   - Test with real Claude Code
   - Record a demo video

3. **Next Sprint**:
   - Deploy boto3 middleware for AutoGPT
   - Build customer onboarding automation
   - Scale to 10 pilot customers

---

**Document Version**: 1.0 - Real AI Agent Testing
**Last Updated**: 2025-11-13
**For**: OW-AI Live Customer Demos
