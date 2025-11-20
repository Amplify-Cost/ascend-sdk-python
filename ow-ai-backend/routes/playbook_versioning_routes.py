"""
🏢 ENTERPRISE PLAYBOOK VERSIONING API ROUTES

Phase 3: Version Control, Analytics, Scheduling

Author: Donald King (OW-kai Enterprise)
Date: 2025-11-18
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta, UTC

from database import get_db
from dependencies import get_current_user, require_admin
from models import AutomationPlaybook, PlaybookExecution, User
from models_playbook_versioning import (
    PlaybookVersion,
    PlaybookExecutionLog,
    PlaybookSchedule,
    PlaybookTemplate
)
from schemas.playbook_advanced import (
    PlaybookVersionCreate,
    PlaybookVersionResponse,
    PlaybookRollbackRequest,
    PlaybookVersionComparison,
    ExecutionAnalytics,
    PlaybookPerformanceMetrics,
    PlaybookScheduleCreate,
    PlaybookScheduleResponse,
    PlaybookTemplateExport,
    PlaybookTemplateImport,
    PlaybookTemplateResponse,
    PlaybookCloneRequest
)

router = APIRouter(prefix="/api/authorization/automation", tags=["Playbook Versioning & Analytics"])


# ============================================================================
# PLAYBOOK VERSIONING ENDPOINTS
# ============================================================================

@router.get("/playbooks/{playbook_id}/versions", response_model=List[PlaybookVersionResponse])
async def get_playbook_versions(
    playbook_id: str,
    include_performance: bool = Query(default=True, description="Include execution metrics"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET ALL VERSIONS OF A PLAYBOOK

    Returns complete version history with performance metrics.

    Business Value:
    - Audit trail for compliance (SOX, PCI-DSS)
    - Performance tracking across versions
    - Rollback decision support
    """
    playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    versions = db.query(PlaybookVersion).filter(
        PlaybookVersion.playbook_id == playbook_id
    ).order_by(desc(PlaybookVersion.version_number)).all()

    return versions


@router.post("/playbooks/{playbook_id}/versions", response_model=PlaybookVersionResponse)
async def create_playbook_version(
    playbook_id: str,
    version_data: PlaybookVersionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 CREATE NEW PLAYBOOK VERSION

    Creates snapshot of current playbook state as new version.
    Automatically detects changed fields and generates diff.

    Pattern: GitLab Merge Request Versioning
    """
    playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Get current version number
    last_version = db.query(PlaybookVersion).filter(
        PlaybookVersion.playbook_id == playbook_id
    ).order_by(desc(PlaybookVersion.version_number)).first()

    next_version_number = (last_version.version_number + 1) if last_version else 1

    # Detect changed fields
    changed_fields = []
    if last_version:
        if last_version.name != version_data.name:
            changed_fields.append("name")
        if last_version.description != version_data.description:
            changed_fields.append("description")
        if last_version.trigger_conditions != version_data.trigger_conditions:
            changed_fields.append("trigger_conditions")
        if last_version.actions != version_data.actions:
            changed_fields.append("actions")
        if last_version.risk_level != version_data.risk_level:
            changed_fields.append("risk_level")

    # Mark previous version as not current
    if last_version and last_version.is_current:
        last_version.is_current = False

    # Create new version
    new_version = PlaybookVersion(
        playbook_id=playbook_id,
        version_number=next_version_number,
        version_tag=version_data.version_tag,
        is_current=True,
        name=version_data.name,
        description=version_data.description,
        status=version_data.status,
        risk_level=version_data.risk_level,
        approval_required=version_data.approval_required,
        trigger_conditions=version_data.trigger_conditions,
        actions=version_data.actions,
        change_summary=version_data.change_summary,
        change_type=version_data.change_type.value,
        changed_fields=changed_fields,
        created_by=current_user.get("user_id")
    )

    db.add(new_version)

    # Update main playbook
    playbook.name = version_data.name
    playbook.description = version_data.description
    playbook.status = version_data.status
    playbook.risk_level = version_data.risk_level
    playbook.approval_required = version_data.approval_required
    playbook.trigger_conditions = version_data.trigger_conditions
    playbook.actions = version_data.actions
    playbook.updated_by = current_user.get("user_id")
    playbook.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(new_version)

    return new_version


@router.post("/playbooks/{playbook_id}/rollback", response_model=PlaybookVersionResponse)
async def rollback_playbook(
    playbook_id: str,
    rollback_request: PlaybookRollbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 ROLLBACK PLAYBOOK TO PREVIOUS VERSION

    Restores playbook to a previous working version.
    Creates new version entry with ROLLBACK change type.

    Business Value:
    - Quick recovery from bad deployments
    - Zero-downtime rollback
    - Complete audit trail maintained
    """
    playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Get target version to rollback to
    target_version = db.query(PlaybookVersion).filter(
        and_(
            PlaybookVersion.playbook_id == playbook_id,
            PlaybookVersion.id == rollback_request.version_id
        )
    ).first()

    if not target_version:
        raise HTTPException(status_code=404, detail="Target version not found")

    # Get current version
    current_version = db.query(PlaybookVersion).filter(
        and_(
            PlaybookVersion.playbook_id == playbook_id,
            PlaybookVersion.is_current == True
        )
    ).first()

    # Mark current version as not current
    if current_version:
        current_version.is_current = False

    # Create new version with rollback type
    next_version_number = current_version.version_number + 1 if current_version else 1

    rollback_version = PlaybookVersion(
        playbook_id=playbook_id,
        version_number=next_version_number,
        version_tag=f"rollback-to-v{target_version.version_number}",
        is_current=True,
        name=target_version.name,
        description=target_version.description,
        status=target_version.status,
        risk_level=target_version.risk_level,
        approval_required=target_version.approval_required,
        trigger_conditions=target_version.trigger_conditions,
        actions=target_version.actions,
        change_summary=f"Rolled back to version {target_version.version_number}",
        change_type="ROLLBACK",
        changed_fields=["rollback"],
        created_by=current_user.get("user_id"),
        rolled_back_at=datetime.now(UTC),
        rolled_back_by=current_user.get("user_id"),
        rollback_reason=rollback_request.rollback_reason
    )

    db.add(rollback_version)

    # Update main playbook to rollback state
    playbook.name = target_version.name
    playbook.description = target_version.description
    playbook.status = target_version.status
    playbook.risk_level = target_version.risk_level
    playbook.approval_required = target_version.approval_required
    playbook.trigger_conditions = target_version.trigger_conditions
    playbook.actions = target_version.actions
    playbook.updated_by = current_user.get("user_id")
    playbook.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(rollback_version)

    return rollback_version


@router.get("/playbooks/{playbook_id}/versions/compare", response_model=PlaybookVersionComparison)
async def compare_playbook_versions(
    playbook_id: str,
    version_a: int = Query(..., description="First version number to compare"),
    version_b: int = Query(..., description="Second version number to compare"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 COMPARE TWO PLAYBOOK VERSIONS

    Returns detailed diff between two versions including:
    - Field-by-field changes
    - Performance comparison
    - Action changes

    Pattern: GitHub Pull Request Diff View
    """
    # Get both versions
    ver_a = db.query(PlaybookVersion).filter(
        and_(
            PlaybookVersion.playbook_id == playbook_id,
            PlaybookVersion.version_number == version_a
        )
    ).first()

    ver_b = db.query(PlaybookVersion).filter(
        and_(
            PlaybookVersion.playbook_id == playbook_id,
            PlaybookVersion.version_number == version_b
        )
    ).first()

    if not ver_a or not ver_b:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    # Calculate differences
    differences = {}

    if ver_a.name != ver_b.name:
        differences["name"] = {"before": ver_a.name, "after": ver_b.name}

    if ver_a.description != ver_b.description:
        differences["description"] = {"before": ver_a.description, "after": ver_b.description}

    if ver_a.trigger_conditions != ver_b.trigger_conditions:
        differences["trigger_conditions"] = {
            "before": ver_a.trigger_conditions,
            "after": ver_b.trigger_conditions
        }

    if ver_a.actions != ver_b.actions:
        differences["actions"] = {
            "before": ver_a.actions,
            "after": ver_b.actions
        }

    # Performance comparison
    performance_comparison = {
        "version_a": {
            "executions": ver_a.execution_count,
            "success_count": ver_a.success_count,
            "failure_count": ver_a.failure_count,
            "success_rate": (ver_a.success_count / ver_a.execution_count * 100) if ver_a.execution_count > 0 else 0
        },
        "version_b": {
            "executions": ver_b.execution_count,
            "success_count": ver_b.success_count,
            "failure_count": ver_b.failure_count,
            "success_rate": (ver_b.success_count / ver_b.execution_count * 100) if ver_b.execution_count > 0 else 0
        }
    }

    return PlaybookVersionComparison(
        version_a_id=ver_a.id,
        version_b_id=ver_b.id,
        version_a_number=ver_a.version_number,
        version_b_number=ver_b.version_number,
        differences=differences,
        changed_trigger_conditions="trigger_conditions" in differences,
        changed_actions="actions" in differences,
        action_changes_count=abs(len(ver_a.actions) - len(ver_b.actions)),
        performance_comparison=performance_comparison
    )


# ============================================================================
# EXECUTION ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/playbooks/{playbook_id}/analytics", response_model=ExecutionAnalytics)
async def get_playbook_analytics(
    playbook_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET PLAYBOOK EXECUTION ANALYTICS

    Comprehensive analytics including:
    - Success rates and performance metrics
    - Cost savings calculations
    - Trend analysis
    - Version performance comparison

    Pattern: Splunk SOAR Analytics Dashboard
    """
    playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    # Get execution logs for time period
    logs = db.query(PlaybookExecutionLog).filter(
        and_(
            PlaybookExecutionLog.playbook_id == playbook_id,
            PlaybookExecutionLog.started_at >= start_date,
            PlaybookExecutionLog.started_at <= end_date
        )
    ).all()

    total_executions = len(logs)
    successful_executions = len([log for log in logs if log.was_successful])
    failed_executions = total_executions - successful_executions
    success_rate_percent = (successful_executions / total_executions * 100) if total_executions > 0 else 0

    # Performance metrics
    durations = [log.duration_ms for log in logs if log.duration_ms is not None]
    avg_duration_ms = sum(durations) / len(durations) if durations else 0
    min_duration_ms = min(durations) if durations else 0
    max_duration_ms = max(durations) if durations else 0

    # Calculate percentiles
    sorted_durations = sorted(durations)
    p50_duration_ms = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
    p95_index = int(len(sorted_durations) * 0.95)
    p95_duration_ms = sorted_durations[p95_index] if sorted_durations else 0
    p99_index = int(len(sorted_durations) * 0.99)
    p99_duration_ms = sorted_durations[p99_index] if sorted_durations else 0

    # Business impact
    total_cost_savings = sum([log.cost_impact for log in logs if log.cost_impact is not None])
    total_actions_automated = total_executions
    manual_approvals_avoided = successful_executions

    # Executions by day
    executions_by_day = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_logs = [log for log in logs if log.started_at.date() == day.date()]
        executions_by_day.append({
            "date": day.isoformat(),
            "count": len(day_logs)
        })

    # Success rate by day
    success_rate_by_day = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_logs = [log for log in logs if log.started_at.date() == day.date()]
        day_successful = len([log for log in day_logs if log.was_successful])
        day_rate = (day_successful / len(day_logs) * 100) if day_logs else 0
        success_rate_by_day.append({
            "date": day.isoformat(),
            "success_rate": day_rate
        })

    # Most common triggers
    trigger_counts = {}
    for log in logs:
        if log.input_snapshot and 'action_type' in log.input_snapshot:
            action_type = log.input_snapshot['action_type']
            trigger_counts[action_type] = trigger_counts.get(action_type, 0) + 1

    most_common_triggers = [
        {"trigger": trigger, "count": count}
        for trigger, count in sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Version performance (placeholder - would need version tracking in logs)
    version_performance = []

    return ExecutionAnalytics(
        playbook_id=playbook_id,
        playbook_name=playbook.name,
        start_date=start_date,
        end_date=end_date,
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        success_rate_percent=success_rate_percent,
        avg_duration_ms=avg_duration_ms,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        p50_duration_ms=p50_duration_ms,
        p95_duration_ms=p95_duration_ms,
        p99_duration_ms=p99_duration_ms,
        total_cost_savings=total_cost_savings,
        total_actions_automated=total_actions_automated,
        manual_approvals_avoided=manual_approvals_avoided,
        executions_by_day=executions_by_day,
        success_rate_by_day=success_rate_by_day,
        most_common_triggers=most_common_triggers,
        version_performance=version_performance
    )


@router.get("/playbooks/{playbook_id}/performance", response_model=PlaybookPerformanceMetrics)
async def get_playbook_performance(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 GET REAL-TIME PLAYBOOK PERFORMANCE METRICS

    Quick health check for playbook performance.
    Returns alerts if performance degrades.
    """
    playbook = db.query(AutomationPlaybook).filter(AutomationPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Get current version
    current_version_obj = db.query(PlaybookVersion).filter(
        and_(
            PlaybookVersion.playbook_id == playbook_id,
            PlaybookVersion.is_current == True
        )
    ).first()

    current_version = current_version_obj.version_number if current_version_obj else 1

    # Last 24 hours
    last_24h = datetime.now(UTC) - timedelta(hours=24)
    logs_24h = db.query(PlaybookExecutionLog).filter(
        and_(
            PlaybookExecutionLog.playbook_id == playbook_id,
            PlaybookExecutionLog.started_at >= last_24h
        )
    ).all()

    last_24h_executions = len(logs_24h)
    last_24h_successful = len([log for log in logs_24h if log.was_successful])
    last_24h_success_rate = (last_24h_successful / last_24h_executions * 100) if last_24h_executions > 0 else 100.0

    durations_24h = [log.duration_ms for log in logs_24h if log.duration_ms is not None]
    last_24h_avg_duration_ms = sum(durations_24h) / len(durations_24h) if durations_24h else 0

    # Last 7 days
    last_7d = datetime.now(UTC) - timedelta(days=7)
    logs_7d = db.query(PlaybookExecutionLog).filter(
        and_(
            PlaybookExecutionLog.playbook_id == playbook_id,
            PlaybookExecutionLog.started_at >= last_7d
        )
    ).all()

    last_7d_executions = len(logs_7d)
    last_7d_successful = len([log for log in logs_7d if log.was_successful])
    last_7d_success_rate = (last_7d_successful / last_7d_executions * 100) if last_7d_executions > 0 else 100.0
    last_7d_cost_savings = sum([log.cost_impact for log in logs_7d if log.cost_impact is not None])

    # Calculate health score (0-100)
    health_score = 100.0
    if last_24h_success_rate < 90:
        health_score -= (90 - last_24h_success_rate)
    if last_24h_executions == 0:
        health_score -= 20

    health_score = max(0, min(100, health_score))

    # Performance alerts
    alerts = []
    if last_24h_success_rate < 90:
        alerts.append(f"⚠️ Success rate dropped to {last_24h_success_rate:.1f}% in last 24h")
    if last_24h_executions == 0:
        alerts.append("⚠️ No executions in last 24 hours")
    if last_24h_avg_duration_ms > 5000:
        alerts.append(f"⚠️ Slow execution times ({last_24h_avg_duration_ms:.0f}ms average)")

    # Trending up?
    trending_up = last_24h_success_rate >= last_7d_success_rate

    return PlaybookPerformanceMetrics(
        playbook_id=playbook_id,
        current_version=current_version,
        last_24h_executions=last_24h_executions,
        last_24h_success_rate=last_24h_success_rate,
        last_24h_avg_duration_ms=last_24h_avg_duration_ms,
        last_7d_executions=last_7d_executions,
        last_7d_success_rate=last_7d_success_rate,
        last_7d_cost_savings=last_7d_cost_savings,
        trending_up=trending_up,
        health_score=health_score,
        alerts=alerts
    )


# ============================================================================
# PLAYBOOK CLONING ENDPOINT
# ============================================================================

@router.post("/playbooks/clone", response_model=dict)
async def clone_playbook(
    clone_request: PlaybookCloneRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 CLONE EXISTING PLAYBOOK

    Creates exact copy of playbook with new ID.
    Optionally includes execution statistics.
    """
    # Get source playbook
    source = db.query(AutomationPlaybook).filter(
        AutomationPlaybook.id == clone_request.source_playbook_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source playbook not found")

    # Check new ID doesn't exist
    existing = db.query(AutomationPlaybook).filter(
        AutomationPlaybook.id == clone_request.new_playbook_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Playbook with this ID already exists")

    # Create new playbook
    new_playbook = AutomationPlaybook(
        id=clone_request.new_playbook_id,
        name=clone_request.new_name,
        description=clone_request.new_description or source.description,
        status=source.status,
        risk_level=source.risk_level,
        approval_required=source.approval_required,
        trigger_conditions=source.trigger_conditions,
        actions=source.actions,
        execution_count=source.execution_count if clone_request.include_execution_history else 0,
        success_rate=source.success_rate if clone_request.include_execution_history else 0.0,
        created_by=current_user.get("user_id"),
        created_at=datetime.now(UTC)
    )

    db.add(new_playbook)

    # Create initial version
    initial_version = PlaybookVersion(
        playbook_id=clone_request.new_playbook_id,
        version_number=1,
        version_tag="initial",
        is_current=True,
        name=clone_request.new_name,
        description=clone_request.new_description or source.description,
        status=source.status,
        risk_level=source.risk_level,
        approval_required=source.approval_required,
        trigger_conditions=source.trigger_conditions,
        actions=source.actions,
        change_summary=f"Cloned from {clone_request.source_playbook_id}",
        change_type="CLONE",
        changed_fields=["all"],
        created_by=current_user.get("user_id")
    )

    db.add(initial_version)
    db.commit()

    return {
        "status": "success",
        "message": f"Playbook cloned successfully",
        "new_playbook_id": clone_request.new_playbook_id,
        "source_playbook_id": clone_request.source_playbook_id
    }
