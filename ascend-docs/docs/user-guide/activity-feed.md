---
sidebar_position: 6
title: Activity Feed
description: Monitor and review agent actions in real-time
---

# Activity Feed

The Enterprise Agent Activity Feed provides comprehensive monitoring of all AI agent actions with CVSS scoring, MITRE ATT&CK mappings, and approval workflow tracking.

## Overview

View all agent actions with detailed security assessments, compliance mappings, and approval status in a unified interface.

**Source**: `owkai-pilot-frontend/src/components/AgentActivityFeed.jsx`

**Compliance**: SOC 2 AU-2, NIST AU-2, PCI-DSS 10.2

## Activity Card

### Activity Information

Each activity displays:

```
┌─────────────────────────────────────────────────────────────┐
│ financial-advisor-001         CVSS: 6.5 (MEDIUM)   PENDING │
├─────────────────────────────────────────────────────────────┤
│ Action Type: database_write                                 │
│ Tool: postgres_connector                                    │
│ Description: Update customer profile with new preferences   │
├─────────────────────────────────────────────────────────────┤
│ 🕐 Dec 7, 2025, 10:30 AM    👤 User ID: usr_123            │
├─────────────────────────────────────────────────────────────┤
│ [▶ Expand Details]  [⚠ Mark False Positive]  [🔁 Replay]   │
└─────────────────────────────────────────────────────────────┘
```

### Basic Fields

| Field | Description |
|-------|-------------|
| `agent_id` | Agent identifier |
| `action_type` | Type of action performed |
| `tool_name` | Tool/connector used |
| `description` | Action description |
| `timestamp` | When action occurred |
| `user_id` | Associated user (if any) |

## Filters

### Available Filters

| Filter | Options |
|--------|---------|
| **Risk Level** | All, High, Medium, Low |
| **Status** | All, Pending, Approved, Denied, In Review |
| **Search** | Agent, tool, or description text |

### Filter Usage

```javascript
// API query with filters
GET /api/v1/actions?risk=high&status=pending
```

## Expanded Details

### Security Assessment Card

| Field | Description | Standard |
|-------|-------------|----------|
| `cvss_score` | CVSS 3.1 score (0.0-10.0) | CVSS v3.1 |
| `cvss_severity` | Severity level | CVSS v3.1 |
| `cvss_vector` | Attack vector string | CVSS v3.1 |
| `risk_score` | Internal risk (0-100) | OW-kai |

### MITRE ATT&CK Mapping

| Field | Description | Example |
|-------|-------------|---------|
| `mitre_tactic` | Attack tactic | Exfiltration |
| `mitre_technique` | Technique ID | T1041 |

### NIST Control Reference

| Field | Description | Example |
|-------|-------------|---------|
| `nist_control` | Control ID | SI-4 |
| `nist_description` | Control name | Information System Monitoring |

### Approval Workflow Card

| Field | Description |
|-------|-------------|
| `status` | Current approval status |
| `current_approval_level` | Current level in workflow |
| `required_approval_level` | Total levels required |
| `approved_by` | Who approved (if applicable) |
| `reviewed_by` | Who reviewed |
| `reviewed_at` | Review timestamp |
| `pending_approvers` | Awaiting approval from |
| `sla_deadline` | Response deadline |

### Target Details Card

| Field | Description |
|-------|-------------|
| `target_system` | Target system name |
| `target_resource` | Target resource path |

### AI Summary

When available, displays AI-generated action summary for quick understanding.

## CVSS Scoring

### Severity Levels

| Score Range | Severity | Color |
|-------------|----------|-------|
| 9.0 - 10.0 | Critical | Red |
| 7.0 - 8.9 | High | Orange |
| 4.0 - 6.9 | Medium | Yellow |
| 0.1 - 3.9 | Low | Green |
| 0.0 | None | Gray |

### CVSS Badge Display

```
CVSS: 6.5 (MEDIUM)
```

Actions without CVSS assessment display "No CVSS" badge.

## Status Badges

| Status | Color | Description |
|--------|-------|-------------|
| **Pending** | Yellow | Awaiting review |
| **Approved** | Green | Action approved |
| **Denied** | Red | Action denied |
| **In Review** | Blue | Under investigation |

## Actions

### Mark as False Positive

1. Click **Mark as False Positive**
2. Action is flagged for model improvement
3. Badge shows "False Positive" indicator

To undo: Click **Unmark False Positive**

### Replay Action

1. Click **Replay Action**
2. Review action parameters
3. Confirm replay in modal
4. Action is re-submitted for processing

## Pagination

Navigate large activity lists:

- **Previous/Next** buttons for sequential navigation
- **Page numbers** for direct access
- **10 items per page** default display

## Upload Agent Logs

Import activity from external sources:

1. Navigate to **Upload Agent Logs** card
2. Select JSON file containing agent actions
3. File is validated and imported
4. Activities appear in feed

### JSON Format

```json
[
  {
    "agent_id": "custom-agent",
    "action_type": "database_read",
    "description": "Query customer records",
    "tool_name": "postgres_connector",
    "timestamp": "2025-01-15T10:30:00Z"
  }
]
```

## Support Integration

Submit issues directly from the activity feed:

1. Navigate to **Need Help?** card
2. Describe your issue
3. Click **Submit Support Request**
4. Confirmation message displayed

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/actions` | GET | List all actions |
| `/api/v1/actions?risk={level}` | GET | Filter by risk |
| `/api/agent-action/false-positive/{id}` | POST | Toggle false positive |
| `/api/v1/actions/upload-json` | POST | Import actions |

**Source**: `ow-ai-backend/routes/actions_v1_routes.py`

## Data Refresh

- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Filter change triggers refresh
- **Real-time**: WebSocket updates for critical actions

## Best Practices

1. **Filter by status**: Focus on pending actions first
2. **Review high-risk items**: Prioritize by CVSS score
3. **Use search**: Find specific agents or tools quickly
4. **Check compliance mappings**: MITRE/NIST references for context
5. **Flag false positives**: Improve model accuracy over time

## Troubleshooting

### Activity not loading

**Solution**: Check authentication; verify API connectivity.

### Filters not working

**Solution**: Clear search term; reset to "All" options.

### CVSS scores missing

**Solution**: Not all actions have CVSS assessment; risk_score provides internal scoring.

### Pagination stuck

**Solution**: Reset currentPage by changing filters.

---

*Source: [AgentActivityFeed.jsx](https://github.com/owkai/owkai-pilot-frontend/blob/main/src/components/AgentActivityFeed.jsx), [actions_v1_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/actions_v1_routes.py)*
