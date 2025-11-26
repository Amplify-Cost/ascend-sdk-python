# OW-AI Enterprise SDK Enforcement Module

**Document Version:** 1.0
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-01-15
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Overview](#overview)
2. [Security Guarantees](#security-guarantees)
3. [Exception Hierarchy](#exception-hierarchy)
4. [EnforcedClient Class](#enforcedclient-class)
5. [Function Decorator](#function-decorator)
6. [boto3 Integration](#boto3-integration)
7. [Configuration Reference](#configuration-reference)
8. [Implementation Examples](#implementation-examples)

---

## Overview

The OW-AI SDK Enforcement Module (`owkai.enforcement`) provides **banking-level mandatory enforcement** for AI agent actions. This module ensures that actions **CANNOT proceed** without explicit governance approval.

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Fail-Closed** | Any error (network, timeout, server) results in BLOCK |
| **Non-Bypassable** | Action callable is wrapped INSIDE governance check |
| **Thread-Safe** | All operations protected by threading locks |
| **Audit Complete** | Every decision logged with full context |

### Module Location

```
owkai-sdk/
└── owkai/
    └── enforcement.py     # This module
```

### Import Statement

```python
from owkai.enforcement import (
    # Client
    EnforcedClient,

    # Exceptions
    GovernanceBlockedError,
    ActionRejectedError,
    ApprovalTimeoutError,
    GovernanceUnavailableError,

    # Configuration
    EnforcementConfig,
    EnforcementMode,

    # Helpers
    governed,
    configure_enforcement,
    enable_mandatory_governance,
)
```

---

## Security Guarantees

### What This Module Guarantees

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY GUARANTEE: NON-BYPASSABLE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │ Agent Code      │                                                       │
│   │                 │                                                       │
│   │ action = lambda: db.execute("DELETE FROM users")                        │
│   │                 │                                                       │
│   │ # Agent CANNOT call action() directly                                   │
│   │ # Agent MUST use execute_governed()                                     │
│   │                 │                                                       │
│   │ result = client.execute_governed(                                       │
│   │     action=action,        # <-- Action is INSIDE                        │
│   │     action_type="...",    #     the governance call                     │
│   │ )                         #     Cannot bypass                           │
│   │                 │                                                       │
│   └────────────────┬┘                                                       │
│                    │                                                        │
│   ┌────────────────▼────────────────────────────────────────────────────┐   │
│   │                    ENFORCEMENT LAYER                                │   │
│   │                                                                     │   │
│   │   1. Submit to OW-AI ───────────────────────────────────────────►   │   │
│   │   2. Wait for decision                                              │   │
│   │   3. IF ALLOW/APPROVED:                                             │   │
│   │        └── Execute action()  ◄── Only path to execute              │   │
│   │   4. IF DENY/REJECT/TIMEOUT:                                        │   │
│   │        └── Raise exception   ◄── Action never executes             │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Is Secure

| Concern | Solution |
|---------|----------|
| Agent skips governance | Impossible - action is inside `execute_governed()` |
| Agent catches exception | Action still didn't execute |
| Network failure | Fail-closed blocks action |
| Timeout waiting for approval | Blocks action (not allows) |

---

## Exception Hierarchy

### Complete Exception Tree

```
OWKAIError (base)
├── GovernanceBlockedError      # Policy permanently blocks
├── ActionRejectedError         # Approver rejected
├── ApprovalTimeoutError        # No approval in time
├── GovernanceUnavailableError  # Service down (fail-closed)
├── AuthenticationError         # Invalid credentials
├── ValidationError             # Invalid request
├── RateLimitError              # Too many requests
├── NetworkError                # Connection issues
└── ServerError                 # Platform errors
```

### GovernanceBlockedError

**When raised:** Policy explicitly denies the action with no approval path.

```python
class GovernanceBlockedError(OWKAIError):
    """
    Action permanently blocked by governance policy.

    Attributes:
        action_id: OW-AI action identifier for audit trail
        policy_id: ID of the policy that blocked the action
        policy_name: Human-readable policy name
        risk_score: Calculated risk score (0-100)
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        blocking_reason: Detailed explanation of why blocked
        remediation: Suggested steps to resolve
        nist_control: Applicable NIST 800-53 control
        mitre_technique: Applicable MITRE ATT&CK technique
    """

    def __init__(
        self,
        message: str,
        *,
        action_id: Optional[int] = None,
        policy_id: Optional[str] = None,
        policy_name: Optional[str] = None,
        risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        blocking_reason: Optional[str] = None,
        remediation: Optional[str] = None,
        nist_control: Optional[str] = None,
        mitre_technique: Optional[str] = None,
    ):
        # ... initialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": "GovernanceBlockedError",
            "error_code": self.error_code,  # "GOVN_BLOCKED_001"
            "message": self.message,
            "action_id": self.action_id,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "blocking_reason": self.blocking_reason,
            "remediation": self.remediation,
            "nist_control": self.nist_control,
            "mitre_technique": self.mitre_technique,
        }
```

**String representation:**
```
[BLOCKED] Action blocked by governance policy
Reason: Production database DELETE operations are prohibited
Risk Score: 95/100 (CRITICAL)
Policy: no-production-deletes
Remediation: Use staging environment or request policy exception
```

### ActionRejectedError

**When raised:** Action required approval and an approver explicitly rejected it.

```python
class ActionRejectedError(OWKAIError):
    """
    Action explicitly rejected by an approver.

    Attributes:
        action_id: OW-AI action identifier
        rejected_by: Email/ID of the approver who rejected
        rejected_at: Timestamp of rejection
        rejection_reason: Approver's explanation
        rejection_category: Category (policy, risk, business, etc.)
        can_resubmit: Whether action can be resubmitted with changes
        resubmit_requirements: What changes are needed to resubmit
    """

    def __init__(
        self,
        message: str,
        *,
        action_id: Optional[int] = None,
        rejected_by: Optional[str] = None,
        rejected_at: Optional[datetime] = None,
        rejection_reason: Optional[str] = None,
        rejection_category: Optional[str] = None,
        can_resubmit: bool = False,
        resubmit_requirements: Optional[List[str]] = None,
    ):
        # ... initialization
```

**String representation:**
```
[REJECTED] Action rejected by approver
Rejected by: security-admin@company.com
Reason: This DELETE would affect 50,000 active users
To resubmit: Provide business justification, Limit scope to inactive users
```

### ApprovalTimeoutError

**When raised:** Action required approval but no approver responded within the timeout.

```python
class ApprovalTimeoutError(OWKAIError):
    """
    Approval not received within timeout period.

    Attributes:
        action_id: OW-AI action identifier
        timeout_seconds: Configured timeout value
        started_at: When approval wait started
        pending_approvers: List of approvers who didn't respond
        escalation_attempted: Whether escalation was tried
    """

    def __init__(
        self,
        message: str,
        *,
        action_id: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        started_at: Optional[datetime] = None,
        pending_approvers: Optional[List[str]] = None,
        escalation_attempted: bool = False,
    ):
        # ... initialization
```

**String representation:**
```
[TIMEOUT] Approval timeout - action blocked
Timeout: 300s
Pending approvers: security-team@company.com, manager@company.com
```

### GovernanceUnavailableError

**When raised:** OW-AI platform unreachable and fail-closed mode is enabled.

```python
class GovernanceUnavailableError(OWKAIError):
    """
    Governance service unavailable - action blocked per fail-closed policy.

    Attributes:
        endpoint: API endpoint that failed
        error_type: Type of network/server error
        retry_attempts: Number of retry attempts made
        fail_mode: Configured failure mode (fail_closed, fail_open)
        retry_after_seconds: Suggested retry delay
        is_retryable: Always True for this error
    """

    def __init__(
        self,
        message: str,
        *,
        endpoint: Optional[str] = None,
        error_type: Optional[str] = None,
        retry_attempts: int = 0,
        fail_mode: str = "fail_closed",
        retry_after_seconds: int = 30,
    ):
        # ... initialization
        self.is_retryable = True
```

**String representation:**
```
[UNAVAILABLE] Governance service unavailable - action blocked (fail-closed)
Fail Mode: fail_closed (action blocked)
Retry after: 30s
```

---

## EnforcedClient Class

### Class Overview

```python
class EnforcedClient:
    """
    Banking-Level Enforced OW-AI Client.

    Security Features:
    - Fail-closed by default (errors = block)
    - Non-bypassable enforcement
    - Complete audit trail
    - CVSS/NIST/MITRE enrichment
    """
```

### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
    enforcement_mode: Union[str, EnforcementMode] = EnforcementMode.MANDATORY,
    fail_closed: bool = True,
    approval_timeout: int = 300,
    agent_id: Optional[str] = None,
):
    """
    Initialize enforced client.

    Args:
        api_key: OW-AI API key (or OWKAI_API_KEY env var)
        base_url: API base URL (default: https://pilot.owkai.app)
        enforcement_mode: Level of enforcement
            - "mandatory" (recommended) - Non-bypassable
            - "cooperative" - Trust-based
            - "advisory" - Logging only
        fail_closed: Block on errors (REQUIRED for mandatory mode)
        approval_timeout: Max seconds to wait for approval
        agent_id: Identifier for this agent

    Raises:
        ValueError: If mandatory mode without fail_closed=True
    """
```

### Primary Method: execute_governed()

```python
def execute_governed(
    self,
    action: Callable[[], T],
    action_type: str,
    description: str,
    tool_name: str = "unknown",
    *,
    target_system: Optional[str] = None,
    target_resource: Optional[str] = None,
    risk_context: Optional[Dict[str, Any]] = None,
) -> T:
    """
    Execute an action with mandatory governance enforcement.

    This is the PRIMARY method for governed execution. The action
    callable is ONLY executed if governance approves.

    Args:
        action: Callable that performs the actual action
        action_type: Type of action (database_delete, file_write, etc.)
        description: Human-readable description
        tool_name: Name of tool being used
        target_system: Target system identifier (production, staging)
        target_resource: Specific resource being accessed
        risk_context: Additional context for risk assessment

    Returns:
        Result of the action callable (only if approved)

    Raises:
        GovernanceBlockedError: Action blocked by policy
        ActionRejectedError: Action rejected by approver
        ApprovalTimeoutError: No approval within timeout
        GovernanceUnavailableError: Service unavailable (fail-closed)

    Example:
        result = client.execute_governed(
            action=lambda: db.execute("DELETE FROM users WHERE inactive=true"),
            action_type="database_delete",
            description="Delete inactive user records",
            tool_name="postgresql",
            target_system="production",
            risk_context={"affected_rows_estimate": 5000}
        )
    """
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        execute_governed() FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. SUBMIT                                                                 │
│      │                                                                      │
│      ├── POST /api/authorization/agent-action                               │
│      │   {                                                                  │
│      │     "agent_id": "agent-001",                                         │
│      │     "action_type": "database_delete",                                │
│      │     "description": "Delete inactive users",                          │
│      │     "tool_name": "postgresql",                                       │
│      │     "target_system": "production",                                   │
│      │     "enforcement_mode": "mandatory"                                  │
│      │   }                                                                  │
│      │                                                                      │
│      ▼                                                                      │
│   2. EVALUATE                                                               │
│      │                                                                      │
│      ├── Response: risk_score, requires_approval, policy_result             │
│      │                                                                      │
│      ├── IF risk_score >= 95: decision = DENY                               │
│      ├── IF requires_approval OR risk_score >= 70: decision = REQUIRE       │
│      └── ELSE: decision = ALLOW                                             │
│      │                                                                      │
│      ▼                                                                      │
│   3. ENFORCE                                                                │
│      │                                                                      │
│      ├── DENY ──────────────► raise GovernanceBlockedError                  │
│      │                                                                      │
│      ├── REQUIRE_APPROVAL                                                   │
│      │       │                                                              │
│      │       └── Poll GET /api/agent-action/status/{id}                     │
│      │           │                                                          │
│      │           ├── "approved" ────► Continue to EXECUTE                   │
│      │           ├── "rejected" ────► raise ActionRejectedError             │
│      │           └── timeout ───────► raise ApprovalTimeoutError            │
│      │                                                                      │
│      ├── ALLOW ─────────────────────► Continue to EXECUTE                   │
│      │                                                                      │
│      ▼                                                                      │
│   4. EXECUTE (only if approved)                                             │
│      │                                                                      │
│      ├── result = action()    # <-- Actual execution                        │
│      │                                                                      │
│      ├── Log audit: action_completed                                        │
│      │                                                                      │
│      └── return result                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Context Manager Support

```python
# Use as context manager for automatic cleanup
with EnforcedClient(api_key="owkai_admin_...") as client:
    result = client.execute_governed(
        action=lambda: db.execute("SELECT * FROM users"),
        action_type="database_read",
        description="Fetch user list"
    )
# HTTP client automatically closed
```

---

## Function Decorator

### @governed Decorator

```python
@governed(
    action_type: str,
    description: str,
    tool_name: str = "unknown",
    *,
    client: Optional[EnforcedClient] = None,
    target_system: Optional[str] = None,
)
```

### Usage Example

```python
from owkai.enforcement import governed, configure_enforcement

# Configure global client once at startup
configure_enforcement(
    api_key="owkai_admin_...",
    enforcement_mode="mandatory",
    fail_closed=True
)

# Decorate functions that need governance
@governed(
    action_type="database_delete",
    description="Delete user records from database",
    tool_name="postgresql",
    target_system="production"
)
def delete_users(user_ids: List[int]) -> int:
    """Delete users by ID. This function is now governed."""
    return db.execute(
        "DELETE FROM users WHERE id IN (%s)",
        user_ids
    )

# Calling the decorated function triggers governance
try:
    count = delete_users([1, 2, 3])  # Will block until approved
    print(f"Deleted {count} users")
except GovernanceBlockedError as e:
    print(f"Cannot delete users: {e.blocking_reason}")
```

### Decorator Implementation

```python
def governed(
    action_type: str,
    description: str,
    tool_name: str = "unknown",
    *,
    client: Optional[EnforcedClient] = None,
    target_system: Optional[str] = None,
):
    """
    Decorator to make a function governed by OW-AI.

    The decorated function will ONLY execute if governance approves.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            _client = client or _get_default_client()

            return _client.execute_governed(
                action=lambda: func(*args, **kwargs),
                action_type=action_type,
                description=description,
                tool_name=tool_name,
                target_system=target_system,
            )

        return wrapper
    return decorator
```

---

## boto3 Integration

### enable_mandatory_governance()

Enable mandatory governance for **all** boto3 AWS API calls.

```python
def enable_mandatory_governance(
    api_key: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
    fail_closed: bool = True,
    risk_threshold: int = 70,
    auto_approve_below: int = 30,
    approval_timeout: int = 300,
    agent_id: Optional[str] = None,
) -> None:
    """
    Enable mandatory governance for all boto3 AWS calls.

    IMPORTANT: Call this BEFORE importing boto3.

    Args:
        api_key: OW-AI API key
        base_url: OW-AI API base URL
        fail_closed: Block on errors (required for security)
        risk_threshold: Risk score requiring approval (default: 70)
        auto_approve_below: Auto-approve below this score (default: 30)
        approval_timeout: Seconds to wait for approval (default: 300)
        agent_id: Identifier for this agent
    """
```

### Usage Pattern

```python
# IMPORTANT: Must be called BEFORE importing boto3
from owkai.enforcement import enable_mandatory_governance

enable_mandatory_governance(
    api_key="owkai_admin_...",
    fail_closed=True,
    risk_threshold=70
)

# Now import boto3 - all calls are governed
import boto3

s3 = boto3.client('s3')

# Low risk - auto-approved
s3.list_buckets()  # Executes immediately

# High risk - requires approval
s3.delete_bucket(Bucket='production-data')  # BLOCKS until approved
```

### AWS Operation Risk Levels

| Operation Pattern | Risk Level | Score Range | Behavior |
|-------------------|------------|-------------|----------|
| `list_*`, `get_*`, `describe_*` | LOW | 10-30 | Auto-approve |
| `put_object`, `create_*` | MEDIUM | 40-60 | Policy-based |
| `delete_object`, `modify_*` | HIGH | 70-85 | Require approval |
| `delete_bucket`, `terminate_instances` | CRITICAL | 90-100 | Block or exec approval |

---

## Configuration Reference

### EnforcementMode Enum

```python
class EnforcementMode(Enum):
    """Enforcement mode levels."""
    ADVISORY = "advisory"          # Log only, no blocking
    COOPERATIVE = "cooperative"    # Trust agent to respect decisions
    MANDATORY = "mandatory"        # Non-bypassable blocking
```

### EnforcementConfig Dataclass

```python
@dataclass
class EnforcementConfig:
    """
    Configuration for mandatory enforcement.

    Attributes:
        mode: Enforcement level (mandatory recommended for production)
        fail_closed: Block on any error (True = secure default)
        approval_timeout: Max seconds to wait for approval
        retry_attempts: Network retry attempts before fail-closed
        retry_delay: Seconds between retries
        log_all_decisions: Log every allow/block decision
        auto_approve_below: Risk score threshold for auto-approval
        require_approval_above: Risk score threshold for required approval
        block_above: Risk score threshold for automatic block
    """
    mode: EnforcementMode = EnforcementMode.MANDATORY
    fail_closed: bool = True
    approval_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0
    log_all_decisions: bool = True

    # Risk thresholds
    auto_approve_below: int = 30
    require_approval_above: int = 70
    block_above: int = 95

    def __post_init__(self):
        """Validate configuration."""
        if self.mode == EnforcementMode.MANDATORY and not self.fail_closed:
            raise ValueError(
                "Mandatory enforcement requires fail_closed=True. "
                "This is a security requirement."
            )
```

### configure_enforcement()

```python
def configure_enforcement(
    api_key: Optional[str] = None,
    enforcement_mode: str = "mandatory",
    fail_closed: bool = True,
    **kwargs
) -> EnforcedClient:
    """
    Configure global enforcement settings.

    Call this once at application startup to configure governance.

    Example:
        from owkai.enforcement import configure_enforcement

        configure_enforcement(
            api_key="owkai_admin_...",
            enforcement_mode="mandatory",
            fail_closed=True
        )

    Returns:
        The configured EnforcedClient instance
    """
```

---

## Implementation Examples

### Example 1: Database Operations

```python
from owkai.enforcement import EnforcedClient, GovernanceBlockedError

client = EnforcedClient(
    api_key="owkai_admin_...",
    enforcement_mode="mandatory"
)

def execute_database_operation():
    try:
        # Low-risk read - auto-approved
        users = client.execute_governed(
            action=lambda: db.execute("SELECT * FROM users WHERE active=true"),
            action_type="database_read",
            description="Fetch active users",
            tool_name="postgresql",
            target_system="production"
        )
        print(f"Found {len(users)} active users")

        # High-risk delete - requires approval
        deleted = client.execute_governed(
            action=lambda: db.execute("DELETE FROM sessions WHERE expired=true"),
            action_type="database_delete",
            description="Clean up expired sessions",
            tool_name="postgresql",
            target_system="production",
            risk_context={
                "estimated_rows": 10000,
                "table": "sessions"
            }
        )
        print(f"Deleted {deleted} expired sessions")

    except GovernanceBlockedError as e:
        print(f"Operation blocked: {e.blocking_reason}")
        print(f"Policy: {e.policy_name}")
        print(f"Risk score: {e.risk_score}")
```

### Example 2: File System Operations

```python
from owkai.enforcement import governed, configure_enforcement

configure_enforcement(api_key="owkai_admin_...")

@governed(
    action_type="file_delete",
    description="Delete log files older than 30 days",
    tool_name="filesystem",
    target_system="production-server"
)
def cleanup_old_logs(directory: str, days_old: int = 30) -> int:
    """Delete old log files. Governed by OW-AI."""
    import os
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days_old)
    deleted = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.getmtime(filepath) < cutoff.timestamp():
            os.remove(filepath)
            deleted += 1

    return deleted

# This call is governed
deleted_count = cleanup_old_logs("/var/log/app", days_old=30)
```

### Example 3: AWS Operations with boto3

```python
from owkai.enforcement import enable_mandatory_governance

# Enable governance BEFORE importing boto3
enable_mandatory_governance(
    api_key="owkai_admin_...",
    fail_closed=True
)

import boto3

def manage_s3_resources():
    s3 = boto3.client('s3')

    # Auto-approved (low risk)
    buckets = s3.list_buckets()
    print(f"Found {len(buckets['Buckets'])} buckets")

    # Requires approval (high risk)
    try:
        s3.delete_bucket(Bucket='old-backup-bucket')
        print("Bucket deleted")
    except Exception as e:
        if "GovernanceBlocked" in str(type(e).__name__):
            print(f"Cannot delete bucket: {e}")

def manage_ec2_instances():
    ec2 = boto3.client('ec2')

    # Auto-approved
    instances = ec2.describe_instances()

    # CRITICAL risk - may be blocked entirely
    # ec2.terminate_instances(InstanceIds=['i-1234567890abcdef0'])
```

### Example 4: Error Handling Best Practices

```python
from owkai.enforcement import (
    EnforcedClient,
    GovernanceBlockedError,
    ActionRejectedError,
    ApprovalTimeoutError,
    GovernanceUnavailableError,
)

client = EnforcedClient(api_key="owkai_admin_...")

def perform_critical_operation():
    try:
        result = client.execute_governed(
            action=lambda: critical_database_update(),
            action_type="database_write",
            description="Update user permissions",
            tool_name="postgresql",
            target_system="production"
        )
        return {"success": True, "result": result}

    except GovernanceBlockedError as e:
        # Policy permanently blocks this action
        return {
            "success": False,
            "error_type": "blocked",
            "reason": e.blocking_reason,
            "policy": e.policy_name,
            "risk_score": e.risk_score,
            "remediation": e.remediation,
        }

    except ActionRejectedError as e:
        # Human approver rejected the action
        return {
            "success": False,
            "error_type": "rejected",
            "rejected_by": e.rejected_by,
            "reason": e.rejection_reason,
            "can_retry": e.can_resubmit,
            "requirements": e.resubmit_requirements,
        }

    except ApprovalTimeoutError as e:
        # No approver responded in time
        return {
            "success": False,
            "error_type": "timeout",
            "timeout": e.timeout_seconds,
            "pending": e.pending_approvers,
            "suggestion": "Try during business hours",
        }

    except GovernanceUnavailableError as e:
        # Service down - action blocked (fail-closed)
        return {
            "success": False,
            "error_type": "service_unavailable",
            "retry_after": e.retry_after_seconds,
            "fail_mode": e.fail_mode,
        }
```

---

## Next Documents

- [04_MCP_ENFORCEMENT.md](./04_MCP_ENFORCEMENT.md) - MCP server enforcement implementation
- [05_INTEGRATION_GUIDE.md](./05_INTEGRATION_GUIDE.md) - Step-by-step integration guide

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | OW-AI Engineering | Initial release |
