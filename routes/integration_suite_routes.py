"""
OW-kai Enterprise Phase 5: Integration Suite Routes
====================================================

Enterprise-grade REST API for unified integration management:
- Integration registry CRUD operations
- Health monitoring endpoints
- Data flow orchestration
- Event correlation queries
- Analytics and metrics

Banking-Level Security: Role-based access control with organization isolation.
No demo data, no fallbacks - production-ready enterprise solution.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from services.integration_suite_service import IntegrationSuiteService
from models_integration_suite import (
    IntegrationCreateRequest,
    IntegrationUpdateRequest,
    IntegrationResponse,
    HealthCheckResponse,
    DataFlowCreateRequest,
    DataFlowResponse,
    DataFlowExecutionResponse,
    IntegrationEventResponse,
    IntegrationMetricsResponse,
    IntegrationDashboardResponse,
    IntegrationTestRequest,
    BulkOperationRequest,
    BulkOperationResponse,
    INTEGRATION_TYPE_CONFIG,
    DATA_FLOW_TEMPLATES,
)

router = APIRouter(prefix="/api/integrations", tags=["Integration Suite"])


def get_org_id(current_user: dict) -> int:
    """Extract organization ID from current user."""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization ID required")
    return org_id


def check_admin_role(current_user: dict):
    """Check if user has admin or integration management role."""
    role = current_user.get("role", "")
    if role not in ["admin", "platform_admin", "integration_manager", "compliance_officer"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or integration manager role required"
        )


# ============================================
# Integration Registry Endpoints
# ============================================

@router.get("/types", summary="List available integration types")
async def list_integration_types(
    current_user: dict = Depends(get_current_user)
):
    """
    List all available integration types with their configurations.
    Returns supported auth methods, required fields, and default settings.
    """
    return {
        "integration_types": [
            {
                "type": t.value if hasattr(t, 'value') else t,
                "display_name": config["display_name"],
                "description": config["description"],
                "required_fields": config["required_fields"],
                "supported_auth": [a.value if hasattr(a, 'value') else a for a in config["supported_auth"]],
                "health_check_interval_seconds": config["health_check_interval_seconds"],
            }
            for t, config in INTEGRATION_TYPE_CONFIG.items()
        ]
    }


@router.get("/templates", summary="List data flow templates")
async def list_data_flow_templates(
    current_user: dict = Depends(get_current_user)
):
    """
    List available data flow templates for quick setup.
    Templates provide pre-configured transformation and filter rules.
    """
    return {
        "templates": [
            {
                "template_id": key,
                "name": template["name"],
                "description": template["description"],
                "source_type": template["source_type"],
                "destination_type": template["destination_type"],
                "data_type": template["data_type"],
            }
            for key, template in DATA_FLOW_TEMPLATES.items()
        ]
    }


@router.post("", summary="Create new integration", response_model=dict)
async def create_integration(
    request: IntegrationCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new integration in the registry.
    Validates configuration against integration type requirements.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    user_id = current_user.get("user_id")

    service = IntegrationSuiteService(db)

    try:
        integration = await service.create_integration(
            organization_id=org_id,
            user_id=user_id,
            integration_type=request.integration_type.value,
            integration_name=request.integration_name,
            endpoint_url=request.endpoint_url,
            auth_type=request.auth_type.value,
            config=request.config,
            display_name=request.display_name,
            description=request.description,
            retry_config=request.retry_config,
            rate_limit_config=request.rate_limit_config,
            tags=request.tags,
        )

        return {
            "status": "created",
            "integration_id": integration.id,
            "integration_name": integration.integration_name,
            "integration_type": integration.integration_type,
            "message": f"Integration '{integration.integration_name}' created successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="List integrations")
async def list_integrations(
    integration_type: Optional[str] = Query(None, description="Filter by integration type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all integrations for the organization with filtering.
    Returns health status, configuration, and metrics for each integration.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    integrations, total = await service.list_integrations(
        organization_id=org_id,
        integration_type=integration_type,
        is_enabled=is_enabled,
        health_status=health_status,
        skip=skip,
        limit=limit,
    )

    return {
        "integrations": [
            {
                "id": i.id,
                "integration_type": i.integration_type,
                "integration_name": i.integration_name,
                "display_name": i.display_name,
                "description": i.description,
                "endpoint_url": i.endpoint_url,
                "auth_type": i.auth_type,
                "is_enabled": i.is_enabled,
                "is_verified": i.is_verified,
                "health_status": i.health_status,
                "last_health_check": i.last_health_check.isoformat() if i.last_health_check else None,
                "uptime_percent_30d": i.uptime_percent_30d,
                "tags": i.tags,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in integrations
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{integration_id}", summary="Get integration details")
async def get_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific integration.
    Includes full configuration and recent health status.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    integration = await service.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return {
        "id": integration.id,
        "integration_type": integration.integration_type,
        "integration_name": integration.integration_name,
        "display_name": integration.display_name,
        "description": integration.description,
        "endpoint_url": integration.endpoint_url,
        "auth_type": integration.auth_type,
        "is_enabled": integration.is_enabled,
        "is_verified": integration.is_verified,
        "health_status": integration.health_status,
        "last_health_check": integration.last_health_check.isoformat() if integration.last_health_check else None,
        "consecutive_failures": integration.consecutive_failures,
        "uptime_percent_30d": integration.uptime_percent_30d,
        "config": integration.config,
        "retry_config": integration.retry_config,
        "rate_limit_config": integration.rate_limit_config,
        "tags": integration.tags,
        "created_at": integration.created_at.isoformat() if integration.created_at else None,
        "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
    }


@router.put("/{integration_id}", summary="Update integration")
async def update_integration(
    integration_id: int,
    request: IntegrationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing integration configuration.
    Only provided fields will be updated.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    updates = request.dict(exclude_unset=True)
    if "auth_type" in updates and updates["auth_type"]:
        updates["auth_type"] = updates["auth_type"].value

    integration = await service.update_integration(integration_id, org_id, **updates)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return {
        "status": "updated",
        "integration_id": integration.id,
        "message": f"Integration '{integration.integration_name}' updated successfully"
    }


@router.delete("/{integration_id}", summary="Delete integration")
async def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an integration and all associated data.
    This action is irreversible.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    deleted = await service.delete_integration(integration_id, org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Integration not found")

    return {
        "status": "deleted",
        "integration_id": integration_id,
        "message": "Integration deleted successfully"
    }


# ============================================
# Health Monitoring Endpoints
# ============================================

@router.post("/{integration_id}/health-check", summary="Run health check")
async def run_health_check(
    integration_id: int,
    check_type: str = Query("ping", description="Type of health check: ping, auth_test, data_test, full_test"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform a health check on an integration.
    Returns response time, status code, and any errors.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    try:
        result = await service.check_integration_health(integration_id, org_id, check_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{integration_id}/health-history", summary="Get health check history")
async def get_health_history(
    integration_id: int,
    hours: int = Query(24, ge=1, le=720, description="Hours of history to retrieve"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get health check history for an integration.
    Returns all checks within the specified time window.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    history = await service.get_health_history(integration_id, org_id, hours)

    return {
        "integration_id": integration_id,
        "period_hours": hours,
        "total_checks": len(history),
        "checks": [
            {
                "id": h.id,
                "check_type": h.check_type,
                "status": h.status,
                "status_code": h.status_code,
                "response_time_ms": h.response_time_ms,
                "error_message": h.error_message,
                "checked_at": h.checked_at.isoformat() if h.checked_at else None,
            }
            for h in history
        ]
    }


# ============================================
# Data Flow Endpoints
# ============================================

@router.post("/data-flows", summary="Create data flow")
async def create_data_flow(
    request: DataFlowCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new data flow configuration.
    Data flows define how data moves between integrations.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    user_id = current_user.get("user_id")
    service = IntegrationSuiteService(db)

    try:
        flow = await service.create_data_flow(
            organization_id=org_id,
            user_id=user_id,
            **request.dict()
        )

        return {
            "status": "created",
            "data_flow_id": flow.id,
            "flow_name": flow.flow_name,
            "message": f"Data flow '{flow.flow_name}' created successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/data-flows/from-template", summary="Create data flow from template")
async def create_data_flow_from_template(
    template_name: str = Query(..., description="Name of the template to use"),
    source_integration_id: int = Query(..., description="Source integration ID"),
    destination_integration_id: Optional[int] = Query(None, description="Destination integration ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a data flow from a predefined template.
    Templates provide pre-configured transformation rules.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    user_id = current_user.get("user_id")
    service = IntegrationSuiteService(db)

    try:
        flow = await service.create_data_flow_from_template(
            organization_id=org_id,
            user_id=user_id,
            template_name=template_name,
            source_integration_id=source_integration_id,
            destination_integration_id=destination_integration_id,
        )

        return {
            "status": "created",
            "data_flow_id": flow.id,
            "flow_name": flow.flow_name,
            "template_used": template_name,
            "message": f"Data flow created from template '{template_name}'"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data-flows", summary="List data flows")
async def list_data_flows(
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all data flows for the organization.
    Includes execution statistics and status.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    flows, total = await service.list_data_flows(
        organization_id=org_id,
        is_enabled=is_enabled,
        data_type=data_type,
        skip=skip,
        limit=limit,
    )

    return {
        "data_flows": [
            {
                "id": f.id,
                "flow_name": f.flow_name,
                "description": f.description,
                "source_integration_id": f.source_integration_id,
                "source_type": f.source_type,
                "destination_integration_id": f.destination_integration_id,
                "destination_type": f.destination_type,
                "data_type": f.data_type,
                "is_enabled": f.is_enabled,
                "last_execution_at": f.last_execution_at.isoformat() if f.last_execution_at else None,
                "last_execution_status": f.last_execution_status,
                "total_records_processed": f.total_records_processed,
                "total_errors": f.total_errors,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in flows
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/data-flows/{data_flow_id}/execute", summary="Execute data flow")
async def execute_data_flow(
    data_flow_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger execution of a data flow.
    Returns immediately with execution ID for tracking.
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    try:
        execution = await service.execute_data_flow(data_flow_id, org_id)

        return {
            "status": "executed",
            "execution_id": execution.execution_id,
            "data_flow_id": data_flow_id,
            "execution_status": execution.status,
            "records_processed": execution.records_processed,
            "records_failed": execution.records_failed,
            "duration_ms": execution.duration_ms,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Event Endpoints
# ============================================

@router.get("/events", summary="Query integration events")
async def query_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    since_hours: Optional[int] = Query(24, ge=1, le=720, description="Hours to look back"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Query integration events with filtering.
    Supports correlation ID for tracing related events.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    since = datetime.utcnow() - timedelta(hours=since_hours) if since_hours else None

    events, total = await service.get_events(
        organization_id=org_id,
        event_type=event_type,
        correlation_id=correlation_id,
        severity=severity,
        source_type=source_type,
        since=since,
        skip=skip,
        limit=limit,
    )

    return {
        "events": [
            {
                "event_id": e.event_id,
                "correlation_id": e.correlation_id,
                "source_type": e.source_type,
                "source_system": e.source_system,
                "event_type": e.event_type,
                "event_category": e.event_category,
                "severity": e.severity,
                "status": e.status,
                "event_time": e.event_time.isoformat() if e.event_time else None,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            }
            for e in events
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/events/correlate", summary="Correlate events")
async def correlate_events(
    event_ids: List[str] = Query(..., description="Event IDs to correlate"),
    correlation_id: Optional[str] = Query(None, description="Optional correlation ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Link multiple events together with a correlation ID.
    Useful for tracking related events across integrations.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    corr_id = await service.correlate_events(org_id, event_ids, correlation_id)

    return {
        "status": "correlated",
        "correlation_id": corr_id,
        "event_count": len(event_ids),
    }


# ============================================
# Dashboard & Analytics Endpoints
# ============================================

@router.get("/dashboard", summary="Get integration dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard summary of all integrations.
    Includes health status, event counts, and recent alerts.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    summary = await service.get_dashboard_summary(org_id)
    return summary


@router.get("/metrics", summary="Get integration metrics")
async def get_metrics(
    integration_id: Optional[int] = Query(None, description="Specific integration ID"),
    period: str = Query("24h", description="Time period: 24h, 7d, 30d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get performance metrics for integrations.
    Includes latency percentiles and success rates.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    metrics = await service.get_integration_metrics(org_id, integration_id, period)
    return metrics


# ============================================
# Bulk Operations
# ============================================

@router.post("/bulk", summary="Bulk operations")
async def bulk_operation(
    request: BulkOperationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform bulk operations on multiple integrations.
    Supported operations: enable, disable, delete, test
    """
    check_admin_role(current_user)
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    if request.operation not in ["enable", "disable", "delete", "test"]:
        raise HTTPException(status_code=400, detail="Invalid operation")

    result = await service.bulk_operation(
        organization_id=org_id,
        integration_ids=request.integration_ids,
        operation=request.operation,
    )

    return result


# ============================================
# Test Endpoint
# ============================================

@router.post("/test", summary="Test integration connection")
async def test_integration(
    request: IntegrationTestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Test an integration connection without affecting state.
    Validates connectivity and authentication.
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    try:
        result = await service.check_integration_health(
            request.integration_id,
            org_id,
            request.test_type
        )

        return {
            "status": "tested",
            "test_type": request.test_type,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# SEC-028: Integration Status Summary Endpoint
# ============================================

@router.get("/status", summary="Get integration status summary")
async def get_integration_status_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    SEC-028: Get summary of all integration statuses for the organization.

    Returns status for each integration type (splunk, qradar, sentinel, etc.)
    in a format suitable for the Settings UI dashboard.

    Multi-Tenant: Returns only integrations for the current user's organization.
    Banking-Level Security: No hardcoded data, no fallbacks.

    Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 7.1

    Authored-By: OW-KAI Engineer
    """
    org_id = get_org_id(current_user)
    service = IntegrationSuiteService(db)

    # Get all integrations for the organization
    integrations, _ = await service.list_integrations(
        organization_id=org_id,
        skip=0,
        limit=100,
    )

    # Build status summary by integration type
    status_summary = {
        "splunk": None,
        "qradar": None,
        "sentinel": None,
        "active_directory": None,
        "sso": None,
        "servicenow": None,
        "jira": None,
        "slack": None,
        "teams": None,
        "pagerduty": None,
        "custom_webhook": None,
    }

    # Map integration types to summary keys
    type_mapping = {
        "splunk": "splunk",
        "qradar": "qradar",
        "sentinel": "sentinel",
        "microsoft_sentinel": "sentinel",
        "active_directory": "active_directory",
        "ldap": "active_directory",
        "okta": "sso",
        "azure_ad": "sso",
        "sso": "sso",
        "servicenow": "servicenow",
        "jira": "jira",
        "slack": "slack",
        "teams": "teams",
        "microsoft_teams": "teams",
        "pagerduty": "pagerduty",
        "webhook": "custom_webhook",
        "custom_webhook": "custom_webhook",
    }

    for integration in integrations:
        int_type = integration.integration_type.lower()
        summary_key = type_mapping.get(int_type)

        if summary_key:
            # Only include if this is the first or primary integration of this type
            if status_summary[summary_key] is None:
                status_summary[summary_key] = {
                    "id": integration.id,
                    "name": integration.display_name or integration.integration_name,
                    "status": _map_health_status(integration.health_status),
                    "is_enabled": integration.is_enabled,
                    "last_sync": integration.last_health_check.isoformat() if integration.last_health_check else None,
                    "user_count": integration.config.get("user_count") if integration.config else None,
                    "uptime_percent": integration.uptime_percent_30d,
                }

    return status_summary


def _map_health_status(health_status: str) -> str:
    """Map internal health status to frontend display status."""
    status_map = {
        "healthy": "active",
        "connected": "active",
        "active": "active",
        "degraded": "syncing",
        "syncing": "syncing",
        "pending": "syncing",
        "unhealthy": "error",
        "error": "error",
        "failed": "error",
        "disconnected": "inactive",
        "disabled": "inactive",
        "inactive": "inactive",
        "unknown": "inactive",
    }
    return status_map.get((health_status or "").lower(), "inactive")
