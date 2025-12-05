# Approval Workflows

Approval workflows enable human oversight of AI agent actions. Ascend automatically routes high-risk actions to qualified approvers based on risk scores and organizational policies.

## How Workflows Work

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        APPROVAL WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Agent Action ──► Risk Score ──► Workflow Matching ──► Approver Assign  │
│                                                                          │
│       ┌─────────────────────────────────────────────────────────┐       │
│       │                   WORKFLOW MATCHING                      │       │
│       ├─────────────────────────────────────────────────────────┤       │
│       │  1. Query active workflows from database               │       │
│       │  2. Check risk score against trigger conditions        │       │
│       │  3. Match workflow if min_risk ≤ score ≤ max_risk     │       │
│       └─────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Workflow Service

**Source:** `services/workflow_service.py`

The Workflow Service handles workflow execution and matching.

### Getting Matching Workflows

**Source:** `workflow_service.py:21-31`

```python
# Source: workflow_service.py:21-28
def get_matching_workflows(self, risk_score: float) -> List:
    """Get active workflows that match risk score"""
    try:
        from models import Workflow
        workflows = self.db.query(Workflow).filter(
            Workflow.status == 'active'
        ).all()
        return [w for w in workflows if self._check_risk_match(w, risk_score)]
    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        return []
```

### Risk Score Matching

**Source:** `workflow_service.py:64-76`

```python
# Source: workflow_service.py:64-76
def _check_risk_match(self, workflow, risk_score: float) -> bool:
    """Check if workflow matches risk score"""
    try:
        conditions = workflow.trigger_conditions
        if isinstance(conditions, str):
            conditions = json.loads(conditions)
        if not conditions:
            return True  # No conditions = matches all
        min_risk = conditions.get('min_risk', 0)
        max_risk = conditions.get('max_risk', 100)
        return min_risk <= risk_score <= max_risk
    except:
        return False
```

**Example Trigger Conditions:**

```json
{
  "min_risk": 70,
  "max_risk": 100,
  "resource_types": ["database", "rds"],
  "environments": ["production"]
}
```

### Triggering Workflow Execution

**Source:** `workflow_service.py:33-62`

```python
# Source: workflow_service.py:33-62
def trigger_workflow(self, workflow_id: str, action_id: int, triggered_by: str = "system") -> Dict:
    """Trigger a workflow execution"""
    try:
        result = self.db.execute(text("""
            INSERT INTO workflow_executions (
                workflow_id, action_id, executed_by, execution_status,
                current_stage, started_at
            )
            VALUES (:workflow_id, :action_id, :executed_by, 'in_progress', 0, :started_at)
            RETURNING id
        """), {
            "workflow_id": workflow_id,
            "action_id": action_id,
            "executed_by": triggered_by,
            "started_at": datetime.utcnow()
        })

        self.db.commit()
        execution_id = result.fetchone()[0]

        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "action_id": action_id,
            "status": "in_progress"
        }
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to trigger workflow: {e}")
        raise
```

## Approver Assignment

**Source:** `services/workflow_approver_service.py`

The Workflow Approver Service automatically assigns qualified approvers when workflows are created.

### Primary and Backup Approvers

**Source:** `workflow_approver_service.py:17-68`

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
    """
    Assign approvers to a workflow execution
    Returns primary and backup approvers
    """

    # Get qualified approvers
    approvers = approver_selector.select_approvers(
        db=db,
        risk_score=risk_score,
        approval_level=required_approval_level,
        department=department
    )

    if not approvers:
        logger.error(f"No approvers found for workflow {workflow_execution_id}")
        return {"primary": None, "backups": []}

    # First approver is primary, rest are backups
    primary = approvers[0]
    backups = approvers[1:3]  # Keep top 2 backups

    # Update agent_action with primary approver
    self._assign_to_action(db, action_id, primary["email"])

    # Store approver chain in workflow_execution
    self._store_approver_chain(
        db, workflow_execution_id, primary, backups
    )

    return {
        "primary": primary,
        "backups": backups,
        "total_available": len(approvers)
    }
```

### Updating Action with Approver

**Source:** `workflow_approver_service.py:70-80`

```python
# Source: workflow_approver_service.py:70-80
def _assign_to_action(self, db: Session, action_id: int, approver_email: str):
    """Update agent_action with assigned approver"""
    query = text("""
        UPDATE agent_actions
        SET pending_approvers = :email,
            updated_at = NOW()
        WHERE id = :action_id
    """)

    db.execute(query, {"email": approver_email, "action_id": action_id})
    db.commit()
```

### Storing Approver Chain

**Source:** `workflow_approver_service.py:82-108`

```python
# Source: workflow_approver_service.py:82-108
def _store_approver_chain(
    self,
    db: Session,
    workflow_execution_id: int,
    primary: Dict,
    backups: List[Dict]
):
    """Store approver information in workflow_execution metadata"""
    approver_data = {
        "primary_approver": {
            "email": primary["email"],
            "level": primary["approval_level"],
            "department": primary["department"]
        },
        "backup_approvers": [
            {
                "email": b["email"],
                "level": b["approval_level"],
                "department": b["department"]
            }
            for b in backups
        ]
    }

    # Store in workflow_executions metadata column (JSONB)
    logger.info(f"Approver chain for workflow {workflow_execution_id}: {approver_data}")
```

## Reassignment When Unavailable

**Source:** `workflow_approver_service.py:110-153`

```python
# Source: workflow_approver_service.py:110-153
def reassign_on_unavailable(
    self,
    db: Session,
    action_id: int,
    unavailable_email: str
) -> str:
    """
    Reassign to backup approver if primary is unavailable
    Returns new approver email
    """
    logger.warning(f"Primary approver {unavailable_email} unavailable for action {action_id}")

    # Get action details to find new approver
    query = text("""
        SELECT risk_score, required_approval_level, user_id
        FROM agent_actions
        WHERE id = :action_id
    """)

    result = db.execute(query, {"action_id": action_id}).fetchone()
    if not result:
        return None

    risk_score, req_level, _ = result

    # Get new approvers, excluding unavailable one
    approvers = approver_selector.select_approvers(
        db=db,
        risk_score=risk_score,
        approval_level=req_level
    )

    # Filter out unavailable approver
    available = [a for a in approvers if a["email"] != unavailable_email]

    if not available:
        logger.error(f"No alternative approvers for action {action_id}")
        return None

    new_approver = available[0]["email"]
    self._assign_to_action(db, action_id, new_approver)

    logger.info(f"Reassigned action {action_id} to {new_approver}")
    return new_approver
```

## Workflow Database Schema

**Source:** `models.py` (Workflow table)

### Workflow Model

```python
class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, paused, archived
    trigger_conditions = Column(JSONB, nullable=True)  # JSON conditions for matching
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=True)
```

### Workflow Execution Model

```python
class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    action_id = Column(Integer, ForeignKey("agent_actions.id"), nullable=False)
    executed_by = Column(String, nullable=False)  # user_id or "system"
    execution_status = Column(String, default="in_progress")  # in_progress, completed, failed
    current_stage = Column(Integer, default=0)  # Current approval stage
    started_at = Column(DateTime, default=datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSONB, nullable=True)  # Stores approver_chain and other data
```

## Example Workflow Configuration

### High-Risk Database Operations

```json
{
  "name": "Production Database Changes",
  "description": "Approval workflow for production database modifications",
  "status": "active",
  "trigger_conditions": {
    "min_risk": 70,
    "max_risk": 100,
    "resource_types": ["rds", "database", "aurora"],
    "environments": ["production"],
    "action_types": ["write", "delete", "update"]
  },
  "approval_levels": [
    {
      "level": 1,
      "required_role": "senior_engineer",
      "approval_threshold": 1
    },
    {
      "level": 2,
      "required_role": "engineering_manager",
      "approval_threshold": 1
    }
  ]
}
```

### Medium-Risk Changes

```json
{
  "name": "Standard Approval",
  "description": "Single approval for medium-risk actions",
  "status": "active",
  "trigger_conditions": {
    "min_risk": 45,
    "max_risk": 69
  },
  "approval_levels": [
    {
      "level": 1,
      "required_role": "engineer",
      "approval_threshold": 1
    }
  ]
}
```

## User Approval Levels

**Source:** `models.py:48-50` (User model)

Users have approval qualifications:

```python
class User(Base):
    # ... other fields ...

    # Enterprise authorization fields
    approval_level = Column(Integer, default=1)  # 1=Junior, 2=Senior, 3=Manager, 4=Executive
    is_emergency_approver = Column(Boolean, default=False)  # Can approve emergency actions
    max_risk_approval = Column(Integer, default=50)  # Maximum risk score they can approve
```

| Approval Level | Role | Max Risk Score | Typical Actions |
|----------------|------|----------------|-----------------|
| 1 | Junior Approver | 50 | Low-risk actions only |
| 2 | Senior Approver | 70 | Medium to high-risk |
| 3 | Manager | 85 | High-risk and critical |
| 4 | Executive | 100 | Any risk level, emergency overrides |

## Integration Example

### Backend Workflow Routing

```python
from services.workflow_service import WorkflowService
from services.workflow_approver_service import workflow_approver_service

# 1. Get workflows matching risk score
workflow_service = WorkflowService(db)
matching_workflows = workflow_service.get_matching_workflows(risk_score=75)

if matching_workflows:
    # 2. Trigger the first matching workflow
    workflow = matching_workflows[0]
    execution = workflow_service.trigger_workflow(
        workflow_id=workflow.id,
        action_id=action_id,
        triggered_by="system"
    )

    # 3. Assign approvers
    assignment = workflow_approver_service.assign_approvers_to_workflow(
        db=db,
        workflow_execution_id=execution["execution_id"],
        action_id=action_id,
        risk_score=75,
        required_approval_level=2,
        department="Engineering"
    )

    # 4. Notify primary approver
    primary = assignment["primary"]
    # Send email/Slack notification to primary["email"]
```

## Current Limitations

The current implementation provides basic workflow routing and approver assignment. The following features are **not yet implemented**:

### Not Yet Available

- **Multi-level approval chains**: Sequential approval through multiple levels
- **Parallel approval**: Multiple approvers must all approve
- **Timeout handling**: Auto-escalate or deny on timeout
- **Delegation**: Out-of-office approver substitution
- **Email/Slack notifications**: Automated approver notifications (requires integration)
- **Approval UI**: Web-based approval interface (frontend implementation pending)
- **Workflow templates**: Pre-built workflow configurations
- **Conditional routing**: Complex routing logic based on multiple factors

### Planned Enhancements

Future versions will include:
- Multi-stage approval workflows with timeout handling
- Notification integrations (Email, Slack, Teams)
- Approval dashboard UI
- Delegation and out-of-office management
- Workflow analytics and metrics
- Approval SLA tracking

## Best Practices

### 1. Define Clear Risk Boundaries

```json
// Good: Clear, non-overlapping ranges
{
  "workflows": [
    {"min_risk": 0, "max_risk": 44, "approvers": "auto_approve"},
    {"min_risk": 45, "max_risk": 69, "approvers": "single_approval"},
    {"min_risk": 70, "max_risk": 100, "approvers": "senior_approval"}
  ]
}

// Bad: Overlapping ranges
{
  "workflows": [
    {"min_risk": 0, "max_risk": 50},
    {"min_risk": 45, "max_risk": 75}  // Overlaps with previous
  ]
}
```

### 2. Maintain Backup Approvers

```python
# Always check backup approvers exist
assignment = workflow_approver_service.assign_approvers_to_workflow(...)

if assignment["primary"] is None:
    logger.error("No primary approver available")
    # Escalate to emergency approvers or deny action

if len(assignment["backups"]) < 2:
    logger.warning("Insufficient backup approvers")
```

### 3. Handle Unavailability

```python
# If primary approver is unavailable
if approver_unavailable:
    new_approver = workflow_approver_service.reassign_on_unavailable(
        db=db,
        action_id=action_id,
        unavailable_email=original_approver
    )

    if new_approver is None:
        # No alternative approvers - escalate or deny
        pass
```

## Next Steps

- [Risk Scoring](/core-concepts/risk-scoring) - Understanding risk calculations that drive workflow routing
- [Multi-Tenancy](/core-concepts/multi-tenancy) - Organization isolation for workflows
- [Audit Logging](/core-concepts/audit-logging) - Workflow execution audit trails
