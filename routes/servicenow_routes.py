"""
OW-kai Enterprise Integration Phase 3: ServiceNow API Routes

Banking-Level ITSM Integration with:
- Connection management (CRUD)
- Ticket creation and sync
- CMDB integration
- Full audit logging
- Multi-tenant isolation

Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, ITIL v4
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models_servicenow import (
    ServiceNowTicketType,
    ServiceNowSyncStatus,
    ServiceNowConnectionCreate,
    ServiceNowConnectionUpdate,
    ServiceNowConnectionResponse,
    ServiceNowTicketCreate,
    ServiceNowTicketUpdate,
    ServiceNowTicketResponse,
    ServiceNowTestResponse,
    ServiceNowMetricsResponse,
    OWKAI_TO_SERVICENOW_MAPPING,
)
from services.servicenow_service import ServiceNowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/servicenow", tags=["ServiceNow Integration"])


# ============================================
# Connection Management
# ============================================

@router.post(
    "/connections",
    response_model=ServiceNowConnectionResponse,
    summary="Create ServiceNow connection",
    status_code=201
)
async def create_connection(
    data: ServiceNowConnectionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new ServiceNow instance connection.

    Requires admin role. Credentials are encrypted with AES-256.

    **Required fields:**
    - name: Connection name
    - instance_url: ServiceNow instance URL (e.g., https://company.service-now.com)
    - Authentication credentials (basic or OAuth2)
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    # Require admin role for connection management
    if current_user.get("role") not in ["admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin role required to manage connections")

    service = ServiceNowService(db)
    connection = service.create_connection(
        data=data,
        organization_id=current_user["organization_id"],
        user_id=current_user["user_id"]
    )

    logger.info(f"Created ServiceNow connection {connection.id} by user {current_user['user_id']}")

    return ServiceNowConnectionResponse(
        id=connection.id,
        connection_id=str(connection.connection_id),
        name=connection.name,
        description=connection.description,
        instance_url=connection.instance_url,
        auth_type=connection.auth_type,
        api_version=connection.api_version,
        timeout_seconds=connection.timeout_seconds,
        max_retries=connection.max_retries,
        default_assignment_group=connection.default_assignment_group,
        default_caller_id=connection.default_caller_id,
        default_category=connection.default_category,
        default_subcategory=connection.default_subcategory,
        cmdb_class=connection.cmdb_class,
        cmdb_lookup_field=connection.cmdb_lookup_field,
        field_mappings=connection.field_mappings,
        custom_fields=connection.custom_fields,
        is_active=connection.is_active,
        is_verified=connection.is_verified,
        last_verified_at=connection.last_verified_at,
        verification_error=connection.verification_error,
        total_tickets_created=connection.total_tickets_created,
        total_sync_errors=connection.total_sync_errors,
        last_sync_at=connection.last_sync_at,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.get(
    "/connections",
    response_model=List[ServiceNowConnectionResponse],
    summary="List ServiceNow connections"
)
async def list_connections(
    active_only: bool = Query(False, description="Filter to active connections only"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all ServiceNow connections for the organization.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    connections = service.list_connections(
        organization_id=current_user["organization_id"],
        active_only=active_only
    )

    return [
        ServiceNowConnectionResponse(
            id=c.id,
            connection_id=str(c.connection_id),
            name=c.name,
            description=c.description,
            instance_url=c.instance_url,
            auth_type=c.auth_type,
            api_version=c.api_version,
            timeout_seconds=c.timeout_seconds,
            max_retries=c.max_retries,
            default_assignment_group=c.default_assignment_group,
            default_caller_id=c.default_caller_id,
            default_category=c.default_category,
            default_subcategory=c.default_subcategory,
            cmdb_class=c.cmdb_class,
            cmdb_lookup_field=c.cmdb_lookup_field,
            field_mappings=c.field_mappings,
            custom_fields=c.custom_fields,
            is_active=c.is_active,
            is_verified=c.is_verified,
            last_verified_at=c.last_verified_at,
            verification_error=c.verification_error,
            total_tickets_created=c.total_tickets_created,
            total_sync_errors=c.total_sync_errors,
            last_sync_at=c.last_sync_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in connections
    ]


@router.get(
    "/connections/{connection_id}",
    response_model=ServiceNowConnectionResponse,
    summary="Get ServiceNow connection"
)
async def get_connection(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific ServiceNow connection by ID.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    connection = service.get_connection(connection_id, current_user["organization_id"])

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return ServiceNowConnectionResponse(
        id=connection.id,
        connection_id=str(connection.connection_id),
        name=connection.name,
        description=connection.description,
        instance_url=connection.instance_url,
        auth_type=connection.auth_type,
        api_version=connection.api_version,
        timeout_seconds=connection.timeout_seconds,
        max_retries=connection.max_retries,
        default_assignment_group=connection.default_assignment_group,
        default_caller_id=connection.default_caller_id,
        default_category=connection.default_category,
        default_subcategory=connection.default_subcategory,
        cmdb_class=connection.cmdb_class,
        cmdb_lookup_field=connection.cmdb_lookup_field,
        field_mappings=connection.field_mappings,
        custom_fields=connection.custom_fields,
        is_active=connection.is_active,
        is_verified=connection.is_verified,
        last_verified_at=connection.last_verified_at,
        verification_error=connection.verification_error,
        total_tickets_created=connection.total_tickets_created,
        total_sync_errors=connection.total_sync_errors,
        last_sync_at=connection.last_sync_at,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.put(
    "/connections/{connection_id}",
    response_model=ServiceNowConnectionResponse,
    summary="Update ServiceNow connection"
)
async def update_connection(
    connection_id: int,
    data: ServiceNowConnectionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a ServiceNow connection.

    Requires admin role. Updating credentials will re-encrypt them.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    if current_user.get("role") not in ["admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin role required to manage connections")

    service = ServiceNowService(db)
    connection = service.update_connection(
        connection_id=connection_id,
        organization_id=current_user["organization_id"],
        data=data,
        user_id=current_user["user_id"]
    )

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    logger.info(f"Updated ServiceNow connection {connection_id} by user {current_user['user_id']}")

    return ServiceNowConnectionResponse(
        id=connection.id,
        connection_id=str(connection.connection_id),
        name=connection.name,
        description=connection.description,
        instance_url=connection.instance_url,
        auth_type=connection.auth_type,
        api_version=connection.api_version,
        timeout_seconds=connection.timeout_seconds,
        max_retries=connection.max_retries,
        default_assignment_group=connection.default_assignment_group,
        default_caller_id=connection.default_caller_id,
        default_category=connection.default_category,
        default_subcategory=connection.default_subcategory,
        cmdb_class=connection.cmdb_class,
        cmdb_lookup_field=connection.cmdb_lookup_field,
        field_mappings=connection.field_mappings,
        custom_fields=connection.custom_fields,
        is_active=connection.is_active,
        is_verified=connection.is_verified,
        last_verified_at=connection.last_verified_at,
        verification_error=connection.verification_error,
        total_tickets_created=connection.total_tickets_created,
        total_sync_errors=connection.total_sync_errors,
        last_sync_at=connection.last_sync_at,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.delete(
    "/connections/{connection_id}",
    status_code=204,
    summary="Delete ServiceNow connection"
)
async def delete_connection(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a ServiceNow connection.

    Requires admin role. This will also delete all associated tickets.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    if current_user.get("role") not in ["admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin role required to manage connections")

    service = ServiceNowService(db)
    success = service.delete_connection(connection_id, current_user["organization_id"])

    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")

    logger.info(f"Deleted ServiceNow connection {connection_id} by user {current_user['user_id']}")
    return None


@router.post(
    "/connections/{connection_id}/test",
    response_model=ServiceNowTestResponse,
    summary="Test ServiceNow connection"
)
async def test_connection(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test a ServiceNow connection by attempting to connect to the instance.

    Updates the verification status of the connection.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    result = await service.test_connection(connection_id, current_user["organization_id"])

    return ServiceNowTestResponse(
        success=result["success"],
        message=result["message"],
        instance_info=result.get("instance_info"),
        response_time_ms=result.get("response_time_ms", 0),
        error_details=result.get("error_details"),
    )


# ============================================
# Ticket Management
# ============================================

@router.post(
    "/tickets",
    response_model=ServiceNowTicketResponse,
    summary="Create ServiceNow ticket",
    status_code=201
)
async def create_ticket(
    data: ServiceNowTicketCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new ServiceNow ticket (incident, change request, problem, etc.).

    The ticket is created locally and then synced to ServiceNow.
    If sync fails, the ticket is saved locally with sync_status=failed.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)

    try:
        ticket = await service.create_ticket(
            data=data,
            organization_id=current_user["organization_id"],
            user_id=current_user["user_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.info(f"Created ServiceNow ticket {ticket.id} by user {current_user['user_id']}")

    return ServiceNowTicketResponse(
        id=ticket.id,
        ticket_id=str(ticket.ticket_id),
        servicenow_sys_id=ticket.servicenow_sys_id,
        servicenow_number=ticket.servicenow_number,
        servicenow_link=ticket.servicenow_link,
        ticket_type=ticket.ticket_type,
        short_description=ticket.short_description,
        description=ticket.description,
        priority=ticket.priority,
        impact=ticket.impact,
        urgency=ticket.urgency,
        state=ticket.state,
        assignment_group=ticket.assignment_group,
        assigned_to=ticket.assigned_to,
        caller_id=ticket.caller_id,
        category=ticket.category,
        subcategory=ticket.subcategory,
        cmdb_ci=ticket.cmdb_ci,
        source_type=ticket.source_type,
        source_id=ticket.source_id,
        sync_status=ticket.sync_status,
        sync_attempts=ticket.sync_attempts,
        last_sync_error=ticket.last_sync_error,
        last_synced_at=ticket.last_synced_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
    )


@router.get(
    "/tickets",
    response_model=List[ServiceNowTicketResponse],
    summary="List ServiceNow tickets"
)
async def list_tickets(
    connection_id: Optional[int] = Query(None, description="Filter by connection"),
    ticket_type: Optional[ServiceNowTicketType] = Query(None, description="Filter by ticket type"),
    sync_status: Optional[ServiceNowSyncStatus] = Query(None, description="Filter by sync status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List ServiceNow tickets for the organization.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    tickets = service.list_tickets(
        organization_id=current_user["organization_id"],
        connection_id=connection_id,
        ticket_type=ticket_type,
        sync_status=sync_status,
        limit=limit,
        offset=offset
    )

    return [
        ServiceNowTicketResponse(
            id=t.id,
            ticket_id=str(t.ticket_id),
            servicenow_sys_id=t.servicenow_sys_id,
            servicenow_number=t.servicenow_number,
            servicenow_link=t.servicenow_link,
            ticket_type=t.ticket_type,
            short_description=t.short_description,
            description=t.description,
            priority=t.priority,
            impact=t.impact,
            urgency=t.urgency,
            state=t.state,
            assignment_group=t.assignment_group,
            assigned_to=t.assigned_to,
            caller_id=t.caller_id,
            category=t.category,
            subcategory=t.subcategory,
            cmdb_ci=t.cmdb_ci,
            source_type=t.source_type,
            source_id=t.source_id,
            sync_status=t.sync_status,
            sync_attempts=t.sync_attempts,
            last_sync_error=t.last_sync_error,
            last_synced_at=t.last_synced_at,
            created_at=t.created_at,
            updated_at=t.updated_at,
            resolved_at=t.resolved_at,
            closed_at=t.closed_at,
        )
        for t in tickets
    ]


@router.get(
    "/tickets/{ticket_id}",
    response_model=ServiceNowTicketResponse,
    summary="Get ServiceNow ticket"
)
async def get_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific ServiceNow ticket by ID.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    ticket = service.get_ticket(ticket_id, current_user["organization_id"])

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ServiceNowTicketResponse(
        id=ticket.id,
        ticket_id=str(ticket.ticket_id),
        servicenow_sys_id=ticket.servicenow_sys_id,
        servicenow_number=ticket.servicenow_number,
        servicenow_link=ticket.servicenow_link,
        ticket_type=ticket.ticket_type,
        short_description=ticket.short_description,
        description=ticket.description,
        priority=ticket.priority,
        impact=ticket.impact,
        urgency=ticket.urgency,
        state=ticket.state,
        assignment_group=ticket.assignment_group,
        assigned_to=ticket.assigned_to,
        caller_id=ticket.caller_id,
        category=ticket.category,
        subcategory=ticket.subcategory,
        cmdb_ci=ticket.cmdb_ci,
        source_type=ticket.source_type,
        source_id=ticket.source_id,
        sync_status=ticket.sync_status,
        sync_attempts=ticket.sync_attempts,
        last_sync_error=ticket.last_sync_error,
        last_synced_at=ticket.last_synced_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
    )


@router.put(
    "/tickets/{ticket_id}",
    response_model=ServiceNowTicketResponse,
    summary="Update ServiceNow ticket"
)
async def update_ticket(
    ticket_id: int,
    data: ServiceNowTicketUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a ServiceNow ticket.

    Changes are synced to ServiceNow if the ticket has been previously synced.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    ticket = await service.update_ticket(
        ticket_id=ticket_id,
        organization_id=current_user["organization_id"],
        data=data
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    logger.info(f"Updated ServiceNow ticket {ticket_id} by user {current_user['user_id']}")

    return ServiceNowTicketResponse(
        id=ticket.id,
        ticket_id=str(ticket.ticket_id),
        servicenow_sys_id=ticket.servicenow_sys_id,
        servicenow_number=ticket.servicenow_number,
        servicenow_link=ticket.servicenow_link,
        ticket_type=ticket.ticket_type,
        short_description=ticket.short_description,
        description=ticket.description,
        priority=ticket.priority,
        impact=ticket.impact,
        urgency=ticket.urgency,
        state=ticket.state,
        assignment_group=ticket.assignment_group,
        assigned_to=ticket.assigned_to,
        caller_id=ticket.caller_id,
        category=ticket.category,
        subcategory=ticket.subcategory,
        cmdb_ci=ticket.cmdb_ci,
        source_type=ticket.source_type,
        source_id=ticket.source_id,
        sync_status=ticket.sync_status,
        sync_attempts=ticket.sync_attempts,
        last_sync_error=ticket.last_sync_error,
        last_synced_at=ticket.last_synced_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
    )


@router.post(
    "/tickets/{ticket_id}/retry",
    response_model=ServiceNowTicketResponse,
    summary="Retry ticket sync"
)
async def retry_ticket_sync(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retry syncing a failed ticket to ServiceNow.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)

    try:
        ticket = await service.retry_sync(ticket_id, current_user["organization_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.info(f"Retried ServiceNow ticket sync {ticket_id} by user {current_user['user_id']}")

    return ServiceNowTicketResponse(
        id=ticket.id,
        ticket_id=str(ticket.ticket_id),
        servicenow_sys_id=ticket.servicenow_sys_id,
        servicenow_number=ticket.servicenow_number,
        servicenow_link=ticket.servicenow_link,
        ticket_type=ticket.ticket_type,
        short_description=ticket.short_description,
        description=ticket.description,
        priority=ticket.priority,
        impact=ticket.impact,
        urgency=ticket.urgency,
        state=ticket.state,
        assignment_group=ticket.assignment_group,
        assigned_to=ticket.assigned_to,
        caller_id=ticket.caller_id,
        category=ticket.category,
        subcategory=ticket.subcategory,
        cmdb_ci=ticket.cmdb_ci,
        source_type=ticket.source_type,
        source_id=ticket.source_id,
        sync_status=ticket.sync_status,
        sync_attempts=ticket.sync_attempts,
        last_sync_error=ticket.last_sync_error,
        last_synced_at=ticket.last_synced_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
    )


# ============================================
# Event Mappings & Metrics
# ============================================

@router.get(
    "/event-mappings",
    summary="Get OW-kai to ServiceNow event mappings"
)
async def get_event_mappings():
    """
    Get the mapping of OW-kai event types to ServiceNow ticket defaults.

    This shows how events like 'alert.critical' map to ServiceNow incidents
    with specific priority, impact, urgency, and category settings.
    """
    return {
        "mappings": {
            event_type: {
                "ticket_type": mapping.get("ticket_type", "incident").value if hasattr(mapping.get("ticket_type"), "value") else str(mapping.get("ticket_type", "incident")),
                "priority": mapping.get("priority", "3").value if hasattr(mapping.get("priority"), "value") else str(mapping.get("priority", "3")),
                "impact": mapping.get("impact", "2").value if hasattr(mapping.get("impact"), "value") else str(mapping.get("impact", "2")),
                "urgency": mapping.get("urgency", "2").value if hasattr(mapping.get("urgency"), "value") else str(mapping.get("urgency", "2")),
                "category": mapping.get("category", "General"),
                "subcategory": mapping.get("subcategory"),
            }
            for event_type, mapping in OWKAI_TO_SERVICENOW_MAPPING.items()
        },
        "supported_event_types": list(OWKAI_TO_SERVICENOW_MAPPING.keys()),
        "ticket_types": [t.value for t in ServiceNowTicketType],
        "priority_levels": {
            "1": "Critical",
            "2": "High",
            "3": "Moderate",
            "4": "Low",
            "5": "Planning",
        },
    }


@router.get(
    "/metrics",
    response_model=ServiceNowMetricsResponse,
    summary="Get ServiceNow integration metrics"
)
async def get_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics for the ServiceNow integration.

    Includes connection counts, ticket statistics, sync success rates,
    and recent activity.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    metrics = service.get_metrics(current_user["organization_id"])

    return ServiceNowMetricsResponse(**metrics)


@router.get(
    "/sync-logs",
    summary="Get sync audit logs"
)
async def get_sync_logs(
    connection_id: Optional[int] = Query(None, description="Filter by connection"),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for ServiceNow sync operations.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = ServiceNowService(db)
    logs = service.get_sync_logs(
        organization_id=current_user["organization_id"],
        connection_id=connection_id,
        limit=limit
    )

    return {
        "logs": [
            {
                "id": log.id,
                "connection_id": log.connection_id,
                "ticket_id": log.ticket_id,
                "operation": log.operation,
                "direction": log.direction,
                "http_status_code": log.http_status_code,
                "response_time_ms": log.response_time_ms,
                "success": log.success,
                "error_message": log.error_message,
                "error_type": log.error_type,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
