---
sidebar_position: 1
title: Dashboard
description: Overview of the Ascend dashboard and key metrics
---

# Dashboard

The Ascend Dashboard provides a real-time overview of your AI governance operations, displaying key metrics, recent activity, and quick actions.

## Overview

The dashboard serves as your central command center for monitoring AI agent activity across your organization. All data is fetched in real-time from backend APIs with multi-tenant isolation.

**Source**: `owkai-pilot-frontend/src/components/Dashboard.jsx`

## Key Metrics

The dashboard displays four primary metric cards:

| Metric | Description | Update Frequency |
|--------|-------------|------------------|
| **Total Actions** | Number of agent actions processed | Real-time |
| **Pending Approvals** | Actions awaiting human review | Real-time |
| **Risk Score** | Average risk across all actions | 30 seconds |
| **Active Agents** | Currently registered and active agents | Real-time |

### Metric Card Features

Each metric card includes:
- **Current Value**: The primary metric number
- **Trend Indicator**: Shows increase (↗), decrease (↘), or stable (→)
- **Sparkline Chart**: Mini trend visualization for the last 24 hours
- **Color Coding**: Blue for info, green for positive, red for alerts

## Activity Feed

The Recent Activities panel shows the latest governance events:

```
┌─────────────────────────────────────────────────────┐
│ 🔍 Recent Activities                                │
├─────────────────────────────────────────────────────┤
│ ⚠️ High-risk action detected                        │
│    5 minutes ago • financial-advisor-001            │
├─────────────────────────────────────────────────────┤
│ ✅ Action approved                                  │
│    12 minutes ago • data-analyzer-002               │
├─────────────────────────────────────────────────────┤
│ 🔍 New action submitted                             │
│    15 minutes ago • customer-service-agent          │
└─────────────────────────────────────────────────────┘
```

### Activity Types

| Icon | Type | Description |
|------|------|-------------|
| ⚠️ | Alert | High-risk action requiring attention |
| ✅ | Approval | Action was approved |
| 🔍 | Action | New action submitted for review |

## Quick Actions

The dashboard provides quick access to common tasks:

| Action | Icon | Description | Access |
|--------|------|-------------|--------|
| **Admin Tools** | 🛠️ | Access enterprise settings | Admin only |
| **Alerts** | 🚨 | View active alerts | Admin only |
| **Generate Rule** | ⚡ | Create new governance rule | Admin only |
| **View Reports** | 📊 | Access analytics and reports | All users |

## Charts and Visualizations

### Actions by Type

A pie chart showing the distribution of action types:
- Database operations
- API calls
- File operations
- System commands

### Risk Trend

A line chart displaying risk scores over time with:
- 24-hour view
- 7-day view
- 30-day view

### Agent Activity

A bar chart comparing activity across registered agents.

## Data Refresh

- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Click the refresh icon in the header
- **Real-time updates**: WebSocket connection for instant alerts

## API Endpoints

The dashboard fetches data from these backend endpoints:

| Endpoint | Method | Description | Source |
|----------|--------|-------------|--------|
| `/api/analytics/trends` | GET | Alert trends | `analytics_routes.py:36` |
| `/api/analytics/realtime/metrics` | GET | Real-time metrics | `analytics_routes.py:209` |
| `/api/agent-activity` | GET | Recent actions | `agent_routes.py` |
| `/api/analytics/executive/dashboard` | GET | Executive metrics | `analytics_routes.py:541` |

## Best Practices

1. **Check daily**: Review the dashboard at the start of each day
2. **Monitor trends**: Watch for sudden spikes in risk scores
3. **Act on alerts**: Address high-priority alerts promptly
4. **Review pending**: Clear pending approvals queue regularly

## Troubleshooting

### Dashboard shows "Loading..."

**Cause**: API connection issue or authentication expired

**Solution**:
1. Check your network connection
2. Refresh the page
3. Log out and log back in if the issue persists

### Metrics show "N/A"

**Cause**: No data available for the selected time period

**Solution**:
1. Verify agents are registered and active
2. Check if actions have been submitted
3. Ensure your organization has activity data

---

*Source: [Dashboard.jsx](https://github.com/owkai/owkai-pilot-frontend/blob/main/src/components/Dashboard.jsx), [analytics_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/analytics_routes.py)*
