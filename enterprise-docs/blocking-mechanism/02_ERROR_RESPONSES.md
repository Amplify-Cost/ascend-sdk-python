# OW-AI Enterprise Error Response Specification

**Document Version:** 1.0
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-01-15
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Error Response Format](#error-response-format)
2. [Blocking Error Types](#blocking-error-types)
3. [Error Codes Reference](#error-codes-reference)
4. [Language-Specific Exceptions](#language-specific-exceptions)
5. [MCP Protocol Errors](#mcp-protocol-errors)

---

## Error Response Format

All blocking errors follow a standardized JSON format for consistent parsing across integrations.

### Standard Error Schema

```json
{
  "error": {
    "code": "GOVN_BLOCKED_001",
    "type": "GovernanceBlockedError",
    "message": "Human-readable error message",
    "blocking_reason": "Detailed explanation of why action was blocked",
    "action_id": 12345,
    "risk_assessment": {
      "score": 95,
      "level": "CRITICAL",
      "cvss_score": 9.1,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    },
    "policy_evaluation": {
      "policy_id": "no-production-deletes",
      "policy_name": "Block Production DELETE Operations",
      "decision": "DENY",
      "matched_conditions": [
        "action_type == 'database_delete'",
        "target_system == 'production'"
      ]
    },
    "governance_context": {
      "agent_id": "agent-001",
      "timestamp": "2025-01-15T10:30:00Z",
      "request_id": "req-abc123",
      "organization_id": 1,
      "enforcement_mode": "mandatory"
    },
    "remediation": {
      "suggestion": "Request approval from security team or use staging environment",
      "approval_url": "https://pilot.owkai.app/actions/12345/approve",
      "documentation_url": "https://docs.owkai.app/policies/no-production-deletes"
    }
  }
}
```

---

## Blocking Error Types

### 1. GOVERNANCE_BLOCKED - Immediate Policy Block

**When:** Policy explicitly denies the action with no approval path.

```json
{
  "error": {
    "code": "GOVN_BLOCKED_001",
    "type": "GovernanceBlockedError",
    "message": "Action blocked by governance policy",
    "blocking_reason": "Production database DELETE operations are prohibited by policy 'no-production-deletes'",
    "action_id": 12345,
    "risk_assessment": {
      "score": 98,
      "level": "CRITICAL"
    },
    "policy_evaluation": {
      "policy_id": "no-production-deletes",
      "decision": "DENY"
    },
    "is_permanent": true,
    "can_request_exception": true,
    "exception_process": "Contact security-team@company.com for policy exception"
  }
}
```

**Python Exception:**
```python
class GovernanceBlockedError(OWKAIError):
    """Action permanently blocked by policy."""

    def __init__(
        self,
        message: str,
        *,
        action_id: int,
        policy_id: str,
        policy_name: str,
        risk_score: float,
        blocking_reason: str,
        remediation: Optional[str] = None,
    ):
        self.action_id = action_id
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.risk_score = risk_score
        self.blocking_reason = blocking_reason
        self.remediation = remediation
```

---

### 2. ACTION_REJECTED - Approver Rejected

**When:** Action required approval and an approver explicitly rejected it.

```json
{
  "error": {
    "code": "GOVN_REJECTED_001",
    "type": "ActionRejectedError",
    "message": "Action rejected by approver",
    "blocking_reason": "Security review determined this action poses unacceptable risk",
    "action_id": 12345,
    "rejection_details": {
      "rejected_by": "security-admin@company.com",
      "rejected_at": "2025-01-15T10:35:00Z",
      "rejection_reason": "This DELETE would affect 50,000 active users. Business justification required.",
      "rejection_category": "business_impact"
    },
    "risk_assessment": {
      "score": 85,
      "level": "HIGH"
    },
    "next_steps": {
      "can_resubmit": true,
      "resubmit_requirements": [
        "Provide business justification",
        "Limit scope to inactive users only",
        "Schedule during maintenance window"
      ],
      "appeal_process": "Contact security-lead@company.com within 24 hours"
    }
  }
}
```

**Python Exception:**
```python
class ActionRejectedError(OWKAIError):
    """Action explicitly rejected by approver."""

    def __init__(
        self,
        message: str,
        *,
        action_id: int,
        rejected_by: str,
        rejected_at: datetime,
        rejection_reason: str,
        rejection_category: Optional[str] = None,
        can_resubmit: bool = False,
        resubmit_requirements: Optional[List[str]] = None,
    ):
        self.action_id = action_id
        self.rejected_by = rejected_by
        self.rejected_at = rejected_at
        self.rejection_reason = rejection_reason
        self.rejection_category = rejection_category
        self.can_resubmit = can_resubmit
        self.resubmit_requirements = resubmit_requirements or []
```

---

### 3. APPROVAL_TIMEOUT - No Response Within Limit

**When:** Action required approval but no approver responded within the timeout period.

```json
{
  "error": {
    "code": "GOVN_TIMEOUT_001",
    "type": "ApprovalTimeoutError",
    "message": "Approval timeout - no response received",
    "blocking_reason": "No approver responded within 300 seconds",
    "action_id": 12345,
    "timeout_details": {
      "timeout_seconds": 300,
      "started_at": "2025-01-15T10:30:00Z",
      "expired_at": "2025-01-15T10:35:00Z",
      "pending_approvers": [
        "security-team@company.com",
        "manager@company.com"
      ],
      "escalation_attempted": true
    },
    "risk_assessment": {
      "score": 75,
      "level": "HIGH"
    },
    "next_steps": {
      "can_retry": true,
      "retry_suggestion": "Try during business hours when approvers are available",
      "emergency_contact": "On-call: +1-555-SECURITY",
      "async_option": "Use async mode to queue for later approval"
    }
  }
}
```

**Python Exception:**
```python
class ApprovalTimeoutError(OWKAIError):
    """Approval not received within timeout period."""

    def __init__(
        self,
        message: str,
        *,
        action_id: int,
        timeout_seconds: int,
        started_at: datetime,
        pending_approvers: List[str],
        escalation_attempted: bool = False,
    ):
        self.action_id = action_id
        self.timeout_seconds = timeout_seconds
        self.started_at = started_at
        self.pending_approvers = pending_approvers
        self.escalation_attempted = escalation_attempted
```

---

### 4. GOVERNANCE_UNAVAILABLE - System Error (Fail-Closed)

**When:** OW-AI platform is unreachable and fail-closed mode is enabled.

```json
{
  "error": {
    "code": "GOVN_UNAVAILABLE_001",
    "type": "GovernanceUnavailableError",
    "message": "Governance service unavailable - action blocked (fail-closed)",
    "blocking_reason": "Cannot reach OW-AI platform for authorization. Blocking action per fail-closed policy.",
    "system_details": {
      "endpoint": "https://pilot.owkai.app/api/authorization/agent-action",
      "error_type": "ConnectionTimeout",
      "retry_attempts": 3,
      "last_attempt_at": "2025-01-15T10:30:05Z"
    },
    "fail_mode": {
      "configured_mode": "fail_closed",
      "action_taken": "BLOCK",
      "reason": "Enterprise security policy requires blocking when governance is unavailable"
    },
    "next_steps": {
      "retry_after_seconds": 30,
      "status_page": "https://status.owkai.app",
      "support_contact": "support@owkai.com"
    }
  }
}
```

**Python Exception:**
```python
class GovernanceUnavailableError(OWKAIError):
    """Governance service unavailable - blocked per fail-closed policy."""

    def __init__(
        self,
        message: str,
        *,
        endpoint: str,
        error_type: str,
        retry_attempts: int,
        fail_mode: str = "fail_closed",
        retry_after_seconds: int = 30,
    ):
        self.endpoint = endpoint
        self.error_type = error_type
        self.retry_attempts = retry_attempts
        self.fail_mode = fail_mode
        self.retry_after_seconds = retry_after_seconds
        self.is_retryable = True
```

---

## Error Codes Reference

### Governance Error Codes (GOVN_*)

| Code | Type | Description | Retryable |
|------|------|-------------|-----------|
| `GOVN_BLOCKED_001` | GovernanceBlockedError | Policy permanently blocks action | No |
| `GOVN_BLOCKED_002` | GovernanceBlockedError | Risk score exceeds maximum threshold | No |
| `GOVN_REJECTED_001` | ActionRejectedError | Approver rejected action | Conditional |
| `GOVN_REJECTED_002` | ActionRejectedError | Action rejected due to policy violation | No |
| `GOVN_TIMEOUT_001` | ApprovalTimeoutError | Approval timeout exceeded | Yes |
| `GOVN_TIMEOUT_002` | ApprovalTimeoutError | Escalation timeout exceeded | Yes |
| `GOVN_UNAVAILABLE_001` | GovernanceUnavailableError | Service unreachable (fail-closed) | Yes |
| `GOVN_UNAVAILABLE_002` | GovernanceUnavailableError | Service error (fail-closed) | Yes |

### Authentication Error Codes (AUTH_*)

| Code | Type | Description | Retryable |
|------|------|-------------|-----------|
| `AUTH_001` | AuthenticationError | Invalid API key | No |
| `AUTH_002` | AuthenticationError | API key expired | No |
| `AUTH_003` | AuthenticationError | Insufficient permissions | No |
| `AUTH_004` | AuthenticationError | Organization suspended | No |

### Validation Error Codes (VALID_*)

| Code | Type | Description | Retryable |
|------|------|-------------|-----------|
| `VALID_001` | ValidationError | Missing required field | No |
| `VALID_002` | ValidationError | Invalid field format | No |
| `VALID_003` | ValidationError | Field exceeds max length | No |

---

## Language-Specific Exceptions

### Python Exception Hierarchy

```python
OWKAIError (base)
├── GovernanceBlockedError      # Policy blocks action
├── ActionRejectedError         # Approver rejected
├── ApprovalTimeoutError        # No approval in time
├── GovernanceUnavailableError  # Service down (fail-closed)
├── AuthenticationError         # Invalid credentials
├── ValidationError             # Invalid request
├── RateLimitError              # Too many requests
├── NetworkError                # Connection issues
└── ServerError                 # Platform errors
```

### JavaScript/TypeScript Exception Classes

```typescript
class OWKAIError extends Error {
  code: string;
  actionId?: number;
  isRetryable: boolean;
  toJSON(): object;
}

class GovernanceBlockedError extends OWKAIError {
  policyId: string;
  policyName: string;
  riskScore: number;
  blockingReason: string;
}

class ActionRejectedError extends OWKAIError {
  rejectedBy: string;
  rejectedAt: Date;
  rejectionReason: string;
  canResubmit: boolean;
}

class ApprovalTimeoutError extends OWKAIError {
  timeoutSeconds: number;
  pendingApprovers: string[];
}

class GovernanceUnavailableError extends OWKAIError {
  failMode: 'fail_closed' | 'fail_open';
  retryAfterSeconds: number;
}
```

---

## MCP Protocol Errors

### MCP Error Response Format

When an MCP tool execution is blocked, the server returns an MCP-compliant error:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Action blocked by OW-AI governance",
    "data": {
      "governance_error": {
        "code": "GOVN_BLOCKED_001",
        "type": "GovernanceBlockedError",
        "message": "Production database DELETE operations are prohibited",
        "action_id": 12345,
        "risk_score": 95,
        "blocking_reason": "Policy 'no-production-deletes' prohibits this action",
        "policy_id": "no-production-deletes"
      }
    }
  }
}
```

### MCP Error Codes

| JSON-RPC Code | OW-AI Mapping | Description |
|---------------|---------------|-------------|
| `-32000` | GovernanceBlockedError | Action blocked by policy |
| `-32001` | ActionRejectedError | Action rejected by approver |
| `-32002` | ApprovalTimeoutError | Approval timeout |
| `-32003` | GovernanceUnavailableError | Governance unavailable |

### Claude Desktop User Experience

When Claude attempts a blocked action, users see:

```
I attempted to execute the database query, but OW-AI governance blocked
the action:

❌ Action Blocked: Policy Violation

Reason: Production database DELETE operations are prohibited by your
organization's security policy.

Risk Score: 95/100 (CRITICAL)

Policy: no-production-deletes

What you can do:
• Use the staging database for testing
• Request a policy exception from security-team@company.com
• Modify the query to be less destructive

Would you like me to help with an alternative approach?
```

---

## Next Documents

- [03_SDK_ENFORCEMENT.md](./03_SDK_ENFORCEMENT.md) - SDK enforcement implementation
- [04_MCP_ENFORCEMENT.md](./04_MCP_ENFORCEMENT.md) - MCP server enforcement implementation

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | OW-AI Engineering | Initial release |
