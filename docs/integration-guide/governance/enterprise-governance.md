# Enterprise Governance Architecture

Ascend provides banking-level governance for AI agents and MCP servers. This guide covers the enterprise features implemented in the backend that enable organizations to maintain full control over autonomous AI systems.

## Overview

Ascend's governance architecture is built on three verified pillars:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASCEND ENTERPRISE GOVERNANCE                              │
│                    (Verified Backend Implementation - SEC-077)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Circuit Breaker │  │ Anomaly Detection│  │ Policy Resolver  │          │
│  │                  │  │                  │  │                  │          │
│  │  Auto-disable    │  │  Z-score based   │  │  Priority-based  │          │
│  │  failing servers │  │  behavior alerts │  │  conflict detect │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           └─────────────────────┼─────────────────────┘                     │
│                                 │                                           │
│                      ┌──────────▼──────────┐                               │
│                      │  Policy Enforcement │                               │
│                      │  Cedar-style engine │                               │
│                      │  Natural language   │                               │
│                      └─────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Backend Source**: `/ow-ai-backend/services/` (SEC-077 implementation)

---

## Circuit Breaker Pattern

The circuit breaker automatically detects and isolates failing MCP servers to prevent cascade failures across your AI infrastructure.

### Implementation

**Backend Service**: `/ow-ai-backend/services/circuit_breaker_service.py` (SEC-077)
**Lines**: 1-456 (456 lines of code)
**Industry Alignment**: Netflix Hystrix, AWS ALB health checks

### States

| State | Description | Request Behavior | Backend Implementation |
|-------|-------------|------------------|----------------------|
| **CLOSED** | Normal operation | Requests pass through | `CircuitState.CLOSED` (line 31) |
| **OPEN** | Failures exceeded threshold | Requests blocked immediately | `CircuitState.OPEN` (line 32) |
| **HALF_OPEN** | Recovery testing | Limited probe requests allowed | `CircuitState.HALF_OPEN` (line 33) |

### State Transitions

```
┌─────────┐  failure_threshold  ┌─────────┐  timeout  ┌───────────┐
│ CLOSED  │ ─────────────────→  │  OPEN   │ ────────→ │ HALF_OPEN │
│(healthy)│                     │(blocked)│           │ (testing) │
└────┬────┘ ←───────────────────└─────────┘ ←──────── └─────┬─────┘
     │         recovery                       failure        │
     └───────────────────────────────────────────────────────┘
                             success
```

**Source**: `circuit_breaker_service.py` (lines 43-54)

### Configuration

Configure circuit breaker thresholds per MCP server:

```json
{
    "server_id": "mcp-production-001",
    "circuit_failure_threshold": 5,
    "circuit_recovery_timeout_seconds": 300,
    "circuit_required_successes": 2
}
```

**Default Values** (from `models_mcp_governance.py`):
- `circuit_failure_threshold`: 5 consecutive failures
- `circuit_recovery_timeout_seconds`: 300 seconds (5 minutes)
- `circuit_required_successes`: 2 successful probes to close

### Key Methods

| Method | Purpose | Line Reference |
|--------|---------|----------------|
| `record_success()` | Record successful MCP call | Lines 61-105 |
| `record_failure()` | Record failed MCP call | Lines 107-169 |
| `check_circuit()` | Check if requests allowed | Lines 171-238 |
| `force_open()` | Emergency shutdown (audit logged) | Lines 240-268 |
| `force_close()` | Manual recovery (audit logged) | Lines 270-300 |

### Audit Trail

All circuit state changes are logged to `circuit_breaker_events` table:

```python
# From circuit_breaker_service.py (lines 411-449)
{
    "organization_id": 1,
    "server_id": "mcp-prod-001",
    "event_time": "2025-12-04T10:00:00Z",
    "previous_state": "CLOSED",
    "new_state": "OPEN",
    "trigger_reason": "failure_threshold_exceeded",
    "failure_count": 5,
    "correlation_id": "sha256:..."
}
```

---

## Anomaly Detection

Real-time statistical analysis of agent behavior to detect unusual patterns that may indicate security threats or misconfigurations.

### Implementation

**Backend Service**: `/ow-ai-backend/services/anomaly_detection_service.py` (SEC-077)
**Lines**: 1-522 (522 lines of code)
**Algorithm**: Z-score based detection (industry standard)

### Algorithm

```python
# From anomaly_detection_service.py (lines 198-199)
z = (current_value - baseline_mean) / standard_deviation

# If |z| > threshold → ANOMALY DETECTED
```

**Thresholds** (lines 451-457):
```python
if z_score > 4.0:
    severity = "CRITICAL"  # Auto-suspend if enabled
elif z_score > 3.0:
    severity = "HIGH"      # Escalation triggered
elif z_score > 2.0:
    severity = "MEDIUM"    # Alert sent
else:
    severity = "LOW"       # Log only
```

### Monitored Metrics

| Metric | Description | Calculation Method | Line Reference |
|--------|-------------|-------------------|----------------|
| **Actions/Hour** | Request frequency | EMA + SMA | Lines 223-225 |
| **Error Rate** | Failed action percentage | Rolling average | Lines 227-229 |
| **Risk Score** | Average risk of actions | Rolling average | Lines 231-233 |

**Data Source**: Hourly aggregates from `agent_actions` table (lines 397-429)

### Severity Levels

| Z-Score Range | Severity | Action | Line Reference |
|---------------|----------|--------|----------------|
| 2.0 - 3.0 | LOW | Log only | Line 452 |
| 3.0 - 4.0 | MEDIUM | Alert sent | Line 456 |
| 4.0 - 5.0 | HIGH | Escalation triggered | Line 454 |
| > 5.0 | CRITICAL | Auto-suspension (if enabled) | Lines 148-158 |

### Configuration

```python
# From anomaly_detection_service.py (lines 318-372)
{
    "agent_id": "agent-001",
    "anomaly_detection_enabled": true,
    "anomaly_sensitivity": 2.0,           # Z-score threshold (1.0-4.0)
    "anomaly_auto_suspend": false,        # Auto-suspend on critical
    "anomaly_escalation_threshold": 3,    # Consecutive anomalies before escalation
    "baseline_window_hours": 168          # 1 week baseline
}
```

### API Methods

| Method | Purpose | Returns | Line Reference |
|--------|---------|---------|----------------|
| `check_agent_anomalies()` | Detect anomalies for agent | Detection results | Lines 72-186 |
| `update_rolling_statistics()` | Update baseline metrics | Updated statistics | Lines 188-266 |
| `get_anomaly_history()` | Historical anomaly events | List of events | Lines 268-316 |
| `configure_agent_detection()` | Configure detection settings | Updated config | Lines 318-372 |

### Auto-Suspension

**Implementation** (lines 148-158):
```python
if (
    agent.anomaly_auto_suspend and
    max_severity == AnomalySeverity.CRITICAL
):
    agent.status = "suspended"
    agent.auto_suspended_at = now
    agent.auto_suspend_reason = f"SEC-077: Critical anomaly detected - {anomalies[0]['metric']}"
    logger.warning(f"SEC-077: Agent {agent.agent_id} AUTO-SUSPENDED due to critical anomaly")
```

---

## Policy Conflict Resolution

Automatically detects and resolves conflicts between overlapping governance policies.

### Implementation

**Backend Service**: `/ow-ai-backend/services/policy_conflict_resolver.py` (SEC-077)
**Lines**: 1-465 (465 lines of code)
**Pattern**: AWS IAM policy evaluation logic, Cedar policy language

### Conflict Types

| Type | Description | Severity | Line Reference |
|------|-------------|----------|----------------|
| **PRIORITY_TIE** | Same priority on overlapping scope | HIGH | Line 30 |
| **EFFECT_CONTRADICTION** | ALLOW vs DENY on same resource | CRITICAL | Line 31 |
| **RESOURCE_OVERLAP** | Ambiguous resource patterns | MEDIUM | Line 32 |
| **CONDITION_AMBIGUITY** | Ambiguous condition evaluation | MEDIUM | Line 33 |

**Source**: `policy_conflict_resolver.py` (lines 28-34)

### Resolution Strategies

| Strategy | Description | Use Case | Line Reference |
|----------|-------------|----------|----------------|
| `MOST_RESTRICTIVE` | DENY always wins | Security-first (default) | Lines 436-443 |
| `MOST_PERMISSIVE` | ALLOW wins unless explicit DENY | Availability-first | Lines 445-450 |
| `HIGHEST_PRIORITY` | Lower number = higher priority | Explicit ordering | Lines 452-454 |
| `FIRST_MATCH` | First matching policy wins | Cedar-style evaluation | Lines 456-458 |

**Default Strategy** (line 76):
```python
self.default_strategy = ResolutionStrategy.MOST_RESTRICTIVE
```

### API Methods

| Method | Purpose | Line Reference |
|--------|---------|----------------|
| `detect_conflicts()` | Scan all policies for conflicts | Lines 78-120 |
| `resolve_policy_match()` | Resolve multiple matching policies | Lines 122-173 |
| `record_conflict()` | Log conflict to database | Lines 175-218 |
| `resolve_conflict()` | Mark conflict as resolved | Lines 220-266 |
| `get_unresolved_conflicts()` | Get pending conflicts | Lines 268-305 |

### Conflict Detection Example

```python
# From policy_conflict_resolver.py (lines 307-360)
# Detects MCP policy conflicts
for policy_a, policy_b in policy_pairs:
    if policy_a.priority == policy_b.priority:
        if self._scopes_overlap(policy_a, policy_b):
            # PRIORITY_TIE conflict detected
            # Record to policy_conflicts table
            # Severity: HIGH
```

### Best Practice: Priority Assignment

```
1-99:    System policies (reserved)
100-199: Security policies
200-299: Compliance policies
300-399: Business policies
400+:    Custom policies
```

---

## Policy Enforcement

Cedar-style policy engine with natural language compilation.

### Implementation

**Backend Service**: `/ow-ai-backend/services/cedar_enforcement_service.py`
**Lines**: 1-321 (321 lines of code)
**Pattern**: AWS Cedar policy language, Open Policy Agent (OPA)

### Policy Compilation

**Compiler Class** (lines 49-126):
```python
class PolicyCompiler:
    @staticmethod
    def compile(natural_language: str, risk_level: str) -> Dict[str, Any]:
        """Convert natural language policy to structured Cedar-style policy"""
        # Extracts: effect, actions, resources, conditions
        # Validation: PolicyValidator.validate_natural_language()
```

**Supported Effects**:
- `deny`: Block the action
- `permit`: Allow the action
- `require_approval`: Require human approval

### Enforcement Engine

**Engine Class** (lines 128-318):
```python
class EnforcementEngine:
    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate action against all policies
        Returns: {decision: "ALLOW|DENY|REQUIRE_APPROVAL", policies_triggered: [...]}
        """
```

**Decision Logic** (lines 182-198):
```python
for policy in self.policies:
    if self._matches_policy(policy, principal, action, resource, context):
        if policy.effect == "deny":
            final_decision = "DENY"  # Deny takes precedence
            break
        elif policy.effect == "require_approval":
            final_decision = "REQUIRE_APPROVAL"
```

### Semantic Action Taxonomy

**Implementation**: `services/action_taxonomy.py`

```python
def actions_match(policy_action: str, actual_action: str) -> bool:
    """
    Semantic matching of actions
    Example: "write" matches "file.write", "database.insert", "api.create"
    """

def resource_matches(policy_resource: str, actual_resource: str) -> bool:
    """
    Hierarchical resource matching with wildcards
    Example: "database:*" matches "database:prod", "database:staging"
    """
```

**Source**: `cedar_enforcement_service.py` (lines 243-258)

---

## Compliance Mapping

| Feature | SOC 2 | PCI-DSS | NIST | GDPR | Backend File |
|---------|-------|---------|------|------|--------------|
| Circuit Breaker | CC7.1 | 6.5.5 | SI-4 | — | `circuit_breaker_service.py` |
| Anomaly Detection | CC7.1 | 10.6 | SI-4 | — | `anomaly_detection_service.py` |
| Policy Resolver | CC6.1 | 7.1 | AC-3 | — | `policy_conflict_resolver.py` |
| Policy Enforcement | CC6.1 | 7.1 | AC-3 | — | `cedar_enforcement_service.py` |

---

## API Endpoints

All governance features are accessible via REST API:

| Endpoint | Method | Description | Backend Route |
|----------|--------|-------------|---------------|
| `/api/governance/circuits` | GET | Get all circuit states | Circuit breaker service |
| `/api/governance/circuits/{server_id}` | GET | Get specific circuit status | Circuit breaker service |
| `/api/governance/anomalies/{agent_id}` | GET | Check agent anomalies | Anomaly detection service |
| `/api/governance/policies/conflicts` | GET | Detect policy conflicts | Policy resolver service |
| `/api/governance/policies/evaluate` | POST | Evaluate policy decision | Policy enforcement service |

---

## Monitoring & Alerts

### Recommended Alerts

| Alert | Condition | Severity | Backend Trigger |
|-------|-----------|----------|-----------------|
| Circuit Open | Any MCP server circuit opens | HIGH | `circuit_state == "OPEN"` |
| Anomaly Streak | 3+ consecutive anomalies | HIGH | `consecutive_anomalies >= 3` |
| Policy Conflict | Critical conflict detected | CRITICAL | `severity == "critical"` |
| Auto-Suspension | Agent auto-suspended | CRITICAL | `auto_suspended_at IS NOT NULL` |

### SIEM Integration

**Metrics for Export**:
```
ascend.circuit_breaker.state (CLOSED/OPEN/HALF_OPEN)
ascend.circuit_breaker.failure_count
ascend.anomaly.detection_count
ascend.anomaly.severity (LOW/MEDIUM/HIGH/CRITICAL)
ascend.policy.conflict_count
ascend.policy.evaluation_count
```

---

## Implementation Verification

All governance features documented here are verified implementations:

| Feature | Backend File | Lines | Status |
|---------|-------------|-------|--------|
| Circuit Breaker | `circuit_breaker_service.py` | 456 | ✅ Implemented (SEC-077) |
| Anomaly Detection | `anomaly_detection_service.py` | 522 | ✅ Implemented (SEC-077) |
| Policy Resolver | `policy_conflict_resolver.py` | 465 | ✅ Implemented (SEC-077) |
| Policy Enforcement | `cedar_enforcement_service.py` | 321 | ✅ Implemented |
| Policy Compiler | `cedar_enforcement_service.py` | 321 | ✅ Implemented |

**Total Backend Code**: 2,085 lines of enterprise-grade governance logic

---

## Next Steps

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>SDK Integration</h3>
      </div>
      <div className="card__body">
        <p>Learn how to integrate verified governance features into your agents.</p>
      </div>
      <div className="card__footer">
        <a className="button button--primary button--block" href="/governance/sdk/governance-integration">View SDK Guide</a>
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

- **Documentation**: You're here!
- **Dashboard**: [pilot.owkai.app](https://pilot.owkai.app)
- **Support**: [support@ascendowkai.com](mailto:support@ascendowkai.com)
