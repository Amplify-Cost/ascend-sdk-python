"""
Enterprise Support Routes with Multi-Tenant Data Isolation

Implements banking-level security for support ticket management:
- Multi-tenant data isolation via organization_id
- CSRF protection for state-changing operations
- Complete audit trail with organization context
- Secure user authentication and authorization

Engineer: Donald King (OW-AI Enterprise)
Created: 2025-11-25
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from models import SupportTicket
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_
import datetime
import logging
from dependencies import get_current_user, require_csrf, get_organization_filter

router = APIRouter()
logger = logging.getLogger(__name__)


class SupportIssue(BaseModel):
    message: str
    priority: str = "medium"  # low, medium, high, critical
    category: str = None  # technical, billing, feature_request, bug_report


@router.post("/support/issue")
async def submit_issue(
    issue: SupportIssue,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Submit a support ticket with multi-tenant isolation

    Security features:
    - CSRF protection
    - Organization-scoped data isolation
    - Authenticated user requirement
    - Complete audit trail
    """

    try:
        # Use the authenticated user from the dependency
        uid = current_user.get("user_id")
        if not uid:
            logger.error(f"❌ Support ticket submission failed: No user_id in token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # 🏢 ENTERPRISE: Verify organization context
        user_org_id = current_user.get("organization_id")
        if org_id is not None and user_org_id != org_id:
            logger.warning(f"⚠️ Organization mismatch for user {uid}: token org_id={user_org_id}, filter org_id={org_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context mismatch"
            )

        # 🏢 ENTERPRISE: Multi-tenant isolation - require organization_id
        if org_id is None:
            logger.error(f"❌ Support ticket submission failed: No organization_id for user {uid}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context required"
            )

        # Create support ticket with organization context
        ticket = SupportTicket(
            user_id=uid,
            organization_id=org_id,  # 🏢 ENTERPRISE: Multi-tenant isolation
            message=issue.message,
            priority=issue.priority,
            category=issue.category,
            timestamp=int(datetime.datetime.utcnow().timestamp()),
            status="open"
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(f"✅ Support ticket created: id={ticket.id}, user_id={uid} [org_id={org_id}]")

        return {
            "status": "success",
            "ticket_id": ticket.id,
            "organization_id": org_id,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create support ticket: {str(e)} [org_id={org_id}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket"
        )


@router.get("/support/tickets")
async def list_support_tickets(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter),
    status_filter: str = None,
    limit: int = 50
):
    """
    List support tickets with multi-tenant isolation

    Security features:
    - Organization-scoped data isolation
    - User can only see their own tickets (or all if admin)
    - Status filtering
    - Pagination support
    """

    try:
        uid = current_user.get("user_id")
        user_role = current_user.get("role", "user")

        # Build query with multi-tenant isolation
        query = db.query(SupportTicket)

        # 🏢 ENTERPRISE: Multi-tenant isolation
        if org_id is not None:
            query = query.filter(SupportTicket.organization_id == org_id)
            logger.debug(f"🏢 Filtering support tickets by org_id={org_id}")
        else:
            logger.warning(f"⚠️ Listing support tickets without org_id filter for user {uid}")

        # Non-admin users can only see their own tickets
        if user_role != "admin":
            query = query.filter(SupportTicket.user_id == uid)

        # Optional status filter
        if status_filter:
            query = query.filter(SupportTicket.status == status_filter)

        # Order by creation time (newest first) and limit
        tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()

        logger.info(f"✅ Listed {len(tickets)} support tickets for user {uid} [org_id={org_id}]")

        return {
            "tickets": [
                {
                    "id": ticket.id,
                    "user_id": ticket.user_id,
                    "organization_id": ticket.organization_id,
                    "message": ticket.message,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "category": ticket.category,
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                    "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
                }
                for ticket in tickets
            ],
            "count": len(tickets),
            "organization_id": org_id
        }

    except Exception as e:
        logger.error(f"❌ Failed to list support tickets: {str(e)} [org_id={org_id}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve support tickets"
        )


@router.get("/support/tickets/{ticket_id}")
async def get_support_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get a specific support ticket with multi-tenant isolation

    Security features:
    - Organization-scoped data isolation
    - User can only access their own tickets (or all if admin)
    - Ticket ownership verification
    """

    try:
        uid = current_user.get("user_id")
        user_role = current_user.get("role", "user")

        # Build query with multi-tenant isolation
        query = db.query(SupportTicket).filter(SupportTicket.id == ticket_id)

        # 🏢 ENTERPRISE: Multi-tenant isolation
        if org_id is not None:
            query = query.filter(SupportTicket.organization_id == org_id)

        ticket = query.first()

        if not ticket:
            logger.warning(f"⚠️ Support ticket not found: id={ticket_id} [org_id={org_id}]")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found"
            )

        # Non-admin users can only access their own tickets
        if user_role != "admin" and ticket.user_id != uid:
            logger.warning(f"⚠️ Unauthorized access to ticket {ticket_id} by user {uid} [org_id={org_id}]")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this support ticket"
            )

        logger.info(f"✅ Retrieved support ticket: id={ticket_id}, user_id={uid} [org_id={org_id}]")

        return {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "organization_id": ticket.organization_id,
            "message": ticket.message,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve support ticket: {str(e)} [org_id={org_id}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve support ticket"
        )