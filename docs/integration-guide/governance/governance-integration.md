---
title: SDK Governance Integration
sidebar_position: 1
---

# SDK Governance Integration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-GOV-002 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

This guide explains how to integrate Ascend's verified enterprise governance features into your AI agents using the REST API.

## Prerequisites

- API key with governance permissions
- Registered agent in [Ascend Dashboard](https://pilot.owkai.app)
- Backend services: Circuit Breaker, Anomaly Detection, Policy Resolver (SEC-077)

## API Authentication

All SDK calls use API key authentication:

```bash
# API key authentication
curl -X GET https://pilot.owkai.app/api/governance/circuits \
  -H "Authorization: Bearer owkai_your_api_key"

# Or using X-API-Key header
curl -X GET https://pilot.owkai.app/api/governance/circuits \
  -H "X-API-Key: owkai_your_api_key"
```

**Source**: `/ow-ai-backend/routes/api_key_routes.py` (SEC-018)

---

## Circuit Breaker Integration

Monitor and respond to circuit breaker states for MCP servers.

### Check Circuit Status

**Endpoint**: `GET /api/governance/circuits/{server_id}`

```python
import requests

def check_circuit_status(server_id: str, api_key: str) -> dict:
    """Check if circuit breaker allows requests to MCP server."""
    response = requests.get(
        f"https://pilot.owkai.app/api/governance/circuits/{server_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code == 200:
        data = response.json()
        # Response structure from circuit_breaker_service.py (lines 302-360)
        return {
            "state": data["state"],              # CLOSED, OPEN, HALF_OPEN
            "failure_count": data["failure_count"],
            "last_failure": data["last_failure_time"],
            "can_request": data["state"] != "OPEN"
        }

    raise Exception(f"Circuit check failed: {response.status_code}")

# Usage
status = check_circuit_status("mcp-production-001", "owkai_your_key")

if status["state"] == "OPEN":
    print(f"Circuit OPEN - blocking requests (failures: {status['failure_count']})")
    # Fallback to alternative service or queue for retry
elif status["state"] == "HALF_OPEN":
    print("Circuit testing recovery - limited requests allowed")
else:
    print("Circuit CLOSED - healthy")
```

**Backend Implementation**: `/ow-ai-backend/services/circuit_breaker_service.py` (SEC-077, lines 171-238)

### Record MCP Call Results

```python
def execute_with_circuit_breaker(server_id: str, api_key: str):
    """Execute MCP call with circuit breaker tracking."""

    # Check circuit before making call
    status = check_circuit_status(server_id, api_key)

    if not status["can_request"]:
        raise CircuitBreakerOpenError(f"Circuit open for {server_id}")

    try:
        # Make MCP call
        result = call_mcp_server(server_id)

        # Circuit breaker service automatically tracks success
        # (via MCP server response monitoring)
        return result

    except Exception as e:
        # Circuit breaker service automatically tracks failure
        # (via MCP server error monitoring)

        # Re-check circuit after failure
        updated_status = check_circuit_status(server_id, api_key)

        if updated_status["state"] == "OPEN":
            # Circuit just opened - log incident
            print(f"Circuit opened after failure: {e}")

        raise
```

### Get All Circuit States

**Endpoint**: `GET /api/governance/circuits`

```python
def get_all_circuits(api_key: str) -> list:
    """Get status of all MCP server circuit breakers."""
    response = requests.get(
        "https://pilot.owkai.app/api/governance/circuits",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    circuits = response.json()["circuits"]

    # Identify unhealthy servers
    open_circuits = [c for c in circuits if c["state"] == "OPEN"]

    if open_circuits:
        print(f"WARNING: {len(open_circuits)} circuits are OPEN")
        for circuit in open_circuits:
            print(f"  - {circuit['server_id']}: {circuit['failure_count']} failures")

    return circuits
```

---

## Anomaly Detection Integration

Detect and respond to unusual agent behavior patterns.

### Check Agent Anomalies

**Endpoint**: `GET /api/governance/anomalies/{agent_id}`

```python
def check_agent_anomalies(agent_id: str, api_key: str) -> dict:
    """Check for anomalous behavior in agent."""
    response = requests.get(
        f"https://pilot.owkai.app/api/governance/anomalies/{agent_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    data = response.json()

    # Response structure from anomaly_detection_service.py (lines 72-186)
    return {
        "has_anomalies": data["has_anomalies"],
        "anomalies": data["anomalies"],          # List of detected anomalies
        "consecutive_count": data["consecutive_anomalies"],
        "max_severity": data["max_severity"],     # LOW, MEDIUM, HIGH, CRITICAL
        "auto_suspended": data.get("auto_suspended", False)
    }

# Usage
anomaly_status = check_agent_anomalies("agent-001", "owkai_your_key")

if anomaly_status["has_anomalies"]:
    severity = anomaly_status["max_severity"]

    if severity == "CRITICAL":
        print("CRITICAL ANOMALY - Agent may be auto-suspended")
        # Immediate escalation

    elif severity == "HIGH":
        print("HIGH SEVERITY - Requires immediate review")
        # Enable enhanced approval mode

    elif severity == "MEDIUM":
        print("MEDIUM SEVERITY - Alert sent to security team")

    else:  # LOW
        print("LOW SEVERITY - Logged for review")
```

**Backend Implementation**: `/ow-ai-backend/services/anomaly_detection_service.py` (SEC-077, lines 72-186)

### Anomaly-Aware Action Execution

```python
def execute_with_anomaly_check(
    agent_id: str,
    action_type: str,
    resource: str,
    api_key: str
):
    """Execute action with pre-flight anomaly check."""

    # Check for anomalous behavior
    anomaly_status = check_agent_anomalies(agent_id, api_key)

    # Adjust risk posture based on anomalies
    require_approval = False

    if anomaly_status["consecutive_count"] >= 2:
        print(f"Agent showing consecutive anomalies - requiring approval")
        require_approval = True

    # Execute action with policy evaluation
    decision = evaluate_policy(
        action_type=action_type,
        resource=resource,
        api_key=api_key,
        context={
            "anomaly_status": anomaly_status["max_severity"],
            "consecutive_anomalies": anomaly_status["consecutive_count"],
            "force_approval": require_approval
        }
    )

    return decision
```

### Webhook Handler for Anomaly Alerts

```python
from flask import Flask, request

app = Flask(__name__)

@app.post("/webhooks/ascend")
def handle_ascend_webhook():
    """Handle anomaly alerts from Ascend."""
    payload = request.json

    if payload["event"] == "anomaly.detected":
        agent_id = payload["data"]["agent_id"]
        severity = payload["data"]["severity"]
        metric = payload["data"]["metric"]
        z_score = payload["data"]["z_score"]

        print(f"Anomaly detected: {agent_id} - {metric} (z={z_score})")

        if severity == "CRITICAL":
            # Agent may be auto-suspended
            pause_agent_operations(agent_id)
            notify_security_team({
                "agent_id": agent_id,
                "metric": metric,
                "z_score": z_score,
                "auto_suspended": payload["data"].get("auto_suspended", False)
            })

        elif severity == "HIGH":
            # Enable enhanced approval mode
            enable_enhanced_approval(agent_id)
            alert_ops_team(payload["data"])

    return {"status": "processed"}
```

---

## Policy Evaluation

Evaluate actions against governance policies with conflict resolution.

### Evaluate Policy Decision

**Endpoint**: `POST /api/governance/policies/evaluate`

```python
def evaluate_policy(
    action_type: str,
    resource: str,
    api_key: str,
    context: dict = None
) -> dict:
    """Evaluate action against governance policies."""
    response = requests.post(
        "https://pilot.owkai.app/api/governance/policies/evaluate",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "action_type": action_type,
            "resource": resource,
            "context": context or {}
        }
    )

    data = response.json()

    # Response from cedar_enforcement_service.py (lines 128-318)
    return {
        "decision": data["decision"],              # ALLOW, DENY, REQUIRE_APPROVAL
        "policies_triggered": data["policies"],    # Which policies matched
        "conflict_detected": data.get("conflict_detected", False),
        "resolution_strategy": data.get("resolution_strategy"),
        "risk_score": data.get("risk_score", 0)
    }

# Usage
decision = evaluate_policy(
    action_type="database.write",
    resource="production_db",
    api_key="owkai_your_key",
    context={
        "user_role": "developer",
        "time_of_day": "business_hours"
    }
)

if decision["decision"] == "ALLOW":
    if decision["conflict_detected"]:
        print(f"Allowed with conflicts resolved via: {decision['resolution_strategy']}")
    execute_action()

elif decision["decision"] == "DENY":
    print(f"Denied by policies: {decision['policies_triggered']}")
    raise PolicyDenialError("Action blocked by governance policy")

elif decision["decision"] == "REQUIRE_APPROVAL":
    approval_id = request_approval(action_type, resource)
    wait_for_approval(approval_id)
```

**Backend Implementation**: `/ow-ai-backend/services/cedar_enforcement_service.py` (lines 128-318)

### Detect Policy Conflicts

**Endpoint**: `GET /api/governance/policies/conflicts`

```python
def detect_policy_conflicts(api_key: str) -> list:
    """Scan all policies for conflicts."""
    response = requests.get(
        "https://pilot.owkai.app/api/governance/policies/conflicts",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    conflicts = response.json()["conflicts"]

    # Conflict types from policy_conflict_resolver.py (lines 28-34)
    critical_conflicts = [
        c for c in conflicts
        if c["conflict_type"] == "EFFECT_CONTRADICTION"
    ]

    if critical_conflicts:
        print(f"CRITICAL: {len(critical_conflicts)} contradictory policies found")
        for conflict in critical_conflicts:
            print(f"  Policy {conflict['policy_a_id']} (ALLOW) vs "
                  f"Policy {conflict['policy_b_id']} (DENY)")

    return conflicts
```

**Backend Implementation**: `/ow-ai-backend/services/policy_conflict_resolver.py` (SEC-077, lines 78-120)

---

## Error Handling

### Comprehensive Error Handler

```python
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker blocks request."""
    pass

class AnomalyDetectedError(Exception):
    """Raised when critical anomaly detected."""
    pass

class PolicyDenialError(Exception):
    """Raised when policy denies action."""
    pass

def governed_action(
    agent_id: str,
    server_id: str,
    action_type: str,
    resource: str,
    api_key: str
):
    """Execute action with comprehensive governance checks."""

    try:
        # 1. Circuit Breaker Check
        circuit = check_circuit_status(server_id, api_key)
        if not circuit["can_request"]:
            raise CircuitBreakerOpenError(f"Circuit open for {server_id}")

        # 2. Anomaly Detection Check
        anomaly = check_agent_anomalies(agent_id, api_key)
        if anomaly["auto_suspended"]:
            raise AnomalyDetectedError(f"Agent {agent_id} auto-suspended")

        # 3. Policy Evaluation
        decision = evaluate_policy(action_type, resource, api_key, context={
            "anomaly_severity": anomaly["max_severity"],
            "circuit_state": circuit["state"]
        })

        if decision["decision"] == "DENY":
            raise PolicyDenialError(f"Denied by policies: {decision['policies_triggered']}")

        # Execute action
        result = execute_action(action_type, resource)
        return result

    except CircuitBreakerOpenError as e:
        print(f"Circuit breaker blocked: {e}")
        # Queue for retry or use fallback service
        return queue_for_retry(action_type, resource)

    except AnomalyDetectedError as e:
        print(f"Anomaly detected: {e}")
        # Escalate to security team
        notify_security_team(agent_id, action_type)
        raise

    except PolicyDenialError as e:
        print(f"Policy denial: {e}")
        # Log denial for audit
        log_policy_denial(agent_id, action_type, resource)
        raise
```

---

## Monitoring Integration

### Health Check Dashboard

```python
def get_governance_health(api_key: str) -> dict:
    """Get comprehensive governance health status."""

    # Check all circuit breakers
    circuits = get_all_circuits(api_key)
    open_circuits = [c for c in circuits if c["state"] == "OPEN"]

    # Check for policy conflicts
    conflicts = detect_policy_conflicts(api_key)
    critical_conflicts = [
        c for c in conflicts
        if c["conflict_type"] == "EFFECT_CONTRADICTION"
    ]

    return {
        "healthy": len(open_circuits) == 0 and len(critical_conflicts) == 0,
        "circuits": {
            "total": len(circuits),
            "open": len(open_circuits),
            "health_percentage": (len(circuits) - len(open_circuits)) / len(circuits) * 100
        },
        "policies": {
            "total_conflicts": len(conflicts),
            "critical_conflicts": len(critical_conflicts)
        }
    }

# Usage
health = get_governance_health("owkai_your_key")

if not health["healthy"]:
    print("GOVERNANCE HEALTH ISSUE:")
    print(f"  - Open circuits: {health['circuits']['open']}")
    print(f"  - Critical conflicts: {health['policies']['critical_conflicts']}")
```

---

## Implementation Verification

All governance APIs documented here are backed by verified services:

| Feature | Backend Service | Lines | API Endpoint |
|---------|----------------|-------|--------------|
| Circuit Breaker | `circuit_breaker_service.py` | 456 | `/api/governance/circuits` |
| Anomaly Detection | `anomaly_detection_service.py` | 522 | `/api/governance/anomalies` |
| Policy Resolver | `policy_conflict_resolver.py` | 465 | `/api/governance/policies/conflicts` |
| Policy Enforcement | `cedar_enforcement_service.py` | 321 | `/api/governance/policies/evaluate` |

**Total Backend**: 1,764 lines of verified governance logic (SEC-077)

---

## Best Practices

### 1. Always Check Circuit Breakers Before Expensive Calls

```python
# GOOD: Check circuit before calling MCP server
circuit = check_circuit_status(server_id, api_key)
if circuit["can_request"]:
    result = call_mcp_server(server_id)

# BAD: Call without checking (may fail immediately)
result = call_mcp_server(server_id)  # Circuit may be OPEN
```

### 2. Implement Anomaly-Aware Risk Adjustment

```python
# GOOD: Adjust behavior based on anomaly status
anomaly = check_agent_anomalies(agent_id, api_key)
if anomaly["consecutive_count"] >= 2:
    # Require approval for high-risk actions
    decision = evaluate_policy(action, resource, api_key, context={
        "force_approval": True
    })

# BAD: Ignore anomaly signals
decision = evaluate_policy(action, resource, api_key)
```

### 3. Handle Policy Conflicts Proactively

```python
# GOOD: Periodic conflict detection
conflicts = detect_policy_conflicts(api_key)
if conflicts:
    for conflict in conflicts:
        if conflict["conflict_type"] == "EFFECT_CONTRADICTION":
            alert_ops_team(conflict)

# BAD: Discover conflicts only when action is blocked
```

---

## Next Steps

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Enterprise Governance</h3>
      </div>
      <div className="card__body">
        <p>Complete guide to governance architecture and backend implementation.</p>
      </div>
      <div className="card__footer">
        <a className="button button--primary button--block" href="/governance/enterprise-governance">View Architecture</a>
      </div>
    </div>
  </div>
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Security Overview</h3>
      </div>
      <div className="card__body">
        <p>Complete security architecture with verified implementations.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/security/overview">View Security</a>
      </div>
    </div>
  </div>
</div>

## Get Help

- **Backend Source**: [github.com/owkai/ow-ai-backend](https://github.com/owkai/ow-ai-backend)
- **Support**: [support@ascendowkai.com](mailto:support@ascendowkai.com)
- **Dashboard**: [pilot.owkai.app](https://pilot.owkai.app)
