# Enterprise Deployment Verification & Monitoring System
**Created:** 2025-11-12
**Purpose:** Ensure zero-downtime deployments with automated verification
**Status:** Implementation Plan

---

## 🚨 Current Problem Analysis

### Root Cause Identified:
**Deployment pipeline works correctly, but lacks enterprise-grade verification:**

1. ✅ GitHub Actions workflow exists and triggers on push to master
2. ✅ Docker image builds with `--no-cache` flag (line 48)
3. ✅ ECS deploys new task definition successfully
4. ❌ **Missing:** Post-deployment verification that new code is actually running
5. ❌ **Missing:** Automated rollback on verification failure
6. ❌ **Missing:** Real-time deployment monitoring dashboard
7. ❌ **Missing:** API contract validation (schema verification)

### Why API Returns Demo Data:

**Theory #1**: Application-level fallback (Most Likely)
- Code: `routes/agent_routes.py:399-497` has try/catch with demo data fallback
- Database query succeeds but returns empty result
- Fallback activates silently without logging

**Theory #2**: Environment variable mismatch
- ECS container may have different DATABASE_URL than expected
- Connects to wrong database or uses default demo mode

**Theory #3**: Code path issue
- Logic error in query construction
- ORM configuration issue causing empty results

---

## 🎯 Enterprise Solution: 5-Layer Deployment Verification System

### Layer 1: Pre-Deployment Validation (Build Time)
**Purpose:** Catch issues before they reach production

#### 1A. API Contract Tests
```yaml
# .github/workflows/deploy-to-ecs.yml (add before deploy)
- name: Run API Contract Tests
  run: |
    python -m pytest tests/contract/ -v
    pytest tests/integration/test_enrichment_api.py -v
```

**New File**: `tests/contract/test_agent_activity_contract.py`
```python
"""
Enterprise API Contract Tests
Validates that /api/agent-activity returns enriched data schema
"""
import requests
import pytest

def test_agent_activity_returns_enrichment_fields():
    """Verify API returns CVSS/MITRE/NIST fields (not NULL)"""
    response = requests.get("http://localhost:8000/api/agent-activity")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "API must return at least 1 action"

    first_action = data[0]
    # Enterprise requirement: Must have enrichment data
    assert first_action.get("cvss_score") is not None, "CVSS score must not be NULL"
    assert first_action.get("mitre_tactic") is not None, "MITRE tactic must not be NULL"
    assert first_action.get("nist_control") is not None, "NIST control must not be NULL"

def test_agent_activity_not_demo_data():
    """Verify API does not return hardcoded demo data"""
    response = requests.get("http://localhost:8000/api/agent-activity")
    data = response.json()

    # Demo data has specific agent_ids - production should not
    demo_agent_ids = ["security-scanner-01", "compliance-checker", "threat-detector"]
    first_agent_id = data[0].get("agent_id")

    assert first_agent_id not in demo_agent_ids, \
        f"API returning demo data (agent_id: {first_agent_id})"
```

#### 1B. Database Connectivity Test
```python
# tests/integration/test_database_connection.py
def test_production_database_has_enriched_actions():
    """Verify database contains enriched actions before deployment"""
    from database import SessionLocal
    from models import AgentAction

    db = SessionLocal()

    # Check that enriched actions exist
    enriched_count = db.query(AgentAction).filter(
        AgentAction.cvss_score != None,
        AgentAction.mitre_tactic != None,
        AgentAction.nist_control != None
    ).count()

    total_count = db.query(AgentAction).count()

    assert enriched_count > 0, "Database has no enriched actions"
    assert enriched_count / total_count > 0.5, \
        f"Only {enriched_count}/{total_count} actions enriched (<50%)"

    db.close()
```

---

### Layer 2: Post-Deployment Health Checks (Immediate)
**Purpose:** Verify new deployment is healthy within 2 minutes

#### 2A. Enhanced Health Check Endpoint
```python
# routes/health_routes.py (NEW FILE)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import AgentAction
import os

router = APIRouter(tags=["Health"])

@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Enterprise health check with deployment verification
    Returns 200 only if:
    - Database connection works
    - Database has enriched actions
    - No critical errors
    """
    try:
        # Check 1: Database connectivity
        total_actions = db.query(AgentAction).count()

        # Check 2: Enriched actions exist
        enriched_count = db.query(AgentAction).filter(
            AgentAction.cvss_score != None
        ).count()

        enrichment_percentage = (enriched_count / total_actions * 100) if total_actions > 0 else 0

        # Check 3: Demo data detection
        demo_agents = db.query(AgentAction).filter(
            AgentAction.agent_id.in_(["security-scanner-01", "compliance-checker", "threat-detector"])
        ).count()

        is_healthy = (
            total_actions > 0 and
            enrichment_percentage > 50 and
            demo_agents < total_actions * 0.1  # Less than 10% demo data
        )

        return {
            "status": "healthy" if is_healthy else "degraded",
            "deployment_verified": is_healthy,
            "checks": {
                "database_connected": True,
                "total_actions": total_actions,
                "enriched_actions": enriched_count,
                "enrichment_percentage": round(enrichment_percentage, 1),
                "demo_data_count": demo_agents,
                "commit_sha": os.getenv("GIT_COMMIT_SHA", "unknown")
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "deployment_verified": False,
            "error": str(e)
        }
```

#### 2B. GitHub Actions Post-Deployment Verification
```yaml
# .github/workflows/deploy-to-ecs.yml (add after deploy)
- name: Verify Deployment Health
  run: |
    echo "⏳ Waiting 60 seconds for deployment to stabilize..."
    sleep 60

    echo "🔍 Running post-deployment health checks..."

    # Check 1: Health endpoint
    HEALTH=$(curl -s https://pilot.owkai.app/health/detailed | jq -r '.deployment_verified')
    if [ "$HEALTH" != "true" ]; then
      echo "❌ Health check failed!"
      exit 1
    fi

    # Check 2: API returns enriched data
    API_RESPONSE=$(curl -s https://pilot.owkai.app/api/agent-activity \
      -H "Authorization: Bearer ${{ secrets.TEST_API_TOKEN }}")

    CVSS_SCORE=$(echo $API_RESPONSE | jq -r '.[0].cvss_score')
    if [ "$CVSS_SCORE" == "null" ]; then
      echo "❌ API returns NULL enrichment data!"
      echo "Response: $API_RESPONSE"
      exit 1
    fi

    echo "✅ Deployment verified successfully"
    echo "CVSS Score: $CVSS_SCORE"
```

---

### Layer 3: Automated Rollback on Failure
**Purpose:** Automatically revert to last known good deployment

```yaml
# .github/workflows/deploy-to-ecs.yml (wrap deploy step)
- name: Deploy with Automatic Rollback
  id: deploy-step
  continue-on-error: true
  uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    task-definition: ${{ steps.task-def.outputs.task-definition }}
    service: ${{ env.ECS_SERVICE }}
    cluster: ${{ env.ECS_CLUSTER }}
    wait-for-service-stability: true

- name: Verify Deployment or Rollback
  run: |
    if [ "${{ steps.deploy-step.outcome }}" != "success" ]; then
      echo "❌ Deployment failed - initiating rollback"
      # Get previous task definition
      PREVIOUS_TASK_DEF=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --query 'services[0].deployments[1].taskDefinition' \
        --output text)

      echo "🔄 Rolling back to $PREVIOUS_TASK_DEF"

      aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --task-definition $PREVIOUS_TASK_DEF \
        --force-new-deployment

      exit 1
    fi

    # Verify health after deployment
    sleep 60
    HEALTH=$(curl -s https://pilot.owkai.app/health/detailed | jq -r '.deployment_verified')

    if [ "$HEALTH" != "true" ]; then
      echo "❌ Health check failed post-deployment - rolling back"

      PREVIOUS_TASK_DEF=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --query 'services[0].deployments[1].taskDefinition' \
        --output text)

      aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --task-definition $PREVIOUS_TASK_DEF \
        --force-new-deployment

      exit 1
    fi

    echo "✅ Deployment verified and healthy"
```

---

### Layer 4: Real-Time Deployment Monitoring
**Purpose:** Dashboard for deployment status and trends

#### 4A. Deployment Metrics Collector
```python
# services/deployment_metrics.py (NEW FILE)
"""
Enterprise Deployment Metrics Service
Tracks deployment success, health, and performance
"""
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models import DeploymentMetric  # New model
import os

class DeploymentMetricsService:
    @staticmethod
    def record_deployment(db: Session, deployment_data: dict):
        """Record deployment event with health metrics"""
        metric = DeploymentMetric(
            commit_sha=os.getenv("GIT_COMMIT_SHA", "unknown"),
            deployment_time=datetime.now(UTC),
            task_definition=deployment_data.get("task_definition"),
            health_check_status=deployment_data.get("health_status"),
            enrichment_percentage=deployment_data.get("enrichment_percentage"),
            api_response_time_ms=deployment_data.get("api_response_time"),
            verified=deployment_data.get("verified", False)
        )
        db.add(metric)
        db.commit()
        return metric.id
```

#### 4B. Deployment Dashboard Endpoint
```python
# routes/deployment_routes.py (NEW FILE)
@router.get("/deployments/status")
def get_deployment_status(db: Session = Depends(get_db)):
    """Enterprise deployment dashboard data"""
    latest_deployments = db.query(DeploymentMetric)\
        .order_by(DeploymentMetric.deployment_time.desc())\
        .limit(10)\
        .all()

    return {
        "current_deployment": {
            "commit_sha": os.getenv("GIT_COMMIT_SHA", "unknown"),
            "task_definition": get_current_task_definition(),
            "health": get_current_health_status(db)
        },
        "recent_deployments": [
            {
                "commit_sha": d.commit_sha[:8],
                "time": d.deployment_time.isoformat(),
                "health": d.health_check_status,
                "verified": d.verified,
                "enrichment_pct": d.enrichment_percentage
            }
            for d in latest_deployments
        ],
        "metrics": {
            "success_rate": calculate_success_rate(db),
            "avg_enrichment_pct": calculate_avg_enrichment(db),
            "avg_response_time_ms": calculate_avg_response_time(db)
        }
    }
```

---

### Layer 5: Continuous Monitoring & Alerting
**Purpose:** Detect degradation in production

#### 5A. CloudWatch Alarms
```bash
# scripts/setup_cloudwatch_alarms.sh (NEW FILE)
#!/bin/bash
# Enterprise CloudWatch Monitoring Setup

# Alarm 1: API returns NULL enrichment data
aws cloudwatch put-metric-alarm \
  --alarm-name "owkai-null-enrichment-data" \
  --alarm-description "API returning NULL CVSS/MITRE/NIST data" \
  --metric-name "NullEnrichmentCount" \
  --namespace "OWKai/Production" \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Alarm 2: Deployment verification failed
aws cloudwatch put-metric-alarm \
  --alarm-name "owkai-deployment-verification-failed" \
  --alarm-description "Post-deployment health check failed" \
  --metric-name "DeploymentVerificationFailures" \
  --namespace "OWKai/Production" \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# Alarm 3: ECS service unstable
aws cloudwatch put-metric-alarm \
  --alarm-name "owkai-ecs-service-unstable" \
  --alarm-description "ECS service deployment not stable" \
  --metric-name "ServiceStabilityStatus" \
  --namespace "AWS/ECS" \
  --dimensions Name=ServiceName,Value=owkai-pilot-backend-service \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2
```

#### 5B. Enrichment Data Quality Monitor
```python
# services/data_quality_monitor.py (NEW FILE)
"""
Continuous Data Quality Monitoring
Alerts if enrichment data becomes NULL in production
"""
import boto3
from sqlalchemy.orm import Session
from models import AgentAction
import logging

cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')
logger = logging.getLogger(__name__)

def monitor_enrichment_quality(db: Session):
    """
    Runs every 5 minutes (CloudWatch Events trigger)
    Checks if API is returning NULL enrichment data
    """
    try:
        # Sample recent actions from API perspective
        recent_actions = db.query(AgentAction)\
            .order_by(AgentAction.timestamp.desc())\
            .limit(50)\
            .all()

        null_enrichment_count = sum(
            1 for action in recent_actions
            if action.cvss_score is None or
               action.mitre_tactic is None or
               action.nist_control is None
        )

        enrichment_percentage = (
            (50 - null_enrichment_count) / 50 * 100
        )

        # Publish metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='OWKai/Production',
            MetricData=[
                {
                    'MetricName': 'EnrichmentPercentage',
                    'Value': enrichment_percentage,
                    'Unit': 'Percent'
                },
                {
                    'MetricName': 'NullEnrichmentCount',
                    'Value': null_enrichment_count,
                    'Unit': 'Count'
                }
            ]
        )

        if null_enrichment_count > 5:
            logger.error(
                f"🚨 ALERT: {null_enrichment_count}/50 actions have NULL enrichment data! "
                f"Enrichment percentage: {enrichment_percentage:.1f}%"
            )

        return enrichment_percentage

    except Exception as e:
        logger.error(f"❌ Data quality monitoring failed: {e}")
        return None
```

---

## 📋 Implementation Checklist

### Phase 1: Immediate Fixes (30 minutes)
- [ ] Add detailed health check endpoint (`/health/detailed`)
- [ ] Update GitHub Actions with post-deployment verification
- [ ] Add API contract test for enrichment fields
- [ ] Deploy and verify fixes work

### Phase 2: Automated Rollback (1 hour)
- [ ] Implement rollback logic in GitHub Actions
- [ ] Test rollback with intentional failure
- [ ] Document rollback procedures

### Phase 3: Monitoring Dashboard (2 hours)
- [ ] Create `DeploymentMetric` model
- [ ] Implement deployment metrics service
- [ ] Add deployment dashboard endpoint
- [ ] Create frontend dashboard component

### Phase 4: CloudWatch Integration (1 hour)
- [ ] Set up CloudWatch alarms
- [ ] Implement data quality monitor
- [ ] Configure SNS notifications
- [ ] Test alarm triggers

### Phase 5: Documentation (30 minutes)
- [ ] Document deployment verification process
- [ ] Create runbook for deployment failures
- [ ] Update README with health check endpoints

---

## 🎯 Success Criteria

### Deployment Verification Must Confirm:
1. ✅ Database connection works
2. ✅ At least 50% of actions have enrichment data
3. ✅ API returns enriched data (not NULL)
4. ✅ No demo data in production responses
5. ✅ Response times < 500ms
6. ✅ Zero critical errors in logs

### If ANY criterion fails:
→ Deployment marked as failed
→ Automatic rollback to previous version
→ CloudWatch alarm triggered
→ SNS notification sent to team

---

## 🔧 Quick Fix for Current Deployment

**Immediate Action** (5 minutes):

```bash
# Add environment variable to track deployment
# Update ECS task definition to include GIT_COMMIT_SHA
aws ecs register-task-definition \
  --cli-input-json file://task-def-with-commit-sha.json

# This allows us to verify which code is running
```

**Diagnostic Query** (Run now):
```bash
# Check what's actually in the database
curl -s "https://pilot.owkai.app/api/agent-activity" | \
  jq '.[0] | {agent_id, cvss_score, mitre_tactic, nist_control}'

# If NULL, check database directly
psql $DATABASE_URL -c "SELECT id, agent_id, cvss_score, mitre_tactic, nist_control FROM agent_actions LIMIT 3;"
```

---

## 💡 Root Cause Resolution Steps

1. **Add debug logging to production** (Option 1 from PHASE2_CURRENT_STATUS.md)
2. **Verify environment variables** (Option 2)
3. **Check database connection** (verify DATABASE_URL in ECS)
4. **Implement all 5 verification layers** (enterprise solution)

---

**Next Steps:**
1. Implement Phase 1 (health checks + verification)
2. Deploy with verification enabled
3. Diagnose and fix current API issue
4. Roll out full monitoring solution

**Estimated Total Time**: 5 hours for complete enterprise solution
**Immediate Fix**: 30 minutes for verification layer
