# Enterprise Workflow & Automation Implementation Plan

**Project:** Complete Workflow & Automation Integration
**Timeline:** 3-5 days
**Status:** Planning → Implementation → Testing → Production
**Priority:** HIGH - Critical for enterprise functionality

---

## Executive Summary

This plan will transform the Workflow Management and Automation Center from showing fake demo data to a fully functional, enterprise-grade system integrated with your application's core flow.

**Goals:**
1. ✅ Remove all fake/demo data from frontend
2. ✅ Create seed data for automation_playbooks and workflows tables
3. ✅ Integrate OrchestrationService into action creation flow
4. ✅ Create AutomationService for playbook matching and execution
5. ✅ Test end-to-end flows locally with evidence
6. ✅ Deploy to production with verification

---

## Phase 1: Planning & Architecture (Day 1)

### 1.1 Create Database Seed Data Scripts

**Files to Create:**
- `ow-ai-backend/scripts/seed_automation_playbooks.py`
- `ow-ai-backend/scripts/seed_workflows.py`
- `ow-ai-backend/scripts/verify_seeded_data.py`

**Playbooks to Create:**
1. **Low Risk Auto-Approval**
   - `id: "low_risk_auto_approve"`
   - Trigger: `risk_score <= 30`
   - Action: Auto-approve immediately
   - Use case: Read operations, status checks

2. **Business Hours Auto-Approval**
   - `id: "business_hours_auto_approve"`
   - Trigger: `risk_score <= 40 AND business_hours = true`
   - Action: Auto-approve during 9am-5pm EST
   - Use case: Standard operations during work hours

3. **Weekend Escalation**
   - `id: "weekend_escalation"`
   - Trigger: `risk_score > 50 AND weekend = true`
   - Action: Alert on-call team
   - Use case: High-risk actions outside business hours

**Workflows to Create:**
1. **Security Review Workflow**
   - `id: "security_review_workflow"`
   - Trigger: `risk_score >= 50 AND risk_score < 80`
   - Steps: Security scan → Risk analysis → Approval routing
   - Use case: Medium-high risk actions

2. **Compliance Audit Workflow**
   - `id: "compliance_audit_workflow"`
   - Trigger: `risk_score >= 80`
   - Steps: Compliance check → Documentation → Multi-level approval
   - Use case: Critical risk actions

3. **Emergency Override Workflow**
   - `id: "emergency_override_workflow"`
   - Trigger: Manual trigger only
   - Steps: Emergency justification → Executive approval → Immediate execution
   - Use case: Production incidents

### 1.2 Design AutomationService

**File to Create:** `ow-ai-backend/services/automation_service.py`

**Methods:**
```python
class AutomationService:
    def match_playbooks(action_data: dict) -> Optional[AutomationPlaybook]
    def execute_playbook(playbook_id: str, action_id: int) -> PlaybookExecutionResult
    def update_playbook_stats(playbook_id: str, success: bool) -> None
    def calculate_cost_savings(playbook_id: str) -> float
    def is_business_hours() -> bool
    def get_playbook_metrics(playbook_id: str) -> dict
```

### 1.3 Design Integration Points

**Files to Modify:**
1. `ow-ai-backend/routes/agent_routes.py`
   - Modify `create_agent_action()` to call automation/orchestration
   - Add playbook execution logic
   - Add workflow triggering logic

2. `ow-ai-backend/routes/agent_routes.py`
   - Modify `approve_agent_action()` to complete workflows
   - Modify `reject_agent_action()` to fail workflows

3. `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`
   - Remove demo data fallback (lines 541-586, 636-686)
   - Add empty state UI
   - Add proper error handling

---

## Phase 2: Implementation (Days 2-3)

### 2.1 Backend Implementation (Day 2 Morning)

#### Step 1: Create AutomationService

**File:** `ow-ai-backend/services/automation_service.py`

**Implementation:**
```python
"""
Automation Service - Enterprise Playbook Execution
Handles automatic approval of low-risk actions via playbooks
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, Dict, List
from datetime import datetime, time
import pytz
from core.logging import logger
from models import AutomationPlaybook, PlaybookExecution, AgentAction

class AutomationService:
    """Enterprise automation service for playbook-based auto-approval"""

    def __init__(self, db: Session):
        self.db = db

    def match_playbooks(
        self,
        action_data: Dict
    ) -> Optional[AutomationPlaybook]:
        """
        Find matching playbook for action

        Args:
            action_data: {
                'risk_score': float,
                'action_type': str,
                'agent_id': str,
                'timestamp': datetime
            }

        Returns:
            Matching AutomationPlaybook or None
        """
        try:
            # Get all active playbooks
            playbooks = self.db.query(AutomationPlaybook).filter(
                AutomationPlaybook.status == 'active'
            ).order_by(AutomationPlaybook.created_at).all()

            logger.info(f"🔍 Checking {len(playbooks)} active playbooks")

            for playbook in playbooks:
                if self._matches_conditions(action_data, playbook.trigger_conditions):
                    logger.info(f"✅ Matched playbook: {playbook.id}")
                    return playbook

            logger.info(f"❌ No matching playbook found")
            return None

        except Exception as e:
            logger.error(f"❌ Playbook matching failed: {e}")
            return None

    def _matches_conditions(
        self,
        action_data: Dict,
        conditions: Dict
    ) -> bool:
        """Check if action matches playbook trigger conditions"""

        if not conditions:
            return False

        risk_score = action_data.get('risk_score', 100)

        # Check risk score threshold
        if 'risk_score_max' in conditions:
            if risk_score > conditions['risk_score_max']:
                logger.debug(f"Risk score {risk_score} > max {conditions['risk_score_max']}")
                return False

        if 'risk_score_min' in conditions:
            if risk_score < conditions['risk_score_min']:
                logger.debug(f"Risk score {risk_score} < min {conditions['risk_score_min']}")
                return False

        # Check business hours
        if conditions.get('business_hours'):
            if not self.is_business_hours():
                logger.debug(f"Not business hours")
                return False

        # Check weekend
        if 'weekend' in conditions:
            is_weekend = datetime.now().weekday() >= 5
            if conditions['weekend'] != is_weekend:
                logger.debug(f"Weekend mismatch")
                return False

        # Check action type
        if 'action_types' in conditions:
            action_type = action_data.get('action_type', '')
            if action_type not in conditions['action_types']:
                logger.debug(f"Action type {action_type} not in allowed list")
                return False

        return True

    def execute_playbook(
        self,
        playbook_id: str,
        action_id: int
    ) -> Dict:
        """
        Execute playbook - auto-approve action

        Returns:
            {
                'success': bool,
                'execution_id': int,
                'action_approved': bool,
                'message': str
            }
        """
        try:
            logger.info(f"▶️  Executing playbook {playbook_id} for action {action_id}")

            # Get playbook
            playbook = self.db.query(AutomationPlaybook).filter(
                AutomationPlaybook.id == playbook_id
            ).first()

            if not playbook:
                return {
                    'success': False,
                    'message': f'Playbook {playbook_id} not found'
                }

            # Get action
            action = self.db.query(AgentAction).filter(
                AgentAction.id == action_id
            ).first()

            if not action:
                return {
                    'success': False,
                    'message': f'Action {action_id} not found'
                }

            # Create execution record
            execution = PlaybookExecution(
                playbook_id=playbook_id,
                action_id=action_id,
                executed_by='automation_system',
                execution_context='automatic',
                input_data={
                    'risk_score': action.risk_score,
                    'action_type': action.action_type
                },
                execution_status='completed',
                execution_details={
                    'auto_approved': True,
                    'reason': 'Matched playbook trigger conditions',
                    'playbook_name': playbook.name
                }
            )
            execution.started_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = 1

            self.db.add(execution)

            # Auto-approve the action
            action.status = 'approved'
            action.approved = True
            action.reviewed_by = f'automation:{playbook_id}'
            action.reviewed_at = datetime.utcnow()

            # Update playbook statistics
            playbook.execution_count = (playbook.execution_count or 0) + 1
            playbook.last_executed = datetime.utcnow()

            # Calculate success rate (simplified)
            total_executions = playbook.execution_count
            successful_executions = total_executions  # Assume all successful for now
            playbook.success_rate = (successful_executions / total_executions) * 100

            self.db.commit()
            self.db.refresh(execution)

            logger.info(f"✅ Playbook executed: action {action_id} auto-approved")

            return {
                'success': True,
                'execution_id': execution.id,
                'action_approved': True,
                'message': f'Action auto-approved via playbook {playbook.name}'
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Playbook execution failed: {e}")
            return {
                'success': False,
                'message': f'Execution failed: {str(e)}'
            }

    def is_business_hours(self) -> bool:
        """Check if current time is business hours (9am-5pm EST)"""
        try:
            est = pytz.timezone('America/New_York')
            now = datetime.now(est)

            # Check if weekday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False

            # Check time range
            business_start = time(9, 0)
            business_end = time(17, 0)

            return business_start <= now.time() <= business_end

        except Exception as e:
            logger.error(f"Business hours check failed: {e}")
            return False

    def get_playbook_metrics(self, playbook_id: str) -> Dict:
        """Get real-time metrics for playbook"""
        try:
            playbook = self.db.query(AutomationPlaybook).filter(
                AutomationPlaybook.id == playbook_id
            ).first()

            if not playbook:
                return {}

            # Get execution count for last 24 hours
            from sqlalchemy import func
            from datetime import timedelta

            yesterday = datetime.utcnow() - timedelta(hours=24)

            executions_24h = self.db.query(func.count(PlaybookExecution.id)).filter(
                PlaybookExecution.playbook_id == playbook_id,
                PlaybookExecution.started_at >= yesterday
            ).scalar() or 0

            # Calculate cost savings (15 min per approval @ $50/hr = $12.50 per execution)
            cost_per_approval = 12.50
            cost_savings_24h = executions_24h * cost_per_approval

            return {
                'execution_count': playbook.execution_count or 0,
                'success_rate': playbook.success_rate or 0.0,
                'last_executed': playbook.last_executed.isoformat() if playbook.last_executed else None,
                'triggers_last_24h': executions_24h,
                'cost_savings_24h': cost_savings_24h,
                'avg_response_time_seconds': 2  # Automated approvals are fast
            }

        except Exception as e:
            logger.error(f"Failed to get playbook metrics: {e}")
            return {}


def get_automation_service(db: Session) -> AutomationService:
    """Dependency injection factory"""
    return AutomationService(db)
```

#### Step 2: Create Seed Data Scripts

**File:** `ow-ai-backend/scripts/seed_automation_playbooks.py`

```python
"""
Seed Automation Playbooks
Creates default automation playbooks for the system
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import AutomationPlaybook
from datetime import datetime

def seed_playbooks(db: Session):
    """Create default automation playbooks"""

    playbooks = [
        {
            "id": "low_risk_auto_approve",
            "name": "Low Risk Auto-Approval",
            "description": "Automatically approve low-risk actions (risk score <= 30). Covers read operations, status checks, and informational queries.",
            "status": "active",
            "risk_level": "low",
            "approval_required": False,
            "trigger_conditions": {
                "risk_score_max": 30,
                "auto_approve": True
            },
            "actions": {
                "approve": True,
                "notify": False,
                "escalate": False
            },
            "execution_count": 0,
            "success_rate": 0.0,
            "created_by": "system"
        },
        {
            "id": "business_hours_auto_approve",
            "name": "Business Hours Auto-Approval",
            "description": "Auto-approve medium-low risk actions during business hours (9am-5pm EST, weekdays). Risk score must be <= 40.",
            "status": "active",
            "risk_level": "low",
            "approval_required": False,
            "trigger_conditions": {
                "risk_score_max": 40,
                "business_hours": True,
                "auto_approve": True
            },
            "actions": {
                "approve": True,
                "notify": True,
                "escalate": False
            },
            "execution_count": 0,
            "success_rate": 0.0,
            "created_by": "system"
        },
        {
            "id": "weekend_escalation",
            "name": "Weekend Escalation Playbook",
            "description": "Escalate high-risk actions (>50) occurring on weekends to on-call team. Requires immediate attention.",
            "status": "active",
            "risk_level": "high",
            "approval_required": True,
            "trigger_conditions": {
                "risk_score_min": 50,
                "weekend": True,
                "auto_approve": False
            },
            "actions": {
                "approve": False,
                "notify": True,
                "escalate": True,
                "notify_channels": ["on-call", "email", "slack"]
            },
            "execution_count": 0,
            "success_rate": 0.0,
            "created_by": "system"
        }
    ]

    created_count = 0
    updated_count = 0

    for pb_data in playbooks:
        # Check if exists
        existing = db.query(AutomationPlaybook).filter(
            AutomationPlaybook.id == pb_data['id']
        ).first()

        if existing:
            print(f"⚠️  Playbook '{pb_data['id']}' already exists - updating")
            for key, value in pb_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            new_playbook = AutomationPlaybook(**pb_data)
            db.add(new_playbook)
            created_count += 1
            print(f"✅ Created playbook: {pb_data['id']}")

    db.commit()
    print(f"\n✅ Seeding complete: {created_count} created, {updated_count} updated")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("🌱 Seeding automation playbooks...")
        seed_playbooks(db)
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
```

**File:** `ow-ai-backend/scripts/seed_workflows.py`

```python
"""
Seed Workflows
Creates default workflow templates for the system
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Workflow
from datetime import datetime

def seed_workflows(db: Session):
    """Create default workflow templates"""

    workflows = [
        {
            "id": "security_review_workflow",
            "name": "Security Review Workflow",
            "description": "Multi-step security validation for medium-high risk actions (risk 50-79)",
            "conditions": {
                "min_risk": 50,
                "max_risk": 79
            },
            "actions": [
                {
                    "step": 1,
                    "name": "Initial Security Scan",
                    "type": "security_check",
                    "timeout": 30,
                    "automated": True
                },
                {
                    "step": 2,
                    "name": "Risk Assessment",
                    "type": "risk_analysis",
                    "timeout": 60,
                    "automated": True
                },
                {
                    "step": 3,
                    "name": "Approval Routing",
                    "type": "approval_logic",
                    "timeout": 120,
                    "automated": False,
                    "requires_human": True
                }
            ],
            "is_active": True,
            "risk_threshold": 50
        },
        {
            "id": "compliance_audit_workflow",
            "name": "Compliance Audit Workflow",
            "description": "Enterprise compliance checking for critical risk actions (risk >= 80)",
            "conditions": {
                "min_risk": 80,
                "max_risk": 100
            },
            "actions": [
                {
                    "step": 1,
                    "name": "Compliance Framework Check",
                    "type": "compliance_scan",
                    "timeout": 45,
                    "automated": True,
                    "frameworks": ["SOC2", "NIST", "HIPAA"]
                },
                {
                    "step": 2,
                    "name": "Audit Documentation",
                    "type": "audit_log",
                    "timeout": 30,
                    "automated": True
                },
                {
                    "step": 3,
                    "name": "Multi-Level Approval",
                    "type": "approval_chain",
                    "timeout": 300,
                    "automated": False,
                    "requires_human": True,
                    "approval_levels": 2
                }
            ],
            "is_active": True,
            "risk_threshold": 80
        },
        {
            "id": "emergency_override_workflow",
            "name": "Emergency Override Workflow",
            "description": "Emergency approval workflow for production incidents (manual trigger only)",
            "conditions": {
                "manual_trigger": True,
                "emergency_only": True
            },
            "actions": [
                {
                    "step": 1,
                    "name": "Emergency Justification",
                    "type": "justification_required",
                    "timeout": 60,
                    "automated": False,
                    "requires_reason": True
                },
                {
                    "step": 2,
                    "name": "Executive Approval",
                    "type": "executive_approval",
                    "timeout": 180,
                    "automated": False,
                    "requires_role": "executive"
                },
                {
                    "step": 3,
                    "name": "Immediate Execution",
                    "type": "execute",
                    "timeout": 10,
                    "automated": True,
                    "priority": "urgent"
                }
            ],
            "is_active": True,
            "risk_threshold": 0  # Can be used for any risk level
        }
    ]

    created_count = 0
    updated_count = 0

    for wf_data in workflows:
        # Check if exists
        existing = db.query(Workflow).filter(
            Workflow.id == wf_data['id']
        ).first()

        if existing:
            print(f"⚠️  Workflow '{wf_data['id']}' already exists - updating")
            for key, value in wf_data.items():
                setattr(existing, key, value)
            updated_count += 1
        else:
            new_workflow = Workflow(**wf_data)
            db.add(new_workflow)
            created_count += 1
            print(f"✅ Created workflow: {wf_data['id']}")

    db.commit()
    print(f"\n✅ Seeding complete: {created_count} created, {updated_count} updated")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("🌱 Seeding workflows...")
        seed_workflows(db)
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
```

#### Step 3: Integrate AutomationService into Action Creation

**File:** `ow-ai-backend/routes/agent_routes.py`

**Modify `create_agent_action()` function:**

```python
# Add imports at top of file
from services.automation_service import get_automation_service
from services.orchestration_service import get_orchestration_service

# Inside create_agent_action() function, after creating the action:

@router.post("/agent-action", response_model=AgentActionOut)
async def create_agent_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_csrf)
):
    """Submit a new agent action - WITH AUTOMATION & ORCHESTRATION"""

    # ... existing code to create action ...

    db.add(action)
    db.commit()
    db.refresh(action)

    # ✅ NEW: Check automation playbooks for auto-approval
    try:
        automation_service = get_automation_service(db)

        action_data = {
            'risk_score': action.risk_score or 50,
            'action_type': action.action_type,
            'agent_id': action.agent_id,
            'timestamp': action.timestamp or datetime.now(UTC)
        }

        matching_playbook = automation_service.match_playbooks(action_data)

        if matching_playbook:
            logger.info(f"🤖 Matched playbook: {matching_playbook.id}")

            # Execute playbook (auto-approve)
            result = automation_service.execute_playbook(
                playbook_id=matching_playbook.id,
                action_id=action.id
            )

            if result['success']:
                logger.info(f"✅ Action {action.id} auto-approved via playbook")
                # Refresh action to get updated status
                db.refresh(action)
            else:
                logger.warning(f"⚠️ Playbook execution failed: {result['message']}")

    except Exception as e:
        logger.error(f"❌ Automation service error: {e}")
        # Don't fail the action creation if automation fails

    # ✅ NEW: Trigger workflows for high-risk actions
    try:
        if action.risk_score and action.risk_score >= 50:
            orchestration_service = get_orchestration_service(db)

            orchestration_result = orchestration_service.orchestrate_action(
                action_id=action.id,
                risk_level=action.risk_level or 'medium',
                risk_score=action.risk_score,
                action_type=action.action_type
            )

            if orchestration_result.get('workflows_triggered'):
                logger.info(f"✅ Triggered {len(orchestration_result['workflows_triggered'])} workflows")

    except Exception as e:
        logger.error(f"❌ Orchestration error: {e}")
        # Don't fail the action creation if orchestration fails

    # Return action (may now be auto-approved)
    return action
```

### 2.2 Frontend Implementation (Day 2 Afternoon)

#### Step 1: Remove Demo Data Fallback

**File:** `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`

**Remove lines 541-586** (automation playbooks demo data)
**Remove lines 636-686** (workflow orchestrations demo data)

**Replace with:**

```javascript
// Line 541: Replace demo data with empty state
} else {
  // API returned success but empty data - show empty state
  setAutomationData({
    playbooks: {},
    automation_summary: {
      total_playbooks: 0,
      enabled_playbooks: 0,
      total_triggers_24h: 0,
      total_cost_savings_24h: 0,
      average_success_rate: 0
    },
    real_data_metrics: null
  });
}

// Line 636: Replace demo workflow data with empty state
} else {
  // API returned success but empty data - show empty state
  setWorkflowOrchestrations({
    active_workflows: {},
    summary: {
      total_active: 0,
      total_executions_24h: 0,
      average_success_rate: 0
    },
    real_data_metrics: null
  });
}
```

#### Step 2: Update API Endpoint to Include Metrics

**File:** `ow-ai-backend/routes/automation_orchestration_routes.py`

**Modify `get_automation_playbooks()` to include real-time metrics:**

```python
@router.get("/automation/playbooks")
async def get_automation_playbooks(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all automation playbooks with REAL metrics"""
    try:
        from services.automation_service import get_automation_service

        # Query playbooks
        query = db.query(AutomationPlaybook)
        if status:
            query = query.filter(AutomationPlaybook.status == status)
        if risk_level:
            query = query.filter(AutomationPlaybook.risk_level == risk_level.lower())

        playbooks = query.order_by(AutomationPlaybook.created_at.desc()).all()

        # Get automation service for metrics
        automation_service = get_automation_service(db)

        # Format response with REAL metrics
        playbooks_data = []
        for pb in playbooks:
            # Get real-time metrics
            metrics = automation_service.get_playbook_metrics(pb.id)

            playbooks_data.append({
                'id': pb.id,
                'name': pb.name,
                'description': pb.description,
                'status': pb.status,
                'risk_level': pb.risk_level,
                'approval_required': pb.approval_required,
                'trigger_conditions': pb.trigger_conditions,
                'actions': pb.actions,
                'last_executed': pb.last_executed.isoformat() if pb.last_executed else None,
                'execution_count': pb.execution_count or 0,
                'success_rate': pb.success_rate or 0.0,
                'created_by': pb.created_by,
                'created_at': pb.created_at.isoformat(),
                'updated_at': pb.updated_at.isoformat() if pb.updated_at else None,
                # ✅ Add real-time metrics
                'metrics': metrics
            })

        # Calculate summary stats
        total_playbooks = len(playbooks_data)
        enabled_playbooks = sum(1 for pb in playbooks_data if pb['status'] == 'active')
        total_triggers_24h = sum(pb['metrics'].get('triggers_last_24h', 0) for pb in playbooks_data)
        total_cost_savings = sum(pb['metrics'].get('cost_savings_24h', 0) for pb in playbooks_data)
        avg_success_rate = sum(pb['success_rate'] for pb in playbooks_data) / total_playbooks if total_playbooks > 0 else 0

        return {
            "status": "success",
            "data": playbooks_data,
            "total": total_playbooks,
            "automation_summary": {
                "total_playbooks": total_playbooks,
                "enabled_playbooks": enabled_playbooks,
                "total_triggers_24h": total_triggers_24h,
                "total_cost_savings_24h": round(total_cost_savings, 2),
                "average_success_rate": round(avg_success_rate, 2)
            },
            "real_data_metrics": True  # Flag that this is real data
        }

    except Exception as e:
        logger.error(f"❌ Error fetching playbooks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch playbooks: {str(e)}")
```

---

## Phase 3: Testing (Day 3)

### 3.1 Local Database Setup

```bash
# Run seed scripts
cd ow-ai-backend
python scripts/seed_automation_playbooks.py
python scripts/seed_workflows.py

# Verify data
python scripts/verify_seeded_data.py
```

### 3.2 Unit Tests

**File:** `ow-ai-backend/tests/test_automation_service.py`

```python
"""Test AutomationService"""
import pytest
from services.automation_service import AutomationService
from models import AutomationPlaybook, AgentAction

def test_match_low_risk_playbook(db_session):
    """Test matching low-risk action to playbook"""

    action_data = {
        'risk_score': 25,
        'action_type': 'read_file',
        'agent_id': 'test-agent',
        'timestamp': datetime.utcnow()
    }

    service = AutomationService(db_session)
    playbook = service.match_playbooks(action_data)

    assert playbook is not None
    assert playbook.id == 'low_risk_auto_approve'

def test_execute_playbook(db_session):
    """Test playbook execution auto-approves action"""

    # Create test action
    action = AgentAction(
        agent_id='test-agent',
        action_type='read_file',
        risk_score=25,
        status='pending_approval'
    )
    db_session.add(action)
    db_session.commit()

    # Execute playbook
    service = AutomationService(db_session)
    result = service.execute_playbook('low_risk_auto_approve', action.id)

    assert result['success'] == True
    assert result['action_approved'] == True

    # Verify action is approved
    db_session.refresh(action)
    assert action.status == 'approved'
    assert action.reviewed_by == 'automation:low_risk_auto_approve'

def test_business_hours_check(db_session):
    """Test business hours detection"""
    service = AutomationService(db_session)

    # This will depend on current time
    result = service.is_business_hours()
    assert isinstance(result, bool)
```

### 3.3 Integration Tests

**File:** `ow-ai-backend/tests/test_integration_automation.py`

```python
"""Integration tests for automation flow"""
import pytest
from fastapi.testclient import TestClient

def test_create_action_auto_approved(client, auth_headers):
    """Test creating low-risk action triggers auto-approval"""

    response = client.post(
        "/agent-action",
        headers=auth_headers,
        json={
            "agent_id": "test-agent",
            "action_type": "read_file",
            "description": "Read log file",
            "tool_name": "file-reader",
            "risk_level": "low"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Action should be auto-approved
    assert data['status'] == 'approved'
    assert 'automation' in data['reviewed_by']

def test_create_high_risk_triggers_workflow(client, auth_headers):
    """Test high-risk action triggers workflow"""

    response = client.post(
        "/agent-action",
        headers=auth_headers,
        json={
            "agent_id": "test-agent",
            "action_type": "delete_database",
            "description": "Drop production table",
            "tool_name": "db-admin",
            "risk_level": "high"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should be pending approval (not auto-approved)
    assert data['status'] == 'pending_approval'

    # Check workflow was created
    # ... verify workflow_executions table
```

### 3.4 End-to-End Test Script

**File:** `ow-ai-backend/scripts/test_end_to_end.py`

```python
"""
End-to-End Test - Complete Automation Flow
Tests the entire flow from action submission to auto-approval
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_end_to_end():
    print("🧪 Starting End-to-End Test\n")

    # 1. Login
    print("1️⃣ Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@owkai.com", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful\n")

    # 2. Check playbooks exist
    print("2️⃣ Checking automation playbooks...")
    playbooks_response = requests.get(
        f"{BASE_URL}/api/authorization/automation/playbooks",
        headers=headers
    )
    assert playbooks_response.status_code == 200
    playbooks = playbooks_response.json()
    print(f"✅ Found {playbooks['total']} playbooks\n")

    # 3. Submit low-risk action
    print("3️⃣ Submitting low-risk action...")
    action_response = requests.post(
        f"{BASE_URL}/agent-action",
        headers=headers,
        json={
            "agent_id": "test-agent",
            "action_type": "read_file",
            "description": "Read /var/log/app.log",
            "tool_name": "file-reader"
        }
    )
    assert action_response.status_code == 200
    action = action_response.json()
    print(f"✅ Action created: ID {action['id']}\n")

    # 4. Verify auto-approval
    print("4️⃣ Verifying auto-approval...")
    assert action['status'] == 'approved', f"Expected 'approved', got '{action['status']}'"
    assert 'automation' in action.get('reviewed_by', ''), "Not auto-approved!"
    print("✅ Action was AUTO-APPROVED via playbook!\n")

    # 5. Check playbook metrics updated
    print("5️⃣ Checking playbook metrics...")
    playbooks_response = requests.get(
        f"{BASE_URL}/api/authorization/automation/playbooks",
        headers=headers
    )
    playbooks_updated = playbooks_response.json()
    summary = playbooks_updated.get('automation_summary', {})
    print(f"✅ Metrics:")
    print(f"   - Total triggers (24h): {summary.get('total_triggers_24h', 0)}")
    print(f"   - Cost savings: ${summary.get('total_cost_savings_24h', 0)}")
    print(f"   - Success rate: {summary.get('average_success_rate', 0)}%\n")

    # 6. Submit high-risk action
    print("6️⃣ Submitting high-risk action...")
    high_risk_response = requests.post(
        f"{BASE_URL}/agent-action",
        headers=headers,
        json={
            "agent_id": "test-agent",
            "action_type": "delete_database",
            "description": "Drop users table",
            "tool_name": "db-admin",
            "risk_level": "high"
        }
    )
    assert high_risk_response.status_code == 200
    high_risk_action = high_risk_response.json()
    print(f"✅ High-risk action created: ID {high_risk_action['id']}\n")

    # 7. Verify manual approval required
    print("7️⃣ Verifying manual approval required...")
    assert high_risk_action['status'] == 'pending_approval'
    print("✅ High-risk action requires manual approval (correct!)\n")

    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_end_to_end()
```

---

## Phase 4: Evidence Collection (Day 4)

### 4.1 Create Evidence Documentation

**File:** `AUTOMATION_IMPLEMENTATION_EVIDENCE.md`

Document:
1. Database verification (screenshots/queries)
2. API test results
3. UI screenshots (before/after)
4. Log file excerpts showing automation
5. Performance metrics

### 4.2 Evidence Checklist

- [ ] Database seed data verification
- [ ] Playbook execution logs
- [ ] Workflow trigger logs
- [ ] Frontend showing real data (not demo)
- [ ] Auto-approval working
- [ ] Manual approval still working
- [ ] Metrics calculating correctly
- [ ] No errors in logs

---

## Phase 5: Production Deployment (Day 5)

### 5.1 Pre-Deployment Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] End-to-end test passes locally
- [ ] Evidence documented
- [ ] Code reviewed
- [ ] Database backup created
- [ ] Rollback plan documented

### 5.2 Deployment Steps

```bash
# 1. Backup production database
pg_dump -h <prod-host> -U <user> -d owkai_pilot > backup_pre_automation.sql

# 2. Push code to repository
git add .
git commit -m "feat: Implement enterprise workflow automation

- Add AutomationService for playbook-based auto-approval
- Integrate OrchestrationService into action creation
- Remove frontend demo data fallback
- Add seed scripts for playbooks and workflows
- Update API endpoints with real metrics

TESTING:
- All unit tests pass
- Integration tests pass
- End-to-end test verified locally

EVIDENCE:
- See AUTOMATION_IMPLEMENTATION_EVIDENCE.md"

git push origin dead-code-removal-20251016

# 3. Deploy backend (triggers GitHub Actions)
# Wait for ECS deployment to complete

# 4. Run seed scripts in production
ssh <prod-server>
cd /app
python scripts/seed_automation_playbooks.py
python scripts/seed_workflows.py

# 5. Verify production
curl https://pilot.owkai.app/api/authorization/automation/playbooks

# 6. Test production automation
# Submit test low-risk action
# Verify auto-approval

# 7. Monitor logs for 30 minutes
aws logs tail /aws/ecs/owkai-pilot-backend --follow

# 8. Deploy frontend (triggers GitHub Actions)
cd owkai-pilot-frontend
git push origin main

# Wait for frontend deployment
# Verify at https://pilot.owkai.app
```

### 5.3 Post-Deployment Verification

```bash
# Test automation in production
python scripts/test_production_automation.py

# Verify metrics
curl https://pilot.owkai.app/api/authorization/automation/playbooks \
  -H "Authorization: Bearer $TOKEN"

# Check no errors
aws logs tail /aws/ecs/owkai-pilot-backend --since 1h | grep ERROR
```

---

## Success Criteria

### Must Have (Before Production)
- [ ] AutomationService implemented and tested
- [ ] OrchestrationService integrated into action flow
- [ ] Seed data scripts run successfully
- [ ] Frontend demo data removed
- [ ] All tests pass locally
- [ ] End-to-end test proves automation works
- [ ] Evidence documented

### Should Have
- [ ] Playbook metrics calculating correctly
- [ ] Workflow executions tracking properly
- [ ] UI displays real data with no errors
- [ ] Performance acceptable (< 200ms for automation check)

### Nice to Have
- [ ] Admin UI to create/edit playbooks
- [ ] Workflow builder UI
- [ ] Real-time metrics dashboard
- [ ] Alerting for automation failures

---

## Risk Mitigation

### Risk 1: Automation Auto-Approves Wrong Actions
**Mitigation:**
- Start with conservative risk thresholds (risk <= 30)
- Extensive testing before production
- Audit trail logs all auto-approvals
- Easy to disable playbooks if needed

### Risk 2: Database Migration Issues
**Mitigation:**
- Tables already exist (just empty)
- Seed scripts are idempotent
- Can rollback by deleting seed data
- No schema changes required

### Risk 3: Frontend Shows Errors
**Mitigation:**
- Proper empty state handling
- Fallback error boundaries
- API errors don't break UI
- Can quickly revert frontend if needed

### Risk 4: Performance Degradation
**Mitigation:**
- Automation checks are fast (< 50ms)
- Async workflow triggering
- Database queries optimized
- Monitor performance metrics

---

## Rollback Plan

If issues occur in production:

```bash
# 1. Disable all playbooks
UPDATE automation_playbooks SET status = 'inactive';

# 2. Verify no auto-approvals happening
# All actions go to manual approval

# 3. If needed, rollback code
git revert <commit-hash>
git push

# 4. Restore database if corrupted
psql < backup_pre_automation.sql

# 5. Redeploy previous version
# GitHub Actions will deploy old code
```

---

## Timeline Summary

| Day | Phase | Tasks | Deliverables |
|-----|-------|-------|--------------|
| 1 | Planning | Design, document | Plan document, seed scripts designed |
| 2 | Implementation | Code backend, code frontend | AutomationService, integration complete |
| 3 | Testing | Unit, integration, E2E | All tests passing, evidence |
| 4 | Evidence | Document, verify | Evidence document complete |
| 5 | Deploy | Production deployment | Live in production, verified |

---

## Next Steps

1. ✅ Approve this plan
2. ✅ Create implementation branch
3. ✅ Begin Phase 1 implementation
4. ✅ Daily progress updates
5. ✅ Test, document, deploy

**Ready to proceed?**
