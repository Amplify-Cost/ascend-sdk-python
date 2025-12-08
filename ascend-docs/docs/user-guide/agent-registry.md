---
sidebar_position: 2
title: Agent Registry
description: Register, configure, and manage AI agents
---

# Agent Registry

The Agent Registry is your central hub for managing all AI agents in your organization. Register new agents, configure risk thresholds, and control agent permissions.

## Overview

The Agent Registry provides enterprise-grade agent lifecycle management with banking-level security controls.

**Source**: `owkai-pilot-frontend/src/components/AgentRegistryManagement.jsx` (SEC-024)

**Compliance**: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2

## Getting Started

### Accessing the Registry

1. Navigate to **Agent Registry** in the sidebar
2. View registered agents in the **Agents** tab
3. View MCP servers in the **MCP Servers** tab

## Registering a New Agent

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `agent_id` | Unique identifier | `financial-advisor-001` |
| `display_name` | Human-readable name | `Financial Advisor AI` |
| `description` | Agent purpose | `Handles investment queries` |
| `agent_type` | Supervision level | `supervised` or `autonomous` |

### Risk Configuration

Configure risk thresholds for each agent:

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| `default_risk_score` | Base risk for actions | 50 | 0-100 |
| `auto_approve_below` | Auto-approve threshold | 30 | 0-100 |
| `max_risk_threshold` | Maximum allowed risk | 80 | 0-100 |
| `requires_mfa_above` | MFA requirement threshold | 70 | 0-100 |

### Autonomous Agent Thresholds (SEC-106c)

Autonomous agents have stricter defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `autonomous_auto_approve_below` | 20 | Lower auto-approve threshold |
| `autonomous_max_risk_threshold` | 60 | Lower maximum risk |

## Agent Configuration

### Permissions & Restrictions

```javascript
{
  "allowed_action_types": ["database_read", "api_read", "query"],
  "allowed_resources": "*.read,public.*",
  "blocked_resources": "*.pii,*.financial",
  "alert_on_high_risk": true,
  "alert_recipients": "security@company.com",
  "webhook_url": "https://slack.webhook.url"
}
```

### Enterprise Action Types (SEC-060)

Actions are classified by risk level:

#### Critical Risk
| Action | NIST Control | MITRE ATT&CK |
|--------|--------------|--------------|
| `database_write` | AC-3 | T1003 |
| `database_delete` | AC-3 | T1485 |
| `privilege_escalation` | AC-6 | T1078 |
| `encryption_key_access` | SC-12 | T1552.004 |
| `firewall_modify` | SC-7 | T1562.004 |

#### High Risk
| Action | NIST Control | MITRE ATT&CK |
|--------|--------------|--------------|
| `pii_access` | AC-3 | T1213 |
| `phi_access` | AC-3 | T1213 |
| `file_write` | AC-3 | T1485 |
| `config_modify` | CM-3 | T1098 |

#### Medium Risk
| Action | NIST Control |
|--------|--------------|
| `database_read` | AU-2 |
| `file_read` | AU-2 |
| `api_read` | AU-2 |

#### Low Risk
| Action | Description |
|--------|-------------|
| `query` | Read-only queries |
| `analytics` | Analytics access |

## Governance Controls (SEC-072)

### Rate Limits

| Setting | Description | Compliance |
|---------|-------------|------------|
| `max_actions_per_minute` | Actions/minute limit | SOC 2 CC6.2, NIST SI-4 |
| `max_actions_per_hour` | Actions/hour limit | SOC 2 CC6.2 |
| `max_actions_per_day` | Daily action limit | SOC 2 CC6.2 |

### Budget Controls

| Setting | Description | Compliance |
|---------|-------------|------------|
| `max_daily_budget_usd` | Daily spending limit | PCI-DSS 7.1, SOC 2 A1.1 |
| `budget_alert_threshold_percent` | Alert at percentage | Default: 80% |
| `auto_suspend_on_budget_exceeded` | Auto-suspend toggle | Default: true |

### Time Windows

Restrict agent operation to specific hours:

| Setting | Description | Example |
|---------|-------------|---------|
| `time_window_enabled` | Enable time restrictions | `true` |
| `time_window_start` | Start time | `09:00` |
| `time_window_end` | End time | `17:00` |
| `time_window_timezone` | Timezone | `America/New_York` |
| `time_window_days` | Allowed days (0=Sun) | `[1,2,3,4,5]` |

### Data Classifications

Control access to sensitive data:

| Classification | Description | Compliance |
|----------------|-------------|------------|
| `public` | Public data | - |
| `internal` | Internal use only | SOC 2 |
| `confidential` | Confidential data | SOC 2, NIST |
| `pii` | Personal data | GDPR, HIPAA |
| `phi` | Health data | HIPAA 164.312 |
| `pci` | Payment data | PCI-DSS 3.4 |

## MCP Server Integration

Register Model Context Protocol (MCP) servers:

### MCP Server Fields

| Field | Description |
|-------|-------------|
| `server_name` | Unique identifier |
| `display_name` | Human-readable name |
| `server_url` | MCP server endpoint |
| `transport_type` | `stdio` or `http` |
| `governance_enabled` | Enable governance |

### MCP Governance Settings

```javascript
{
  "auto_approve_tools": "read_file,list_directory",
  "blocked_tools": "delete_file,execute_command",
  "tool_risk_overrides": {
    "write_file": { "risk_score": 75 }
  }
}
```

## Agent Actions

### Activate Agent

1. Select agent from list
2. Click **Activate**
3. Confirm activation

**Audit Trail**: All activations logged with timestamp and user.

### Suspend Agent

1. Select agent
2. Click **Suspend**
3. Provide reason (optional)

### Emergency Suspend

For immediate security response:

1. Click **Emergency Suspend**
2. Provide justification (required)
3. Type agent ID to confirm

**Note**: Emergency suspensions trigger security team alerts.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent-registry/agents` | GET | List all agents |
| `/api/agent-registry/agents` | POST | Register new agent |
| `/api/agent-registry/agents/{id}` | GET | Get agent details |
| `/api/agent-registry/agents/{id}` | PUT | Update agent |
| `/api/agent-registry/agents/{id}/activate` | POST | Activate agent |
| `/api/agent-registry/agents/{id}/suspend` | POST | Suspend agent |

**Source**: `ow-ai-backend/routes/agent_registry_routes.py`

## Best Practices

1. **Use descriptive IDs**: Include team and purpose in agent_id
2. **Start conservative**: Use low auto-approve thresholds initially
3. **Enable time windows**: Restrict autonomous agents to business hours
4. **Set budget limits**: Always configure daily spending limits
5. **Review regularly**: Audit agent permissions monthly

---

*Source: [AgentRegistryManagement.jsx](https://github.com/owkai/owkai-pilot-frontend/blob/main/src/components/AgentRegistryManagement.jsx), [agent_registry_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/agent_registry_routes.py)*
