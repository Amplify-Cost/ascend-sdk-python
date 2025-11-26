# OW-AI Enterprise Integration Examples

Complete, production-ready examples showing how to integrate OW-AI governance into your AI agent and automation infrastructure.

## Quick Start

```bash
# Set your OW-AI API key
export OWKAI_API_KEY="owkai_admin_your_key_here"
export OWKAI_BASE_URL="https://pilot.owkai.app"

# Run any example
python 01_langchain_agent.py
```

---

## Example 1: LangChain Agent (`01_langchain_agent.py`)

**Use Case:** AI agents using LangChain/LlamaIndex that execute tools (database queries, file operations, API calls).

**Key Features:**
- Wrap any LangChain tool with governance
- Risk assessment before execution
- Approval workflow integration
- Works with GPT-4, Claude, or any LLM

**Architecture:**
```
User Request → LangChain Agent → Governed Tool → OW-AI → Execute if Approved
```

**Example:**
```python
from owkai import OWKAIClient

client = OWKAIClient(api_key="owkai_admin_...")

# Before executing any tool action
result = client.execute_action(
    action_type="database_write",
    description="UPDATE users SET role='admin'",
    tool_name="postgresql"
)

if result.requires_approval:
    status = client.wait_for_approval(result.action_id)
```

---

## Example 2: AWS Lambda (`02_aws_lambda.py`)

**Use Case:** Serverless functions making AWS API calls (S3, EC2, RDS, IAM) with transparent governance.

**Key Features:**
- Zero code changes to existing boto3 code
- Automatic risk classification by AWS operation
- Auto-approve low-risk, block high-risk
- Works with any Lambda runtime

**Architecture:**
```
Lambda Trigger → Lambda Function → boto3 (patched) → OW-AI → AWS API
```

**Example:**
```python
from owkai.boto3_patch import enable_governance
enable_governance(api_key="owkai_admin_...")

import boto3
s3 = boto3.client('s3')

# Low risk - auto-approved
s3.get_object(Bucket='data', Key='file.csv')

# High risk - requires approval
s3.delete_bucket(Bucket='production-backup')  # Blocks until approved
```

**Risk Levels:**
| Operation | Risk | Score |
|-----------|------|-------|
| `list_*`, `get_*`, `describe_*` | LOW | 15-30 |
| `put_object`, `create_*` | MEDIUM | 40-60 |
| `delete_object`, `modify_*` | HIGH | 70-85 |
| `delete_bucket`, `terminate_instances` | CRITICAL | 90-100 |

---

## Example 3: MCP Server (`03_mcp_server.py`)

**Use Case:** Model Context Protocol (MCP) servers that need governance for tool execution by Claude and other LLM clients.

**Key Features:**
- Full MCP protocol implementation
- Per-tool risk classification
- Async approval support
- Claude Desktop compatible

**Architecture:**
```
Claude Desktop → MCP Protocol → MCP Server → OW-AI Governance → Tool Execution
```

**Available Tools:**
| Tool | Risk Level | Description |
|------|------------|-------------|
| `query_database` | Varies | Execute SQL queries |
| `read_file` | Low | Read filesystem |
| `write_file` | Medium | Write filesystem |
| `call_api` | Medium | HTTP API calls |
| `run_command` | High | Shell commands |

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "enterprise-tools": {
      "command": "python",
      "args": ["/path/to/03_mcp_server.py"]
    }
  }
}
```

**Run Tests:**
```bash
python 03_mcp_server.py --test
```

---

## Example 4: FastAPI Middleware (`04_fastapi_middleware.py`)

**Use Case:** API backend that needs to govern requests from AI agents vs human users.

**Key Features:**
- Automatic agent detection via headers
- Risk-based endpoint classification
- Sync approval with timeout
- Compliance headers in response

**Architecture:**
```
Agent Request → FastAPI → Governance Middleware → OW-AI → Route Handler
                              ↓
                    X-Governance-Status: approved
                    X-Risk-Level: medium
                    X-Action-ID: 12345
```

**Agent Request Headers:**
```
X-Agent-ID: your-agent-id       # Identifies as agent (triggers governance)
X-Bypass-Governance: secret     # For trusted service accounts
```

**Endpoint Risk Mapping:**
```
GET /api/*           → LOW (auto-approve)
POST /api/*          → MEDIUM (evaluate)
DELETE /api/*        → HIGH (requires approval)
POST /api/admin/*    → CRITICAL (executive approval)
```

**Run Server:**
```bash
python 04_fastapi_middleware.py
# Server starts on http://localhost:8000

# Test agent request
curl -H "X-Agent-ID: test-agent" http://localhost:8000/api/users
```

---

## Example 5: Automation & Cron Jobs (`05_automation_cron.py`)

**Use Case:** Scheduled tasks (cron, Airflow, Jenkins) that need governance for database maintenance, backups, data exports.

**Key Features:**
- Multiple governance modes (sync, async, fail-fast)
- Batch action submission
- Compliance reporting
- Cron-friendly CLI interface

**Governance Modes:**

| Mode | Behavior | Best For |
|------|----------|----------|
| `sync` | Wait for approval (blocking) | Critical operations |
| `async` | Queue and continue | Non-urgent batch jobs |
| `fail_fast` | Abort if approval needed | CI/CD pipelines |
| `pre_approved` | Check maintenance window | Regular maintenance |

**Tasks Included:**
- `database_cleanup` - Delete old records (HIGH risk)
- `log_rotation` - Rotate log files (MEDIUM risk)
- `backup_verification` - Verify backups (LOW risk)
- `data_export` - Export data (HIGH risk)
- `security_scan` - Vulnerability scan (MEDIUM risk)

**Run Examples:**
```bash
# All tasks in sync mode
python 05_automation_cron.py --tasks all --mode sync

# Specific tasks in async mode
python 05_automation_cron.py --tasks database_cleanup,log_rotation --mode async

# CI/CD friendly (abort if approval needed)
python 05_automation_cron.py --tasks backup_verification --mode fail_fast
```

**Crontab Example:**
```cron
# Daily log rotation at 2 AM
0 2 * * * /usr/bin/python /path/to/05_automation_cron.py --tasks log_rotation --mode async

# Weekly database cleanup (Sunday 3 AM)
0 3 * * 0 /usr/bin/python /path/to/05_automation_cron.py --tasks database_cleanup --mode sync
```

---

## Common Configuration

All examples use these environment variables:

```bash
# Required
export OWKAI_API_KEY="owkai_admin_your_key_here"

# Optional (defaults shown)
export OWKAI_BASE_URL="https://pilot.owkai.app"
export SYNC_APPROVAL_TIMEOUT="300"  # seconds

# For LangChain example
export OPENAI_API_KEY="sk-..."

# For automation example
export AUTOMATION_AGENT_ID="scheduled-automation-agent"
```

---

## Integration Flow

All examples follow this governance flow:

```
1. SUBMIT    → Client sends action details to OW-AI
2. ASSESS    → OW-AI calculates risk (0-100) using CVSS, NIST, MITRE
3. ROUTE     → Based on risk score:
               • 0-30:   Auto-approve
               • 31-70:  Level 1 approval
               • 71-85:  Level 2 approval
               • 86-100: Level 3 executive approval
4. DECIDE    → Approver reviews in dashboard
5. EXECUTE   → Client proceeds if approved
6. AUDIT     → Everything logged for compliance
```

---

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/authorization/agent-action` | Submit action |
| `GET /api/agent-action/status/{id}` | Check approval status |
| `POST /mcp/governance/evaluate` | MCP action evaluation |

---

## Support

- **Documentation:** https://docs.owkai.app
- **Support Email:** support@owkai.com
- **Enterprise Support:** Contact your account manager

---

*OW-AI Enterprise - Governing AI Actions at Enterprise Scale*
