---
title: How Ascend Works
sidebar_position: 1
---

# How Ascend Works

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-CORE-004 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Ascend provides a governance layer between your AI agents and the systems they interact with, ensuring every action is evaluated, logged, and controlled.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR AI AGENTS                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ LangChain │  │ AutoGPT  │  │  Claude  │  │ Custom   │                │
│  │   Agent   │  │   Agent  │  │   Agent  │  │  Agent   │                │
│  └─────┬─────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘                │
│        │              │              │              │                    │
│        └──────────────┴──────────────┴──────────────┘                    │
│                              │                                           │
│                    ┌─────────▼─────────┐                                │
│                    │    Ascend SDK     │                                │
│                    └─────────┬─────────┘                                │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ASCEND PLATFORM   │
                    │  ┌───────────────┐  │
                    │  │ Risk Engine   │  │
                    │  ├───────────────┤  │
                    │  │ Policy Engine │  │
                    │  ├───────────────┤  │
                    │  │ Workflow      │  │
                    │  │ Service       │  │
                    │  ├───────────────┤  │
                    │  │ Audit Logger  │  │
                    │  └───────────────┘  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   YOUR SYSTEMS      │
                    │  ┌─────┐ ┌─────┐   │
                    │  │ DB  │ │ API │   │
                    │  └─────┘ └─────┘   │
                    └─────────────────────┘
```

## The Governance Flow

Every agent action flows through Ascend in a defined sequence:

### 1. Action Submission

When your AI agent wants to perform an action, it submits a request to Ascend:

```python
# SDK submission (planned feature)
result = client.submit_action(
    agent_id="my-agent",
    action_type="write",
    resource="customer_database",
    environment="production",
    contains_pii=True
)
```

### 2. Risk Evaluation

Ascend's Enterprise Risk Engine calculates a hybrid risk score (0-100) based on:

**Source:** `services/enterprise_risk_calculator_v2.py:451-665`

| Component | Weight | Description |
|-----------|--------|-------------|
| Environment | 35% (0-35 points) | Production=35, Staging=18, Development=5 |
| Data Sensitivity | 30% (0-30 points) | PII detection with regex patterns |
| Action Type | 25% (0-25 points) | Delete=25, Write=23, Create=21, Read=10 |
| Operational Context | 10% (0-10 points) | Time of day, maintenance windows |
| Resource Type Multiplier | 0.8x - 1.2x | RDS=1.2x, Lambda=0.8x, S3=1.0x |

**Actual Formula:**
```python
# Source: enterprise_risk_calculator_v2.py:558-593
base_score = environment_score + sensitivity_score + action_score + context_score

# Risk amplification for dangerous combinations
if environment_score >= 30:  # Production
    if sensitivity_score >= 20 and action_score >= 20:
        amplification_bonus = 10  # Production + PII + Destructive
    elif action_score >= 20:
        amplification_bonus = 8  # Production + Destructive

final_score = min((base_score + amplification_bonus) * resource_multiplier, 100)
```

### 3. Risk Level Classification

**Source:** `services/enterprise_risk_calculator_v2.py:595-605`

| Risk Level | Score Range | Typical Handling |
|------------|-------------|------------------|
| Critical | 85-100 | Block and alert security team |
| High | 70-84 | Senior approval required |
| Medium | 45-69 | Single approval required |
| Low | 25-44 | Quick approval or auto-approve |
| Minimal | 0-24 | Auto-approve |

### 4. Workflow Routing

**Source:** `services/workflow_service.py:21-76`

Based on risk score, actions are routed to matching workflows:

```python
# Source: workflow_service.py:21-28
def get_matching_workflows(self, risk_score: float) -> List:
    """Get active workflows that match risk score"""
    workflows = self.db.query(Workflow).filter(
        Workflow.status == 'active'
    ).all()
    return [w for w in workflows if self._check_risk_match(w, risk_score)]
```

Workflows check risk score against trigger conditions:

```python
# Source: workflow_service.py:64-76
def _check_risk_match(self, workflow, risk_score: float) -> bool:
    conditions = workflow.trigger_conditions  # JSON
    min_risk = conditions.get('min_risk', 0)
    max_risk = conditions.get('max_risk', 100)
    return min_risk <= risk_score <= max_risk
```

### 5. Approver Assignment

**Source:** `services/workflow_approver_service.py:17-68`

The Workflow Approver Service assigns qualified approvers:

```python
# Source: workflow_approver_service.py:17-46
def assign_approvers_to_workflow(
    self,
    db: Session,
    workflow_execution_id: int,
    action_id: int,
    risk_score: float,
    required_approval_level: int,
    department: str = "Engineering"
) -> Dict:
    """Assign approvers to a workflow execution"""

    # Get qualified approvers based on risk and level
    approvers = approver_selector.select_approvers(
        db=db,
        risk_score=risk_score,
        approval_level=required_approval_level,
        department=department
    )

    # First approver is primary, rest are backups
    primary = approvers[0]
    backups = approvers[1:3]  # Keep top 2 backups

    return {
        "primary": primary,
        "backups": backups,
        "total_available": len(approvers)
    }
```

### 6. Audit Logging

**Source:** `services/immutable_audit_service.py:22-80`

Every action is logged with immutable hash-chaining:

```python
# Source: immutable_audit_service.py:22-75
def log_event(
    self,
    event_type: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    event_data: Dict[str, Any],
    risk_level: str = "MEDIUM",
    compliance_tags: List[str] = None
) -> ImmutableAuditLog:
    """Create immutable audit log entry with hash-chaining"""

    # Get last log for hash chaining
    last_log = self.db.query(ImmutableAuditLog).order_by(
        desc(ImmutableAuditLog.sequence_number)
    ).first()

    audit_log = ImmutableAuditLog(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        event_data=event_data,
        risk_level=risk_level,
        compliance_tags=compliance_tags or []
    )

    # Calculate content hash
    audit_log.content_hash = audit_log.calculate_content_hash()

    # Hash-chain to previous entry (WORM guarantee)
    previous_hash = last_log.chain_hash if last_log else None
    audit_log.previous_hash = previous_hash
    audit_log.chain_hash = audit_log.calculate_chain_hash(previous_hash)

    # Set retention based on compliance
    audit_log.retention_until = self._calculate_retention_date(compliance_tags)

    self.db.add(audit_log)
    self.db.commit()

    return audit_log
```

## Key Components

### Risk Engine

**Source:** `services/enterprise_risk_calculator_v2.py`

The Enterprise Hybrid Multi-Factor Risk Scoring Engine (v2.0.0) provides:

- **Environment Analysis**: Production vs Staging vs Development environments
- **Data Sensitivity Detection**: Enhanced PII detection with regex patterns for SSN, credit cards, emails, phone numbers
- **Action Type Risk**: Based on CVSS scoring or action type lookup (delete, write, create, read)
- **Operational Context**: Maintenance windows, peak hours, anomaly detection
- **Resource Type Weighting**: Database operations (1.2x), Lambda functions (0.8x), IAM operations (1.2x)
- **Error Handling**: Graceful fallback to conservative risk scores on validation failures

### Workflow Service

**Source:** `services/workflow_service.py`

Enterprise workflow service handles:

- **Workflow Matching**: Query active workflows and match against risk score
- **Workflow Triggering**: Create workflow executions linked to actions
- **Stage Management**: Track current stage and execution status

### Approver Service

**Source:** `services/workflow_approver_service.py`

Automated approver assignment:

- **Primary/Backup Assignment**: Assign primary approver with 2 backup approvers
- **Risk-Based Selection**: Select approvers qualified for risk level and approval level
- **Department Routing**: Route to appropriate department approvers
- **Reassignment**: Automatic reassignment when primary approver unavailable

### Audit Logger

**Source:** `services/immutable_audit_service.py`

Immutable compliance logging:

- **Hash-Chaining**: Each entry cryptographically linked to previous entry (WORM guarantee)
- **Integrity Verification**: `verify_chain_integrity()` method detects tampering
- **Compliance Retention**: Automatic retention periods (SOX: 7 years, HIPAA: 6 years, PCI: 1 year)
- **Content Hashing**: SHA-256 hashing of all event data

## Multi-Tenancy

**Source:** `dependencies.py:302-318`

Ascend enforces complete data isolation between organizations:

```python
# Source: dependencies.py:302-318
def get_organization_filter(current_user: dict = Depends(require_organization_context)):
    """
    Get organization filter for database queries.

    Returns the organization_id that MUST be used in all database queries
    to ensure multi-tenant data isolation.

    Usage in routes:
        @router.get("/data")
        async def get_data(
            org_filter: int = Depends(get_organization_filter),
            db: Session = Depends(get_db)
        ):
            # All queries MUST filter by org_filter
            data = db.query(Model).filter(Model.organization_id == org_filter).all()
    """
    return current_user.get("organization_id")
```

**Implementation Pattern:**

All 200+ route endpoints use the organization filter dependency:

```python
@router.get("/alerts")
async def get_alerts(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    # Query automatically filtered by organization
    alerts = db.query(Alert).filter(
        Alert.organization_id == org_id
    ).all()
```

**Source:** See usage in `main.py`, `routes/agent_routes.py`, `routes/alert_routes.py`, etc.

## Security Model

### Data Protection

**Source:** Database models in `models.py`

- **Row-Level Security**: Every table has `organization_id` column with index
- **Composite Constraints**: Email uniqueness enforced per-organization (not globally)
- **Encrypted Storage**: Sensitive data stored with encryption at rest

### Access Control

**Source:** `dependencies.py:119-242`

- **JWT Authentication**: HttpOnly cookie sessions with CSRF protection
- **Role-Based Access**: Admin, Manager, User roles
- **Organization Context**: Mandatory organization validation on every request

### Compliance

**Source:** `services/immutable_audit_service.py:165-186`

Compliance retention periods:
- SOC 2: 7 years (2555 days)
- HIPAA: 6 years (2190 days)
- PCI-DSS: 1 year (365 days)
- GDPR: 6 years (2190 days)
- CCPA: 3 years (1095 days)
- FERPA: 5 years (1825 days)

## Next Steps

- [Risk Scoring](/core-concepts/risk-scoring) - Deep dive into risk calculation
- [Approval Workflows](/core-concepts/approval-workflows) - Configure human review
- [Multi-Tenancy](/core-concepts/multi-tenancy) - Enterprise deployment
- [Audit Logging](/core-concepts/audit-logging) - Compliance logging
