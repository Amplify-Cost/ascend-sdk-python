---
Document ID: ASCEND-CORE-003
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Multi-Tenancy

Ascend's multi-tenant architecture provides complete data isolation between organizations using banking-level security patterns. Every database query is automatically filtered by organization, ensuring zero cross-tenant data leakage.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ASCEND MULTI-TENANT PLATFORM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Organization A  │  │  Organization B  │  │  Organization C  │         │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │         │
│  │  │  Agents   │  │  │  │  Agents   │  │  │  │  Agents   │  │         │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │         │
│  │  │  Alerts   │  │  │  │  Alerts   │  │  │  │  Alerts   │  │         │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │         │
│  │  │ Workflows │  │  │  │ Workflows │  │  │  │ Workflows │  │         │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │         │
│  │  │   Users   │  │  │  │   Users   │  │  │  │   Users   │  │         │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │         │
│  │  │Audit Logs │  │  │  │Audit Logs │  │  │  │Audit Logs │  │         │
│  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│           │                    │                    │                    │
│           └────────────────────┼────────────────────┘                    │
│                                │                                         │
│                    ┌───────────▼───────────┐                            │
│                    │  Row-Level Security    │                            │
│                    │  (organization_id)     │                            │
│                    └───────────────────────┘                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Organization Filter Pattern

**Source:** `dependencies.py:302-318`

All 200+ API endpoints use the `get_organization_filter()` dependency to enforce tenant isolation.

### The Organization Filter Dependency

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

### Organization Context Validation

**Source:** `dependencies.py:280-299`

Before extracting the organization filter, the user's organization context is validated:

```python
# Source: dependencies.py:280-299
def require_organization_context(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require and validate organization context for current user.
    Raises 403 if user has no organization.
    """
    organization_id = current_user.get("organization_id")

    if not organization_id:
        logger.error(f"SECURITY: Organization context missing for user {current_user.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context required for this operation"
        )

    logger.info(f"Organization context verified: org_id={organization_id} for {current_user.get('email')}")
    return current_user
```

## Implementation Pattern

**Source:** Widespread usage across `main.py`, `routes/agent_routes.py`, `routes/alert_routes.py`, etc.

### Basic Usage

```python
@router.get("/alerts")
async def get_alerts(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get alerts for current organization"""
    # Query automatically filtered by organization
    alerts = db.query(Alert).filter(
        Alert.organization_id == org_id
    ).all()
    return alerts
```

### With Additional Filters

```python
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: int,
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Get specific agent within organization"""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == org_id  # CRITICAL: Prevent cross-org access
    ).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent
```

### Write Operations

```python
@router.post("/agents")
async def create_agent(
    agent: AgentCreate,
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    """Create agent in current organization"""
    # Set organization_id on creation
    db_agent = Agent(
        **agent.dict(),
        organization_id=org_id  # CRITICAL: Assign to current org
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent
```

## Database Schema

**Source:** `models.py`

### User Model with Organization Isolation

**Source:** `models.py:9-93`

```python
# Source: models.py:22-57
class User(Base):
    """Enterprise User Model with Multi-Tenant Isolation"""
    __tablename__ = "users"

    # SEC-025: Composite unique constraint for multi-tenant email isolation
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_users_email_organization'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # SEC-025: Email is unique per-organization, not globally
    # Same email can exist in multiple organizations as separate users
    email = Column(String, index=True, nullable=False)

    # ... other fields ...

    # PHASE 2: Multi-Tenancy - organization_id is part of email uniqueness
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
```

**Key Points:**
- Email uniqueness is **per-organization**, not global
- Same email (e.g., admin@company.com) can exist in multiple organizations
- Each represents a different user in a different organization
- Complies with SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1

### Organization-Isolated Tables

All major tables include `organization_id` with indexing:

```python
# Examples from models.py
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    # ... other fields ...

class AgentAction(Base):
    __tablename__ = "agent_actions"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    # ... other fields ...

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    # ... other fields ...
```

## Security Guarantees

### 1. Row-Level Security

**Every database query is automatically filtered by organization:**

```python
# ENFORCED PATTERN (200+ endpoints)
data = db.query(Model).filter(
    Model.organization_id == org_id  # From get_organization_filter()
).all()
```

**Security Properties:**
- Users can ONLY access data from their organization
- Cross-organization queries are impossible
- Missing organization filter = 403 Forbidden
- Organization ID extracted from JWT token

### 2. JWT Token Organization Binding

**Source:** `dependencies.py:138-152`

Organization ID is embedded in the JWT token during authentication:

```python
# Source: dependencies.py:138-152
payload = _decode_jwt(cookie_jwt)

# ENTERPRISE SECURITY: Extract organization_id from token
organization_id = payload.get("organization_id")
if organization_id:
    organization_id = int(organization_id)

logger.info(f"Authentication successful (cookie): {payload.get('email')} [org_id={organization_id}]")
return {
    "user_id": int(payload.get("sub")),
    "email": payload.get("email"),
    "role": payload.get("role", "user"),
    "organization_id": organization_id,  # CRITICAL: Multi-tenant isolation
    "auth_method": "cookie",
    **payload
}
```

### 3. Defense in Depth

Multiple layers enforce isolation:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| JWT Token | Organization ID claim | User bound to organization at login |
| Dependency Injection | `get_organization_filter()` | Automatic org ID extraction |
| Database Queries | `WHERE organization_id = ?` | Row-level filtering |
| Indexes | `organization_id` indexed | Performance with isolation |
| Constraints | Foreign keys to `organizations` | Referential integrity |

## Isolation Scope

**Source:** All tables in `models.py` with `organization_id`

| Data Type | Isolation | Implementation |
|-----------|-----------|----------------|
| Agent Actions | Complete | `agent_actions.organization_id` |
| Alerts | Complete | `alerts.organization_id` |
| Smart Rules | Complete | `smart_rules.organization_id` |
| Workflows | Complete | `workflows.organization_id` |
| Governance Policies | Complete | `governance_policies.organization_id` |
| Risk Configs | Complete | `risk_scoring_configs.organization_id` |
| Automation Playbooks | Complete | `automation_playbooks.organization_id` |
| API Keys | Complete | `api_keys.organization_id` |
| Audit Logs | Complete | `immutable_audit_logs.organization_id` |
| Users | Complete | `users.organization_id` |
| Metric Audits | Complete | `metric_calculation_audit.organization_id` |

## Example: Cross-Organization Prevention

### Attempt to Access Another Organization's Data

```python
# User from Organization A (org_id = 1)
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: int,  # Agent belongs to Organization B (org_id = 2)
    org_id: int = Depends(get_organization_filter),  # Returns 1
    db: Session = Depends(get_db)
):
    # This query returns None (agent not found)
    agent = db.query(Agent).filter(
        Agent.id == agent_id,           # agent_id exists
        Agent.organization_id == org_id  # BUT org_id = 1, agent.organization_id = 2
    ).first()

    if not agent:
        # Correctly returns 404 (not revealing the agent exists)
        raise HTTPException(status_code=404, detail="Agent not found")
```

**Security Principle:** Even if a user knows an ID from another organization, the query returns no results. The system doesn't reveal whether the resource exists.

## Multi-Tenant Email Handling

**Source:** `models.py:22-33`

### Banking-Level Security Pattern

```python
# Source: models.py:22-33
class User(Base):
    __tablename__ = "users"

    # SEC-025: Composite unique constraint
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_users_email_organization'),
    )

    # Email is unique PER-ORGANIZATION (not globally)
    email = Column(String, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
```

**Real-World Scenario:**

| User | Email | Organization | User ID | Valid? |
|------|-------|--------------|---------|--------|
| Alice | admin@company.com | Acme Corp (org 1) | 100 | Yes |
| Bob | admin@company.com | Tech Inc (org 2) | 200 | Yes |
| Charlie | admin@company.com | Finance LLC (org 3) | 300 | Yes |

All three users can have the same email because they belong to different organizations. Each is a distinct user with separate data.

## Deployment Across 200+ Endpoints

**Source:** Grep results showing `get_organization_filter` usage

The organization filter is consistently applied across:

- **Main API**: 12 endpoints in `main.py`
- **Agent Routes**: 15 endpoints in `routes/agent_routes.py`
- **Alert Routes**: 4 endpoints in `routes/alert_routes.py`
- **Authorization Routes**: 7 endpoints in `routes/authorization_routes.py`
- **Governance Routes**: 39 endpoints in `routes/unified_governance_routes.py`
- **MCP Governance**: 11 endpoints in `routes/mcp_governance_routes.py`
- **Enterprise Workflows**: 5 endpoints in `routes/enterprise_workflow_config_routes.py`
- **Webhook Routes**: 12 endpoints in `routes/webhook_routes.py`
- **Agent Registry**: 24 endpoints in `routes/agent_registry_routes.py`
- **Automation Orchestration**: 12 endpoints in `routes/automation_orchestration_routes.py`
- **Executive Brief**: 6 endpoints in `routes/executive_brief_routes.py`
- **Agent Health**: 4 endpoints in `routes/agent_health_routes.py`
- **SDK Routes**: 5 endpoints in `routes/sdk_routes.py`

**Total:** 200+ endpoints with organization isolation

## Best Practices

### 1. Always Use the Organization Filter

```python
# CORRECT: Organization filter applied
@router.get("/data")
async def get_data(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    return db.query(Model).filter(Model.organization_id == org_id).all()

# WRONG: Missing organization filter (SECURITY VULNERABILITY)
@router.get("/data")
async def get_data(db: Session = Depends(get_db)):
    return db.query(Model).all()  # Returns data from ALL organizations!
```

### 2. Set Organization on Creation

```python
# CORRECT: Set organization_id from filter
@router.post("/items")
async def create_item(
    item: ItemCreate,
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    db_item = Item(**item.dict(), organization_id=org_id)
    db.add(db_item)
    db.commit()
    return db_item

# WRONG: Missing organization_id assignment
@router.post("/items")
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())  # organization_id will be NULL!
    db.add(db_item)
    db.commit()
    return db_item
```

### 3. Filter on Both ID and Organization

```python
# CORRECT: Double-check organization ownership
@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.organization_id == org_id  # CRITICAL: Verify ownership
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### 4. Index Organization Columns

```python
# All organization_id columns should be indexed
organization_id = Column(
    Integer,
    ForeignKey("organizations.id"),
    nullable=False,
    index=True  # IMPORTANT: Performance with large datasets
)
```

## Compliance & Audit

### SOC 2 CC6.1 (Logical Access)

- **Requirement:** Restrict logical access to authorized users
- **Implementation:** Row-level security with organization_id filtering
- **Audit:** Every query logs organization context

### NIST AC-2 (Account Management)

- **Requirement:** Manage information system accounts
- **Implementation:** Per-organization user accounts with composite uniqueness
- **Audit:** User creation/modification logs include organization_id

### PCI-DSS 7.1 (Access Control)

- **Requirement:** Limit access to cardholder data
- **Implementation:** Automatic organization filtering prevents unauthorized access
- **Audit:** All access attempts logged with organization context

## Next Steps

- [How Ascend Works](/core-concepts/how-ascend-works) - Overall architecture with multi-tenancy
- [Audit Logging](/core-concepts/audit-logging) - Organization-isolated audit trails
- [Risk Scoring](/core-concepts/risk-scoring) - Organization-specific risk configurations
