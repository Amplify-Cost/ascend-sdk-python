"""
Platform Admin Routes - OW-AI Internal Dashboard

This module provides platform administrators (OW-AI Internal) with secure
cross-organization monitoring and management capabilities.

Key Features:
- View all organizations (metadata only, no customer data)
- Aggregated usage statistics across platform
- Create new organizations
- Monitor agent actions across all tenants
- Platform-wide analytics and health monitoring

Security Architecture:
- Platform owner enforcement (organization_id = 1)
- Metadata-only access (no customer data decryption)
- Read-only access to customer agent actions (audit purposes)
- Complete audit logging of platform admin actions
- PostgreSQL RLS bypass for platform owner organization

IMPORTANT: This module adheres to zero-trust security principles.
Platform admins can see metadata but CANNOT decrypt customer data.

Engineer: Donald King (OW-AI Enterprise)
Created: 2025-11-20
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, timedelta
import bleach

from database import get_db
from models import (
    Organization,
    User,
    AgentAction,
    AuthAuditLog,
    LoginAttempt,
    CognitoToken
)
from dependencies_cognito import require_platform_owner, log_auth_event
from dependencies import get_organization_filter

router = APIRouter(
    prefix="/platform",
    tags=["Platform Admin"]
)


# ============================================================================
# PYDANTIC SCHEMAS - Platform Admin Responses
# ============================================================================

class OrganizationMetadata(BaseModel):
    """
    Organization metadata (safe for platform admins to view).

    Security: No customer data, only operational metadata.
    """
    id: int
    name: str
    slug: str
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    user_count: int
    action_count_30d: int
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True


class PlatformUsageStats(BaseModel):
    """Aggregated platform-wide usage statistics"""
    total_organizations: int
    active_organizations: int
    total_users: int
    total_actions_30d: int
    total_actions_7d: int
    total_actions_24h: int
    by_subscription_tier: dict
    by_status: dict


class AgentActionMetadata(BaseModel):
    """
    Agent action metadata for cross-org monitoring.

    Security: NO customer data decryption. Metadata only.
    """
    id: int
    organization_id: int
    organization_name: str
    action_type: str
    risk_score: Optional[float]
    status: str
    created_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CreateOrganizationRequest(BaseModel):
    """Request to create new organization"""
    name: str
    slug: str
    subscription_tier: str = "trial"

    @validator("name")
    def validate_name(cls, v):
        """Sanitize organization name"""
        sanitized = bleach.clean(v, tags=[], strip=True).strip()
        if len(sanitized) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(sanitized) > 100:
            raise ValueError("Organization name must be less than 100 characters")
        return sanitized

    @validator("slug")
    def validate_slug(cls, v):
        """Validate organization slug"""
        # Only lowercase letters, numbers, hyphens
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        if len(v) < 2:
            raise ValueError("Slug must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("Slug must be less than 50 characters")
        return v

    @validator("subscription_tier")
    def validate_tier(cls, v):
        """Validate subscription tier"""
        allowed_tiers = ['trial', 'startup', 'business', 'enterprise']
        if v not in allowed_tiers:
            raise ValueError(f"Tier must be one of: {allowed_tiers}")
        return v


class AuthAuditLogEntry(BaseModel):
    """Authentication audit log entry"""
    id: int
    event_type: str
    organization_id: Optional[int]
    user_id: Optional[int]
    success: bool
    timestamp: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# PLATFORM ADMIN ROUTES - Organization Management
# ============================================================================

@router.get("/organizations", response_model=List[OrganizationMetadata])
async def list_all_organizations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    List all organizations on the platform (metadata only).

    Security:
    - Requires platform owner permissions
    - Returns metadata only (no customer data)
    - Supports pagination
    - Supports filtering by status and tier
    - Multi-tenant isolation (optional for platform owners)

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status: Filter by subscription status
        tier: Filter by subscription tier
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (None for platform-wide access)

    Returns:
        List of organization metadata
    """
    # Build query
    query = db.query(Organization)

    # 🏢 ENTERPRISE: Multi-tenant isolation (optional for platform owners)
    if org_id is not None:
        query = query.filter(Organization.id == org_id)

    # Apply filters
    if status:
        query = query.filter(Organization.subscription_status == status)
    if tier:
        query = query.filter(Organization.subscription_tier == tier)

    # Get organizations
    orgs = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit).all()

    # Enrich with statistics
    results = []
    for org in orgs:
        # Count users
        user_count = db.query(User).filter(User.organization_id == org.id).count()

        # Count recent actions (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        action_count = db.query(AgentAction).filter(
            AgentAction.organization_id == org.id,
            AgentAction.created_at >= thirty_days_ago
        ).count()

        # Get last activity
        last_action = db.query(AgentAction).filter(
            AgentAction.organization_id == org.id
        ).order_by(AgentAction.created_at.desc()).first()

        results.append(OrganizationMetadata(
            id=org.id,
            name=org.name,
            slug=org.slug,
            subscription_tier=org.subscription_tier,
            subscription_status=org.subscription_status,
            created_at=org.created_at,
            user_count=user_count,
            action_count_30d=action_count,
            last_activity=last_action.created_at if last_action else None
        ))

    return results


@router.post("/organizations", response_model=OrganizationMetadata)
async def create_organization(
    request: CreateOrganizationRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    Create new organization on the platform.

    Security:
    - Requires platform owner permissions
    - Validates slug uniqueness
    - Complete audit logging
    - Multi-tenant isolation enforcement

    Args:
        request: Organization creation details
        req: Request object for IP address
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (logged for audit trail)

    Returns:
        Created organization metadata
    """
    # Check if slug already exists
    existing_org = db.query(Organization).filter(
        Organization.slug == request.slug
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail=f"Organization with slug '{request.slug}' already exists"
        )

    # Create organization
    new_org = Organization(
        name=request.name,
        slug=request.slug,
        subscription_tier=request.subscription_tier,
        subscription_status='trial',
        created_at=datetime.now()
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    # Log organization creation
    log_auth_event(
        event_type="organization_created",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=current_user.get("organization_id"),  # Platform org
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "created_organization_id": new_org.id,
            "created_organization_name": new_org.name,
            "created_organization_slug": new_org.slug,
            "subscription_tier": request.subscription_tier,
            "creator_org_id": org_id  # 🏢 ENTERPRISE: Track creator's org context
        },
        db=db
    )

    return OrganizationMetadata(
        id=new_org.id,
        name=new_org.name,
        slug=new_org.slug,
        subscription_tier=new_org.subscription_tier,
        subscription_status=new_org.subscription_status,
        created_at=new_org.created_at,
        user_count=0,
        action_count_30d=0,
        last_activity=None
    )


@router.get("/organizations/{org_id}")
async def get_organization_details(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    filter_org_id: int = Depends(get_organization_filter)
):
    """
    Get detailed organization information.

    Security:
    - Multi-tenant isolation (validates org access)

    Args:
        org_id: Organization ID (path parameter)
        db: Database session
        current_user: Current authenticated platform admin
        filter_org_id: Organization filter (None for platform-wide access)

    Returns:
        Detailed organization metadata
    """
    # 🏢 ENTERPRISE: Multi-tenant isolation
    # If org filter is set, ensure requested org matches filter
    if filter_org_id is not None and org_id != filter_org_id:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to organization {org_id} [org_id={filter_org_id}]"
        )

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=404,
            detail=f"Organization not found [org_id={filter_org_id}]"
        )

    # Get statistics
    user_count = db.query(User).filter(User.organization_id == org.id).count()

    thirty_days_ago = datetime.now() - timedelta(days=30)
    seven_days_ago = datetime.now() - timedelta(days=7)
    one_day_ago = datetime.now() - timedelta(days=1)

    action_count_30d = db.query(AgentAction).filter(
        AgentAction.organization_id == org.id,
        AgentAction.created_at >= thirty_days_ago
    ).count()

    action_count_7d = db.query(AgentAction).filter(
        AgentAction.organization_id == org.id,
        AgentAction.created_at >= seven_days_ago
    ).count()

    action_count_24h = db.query(AgentAction).filter(
        AgentAction.organization_id == org.id,
        AgentAction.created_at >= one_day_ago
    ).count()

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "subscription_tier": org.subscription_tier,
        "subscription_status": org.subscription_status,
        "created_at": org.created_at,
        "user_count": user_count,
        "action_count_30d": action_count_30d,
        "action_count_7d": action_count_7d,
        "action_count_24h": action_count_24h
    }


# ============================================================================
# PLATFORM ADMIN ROUTES - Usage Statistics
# ============================================================================

@router.get("/usage-stats", response_model=PlatformUsageStats)
async def get_platform_usage_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get aggregated platform-wide usage statistics.

    Security:
    - Requires platform owner permissions
    - Aggregated data only (no individual customer data)
    - Multi-tenant isolation (optional for platform owners)

    Args:
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (None for platform-wide stats)

    Returns:
        Platform-wide usage statistics
    """
    # 🏢 ENTERPRISE: Multi-tenant isolation
    # Build base organization query with optional filtering
    org_query = db.query(Organization)
    if org_id is not None:
        org_query = org_query.filter(Organization.id == org_id)

    # Count organizations
    total_orgs = org_query.count()
    active_orgs = org_query.filter(
        Organization.subscription_status.in_(['active', 'trial'])
    ).count()

    # Count users
    user_query = db.query(User)
    if org_id is not None:
        user_query = user_query.filter(User.organization_id == org_id)
    total_users = user_query.count()

    # Count actions
    thirty_days_ago = datetime.now() - timedelta(days=30)
    seven_days_ago = datetime.now() - timedelta(days=7)
    one_day_ago = datetime.now() - timedelta(days=1)

    action_query_30d = db.query(AgentAction).filter(AgentAction.created_at >= thirty_days_ago)
    action_query_7d = db.query(AgentAction).filter(AgentAction.created_at >= seven_days_ago)
    action_query_24h = db.query(AgentAction).filter(AgentAction.created_at >= one_day_ago)

    if org_id is not None:
        action_query_30d = action_query_30d.filter(AgentAction.organization_id == org_id)
        action_query_7d = action_query_7d.filter(AgentAction.organization_id == org_id)
        action_query_24h = action_query_24h.filter(AgentAction.organization_id == org_id)

    total_actions_30d = action_query_30d.count()
    total_actions_7d = action_query_7d.count()
    total_actions_24h = action_query_24h.count()

    # Breakdown by subscription tier
    tier_query = db.query(
        Organization.subscription_tier,
        func.count(Organization.id).label('count')
    )
    if org_id is not None:
        tier_query = tier_query.filter(Organization.id == org_id)
    tier_breakdown = tier_query.group_by(Organization.subscription_tier).all()

    by_tier = {tier: count for tier, count in tier_breakdown}

    # Breakdown by status
    status_query = db.query(
        Organization.subscription_status,
        func.count(Organization.id).label('count')
    )
    if org_id is not None:
        status_query = status_query.filter(Organization.id == org_id)
    status_breakdown = status_query.group_by(Organization.subscription_status).all()

    by_status = {status: count for status, count in status_breakdown}

    return PlatformUsageStats(
        total_organizations=total_orgs,
        active_organizations=active_orgs,
        total_users=total_users,
        total_actions_30d=total_actions_30d,
        total_actions_7d=total_actions_7d,
        total_actions_24h=total_actions_24h,
        by_subscription_tier=by_tier,
        by_status=by_status
    )


# ============================================================================
# PLATFORM ADMIN ROUTES - Cross-Organization Monitoring
# ============================================================================

@router.get("/actions", response_model=List[AgentActionMetadata])
async def view_agent_actions_across_orgs(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    risk_threshold: Optional[float] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    View agent actions across all organizations (metadata only).

    Security:
    - Requires platform owner permissions
    - Returns metadata only (NO customer data decryption)
    - Read-only access for audit purposes
    - Supports filtering by org, risk score, and status
    - Multi-tenant isolation (optional for platform owners)

    IMPORTANT: This endpoint does NOT decrypt customer data.
    Platform admins can see action metadata for monitoring, but cannot
    access encrypted customer information.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        organization_id: Filter by specific organization (query parameter)
        risk_threshold: Only show actions above this risk score
        status: Filter by action status
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter from token (None for platform-wide access)

    Returns:
        List of agent action metadata across all organizations
    """
    # Build query
    query = db.query(
        AgentAction.id,
        AgentAction.organization_id,
        Organization.name.label('organization_name'),
        AgentAction.action_type,
        AgentAction.risk_score,
        AgentAction.status,
        AgentAction.created_at,
        AgentAction.executed_at
    ).join(Organization, AgentAction.organization_id == Organization.id)

    # 🏢 ENTERPRISE: Multi-tenant isolation
    # org_id from token takes precedence over query parameter
    if org_id is not None:
        query = query.filter(AgentAction.organization_id == org_id)
    elif organization_id:
        query = query.filter(AgentAction.organization_id == organization_id)

    # Apply filters
    if risk_threshold is not None:
        query = query.filter(AgentAction.risk_score >= risk_threshold)
    if status:
        query = query.filter(AgentAction.status == status)

    # Order by most recent
    actions = query.order_by(AgentAction.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to response format
    results = []
    for action in actions:
        results.append(AgentActionMetadata(
            id=action.id,
            organization_id=action.organization_id,
            organization_name=action.organization_name,
            action_type=action.action_type,
            risk_score=action.risk_score,
            status=action.status,
            created_at=action.created_at,
            executed_at=action.executed_at
        ))

    return results


@router.get("/high-risk-actions")
async def get_high_risk_actions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get high-risk actions across all organizations (risk score >= 70).

    Security:
    - Metadata only, no customer data decryption
    - Multi-tenant isolation (optional for platform owners)

    Args:
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (None for platform-wide access)

    Returns:
        High-risk actions requiring attention
    """
    # Query high-risk actions (risk_score >= 70)
    query = db.query(
        AgentAction.id,
        AgentAction.organization_id,
        Organization.name.label('organization_name'),
        AgentAction.action_type,
        AgentAction.risk_score,
        AgentAction.status,
        AgentAction.created_at
    ).join(Organization, AgentAction.organization_id == Organization.id).filter(
        AgentAction.risk_score >= 70
    )

    # 🏢 ENTERPRISE: Multi-tenant isolation
    if org_id is not None:
        query = query.filter(AgentAction.organization_id == org_id)

    high_risk_actions = query.order_by(
        AgentAction.risk_score.desc(),
        AgentAction.created_at.desc()
    ).limit(50).all()

    results = []
    for action in high_risk_actions:
        results.append({
            "id": action.id,
            "organization_id": action.organization_id,
            "organization_name": action.organization_name,
            "action_type": action.action_type,
            "risk_score": action.risk_score,
            "status": action.status,
            "created_at": action.created_at
        })

    return results


# ============================================================================
# PLATFORM ADMIN ROUTES - Security Monitoring
# ============================================================================

@router.get("/auth-audit-log", response_model=List[AuthAuditLogEntry])
async def get_auth_audit_log(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    event_type: Optional[str] = None,
    failed_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    View authentication audit log across all organizations.

    Security:
    - Requires platform owner permissions
    - Used for security monitoring and compliance
    - Supports filtering by org, event type, and success status
    - Multi-tenant isolation (optional for platform owners)

    Args:
        skip: Pagination offset
        limit: Maximum records to return
        organization_id: Filter by specific organization (query parameter)
        event_type: Filter by event type
        failed_only: Only show failed authentication attempts
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter from token (None for platform-wide access)

    Returns:
        Authentication audit log entries
    """
    # Build query
    query = db.query(AuthAuditLog)

    # 🏢 ENTERPRISE: Multi-tenant isolation
    # org_id from token takes precedence over query parameter
    if org_id is not None:
        query = query.filter(AuthAuditLog.organization_id == org_id)
    elif organization_id:
        query = query.filter(AuthAuditLog.organization_id == organization_id)

    # Apply filters
    if event_type:
        query = query.filter(AuthAuditLog.event_type == event_type)
    if failed_only:
        query = query.filter(AuthAuditLog.success == False)

    # Get results
    logs = query.order_by(AuthAuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return logs


@router.get("/brute-force-attempts")
async def get_brute_force_attempts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    Detect potential brute force attacks across the platform.

    Security:
    - Analyzes failed login attempts for security threats
    - Multi-tenant isolation (optional for platform owners)

    Args:
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (None for platform-wide access)

    Returns:
        IPs and emails with suspicious login patterns
    """
    # Get failed login attempts in last 24 hours
    one_day_ago = datetime.now() - timedelta(days=1)

    # Build base query for IP attempts
    ip_query = db.query(
        LoginAttempt.ip_address,
        func.count(LoginAttempt.id).label('attempt_count'),
        func.count(case((LoginAttempt.success == False, 1))).label('failed_count')
    ).filter(
        LoginAttempt.attempted_at >= one_day_ago,
        LoginAttempt.ip_address.isnot(None)
    )

    # 🏢 ENTERPRISE: Multi-tenant isolation
    if org_id is not None:
        ip_query = ip_query.filter(LoginAttempt.organization_id == org_id)

    ip_attempts = ip_query.group_by(LoginAttempt.ip_address).having(
        func.count(case((LoginAttempt.success == False, 1))) >= 5
    ).order_by(func.count(LoginAttempt.id).desc()).all()

    # Build base query for email attempts
    email_query = db.query(
        LoginAttempt.email,
        func.count(LoginAttempt.id).label('attempt_count'),
        func.count(case((LoginAttempt.success == False, 1))).label('failed_count')
    ).filter(
        LoginAttempt.attempted_at >= one_day_ago
    )

    # 🏢 ENTERPRISE: Multi-tenant isolation
    if org_id is not None:
        email_query = email_query.filter(LoginAttempt.organization_id == org_id)

    email_attempts = email_query.group_by(LoginAttempt.email).having(
        func.count(case((LoginAttempt.success == False, 1))) >= 5
    ).order_by(func.count(LoginAttempt.id).desc()).all()

    return {
        "suspicious_ips": [
            {
                "ip_address": ip,
                "total_attempts": total,
                "failed_attempts": failed
            }
            for ip, total, failed in ip_attempts
        ],
        "suspicious_emails": [
            {
                "email": email,
                "total_attempts": total,
                "failed_attempts": failed
            }
            for email, total, failed in email_attempts
        ]
    }


@router.delete("/organizations/{target_org_id}")
async def delete_organization(
    target_org_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    SEC-021: Delete an organization and all its data.

    Security:
    - Requires platform owner permissions (org_id = 1)
    - Cannot delete owkai-internal (org_id = 1)
    - Full audit logging
    - Deletes all related data (users, signups, etc.)

    Args:
        target_org_id: Organization ID to delete
        req: Request object for IP logging
        db: Database session
        current_user: Current authenticated platform admin

    Returns:
        Deletion confirmation with details
    """
    from sqlalchemy import text
    import logging
    logger = logging.getLogger(__name__)

    # Protect owkai-internal
    if target_org_id == 1:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete owkai-internal (platform owner organization)"
        )

    # Verify org exists
    org = db.query(Organization).filter(Organization.id == target_org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {target_org_id} not found")

    org_name = org.name
    org_slug = org.slug

    logger.info(f"SEC-021: Platform admin deleting org {target_org_id} ({org_name})")

    # Tables to clean (order matters for FK constraints)
    tables = [
        'pending_actions', 'agent_actions', 'alerts', 'smart_rules',
        'rule_feedback', 'automation_playbooks', 'playbook_versions',
        'playbook_execution_logs', 'workflows', 'workflow_steps',
        'enterprise_policies', 'policy_templates', 'api_keys', 'audit_logs',
        'risk_scoring_configs', 'notification_channels', 'webhook_endpoints',
        'servicenow_configs', 'integration_configs', 'compliance_export_jobs',
        'cognito_pool_audit', 'email_audit_log', 'mcp_governance_decisions',
        'agent_registry'
    ]

    deleted_counts = {}
    for table in tables:
        try:
            result = db.execute(
                text(f"DELETE FROM {table} WHERE organization_id = :oid"),
                {"oid": target_org_id}
            )
            if result.rowcount > 0:
                deleted_counts[table] = result.rowcount
        except Exception:
            pass  # Table might not exist

    # Handle users and their signup data
    users = db.query(User).filter(User.organization_id == target_org_id).all()
    user_emails = []
    for user in users:
        user_emails.append(user.email)
        # Delete signup audits
        db.execute(
            text("""
                DELETE FROM email_verification_audits
                WHERE signup_request_id IN (
                    SELECT id FROM signup_requests WHERE user_id = :uid
                )
            """),
            {"uid": user.id}
        )
        db.execute(text("DELETE FROM signup_requests WHERE user_id = :uid"), {"uid": user.id})

    if users:
        db.execute(text("DELETE FROM users WHERE organization_id = :oid"), {"oid": target_org_id})
        deleted_counts["users"] = len(users)

    # Delete signup_requests with this org
    result = db.execute(
        text("DELETE FROM signup_requests WHERE organization_id = :oid"),
        {"oid": target_org_id}
    )
    if result.rowcount > 0:
        deleted_counts["signup_requests"] = result.rowcount

    # Delete the organization
    db.execute(text("DELETE FROM organizations WHERE id = :oid"), {"oid": target_org_id})

    db.commit()

    # Log the deletion
    log_auth_event(
        event_type="organization_deleted",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=current_user.get("organization_id"),
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "deleted_organization_id": target_org_id,
            "deleted_organization_name": org_name,
            "deleted_organization_slug": org_slug,
            "deleted_counts": deleted_counts,
            "deleted_user_emails": user_emails
        },
        db=db
    )

    logger.info(f"SEC-021: Successfully deleted org {target_org_id}: {deleted_counts}")

    return {
        "success": True,
        "message": f"Organization {target_org_id} ({org_name}) deleted",
        "deleted_counts": deleted_counts,
        "deleted_user_emails": user_emails
    }


@router.delete("/cleanup/orphaned-orgs")
async def cleanup_orphaned_organizations(
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    SEC-021: Delete all orphaned organizations (keeping only owkai-internal).

    Security:
    - Requires platform owner permissions (org_id = 1)
    - Protects owkai-internal (org_id = 1)
    - Full audit logging

    Returns:
        Summary of deleted organizations
    """
    from sqlalchemy import text
    import logging
    logger = logging.getLogger(__name__)

    logger.info("SEC-021: Starting orphaned organization cleanup")

    # Get all orgs except owkai-internal
    orgs = db.query(Organization).filter(Organization.id != 1).order_by(Organization.id).all()

    if not orgs:
        return {"success": True, "message": "No orphaned organizations found", "deleted": []}

    deleted = []
    failed = []

    for org in orgs:
        try:
            # Tables to clean
            tables = [
                'pending_actions', 'agent_actions', 'alerts', 'smart_rules',
                'rule_feedback', 'automation_playbooks', 'playbook_versions',
                'playbook_execution_logs', 'workflows', 'workflow_steps',
                'enterprise_policies', 'policy_templates', 'api_keys', 'audit_logs',
                'risk_scoring_configs', 'notification_channels', 'webhook_endpoints',
                'servicenow_configs', 'integration_configs', 'compliance_export_jobs',
                'cognito_pool_audit', 'email_audit_log', 'mcp_governance_decisions',
                'agent_registry'
            ]

            for table in tables:
                try:
                    db.execute(
                        text(f"DELETE FROM {table} WHERE organization_id = :oid"),
                        {"oid": org.id}
                    )
                except Exception:
                    pass

            # Delete users and signup data
            users = db.query(User).filter(User.organization_id == org.id).all()
            for user in users:
                db.execute(
                    text("""
                        DELETE FROM email_verification_audits
                        WHERE signup_request_id IN (
                            SELECT id FROM signup_requests WHERE user_id = :uid
                        )
                    """),
                    {"uid": user.id}
                )
                db.execute(text("DELETE FROM signup_requests WHERE user_id = :uid"), {"uid": user.id})

            db.execute(text("DELETE FROM users WHERE organization_id = :oid"), {"oid": org.id})
            db.execute(text("DELETE FROM signup_requests WHERE organization_id = :oid"), {"oid": org.id})
            db.execute(text("DELETE FROM organizations WHERE id = :oid"), {"oid": org.id})

            deleted.append({"id": org.id, "name": org.name, "slug": org.slug})
            logger.info(f"SEC-021: Deleted org {org.id} ({org.name})")

        except Exception as e:
            failed.append({"id": org.id, "name": org.name, "error": str(e)[:100]})
            logger.error(f"SEC-021: Failed to delete org {org.id}: {e}")

    db.commit()

    # Clean orphaned signups
    db.execute(text("""
        DELETE FROM email_verification_audits
        WHERE signup_request_id IN (
            SELECT id FROM signup_requests WHERE organization_id IS NULL
        )
    """))
    db.execute(text("DELETE FROM signup_requests WHERE organization_id IS NULL"))
    db.execute(text("DELETE FROM signup_attempts"))
    db.commit()

    # Log the cleanup
    log_auth_event(
        event_type="orphaned_orgs_cleanup",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=current_user.get("organization_id"),
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "deleted_count": len(deleted),
            "failed_count": len(failed),
            "deleted_orgs": deleted,
            "failed_orgs": failed
        },
        db=db
    )

    return {
        "success": True,
        "message": f"Cleanup complete: {len(deleted)} deleted, {len(failed)} failed",
        "deleted": deleted,
        "failed": failed
    }


@router.get("/active-tokens")
async def get_active_token_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get statistics on active tokens across the platform.

    Security:
    - Multi-tenant isolation (optional for platform owners)

    Args:
        db: Database session
        current_user: Current authenticated platform admin
        org_id: Organization filter (None for platform-wide access)

    Returns:
        Token usage statistics
    """
    # Build query for active tokens by organization
    tokens_query = db.query(
        CognitoToken.organization_id,
        Organization.name.label('organization_name'),
        func.count(CognitoToken.id).label('token_count')
    ).join(Organization, CognitoToken.organization_id == Organization.id).filter(
        CognitoToken.is_revoked == False,
        CognitoToken.expires_at > datetime.now()
    )

    # 🏢 ENTERPRISE: Multi-tenant isolation
    if org_id is not None:
        tokens_query = tokens_query.filter(CognitoToken.organization_id == org_id)

    active_tokens = tokens_query.group_by(
        CognitoToken.organization_id, Organization.name
    ).all()

    # Total active tokens
    total_query = db.query(CognitoToken).filter(
        CognitoToken.is_revoked == False,
        CognitoToken.expires_at > datetime.now()
    )
    if org_id is not None:
        total_query = total_query.filter(CognitoToken.organization_id == org_id)
    total_active = total_query.count()

    # Revoked tokens (last 24 hours)
    one_day_ago = datetime.now() - timedelta(days=1)
    revoked_query = db.query(CognitoToken).filter(
        CognitoToken.is_revoked == True,
        CognitoToken.revoked_at >= one_day_ago
    )
    if org_id is not None:
        revoked_query = revoked_query.filter(CognitoToken.organization_id == org_id)
    recently_revoked = revoked_query.count()

    return {
        "total_active_tokens": total_active,
        "recently_revoked_24h": recently_revoked,
        "by_organization": [
            {
                "organization_id": org_id,
                "organization_name": org_name,
                "active_tokens": count
            }
            for org_id, org_name, count in active_tokens
        ]
    }
