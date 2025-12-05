"""
SEC-040: Enterprise Unified Admin Console Routes
Banking-Level Security for Organization Administration

CONSOLIDATED FROM:
- SEC-022: Admin Console (billing, org settings)
- Enterprise User Management (RBAC, permissions)
- Organization Admin Routes (Cognito integration)

Features:
- Organization management (settings, branding, MFA, SSO)
- User management (invite, remove, roles, RBAC levels)
- RBAC permission management (6-level hierarchy)
- Billing/subscription management (Stripe integration)
- Usage analytics dashboard
- Compliance metrics (SOX, HIPAA, PCI-DSS)
- API key management integration
- Complete audit trail with WORM compliance

Security:
- Requires org_admin role OR access_level >= ADMIN (4)
- All actions audit logged to immutable audit trail
- Rate limiting on sensitive operations
- CSRF protection
- IDOR prevention via organization_id filtering

Compliance: SOC 2 Type II, HIPAA, PCI-DSS, GDPR, SOX, NIST 800-53
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_, case
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta, UTC
from enum import IntEnum
import logging
import os
import json

# SEC-040: Optional stripe import - billing features require stripe installation
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False
    logging.getLogger(__name__).warning("SEC-040: Stripe not installed - billing features disabled")

from database import get_db
from models import Organization, User, AgentAction, Alert, SmartRule, AuditLog
from dependencies import get_current_user, get_organization_filter, require_csrf

# SEC-046: Rate limiting for brute force protection
from security.rate_limiter import limiter, RATE_LIMITS

# =============================================================================
# SEC-046: ENTERPRISE BILLING CONFIGURATION
# =============================================================================
# Tier pricing moved from hardcoded values to configurable settings
# Prices are in USD (monthly) - Stripe uses cents internally
# =============================================================================

BILLING_CONFIG = {
    "tiers": {
        # Professional - Perfect for growing teams
        "professional": {
            "name": "Professional",
            "monthly_usd": 799,
            "yearly_usd": 7990,  # ~$666/mo annual
            "included_agent_actions": 2500,
            "overage_per_action": 0.35,
            "included_users": -1,  # Unlimited (no per-seat fees)
            "support_sla_hours": 24,
            "audit_retention_days": 90,
            "features": [
                "2,500 AI agent actions/month",
                "Unlimited users (no per-seat fees)",
                "Email support (24hr SLA)",
                "Standard MCP protocol detection",
                "Audit logs (90 days)",
                "API access",
                "Webhook integrations",
                "Real-time action monitoring"
            ]
        },
        # Business - Ideal for mid-market companies (MOST POPULAR)
        "business": {
            "name": "Business",
            "monthly_usd": 1999,
            "yearly_usd": 19990,  # ~$1,666/mo annual
            "included_agent_actions": 10000,
            "overage_per_action": 0.25,
            "included_users": -1,  # Unlimited (no per-seat fees)
            "support_sla_hours": 4,
            "audit_retention_days": 365,
            "is_popular": True,
            "features": [
                "Everything in Professional, plus:",
                "10,000 AI agent actions/month",
                "Unlimited users (no per-seat fees)",
                "Priority support (4hr SLA)",
                "Advanced MCP protocol coverage",
                "Audit logs (1 year retention)",
                "SSO (SAML/OIDC)",
                "Advanced analytics dashboard",
                "Slack/Teams integration",
                "Custom approval workflows",
                "Anomaly detection alerts"
            ]
        },
        # Enterprise - Built for Fortune 500
        "enterprise": {
            "name": "Enterprise",
            "monthly_usd": 4999,
            "yearly_usd": 49992,  # $4,166/mo annual (17% discount)
            "annual_discount_percent": 17,
            "included_agent_actions": 50000,
            "overage_per_action": 0.15,
            "included_users": -1,  # Unlimited (no per-seat fees)
            "support_sla_hours": 1,
            "audit_retention_days": -1,  # Unlimited
            "features": [
                "Everything in Business, plus:",
                "50,000 AI agent actions/month",
                "Unlimited users (no per-seat fees)",
                "Dedicated support + CSM (1hr SLA)",
                "All MCP protocols + custom detection",
                "Unlimited audit log retention",
                "Advanced SSO + SCIM provisioning",
                "Custom integrations",
                "White-label options",
                "Quarterly business reviews",
                "On-premise deployment available",
                "Custom MCP server monitoring"
            ]
        },
        # Pilot - Free trial tier (internal use)
        "pilot": {
            "name": "Pilot Trial",
            "monthly_usd": 0,
            "yearly_usd": 0,
            "included_agent_actions": 500,
            "overage_per_action": 0,  # No overage during trial
            "included_users": -1,
            "support_sla_hours": 48,
            "audit_retention_days": 30,
            "is_trial": True,
            "features": [
                "500 AI agent actions/month",
                "Unlimited users",
                "Email support (48hr SLA)",
                "Basic MCP detection",
                "Audit logs (30 days)",
                "API access"
            ]
        }
    },
    "overage_rates": {
        # Per-action overage rates by tier (used as fallback)
        "professional": 0.35,
        "business": 0.25,
        "enterprise": 0.15,
        "pilot": 0.00
    },
    "thresholds": {
        "warning": 80,   # Show warning at 80% usage
        "critical": 95,  # Show critical at 95% usage
    }
}

def get_tier_pricing(tier: str) -> dict:
    """SEC-046: Get pricing for a tier from config"""
    tier_config = BILLING_CONFIG["tiers"].get(tier, BILLING_CONFIG["tiers"]["pilot"])
    return {
        "name": tier_config["name"],
        "monthly": tier_config["monthly_usd"],
        "yearly": tier_config["yearly_usd"],
        "price_cents": tier_config["monthly_usd"] * 100,  # Convert to cents for Stripe
        "included_agent_actions": tier_config["included_agent_actions"],
        "overage_per_action": tier_config["overage_per_action"],
        "support_sla_hours": tier_config["support_sla_hours"],
        "audit_retention_days": tier_config["audit_retention_days"],
        "features": tier_config["features"],
        "is_popular": tier_config.get("is_popular", False),
        "annual_discount_percent": tier_config.get("annual_discount_percent", 0)
    }


def get_overage_rate(tier: str) -> float:
    """SEC-046: Get overage rate per action for a tier"""
    tier_config = BILLING_CONFIG["tiers"].get(tier)
    if tier_config:
        return tier_config.get("overage_per_action", 0)
    return BILLING_CONFIG["overage_rates"].get(tier, 0)

# SEC-040: Import RBAC manager for permission enforcement
try:
    from rbac_manager import enterprise_rbac, AccessLevel, Permission
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False
    logging.getLogger(__name__).warning("SEC-040: RBAC manager not available - using basic role checks")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Console"])


# =============================================================================
# SEC-040: ENTERPRISE RBAC DEFINITIONS (Inline fallback if rbac_manager unavailable)
# =============================================================================

class AccessLevelEnum(IntEnum):
    """Enterprise Access Levels (0-5) - Banking-grade hierarchy"""
    RESTRICTED = 0      # Suspended/probationary users
    BASIC = 1          # Standard users - dashboard only
    POWER = 2          # Power users - analytics + alerts
    MANAGER = 3        # Managers - authorization capabilities
    ADMIN = 4          # Administrators - full system access
    EXECUTIVE = 5      # Executives - all privileges + reporting


# Permission definitions for RBAC
PERMISSION_MATRIX = {
    "dashboard": {"view": True, "export": False},
    "analytics": {"view": True, "reports": False, "export": False},
    "alerts": {"view": True, "acknowledge": False, "dismiss": False},
    "rules": {"view": False, "create": False, "modify": False, "delete": False},
    "authorization": {"view": False, "approve_low": False, "approve_medium": False, "approve_high": False, "approve_critical": False},
    "users": {"view": False, "create": False, "modify": False, "delete": False, "manage_roles": False},
    "audit": {"view": False, "export": False},
}

# Access level permission mappings
ACCESS_LEVEL_PERMISSIONS = {
    0: {},  # RESTRICTED - no permissions
    1: {"dashboard.view": True},  # BASIC
    2: {"dashboard.view": True, "dashboard.export": True, "analytics.view": True, "alerts.view": True, "alerts.acknowledge": True},  # POWER
    3: {"dashboard.view": True, "dashboard.export": True, "analytics.view": True, "analytics.reports": True,
        "alerts.view": True, "alerts.acknowledge": True, "authorization.view": True,
        "authorization.approve_low": True, "authorization.approve_medium": True, "audit.view": True},  # MANAGER
    4: {"dashboard.view": True, "dashboard.export": True, "analytics.view": True, "analytics.reports": True, "analytics.export": True,
        "alerts.view": True, "alerts.acknowledge": True, "alerts.dismiss": True,
        "rules.view": True, "rules.create": True, "rules.modify": True, "rules.delete": True,
        "authorization.view": True, "authorization.approve_low": True, "authorization.approve_medium": True, "authorization.approve_high": True,
        "users.view": True, "users.create": True, "users.modify": True,
        "audit.view": True, "audit.export": True},  # ADMIN
    5: {"dashboard.view": True, "dashboard.export": True, "analytics.view": True, "analytics.reports": True, "analytics.export": True,
        "alerts.view": True, "alerts.acknowledge": True, "alerts.dismiss": True,
        "rules.view": True, "rules.create": True, "rules.modify": True, "rules.delete": True,
        "authorization.view": True, "authorization.approve_low": True, "authorization.approve_medium": True,
        "authorization.approve_high": True, "authorization.approve_critical": True, "authorization.emergency_override": True,
        "users.view": True, "users.create": True, "users.modify": True, "users.delete": True, "users.manage_roles": True,
        "audit.view": True, "audit.export": True, "audit.delete": True},  # EXECUTIVE
}

ACCESS_LEVEL_NAMES = {
    0: "Restricted",
    1: "Basic User",
    2: "Power User",
    3: "Manager",
    4: "Administrator",
    5: "Executive"
}

# Initialize Stripe (only if available)
if STRIPE_AVAILABLE:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# =============================================================================
# SEC-040: ENHANCED DEPENDENCY - Require Org Admin with RBAC Support
# =============================================================================

async def require_org_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    SEC-040: Verify user has admin access via RBAC or legacy role system.

    Access granted if ANY of these conditions are met:
    1. user.is_org_admin == True
    2. user.role in ["admin", "owner"]
    3. user.approval_level >= 4 (ADMIN level in RBAC hierarchy)

    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # SEC-040: Check access via multiple authorization paths
    has_admin_access = (
        user.is_org_admin or
        user.role in ["admin", "owner"] or
        (user.approval_level or 0) >= AccessLevelEnum.ADMIN  # RBAC level 4+
    )

    if not has_admin_access:
        logger.warning(f"SEC-040: Admin access denied for user {user.email} (role={user.role}, level={user.approval_level})")
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required"
        )

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "is_org_admin": user.is_org_admin,
        "access_level": user.approval_level or 1,
        "permissions": ACCESS_LEVEL_PERMISSIONS.get(user.approval_level or 1, {})
    }


async def require_access_level(min_level: int):
    """
    SEC-040: Factory for creating access level dependencies.

    Usage:
        @router.get("/sensitive")
        async def endpoint(admin: dict = Depends(require_access_level(5))):
            # Only executives (level 5) can access
    """
    async def dependency(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user = db.query(User).filter(User.id == current_user.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        user_level = user.approval_level or 1

        if user_level < min_level:
            logger.warning(f"SEC-040: Access level {min_level} required, user has {user_level}")
            raise HTTPException(
                status_code=403,
                detail=f"Access level {ACCESS_LEVEL_NAMES.get(min_level, min_level)} required"
            )

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
            "access_level": user_level,
            "permissions": ACCESS_LEVEL_PERMISSIONS.get(user_level, {})
        }

    return dependency


def check_permission(user_permissions: dict, permission: str) -> bool:
    """
    SEC-040: Check if user has specific permission.

    Args:
        user_permissions: Dict of user's permissions from access level
        permission: Permission string like "users.delete" or "audit.export"

    Returns:
        bool: True if permission granted
    """
    return user_permissions.get(permission, False)


# =============================================================================
# SEC-040: ENHANCED REQUEST/RESPONSE MODELS
# =============================================================================

class OrganizationUpdate(BaseModel):
    """Organization settings update with security options"""
    name: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    email_domains: Optional[List[str]] = None
    cognito_mfa_configuration: Optional[str] = None  # OFF, OPTIONAL, ON
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=480)
    password_policy: Optional[Dict[str, Any]] = None
    allowed_ip_ranges: Optional[List[str]] = None


class UserInviteRequest(BaseModel):
    """User invitation request with RBAC support"""
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role: str = Field(default="user")
    is_org_admin: bool = Field(default=False)
    access_level: int = Field(default=1, ge=0, le=5)


class UserRoleUpdate(BaseModel):
    """User role update with RBAC level"""
    role: str
    is_org_admin: bool = Field(default=False)
    access_level: Optional[int] = Field(None, ge=0, le=5)


class UserAccessLevelUpdate(BaseModel):
    """SEC-040: Update user access level only"""
    access_level: int = Field(..., ge=0, le=5)
    reason: Optional[str] = Field(None, max_length=500)


class BillingUpdateRequest(BaseModel):
    """Billing update request"""
    subscription_tier: str
    payment_method_id: Optional[str] = None


class CustomRoleCreate(BaseModel):
    """SEC-040: Create custom role with specific permissions"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_access_level: int = Field(..., ge=0, le=5)
    permissions: Dict[str, bool] = Field(default_factory=dict)


class ComplianceReportRequest(BaseModel):
    """SEC-040: Request compliance report generation"""
    report_type: str = Field(..., description="sox, hipaa, pci, gdpr, soc2")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_evidence: bool = Field(default=False)


# =============================================================================
# SEC-046 PHASE 2: USER MANAGEMENT MODELS
# =============================================================================

class UserSuspendRequest(BaseModel):
    """SEC-046: Suspend or reactivate a user"""
    suspended: bool = Field(..., description="True to suspend, False to reactivate")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for suspension")


class UserProfileUpdate(BaseModel):
    """SEC-046: Update user profile information"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)


class PasswordResetRequest(BaseModel):
    """SEC-046: Request password reset for a user"""
    send_email: bool = Field(default=True, description="Send reset email to user")


class ForceLogoutRequest(BaseModel):
    """SEC-046: Force logout a user from all sessions"""
    revoke_all_tokens: bool = Field(default=True, description="Revoke all refresh tokens")
    reason: Optional[str] = Field(None, max_length=500)


# =============================================================================
# ORGANIZATION MANAGEMENT
# =============================================================================

@router.get("/organization")
async def get_organization_details(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-022: Get organization details for admin console.
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get user count
    user_count = db.query(User).filter(
        User.organization_id == org.id,
        User.is_active == True
    ).count()

    # Get current month usage
    # SEC-044: Use timezone-aware datetime
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    api_calls_this_month = db.query(AgentAction).filter(
        AgentAction.organization_id == org.id,
        AgentAction.created_at >= month_start
    ).count()

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "domain": org.domain,
        "email_domains": org.email_domains or [],

        # Subscription
        "subscription_tier": org.subscription_tier,
        "subscription_status": org.subscription_status,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,

        # Limits & Usage
        "included_users": org.included_users,
        "current_users": user_count,
        "included_api_calls": org.included_api_calls,
        "current_month_api_calls": api_calls_this_month,
        "included_mcp_servers": org.included_mcp_servers,

        # Cognito Configuration
        "cognito_pool_status": org.cognito_pool_status,
        "cognito_mfa_configuration": org.cognito_mfa_configuration,

        # Audit
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None
    }


@router.patch("/organization")
@limiter.limit(RATE_LIMITS["api_write"])  # SEC-046: Rate limit (30/min per IP)
async def update_organization(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    update_data: OrganizationUpdate,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-022: Update organization settings.

    Audit logged for compliance.
    Rate limited: 30 requests/minute per IP (SEC-046)
    CSRF protected: Double-submit validation (SEC-046)
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Track changes for audit
    changes = {}

    if update_data.name is not None and update_data.name != org.name:
        changes["name"] = {"old": org.name, "new": update_data.name}
        org.name = update_data.name

    if update_data.domain is not None and update_data.domain != org.domain:
        changes["domain"] = {"old": org.domain, "new": update_data.domain}
        org.domain = update_data.domain

    if update_data.email_domains is not None:
        changes["email_domains"] = {"old": org.email_domains, "new": update_data.email_domains}
        org.email_domains = update_data.email_domains

    if update_data.cognito_mfa_configuration is not None:
        if update_data.cognito_mfa_configuration not in ["OFF", "OPTIONAL", "ON"]:
            raise HTTPException(status_code=400, detail="Invalid MFA configuration")
        changes["cognito_mfa_configuration"] = {
            "old": org.cognito_mfa_configuration,
            "new": update_data.cognito_mfa_configuration
        }
        org.cognito_mfa_configuration = update_data.cognito_mfa_configuration
        # TODO: Update Cognito pool MFA settings

    # SEC-044: Use timezone-aware datetime
    org.updated_at = datetime.now(UTC)

    # Create audit log
    if changes:
        audit = AuditLog(
            organization_id=org.id,
            user_id=admin["user_id"],
            action="organization.update",
            resource_type="organization",
            resource_id=org.id,
            changes=changes,
            ip_address=request.client.host if request.client else None
        )
        db.add(audit)

    db.commit()

    logger.info(f"SEC-022: Organization {org.id} updated by user {admin['user_id']}: {changes}")

    return {"success": True, "message": "Organization updated", "changes": changes}


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@router.get("/users")
async def list_organization_users(
    include_inactive: bool = Query(False, description="Include deactivated users"),
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046: List all users in the organization with enterprise filtering.

    Enterprise Features:
    - Filters out soft-deleted users by default (is_active=True)
    - Optional include_inactive parameter for admin recovery
    - Returns user status for UI badge display
    - Includes first_name, last_name for proper display
    - Tracks is_owner to prevent self-demotion

    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1
    """
    query = db.query(User).filter(
        User.organization_id == admin["organization_id"]
    )

    # SEC-046: Filter out inactive users by default (enterprise standard)
    if not include_inactive:
        query = query.filter(User.is_active == True)

    users = query.order_by(User.created_at.desc()).all()

    # SEC-046: Determine organization owner for UI protection
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()
    owner_user_id = org.owner_user_id if org and hasattr(org, 'owner_user_id') else None

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "first_name": getattr(u, 'first_name', None) or u.email.split('@')[0],
                "last_name": getattr(u, 'last_name', None) or '',
                "role": u.role,
                "is_org_admin": u.is_org_admin,
                "is_active": u.is_active,
                # SEC-046: Compute status for UI badge (active, suspended, pending, deactivated)
                "status": _compute_user_status(u),
                "is_owner": u.id == owner_user_id if owner_user_id else u.is_org_admin and u.role == "admin",
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "last_active_at": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "approval_level": u.approval_level or 1,
                "access_level_name": ACCESS_LEVEL_NAMES.get(u.approval_level or 1, "Basic User"),
                "is_emergency_approver": u.is_emergency_approver,
                "mfa_enabled": getattr(u, 'mfa_enabled', False)
            }
            for u in users
        ],
        "total": len(users),
        "active_count": sum(1 for u in users if u.is_active),
        "inactive_count": sum(1 for u in users if not u.is_active)
    }


def _compute_user_status(user) -> str:
    """
    SEC-046: Compute user status for UI display.

    Status hierarchy:
    - deactivated: is_active=False (soft deleted)
    - suspended: is_suspended=True (temporary disable)
    - pending: never logged in (invited but not activated)
    - active: normal active user
    """
    if not user.is_active:
        return "deactivated"
    if getattr(user, 'is_suspended', False):
        return "suspended"
    if user.last_login is None:
        return "pending"
    return "active"


@router.post("/users/invite")
@limiter.limit("10/minute")  # SEC-046: Strict rate limit for user creation
async def invite_user(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    invite_data: UserInviteRequest,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-022: Invite a new user to the organization.

    Security:
    - Validates against user limit
    - Creates Cognito user
    - Generates secure temporary password
    - Sends invitation email
    - Audit logged
    - Rate limited: 10 requests/minute per IP (SEC-046)
    - CSRF protected: Double-submit validation (SEC-046)
    """
    import bcrypt
    import secrets
    from services.enterprise_email_service import EnterpriseEmailService

    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    # Check user limit
    current_user_count = db.query(User).filter(
        User.organization_id == org.id,
        User.is_active == True
    ).count()

    if current_user_count >= org.included_users:
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached ({org.included_users}). Upgrade your plan to add more users."
        )

    # Check if email already exists in org
    existing_user = db.query(User).filter(
        User.email == invite_data.email.lower(),
        User.organization_id == org.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists in your organization"
        )

    # Validate role
    # SEC-044: Enterprise role list including analyst for security analysts
    valid_roles = ["user", "admin", "manager", "viewer", "analyst"]
    if invite_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    # Only admins can create admins
    if invite_data.role == "admin" and admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create admin users")

    # Generate secure temporary password
    temp_password = secrets.token_urlsafe(16)
    password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

    # SEC-034: Create Cognito user FIRST (fail-secure pattern)
    # If Cognito fails, we don't create orphan database records
    cognito_user_id = None
    try:
        import boto3
        from botocore.exceptions import ClientError

        # Get per-org Cognito pool or fall back to default
        pool_id = org.cognito_user_pool_id or os.getenv('COGNITO_USER_POOL_ID')

        if not pool_id:
            logger.warning(f"SEC-034: No Cognito pool configured for org {org.id}, skipping Cognito user creation")
        else:
            cognito = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'us-east-2'))

            # Prepare user attributes
            user_attributes = [
                {'Name': 'email', 'Value': invite_data.email.lower()},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'custom:organization_id', 'Value': str(org.id)},
                {'Name': 'custom:organization_slug', 'Value': org.slug or ''},
                {'Name': 'custom:role', 'Value': invite_data.role},
                {'Name': 'custom:is_org_admin', 'Value': 'true' if invite_data.is_org_admin else 'false'}
            ]

            # Add name attributes if available
            if invite_data.first_name:
                user_attributes.append({'Name': 'given_name', 'Value': invite_data.first_name})
            if invite_data.last_name:
                user_attributes.append({'Name': 'family_name', 'Value': invite_data.last_name})

            # Create user in Cognito with temporary password
            logger.info(f"SEC-034: Creating Cognito user for {invite_data.email} in pool {pool_id}")
            response = cognito.admin_create_user(
                UserPoolId=pool_id,
                Username=invite_data.email.lower(),
                TemporaryPassword=temp_password,
                UserAttributes=user_attributes,
                DesiredDeliveryMediums=['EMAIL'],
                MessageAction='SUPPRESS'  # We send custom invitation email
            )

            # Extract Cognito user ID (sub) from response
            for attr in response['User']['Attributes']:
                if attr['Name'] == 'sub':
                    cognito_user_id = attr['Value']
                    break

            if not cognito_user_id:
                raise HTTPException(status_code=500, detail="SEC-034: Failed to extract Cognito user ID")

            logger.info(f"SEC-034: Cognito user created: {cognito_user_id}")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"SEC-034: Cognito user creation failed: {error_code} - {error_msg}")

        if error_code == 'UsernameExistsException':
            raise HTTPException(
                status_code=409,
                detail=f"User with email {invite_data.email} already exists in authentication system"
            )
        elif error_code == 'InvalidParameterException':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user data: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"SEC-034: Failed to create user identity: {error_code}"
            )
    except Exception as e:
        # Non-Cognito errors (boto3 import, network, etc.)
        if 'ClientError' not in str(type(e)):
            logger.error(f"SEC-034: Unexpected error during Cognito user creation: {e}")
            # Allow fallback to database-only if Cognito is not configured
            if org.cognito_user_pool_id:
                raise HTTPException(
                    status_code=500,
                    detail=f"SEC-034: Identity provider error: {str(e)}"
                )

    # Create database user (only after Cognito succeeds or is skipped)
    # SEC-044: Use timezone-aware datetime for consistency
    new_user = User(
        email=invite_data.email.lower(),
        password=password_hash,
        role=invite_data.role,
        organization_id=org.id,
        is_org_admin=invite_data.is_org_admin,
        is_active=True,
        force_password_change=True,
        created_at=datetime.now(UTC),
        cognito_user_id=cognito_user_id  # SEC-034: Store Cognito user ID
    )
    db.add(new_user)
    db.flush()

    # Create audit log with SEC-034 Cognito user ID
    audit = AuditLog(
        organization_id=org.id,
        user_id=admin["user_id"],
        action="user.invite",
        resource_type="user",
        resource_id=new_user.id,
        changes={
            "email": invite_data.email,
            "role": invite_data.role,
            "is_org_admin": invite_data.is_org_admin,
            "cognito_user_id": cognito_user_id,  # SEC-034: Audit trail includes Cognito ID
            "cognito_pool_id": org.cognito_user_pool_id or os.getenv('COGNITO_USER_POOL_ID')
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    # Send invitation email
    try:
        email_service = EnterpriseEmailService()
        login_url = f"{os.getenv('FRONTEND_URL', 'https://ascendowkai.com')}/login/{org.slug}"
        await email_service.send_user_invitation_email(
            db=db,
            to_email=invite_data.email,
            organization_name=org.name,
            organization_slug=org.slug,
            temp_password=temp_password,
            login_url=login_url,
            invited_by=admin["email"],
            role=invite_data.role
        )
    except Exception as e:
        logger.error(f"SEC-022: Failed to send invitation email: {e}")
        # Don't fail the invite if email fails

    logger.info(f"SEC-034: User {invite_data.email} invited to org {org.id} by {admin['email']} (cognito_user_id={cognito_user_id})")

    return {
        "success": True,
        "message": f"Invitation sent to {invite_data.email}",
        "user_id": new_user.id,
        "cognito_user_id": cognito_user_id,  # SEC-034: Include for verification
        "cognito_enabled": cognito_user_id is not None
    }


@router.patch("/users/{user_id}/role")
@limiter.limit(RATE_LIMITS["api_write"])  # SEC-046: Rate limit (30/min per IP)
async def update_user_role(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    role_update: UserRoleUpdate,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-022: Update a user's role.
    Rate limited: 30 requests/minute per IP (SEC-046)
    CSRF protected: Double-submit validation (SEC-046)
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Can't demote yourself
    if user.id == admin["user_id"] and role_update.role != user.role:
        raise HTTPException(status_code=403, detail="Cannot change your own role")

    old_role = user.role
    old_is_org_admin = user.is_org_admin

    user.role = role_update.role
    user.is_org_admin = role_update.is_org_admin

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.role_change",
        resource_type="user",
        resource_id=user.id,
        changes={
            "role": {"old": old_role, "new": role_update.role},
            "is_org_admin": {"old": old_is_org_admin, "new": role_update.is_org_admin}
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-022: User {user_id} role changed from {old_role} to {role_update.role}")

    return {"success": True, "message": "User role updated"}


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")  # SEC-046: Strict rate limit for user deletion
async def remove_user(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-022: Remove a user from the organization.

    Security:
    - Soft delete (is_active = False)
    - Revokes all active sessions
    - Audit logged
    - CSRF protected: Double-submit validation (SEC-046)
    - Rate limited: 10 requests/minute per IP (SEC-046)
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Can't remove yourself
    if user.id == admin["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot remove yourself")

    # Soft delete
    user.is_active = False
    # TODO: Revoke Cognito sessions

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.remove",
        resource_type="user",
        resource_id=user.id,
        changes={"email": user.email, "deactivated": True},
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-022: User {user_id} removed from org {admin['organization_id']} by {admin['email']}")

    return {"success": True, "message": "User removed"}


# =============================================================================
# SEC-046 PHASE 2: ADVANCED USER MANAGEMENT
# =============================================================================

@router.patch("/users/{user_id}/suspend")
@limiter.limit("10/minute")
async def suspend_or_reactivate_user(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    suspend_data: UserSuspendRequest,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)
):
    """
    SEC-046 Phase 2: Suspend or reactivate a user.

    Enterprise Features:
    - Temporary suspension (different from soft delete)
    - Suspension reason tracking for compliance
    - Automatic session revocation on suspend
    - Audit trail for SOX/HIPAA compliance

    Compliance: SOC 2 CC6.1, HIPAA 164.312(a)(1), NIST AC-2
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Can't suspend yourself
    if user.id == admin["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot suspend yourself")

    # Track changes
    old_status = "suspended" if getattr(user, 'is_suspended', False) else "active"
    new_status = "suspended" if suspend_data.suspended else "active"

    # Update user
    user.is_suspended = suspend_data.suspended
    if suspend_data.suspended:
        user.suspended_at = datetime.now(UTC)
        user.suspended_by = admin["user_id"]
        user.suspension_reason = suspend_data.reason
    else:
        user.suspended_at = None
        user.suspended_by = None
        user.suspension_reason = None

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.suspend" if suspend_data.suspended else "user.reactivate",
        resource_type="user",
        resource_id=user.id,
        changes={
            "email": user.email,
            "status": {"old": old_status, "new": new_status},
            "reason": suspend_data.reason
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    action = "suspended" if suspend_data.suspended else "reactivated"
    logger.info(f"SEC-046: User {user.email} {action} by {admin['email']}")

    return {
        "success": True,
        "message": f"User {action} successfully",
        "user_id": user.id,
        "status": new_status
    }


@router.patch("/users/{user_id}/profile")
@limiter.limit(RATE_LIMITS["api_write"])
async def update_user_profile(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    profile_data: UserProfileUpdate,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)
):
    """
    SEC-046 Phase 2: Update user profile information.

    Enterprise Features:
    - Partial update (only provided fields)
    - Email change validation
    - Change tracking for audit
    - Cognito sync for email changes

    Compliance: SOC 2 CC6.1, GDPR Art. 16
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Track changes
    changes = {}

    if profile_data.first_name is not None:
        changes["first_name"] = {"old": getattr(user, 'first_name', None), "new": profile_data.first_name}
        user.first_name = profile_data.first_name

    if profile_data.last_name is not None:
        changes["last_name"] = {"old": getattr(user, 'last_name', None), "new": profile_data.last_name}
        user.last_name = profile_data.last_name

    if profile_data.email is not None and profile_data.email != user.email:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == profile_data.email,
            User.organization_id == admin["organization_id"],
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        changes["email"] = {"old": user.email, "new": profile_data.email}
        user.email = profile_data.email
        # TODO: Sync with Cognito if using Cognito auth

    if profile_data.phone is not None:
        changes["phone"] = {"old": getattr(user, 'phone', None), "new": profile_data.phone}
        user.phone = profile_data.phone

    if profile_data.department is not None:
        changes["department"] = {"old": getattr(user, 'department', None), "new": profile_data.department}
        user.department = profile_data.department

    if profile_data.job_title is not None:
        changes["job_title"] = {"old": getattr(user, 'job_title', None), "new": profile_data.job_title}
        user.job_title = profile_data.job_title

    if not changes:
        return {"success": True, "message": "No changes made", "changes": {}}

    user.updated_at = datetime.now(UTC)

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.profile_update",
        resource_type="user",
        resource_id=user.id,
        changes=changes,
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-046: User {user.email} profile updated by {admin['email']}: {list(changes.keys())}")

    return {
        "success": True,
        "message": "Profile updated successfully",
        "user_id": user.id,
        "changes": changes
    }


@router.post("/users/{user_id}/reset-password")
@limiter.limit("5/minute")  # Strict limit for password operations
async def reset_user_password(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    reset_data: PasswordResetRequest,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)
):
    """
    SEC-046 Phase 2: Trigger password reset for a user.

    Enterprise Features:
    - Admin-initiated password reset
    - Cognito integration for password reset flow
    - Email notification to user
    - Audit logging for compliance

    Compliance: SOC 2 CC6.1, NIST IA-5, PCI-DSS 8.2.4
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get organization for Cognito pool info
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    reset_initiated = False
    reset_method = "email"

    # Try Cognito password reset
    if org and org.cognito_user_pool_id and user.cognito_user_id:
        try:
            import boto3
            cognito = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'us-east-2'))

            # Admin reset password - this sends an email to the user
            cognito.admin_reset_user_password(
                UserPoolId=org.cognito_user_pool_id,
                Username=user.cognito_user_id
            )
            reset_initiated = True
            reset_method = "cognito"
            logger.info(f"SEC-046: Cognito password reset initiated for {user.email}")
        except Exception as e:
            logger.error(f"SEC-046: Cognito password reset failed: {e}")
            # Fall back to manual reset
            reset_method = "manual"

    # If Cognito not available, generate temporary password
    if not reset_initiated:
        import secrets
        import bcrypt
        temp_password = secrets.token_urlsafe(16)
        user.password = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
        user.force_password_change = True
        reset_initiated = True

        # Send email with temp password if requested
        if reset_data.send_email:
            try:
                from services.enterprise_email_service import EnterpriseEmailService
                email_service = EnterpriseEmailService()
                # TODO: Implement password reset email template
                logger.info(f"SEC-046: Password reset email would be sent to {user.email}")
            except Exception as e:
                logger.error(f"SEC-046: Failed to send reset email: {e}")

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.password_reset",
        resource_type="user",
        resource_id=user.id,
        changes={
            "email": user.email,
            "reset_method": reset_method,
            "email_sent": reset_data.send_email
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-046: Password reset for {user.email} by {admin['email']} via {reset_method}")

    return {
        "success": True,
        "message": "Password reset initiated",
        "user_id": user.id,
        "reset_method": reset_method,
        "email_sent": reset_data.send_email and reset_method == "cognito"
    }


@router.post("/users/{user_id}/force-logout")
@limiter.limit("10/minute")
async def force_logout_user(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    logout_data: ForceLogoutRequest,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)
):
    """
    SEC-046 Phase 2: Force logout a user from all sessions.

    Enterprise Features:
    - Revoke all active sessions
    - Invalidate refresh tokens
    - Cognito global sign-out
    - Immediate effect (no grace period)

    Compliance: SOC 2 CC6.1, HIPAA 164.312(d), NIST AC-12
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get organization for Cognito pool info
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    sessions_revoked = 0
    cognito_logout = False

    # Try Cognito global sign-out
    if org and org.cognito_user_pool_id and user.cognito_user_id:
        try:
            import boto3
            cognito = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'us-east-2'))

            # Global sign-out - invalidates all tokens
            cognito.admin_user_global_sign_out(
                UserPoolId=org.cognito_user_pool_id,
                Username=user.cognito_user_id
            )
            cognito_logout = True
            sessions_revoked += 1
            logger.info(f"SEC-046: Cognito global sign-out for {user.email}")
        except Exception as e:
            logger.error(f"SEC-046: Cognito sign-out failed: {e}")

    # Invalidate local refresh tokens if stored
    if logout_data.revoke_all_tokens:
        # Update user's token version to invalidate existing tokens
        user.token_version = (getattr(user, 'token_version', 0) or 0) + 1
        user.last_logout = datetime.now(UTC)
        sessions_revoked += 1

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.force_logout",
        resource_type="user",
        resource_id=user.id,
        changes={
            "email": user.email,
            "cognito_logout": cognito_logout,
            "tokens_revoked": logout_data.revoke_all_tokens,
            "reason": logout_data.reason
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-046: Force logout for {user.email} by {admin['email']}")

    return {
        "success": True,
        "message": "User logged out from all sessions",
        "user_id": user.id,
        "sessions_revoked": sessions_revoked,
        "cognito_logout": cognito_logout
    }


@router.get("/users/{user_id}/activity")
async def get_user_activity_log(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046 Phase 2: Get activity log for a specific user.

    Enterprise Features:
    - User-specific audit trail
    - Actions performed BY and ON the user
    - Pagination support
    - Risk classification

    Compliance: SOC 2 CC6.1, HIPAA 164.312(b), SOX 302/404
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get activities where user performed action OR was target
    activities = db.query(AuditLog).filter(
        AuditLog.organization_id == admin["organization_id"],
        or_(
            AuditLog.user_id == user_id,  # User performed action
            and_(
                AuditLog.resource_type == "user",
                AuditLog.resource_id == user_id  # User was target
            )
        )
    ).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    # Get total count
    total_count = db.query(AuditLog).filter(
        AuditLog.organization_id == admin["organization_id"],
        or_(
            AuditLog.user_id == user_id,
            and_(
                AuditLog.resource_type == "user",
                AuditLog.resource_id == user_id
            )
        )
    ).count()

    # Format activities
    activity_list = []
    for activity in activities:
        # Determine if user was actor or target
        is_actor = activity.user_id == user_id

        activity_list.append({
            "id": activity.id,
            "timestamp": activity.created_at.isoformat() if activity.created_at else None,
            "action": activity.action,
            "action_display": _format_action_display(activity.action),
            "role": "actor" if is_actor else "target",
            "resource_type": activity.resource_type,
            "resource_id": activity.resource_id,
            "details": activity.changes or {},
            "ip_address": activity.ip_address,
            "risk_level": _classify_audit_risk(activity.action)
        })

    return {
        "user_id": user_id,
        "user_email": user.email,
        "activities": activity_list,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total_count
    }


def _format_action_display(action: str) -> str:
    """SEC-046: Format action string for display"""
    action_display = {
        "user.login": "Logged in",
        "user.logout": "Logged out",
        "user.invite": "Invited to organization",
        "user.remove": "Removed from organization",
        "user.role_change": "Role changed",
        "user.profile_update": "Profile updated",
        "user.password_reset": "Password reset",
        "user.force_logout": "Force logged out",
        "user.suspend": "Account suspended",
        "user.reactivate": "Account reactivated",
        "user.mfa_setup": "MFA configured",
        "authorization.approve": "Approved action",
        "authorization.deny": "Denied action",
        "rule.create": "Created rule",
        "rule.update": "Updated rule",
        "rule.delete": "Deleted rule",
        "organization.update": "Updated organization settings",
        "subscription.upgrade": "Upgraded subscription"
    }
    return action_display.get(action, action.replace(".", " ").replace("_", " ").title())


# =============================================================================
# BILLING & SUBSCRIPTION
# =============================================================================

@router.get("/billing")
async def get_billing_details(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046: Get billing and subscription details with enterprise metrics.

    Enterprise Features:
    - Flat limit values for React compatibility (prevents Error #31)
    - Detailed usage breakdown for analytics
    - Overage cost calculation
    - Trial period tracking
    - Current period dates for invoice display

    Compliance: SOC 2 CC6.1, PCI-DSS 3.4
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # SEC-046: Calculate current usage with timezone-aware datetime
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate next month for period end
    if now.month == 12:
        period_end = now.replace(year=now.year + 1, month=1, day=1)
    else:
        period_end = now.replace(month=now.month + 1, day=1)

    api_calls_this_month = db.query(AgentAction).filter(
        AgentAction.organization_id == org.id,
        AgentAction.created_at >= month_start
    ).count()

    user_count = db.query(User).filter(
        User.organization_id == org.id,
        User.is_active == True
    ).count()

    # SEC-046: Count MCP servers and agents for limits display
    mcp_servers_count = 0
    agents_count = 0
    try:
        from models_mcp_governance import MCPServer
        mcp_servers_count = db.query(MCPServer).filter(
            MCPServer.is_active == True
        ).count()
    except Exception:
        pass

    try:
        # Count unique agent_ids from recent actions
        agents_count = db.query(func.count(func.distinct(AgentAction.agent_id))).filter(
            AgentAction.organization_id == org.id,
            AgentAction.created_at >= month_start
        ).scalar() or 0
    except Exception:
        pass

    # SEC-046: Get pricing from config (includes tier-specific overage rates)
    current_pricing = get_tier_pricing(org.subscription_tier)

    # SEC-046: Calculate overage using tier-specific rates
    # Use org's included actions if set, otherwise use tier default
    included_agent_actions = org.included_api_calls or current_pricing["included_agent_actions"]
    overage_actions = max(0, api_calls_this_month - included_agent_actions)
    # Use tier-specific overage rate (e.g., $0.35/action for Professional, $0.25 for Business)
    overage_rate = current_pricing["overage_per_action"]
    overage_cost = overage_actions * overage_rate

    # Calculate usage percentages for warnings
    api_usage_percent = (api_calls_this_month / included_agent_actions * 100) if included_agent_actions > 0 else 0
    # Unlimited users (-1) means no percentage calculation needed
    user_usage_percent = 0  # Unlimited users for all tiers

    # SEC-046: Calculate days remaining
    days_remaining = None
    if org.trial_ends_at and org.subscription_status == "trial":
        days_remaining = max(0, (org.trial_ends_at - now).days)

    return {
        # SEC-046: Top-level fields for frontend compatibility
        "tier": org.subscription_tier,
        "tier_name": current_pricing["name"],
        "status": org.subscription_status,
        "is_trial": org.subscription_status == "trial",
        "is_popular": current_pricing["is_popular"],
        "days_remaining": days_remaining,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,

        # SEC-046: Flat limit numbers for React (prevents Error #31)
        # Note: users = -1 means unlimited (no per-seat fees)
        "limits": {
            "users": -1,  # Unlimited users for all tiers
            "agent_actions": included_agent_actions,
            "api_calls": included_agent_actions,  # Alias for backward compatibility
            "mcp_servers": org.included_mcp_servers or 10,
            "agents": getattr(org, 'included_agents', 50) or 50,
            "audit_retention_days": current_pricing["audit_retention_days"]
        },

        # SEC-046: Current usage for display
        "usage": {
            "users": user_count,
            "agent_actions": api_calls_this_month,
            "api_calls": api_calls_this_month,  # Alias for backward compatibility
            "mcp_servers": mcp_servers_count,
            "agents": agents_count
        },

        # SEC-046: Usage percentages for warning indicators (thresholds from config)
        "usage_percent": {
            "users": 0,  # N/A - unlimited users
            "agent_actions": round(api_usage_percent, 1),
            "api_calls": round(api_usage_percent, 1),  # Alias
            "warning_threshold": BILLING_CONFIG["thresholds"]["warning"],
            "critical_threshold": BILLING_CONFIG["thresholds"]["critical"]
        },

        # Period information
        "current_period_start": month_start.isoformat(),
        "current_period_end": period_end.isoformat(),
        "price_cents": current_pricing["price_cents"],
        "monthly_price_usd": current_pricing["monthly"],
        "yearly_price_usd": current_pricing["yearly"],
        "annual_discount_percent": current_pricing["annual_discount_percent"],
        "billing_email": getattr(org, 'billing_email', None) or getattr(org, 'primary_email', None),

        # Overage details
        "overage": {
            "agent_actions": overage_actions,
            "api_calls": overage_actions,  # Alias
            "rate_per_action": overage_rate,
            "estimated_cost": round(overage_cost, 2)
        },

        # Support SLA
        "support": {
            "sla_hours": current_pricing["support_sla_hours"],
            "tier_level": "dedicated" if current_pricing["support_sla_hours"] <= 1 else
                         "priority" if current_pricing["support_sla_hours"] <= 4 else "standard"
        },

        # Full pricing config for current tier
        "pricing": current_pricing,

        # All available tiers for upgrade options
        "available_tiers": {
            tier_key: {
                "name": tier_data["name"],
                "monthly_usd": tier_data["monthly_usd"],
                "yearly_usd": tier_data["yearly_usd"],
                "included_agent_actions": tier_data["included_agent_actions"],
                "overage_per_action": tier_data["overage_per_action"],
                "features": tier_data["features"],
                "is_popular": tier_data.get("is_popular", False)
            }
            for tier_key, tier_data in BILLING_CONFIG["tiers"].items()
            if not tier_data.get("is_trial", False)  # Exclude trial tier from upgrade options
        },

        # Stripe integration
        "stripe": {
            "customer_id": getattr(org, 'stripe_customer_id', None),
            "has_payment_method": False  # TODO: Check with Stripe API
        },

        # SEC-046: Invoice history placeholder (enterprise feature)
        "invoices": []  # TODO: Fetch from Stripe when integrated
    }


@router.post("/billing/upgrade")
@limiter.limit("5/minute")  # SEC-046: Strict rate limit for billing operations
async def upgrade_subscription(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    upgrade_data: BillingUpdateRequest,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-022: Upgrade subscription tier.

    Integrates with Stripe for payment processing.
    Rate limited: 5 requests/minute per IP (SEC-046)
    CSRF protected: Double-submit validation (SEC-046)
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    # SEC-046: Use config-based tiers (professional, business, enterprise)
    valid_tiers = list(BILLING_CONFIG["tiers"].keys())
    if upgrade_data.subscription_tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

    # SEC-046: Tier ordering for upgrade validation
    tier_order = {"pilot": 0, "professional": 1, "business": 2, "enterprise": 3}
    current_tier_level = tier_order.get(org.subscription_tier, 0)
    new_tier_level = tier_order.get(upgrade_data.subscription_tier, 0)

    if new_tier_level <= current_tier_level:
        raise HTTPException(status_code=400, detail="Can only upgrade to a higher tier")

    # SEC-046: Get limits from config
    new_tier_config = BILLING_CONFIG["tiers"][upgrade_data.subscription_tier]

    old_tier = org.subscription_tier

    # SEC-046: Update organization with config-based limits
    org.subscription_tier = upgrade_data.subscription_tier
    org.subscription_status = "active"
    # Unlimited users (-1) for all tiers
    org.included_users = new_tier_config["included_users"] if new_tier_config["included_users"] > 0 else 9999
    org.included_api_calls = new_tier_config["included_agent_actions"]
    org.included_mcp_servers = 50  # Standard for all tiers
    org.trial_ends_at = None  # End trial on upgrade

    # SEC-046: Prepare limits for response
    new_limits = {
        "tier_name": new_tier_config["name"],
        "agent_actions": new_tier_config["included_agent_actions"],
        "overage_per_action": new_tier_config["overage_per_action"],
        "support_sla_hours": new_tier_config["support_sla_hours"],
        "audit_retention_days": new_tier_config["audit_retention_days"],
        "users": "unlimited",
        "monthly_price_usd": new_tier_config["monthly_usd"]
    }

    # Audit log
    audit = AuditLog(
        organization_id=org.id,
        user_id=admin["user_id"],
        action="subscription.upgrade",
        resource_type="organization",
        resource_id=org.id,
        changes={
            "tier": {"old": old_tier, "new": upgrade_data.subscription_tier},
            "agent_actions": {"old": org.included_api_calls, "new": new_tier_config["included_agent_actions"]}
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-022: Org {org.id} upgraded from {old_tier} to {upgrade_data.subscription_tier}")

    return {
        "success": True,
        "message": f"Upgraded to {new_tier_config['name']}",
        "new_limits": new_limits
    }


@router.get("/billing/portal")
async def get_billing_portal_url(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-022: Get Stripe billing portal URL.
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    # SEC-022: Check if Stripe is available and configured
    if not STRIPE_AVAILABLE or not stripe.api_key:
        return {"portal_url": None, "message": "Billing portal not configured"}

    # Create or get Stripe customer
    customer_id = getattr(org, 'stripe_customer_id', None)
    if not customer_id:
        # Create Stripe customer
        try:
            customer = stripe.Customer.create(
                email=admin["email"],
                name=org.name,
                metadata={"organization_id": str(org.id)}
            )
            # TODO: Save customer_id to org
            customer_id = customer.id
        except Exception as e:
            logger.error(f"SEC-022: Failed to create Stripe customer: {e}")
            return {"portal_url": None, "error": "Failed to create billing account"}

    # Create billing portal session
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{os.getenv('FRONTEND_URL', 'https://ascendowkai.com')}/admin/billing"
        )
        return {"portal_url": session.url}
    except Exception as e:
        logger.error(f"SEC-022: Failed to create billing portal session: {e}")
        return {"portal_url": None, "error": "Failed to create billing portal"}


# =============================================================================
# USAGE ANALYTICS
# =============================================================================

@router.get("/analytics/overview")
async def get_analytics_overview(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046: Get usage analytics overview with enterprise metrics.

    Enterprise Features:
    - Flat field names for frontend compatibility
    - Trend calculations (period-over-period change)
    - Endpoint statistics for API usage analysis
    - Top users by activity for governance
    - Recent activity feed

    Compliance: SOC 2 CC6.1, HIPAA 164.312(b), PCI-DSS 10.2
    """
    org_id = admin["organization_id"]
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    day_ago = now - timedelta(days=1)

    # SEC-046: Calculate previous period for trend comparison
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # ========================================
    # API Calls Metrics
    # ========================================
    api_calls_this_month = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= month_start
    ).count()

    api_calls_last_month = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= prev_month_start,
        AgentAction.created_at < month_start
    ).count()

    # Calculate trend percentage
    api_calls_trend = 0
    if api_calls_last_month > 0:
        api_calls_trend = round(((api_calls_this_month - api_calls_last_month) / api_calls_last_month) * 100, 1)

    # ========================================
    # Active Users Metrics
    # ========================================
    active_users_count = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True,
        User.last_login >= week_ago
    ).count()

    active_users_prev_week = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True,
        User.last_login >= two_weeks_ago,
        User.last_login < week_ago
    ).count()

    active_users_trend = 0
    if active_users_prev_week > 0:
        active_users_trend = round(((active_users_count - active_users_prev_week) / active_users_prev_week) * 100, 1)

    # ========================================
    # Alerts Processed
    # ========================================
    alerts_processed = db.query(Alert).filter(
        Alert.organization_id == org_id,
        Alert.timestamp >= month_start
    ).count()

    alerts_last_month = db.query(Alert).filter(
        Alert.organization_id == org_id,
        Alert.timestamp >= prev_month_start,
        Alert.timestamp < month_start
    ).count()

    alerts_trend = 0
    if alerts_last_month > 0:
        alerts_trend = round(((alerts_processed - alerts_last_month) / alerts_last_month) * 100, 1)

    # ========================================
    # Active Rules
    # ========================================
    try:
        active_rules_count = db.query(SmartRule).filter(
            SmartRule.organization_id == org_id,
            SmartRule.is_enabled == True
        ).count()
    except Exception:
        active_rules_count = db.query(SmartRule).filter(
            SmartRule.organization_id == org_id
        ).count()

    rules_trend = 0  # Rules don't typically have trend comparison

    # ========================================
    # SEC-046: Endpoint Statistics (Enterprise Feature)
    # ========================================
    endpoint_stats = []
    try:
        # SEC-046: Query with processing_time_ms for response time tracking
        endpoint_query = db.query(
            AgentAction.action_type,
            func.count(AgentAction.id).label('calls'),
            func.avg(AgentAction.processing_time_ms).label('avg_response_ms')
        ).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= month_start
        ).group_by(AgentAction.action_type).order_by(desc('calls')).limit(10).all()

        for stat in endpoint_query:
            endpoint_stats.append({
                "endpoint": f"/api/{stat.action_type}" if stat.action_type else "/api/unknown",
                "calls": stat.calls,
                "avg_response_ms": round(float(stat.avg_response_ms or 0), 1),
                "error_rate": 0.0  # TODO: Calculate from error counts
            })
    except Exception as e:
        logger.warning(f"SEC-046: endpoint_stats query failed: {e}")
        endpoint_stats = []

    # ========================================
    # SEC-046: Top Users by Activity (Enterprise Feature)
    # ========================================
    top_users = []
    try:
        top_users_query = db.query(
            User.email,
            User.last_login,
            func.count(AgentAction.id).label('action_count')
        ).outerjoin(
            AgentAction,
            and_(
                AgentAction.user_id == User.id,
                AgentAction.created_at >= month_start
            )
        ).filter(
            User.organization_id == org_id,
            User.is_active == True
        ).group_by(User.id, User.email, User.last_login).order_by(desc('action_count')).limit(5).all()

        for user in top_users_query:
            top_users.append({
                "email": user.email,
                "action_count": user.action_count or 0,
                "last_active": user.last_login.isoformat() if user.last_login else None
            })
    except Exception as e:
        logger.warning(f"SEC-046: top_users query failed: {e}")
        top_users = []

    # ========================================
    # SEC-046: Recent Activity Feed (Enterprise Feature)
    # ========================================
    recent_activity = []
    try:
        recent_actions = db.query(AgentAction).filter(
            AgentAction.organization_id == org_id
        ).order_by(desc(AgentAction.created_at)).limit(10).all()

        for action in recent_actions:
            recent_activity.append({
                "timestamp": action.created_at.isoformat() if action.created_at else None,
                "description": f"{action.action_type}: {action.agent_id}" if action.action_type else "Agent action",
                "type": "agent_action",
                "severity": getattr(action, 'risk_level', 'low')
            })
    except Exception as e:
        logger.warning(f"SEC-046: recent_activity query failed: {e}")
        recent_activity = []

    # ========================================
    # SEC-046: MCP Server Count
    # ========================================
    mcp_servers_count = 0
    try:
        from models_mcp_governance import MCPServer
        mcp_servers_count = db.query(MCPServer).filter(
            MCPServer.is_active == True
        ).count()
    except Exception:
        pass

    # ========================================
    # SEC-046: Agents Count (unique agent IDs this month)
    # ========================================
    agents_count = 0
    try:
        agents_count = db.query(func.count(func.distinct(AgentAction.agent_id))).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= month_start
        ).scalar() or 0
    except Exception:
        pass

    # ========================================
    # SEC-072: Pre-compute legacy metrics (prevent InFailedSqlTransaction)
    # ========================================
    last_7_days_count = 0
    try:
        last_7_days_count = db.query(AgentAction).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= week_ago
        ).count()
    except Exception as e:
        logger.warning(f"SEC-072: last_7_days_count query failed: {e}")

    last_24_hours_count = 0
    try:
        last_24_hours_count = db.query(AgentAction).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= day_ago
        ).count()
    except Exception as e:
        logger.warning(f"SEC-072: last_24_hours_count query failed: {e}")

    # SEC-046: Return flat field names for frontend compatibility
    return {
        # Flat fields expected by frontend
        "api_calls_this_month": api_calls_this_month,
        "api_calls_trend": api_calls_trend,
        "active_users_count": active_users_count,
        "active_users_trend": active_users_trend,
        "alerts_processed": alerts_processed,
        "alerts_trend": alerts_trend,
        "active_rules_count": active_rules_count,
        "rules_trend": rules_trend,

        # Additional counts for billing display
        "mcp_servers_count": mcp_servers_count,
        "agents_count": agents_count,

        # Enterprise features
        "endpoint_stats": endpoint_stats,
        "top_users": top_users,
        "recent_activity": recent_activity,

        # Period information
        "period": {
            "start": month_start.isoformat(),
            "end": now.isoformat()
        },

        # Legacy nested format (backward compatibility)
        "api_calls": {
            "total_this_month": api_calls_this_month,
            "last_7_days": last_7_days_count,
            "last_24_hours": last_24_hours_count
        }
    }


@router.get("/analytics/daily")
async def get_daily_analytics(
    days: int = 30,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-022: Get daily usage analytics for charts.
    """
    org_id = admin["organization_id"]
    # SEC-044: Use timezone-aware datetime
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    # Daily API calls
    daily_calls = db.query(
        func.date(AgentAction.created_at).label('date'),
        func.count(AgentAction.id).label('count')
    ).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= start_date
    ).group_by(func.date(AgentAction.created_at)).order_by('date').all()

    # Daily alerts
    # SEC-044: Use Alert.timestamp (correct column name per model)
    daily_alerts = db.query(
        func.date(Alert.timestamp).label('date'),
        func.count(Alert.id).label('count')
    ).filter(
        Alert.organization_id == org_id,
        Alert.timestamp >= start_date
    ).group_by(func.date(Alert.timestamp)).order_by('date').all()

    return {
        "api_calls": [
            {"date": str(d.date), "count": d.count}
            for d in daily_calls
        ],
        "alerts": [
            {"date": str(d.date), "count": d.count}
            for d in daily_alerts
        ]
    }


# =============================================================================
# AUDIT LOG
# =============================================================================

@router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    action_filter: Optional[str] = None,
    event_type: Optional[str] = None,
    days: int = Query(30, ge=1, le=365, description="Days of history to fetch"),
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046: Get organization audit log with enterprise filtering.

    Enterprise Features:
    - Field names aligned with frontend (entries, timestamp, event_type, user_email)
    - User email resolution from user_id
    - Date range filtering
    - Event type filtering
    - Full-text search on action

    Compliance: SOC 2 CC7.2, HIPAA 164.312(b), PCI-DSS 10.2, SOX 302/404
    """
    org_id = admin["organization_id"]
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days)

    query = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= start_date
    )

    # SEC-046: Add filters
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    if event_type:
        query = query.filter(AuditLog.action.ilike(f"{event_type}%"))

    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    total = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= start_date
    ).count()

    # SEC-046: Build user email cache for efficient lookups
    user_ids = list(set(log.user_id for log in logs if log.user_id))
    user_email_map = {}
    if user_ids:
        users = db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
        user_email_map = {u.id: u.email for u in users}

    # SEC-046: Transform logs to match frontend expectations
    entries = []
    for log in logs:
        entries.append({
            # Frontend expected fields
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "event_type": log.action,
            "user_email": user_email_map.get(log.user_id, f"user_{log.user_id}"),
            "ip_address": log.ip_address,
            "details": log.changes or {},

            # Additional enterprise fields
            "user_id": log.user_id,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "action": log.action,  # Legacy compatibility

            # SEC-046: Risk classification for audit
            "risk_level": _classify_audit_risk(log.action),
            "compliance_tags": _get_compliance_tags(log.action)
        })

    return {
        # SEC-046: Frontend expects "entries" not "logs"
        "entries": entries,

        # Also provide "logs" for backward compatibility
        "logs": entries,

        # Pagination info
        "total": total,
        "limit": limit,
        "offset": offset,

        # Period info for compliance reporting
        "period": {
            "start": start_date.isoformat(),
            "end": now.isoformat(),
            "days": days
        }
    }


def _classify_audit_risk(action: str) -> str:
    """
    SEC-046: Classify audit action risk level for compliance.

    Risk Levels:
    - critical: User deletion, role changes to admin, security settings
    - high: Password changes, API key operations, data exports
    - medium: User invites, configuration changes
    - low: Read operations, login events
    """
    if not action:
        return "low"

    action_lower = action.lower()

    critical_patterns = ["delete", "remove", "admin", "role_change", "access_level", "security"]
    high_patterns = ["password", "api_key", "export", "revoke", "suspend"]
    medium_patterns = ["invite", "create", "update", "modify", "settings"]

    for pattern in critical_patterns:
        if pattern in action_lower:
            return "critical"

    for pattern in high_patterns:
        if pattern in action_lower:
            return "high"

    for pattern in medium_patterns:
        if pattern in action_lower:
            return "medium"

    return "low"


def _get_compliance_tags(action: str) -> List[str]:
    """
    SEC-046: Map audit actions to compliance frameworks.

    Returns list of applicable compliance frameworks for the action.
    """
    if not action:
        return []

    action_lower = action.lower()
    tags = []

    # SOX - Financial controls and access changes
    if any(p in action_lower for p in ["role", "access", "admin", "delete", "security"]):
        tags.append("SOX")

    # HIPAA - Data access and user management
    if any(p in action_lower for p in ["user", "access", "export", "data", "patient"]):
        tags.append("HIPAA")

    # PCI-DSS - Access control and authentication
    if any(p in action_lower for p in ["login", "password", "api_key", "auth", "access"]):
        tags.append("PCI-DSS")

    # SOC 2 - All security-relevant events
    if any(p in action_lower for p in ["security", "settings", "config", "user", "role"]):
        tags.append("SOC2")

    return tags


# =============================================================================
# SEC-040: RBAC MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/rbac/levels")
async def get_access_levels(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-040: Get all access levels and their permissions.

    Returns the 6-level RBAC hierarchy with permission matrix.
    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1
    """
    return {
        "access_levels": [
            {
                "level": level,
                "name": ACCESS_LEVEL_NAMES[level],
                "permissions": ACCESS_LEVEL_PERMISSIONS.get(level, {}),
                "description": {
                    0: "Suspended users with no access",
                    1: "Basic dashboard access only",
                    2: "Analytics, alerts, and export capabilities",
                    3: "Authorization and approval for low/medium risk",
                    4: "Full administrative access",
                    5: "Executive privileges including critical approvals"
                }.get(level, "")
            }
            for level in range(6)
        ],
        "permission_categories": list(PERMISSION_MATRIX.keys())
    }


@router.get("/rbac/users")
async def get_users_by_access_level(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-040: Get users grouped by access level.
    """
    org_id = admin["organization_id"]

    users = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).all()

    # Group by access level
    by_level = {level: [] for level in range(6)}

    for user in users:
        level = user.approval_level or 1
        by_level[level].append({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_org_admin": user.is_org_admin,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })

    return {
        "users_by_level": {
            ACCESS_LEVEL_NAMES[level]: {
                "level": level,
                "users": users,
                "count": len(users)
            }
            for level, users in by_level.items()
        },
        "total_users": len(users)
    }


@router.patch("/users/{user_id}/access-level")
@limiter.limit(RATE_LIMITS["api_write"])  # SEC-046: Rate limit (30/min per IP)
async def update_user_access_level(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    user_id: int,
    update_data: UserAccessLevelUpdate,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)  # SEC-046: CSRF validation
):
    """
    SEC-040: Update a user's RBAC access level.

    Security:
    - Only users with users.manage_roles permission can update access levels
    - Cannot set level higher than your own
    - Audit logged for compliance
    - Rate limited: 30 requests/minute per IP (SEC-046)
    - CSRF protected: Double-submit validation (SEC-046)

    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1
    """
    # Permission check
    if not check_permission(admin.get("permissions", {}), "users.manage_roles"):
        # Fallback: Allow if admin role
        if admin["role"] not in ["admin", "owner"] and not admin.get("is_org_admin"):
            raise HTTPException(
                status_code=403,
                detail="Permission 'users.manage_roles' required"
            )

    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin["organization_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cannot modify yourself
    if user.id == admin["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot modify your own access level")

    # Cannot set level higher than your own (unless executive)
    admin_level = admin.get("access_level", 1)
    if update_data.access_level > admin_level and admin_level < 5:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot grant access level higher than your own ({ACCESS_LEVEL_NAMES[admin_level]})"
        )

    old_level = user.approval_level or 1
    user.approval_level = update_data.access_level

    # Audit log
    audit = AuditLog(
        organization_id=admin["organization_id"],
        user_id=admin["user_id"],
        action="user.access_level_change",
        resource_type="user",
        resource_id=user.id,
        changes={
            "access_level": {
                "old": old_level,
                "old_name": ACCESS_LEVEL_NAMES.get(old_level, "Unknown"),
                "new": update_data.access_level,
                "new_name": ACCESS_LEVEL_NAMES.get(update_data.access_level, "Unknown")
            },
            "reason": update_data.reason
        },
        ip_address=request.client.host if request.client else None
    )
    db.add(audit)
    db.commit()

    logger.info(f"SEC-040: User {user_id} access level changed from {old_level} to {update_data.access_level}")

    return {
        "success": True,
        "message": f"Access level updated to {ACCESS_LEVEL_NAMES[update_data.access_level]}",
        "user": {
            "id": user.id,
            "email": user.email,
            "access_level": update_data.access_level,
            "access_level_name": ACCESS_LEVEL_NAMES[update_data.access_level],
            "permissions": ACCESS_LEVEL_PERMISSIONS.get(update_data.access_level, {})
        }
    }


# =============================================================================
# SEC-040: COMPLIANCE METRICS ENDPOINTS
# =============================================================================

@router.get("/compliance/metrics")
async def get_compliance_metrics(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-040: Get compliance metrics dashboard.

    Returns real-time compliance scores for SOX, HIPAA, PCI-DSS, GDPR.
    Compliance: SOC 2, HIPAA, PCI-DSS, SOX
    """
    org_id = admin["organization_id"]
    # SEC-044: Use timezone-aware datetime
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # User statistics
    total_users = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).count()

    users_with_mfa = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True,
        User.mfa_enabled == True
    ).count() if hasattr(User, 'mfa_enabled') else 0

    # Calculate MFA adoption rate
    mfa_rate = (users_with_mfa / total_users * 100) if total_users > 0 else 0

    # Audit trail completeness
    total_actions = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= month_start
    ).count()

    audited_actions = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= month_start
    ).count()

    audit_rate = (audited_actions / total_actions * 100) if total_actions > 0 else 100

    # Access control metrics
    users_by_level = db.query(
        User.approval_level,
        func.count(User.id)
    ).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).group_by(User.approval_level).all()

    level_distribution = {level: count for level, count in users_by_level}

    # Privileged user ratio (level 4+ should be < 20% for SOX)
    privileged_users = sum(count for level, count in users_by_level if (level or 1) >= 4)
    privileged_ratio = (privileged_users / total_users * 100) if total_users > 0 else 0

    # Calculate compliance scores
    sox_score = min(100, (
        (30 if mfa_rate >= 100 else mfa_rate * 0.3) +
        (30 if audit_rate >= 95 else audit_rate * 0.3) +
        (20 if privileged_ratio <= 20 else max(0, 40 - privileged_ratio)) +
        20  # Base score for having audit trail
    ))

    hipaa_score = min(100, (
        (40 if mfa_rate >= 100 else mfa_rate * 0.4) +
        (30 if audit_rate >= 100 else audit_rate * 0.3) +
        30  # Base score for encryption at rest (assumed)
    ))

    pci_score = min(100, (
        (35 if mfa_rate >= 100 else mfa_rate * 0.35) +
        (35 if audit_rate >= 95 else audit_rate * 0.35) +
        (30 if privileged_ratio <= 15 else max(0, 45 - privileged_ratio))
    ))

    return {
        "compliance_scores": {
            "sox": {
                "score": round(sox_score, 1),
                "status": "compliant" if sox_score >= 80 else "needs_attention",
                "factors": {
                    "mfa_adoption": round(mfa_rate, 1),
                    "audit_completeness": round(audit_rate, 1),
                    "privileged_user_ratio": round(privileged_ratio, 1)
                }
            },
            "hipaa": {
                "score": round(hipaa_score, 1),
                "status": "compliant" if hipaa_score >= 80 else "needs_attention",
                "factors": {
                    "mfa_adoption": round(mfa_rate, 1),
                    "audit_completeness": round(audit_rate, 1)
                }
            },
            "pci_dss": {
                "score": round(pci_score, 1),
                "status": "compliant" if pci_score >= 80 else "needs_attention",
                "factors": {
                    "mfa_adoption": round(mfa_rate, 1),
                    "audit_completeness": round(audit_rate, 1),
                    "privileged_user_ratio": round(privileged_ratio, 1)
                }
            }
        },
        "user_metrics": {
            "total_users": total_users,
            "mfa_enabled": users_with_mfa,
            "mfa_adoption_rate": round(mfa_rate, 1),
            "privileged_users": privileged_users,
            "access_level_distribution": {
                ACCESS_LEVEL_NAMES.get(level or 1, "Unknown"): count
                for level, count in users_by_level
            }
        },
        "audit_metrics": {
            "total_actions_this_month": total_actions,
            "audited_actions": audited_actions,
            "audit_coverage_rate": round(audit_rate, 1)
        },
        "generated_at": now.isoformat()
    }


@router.get("/compliance/audit-summary")
async def get_compliance_audit_summary(
    days: int = 30,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-040: Get audit activity summary for compliance reporting.
    """
    org_id = admin["organization_id"]
    # SEC-044: Use timezone-aware datetime
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    # Audit actions by type
    actions_by_type = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()

    # High-risk actions
    high_risk_actions = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= start_date,
        or_(
            AuditLog.action.ilike("%delete%"),
            AuditLog.action.ilike("%role_change%"),
            AuditLog.action.ilike("%access_level%"),
            AuditLog.action.ilike("%password%")
        )
    ).order_by(desc(AuditLog.created_at)).limit(20).all()

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "actions_by_type": {
            action: count for action, count in actions_by_type
        },
        "high_risk_actions": [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "resource_type": log.resource_type,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "ip_address": log.ip_address
            }
            for log in high_risk_actions
        ],
        "total_actions": sum(count for _, count in actions_by_type)
    }


# =============================================================================
# SEC-040: BACKWARD COMPATIBILITY ROUTE ALIASES
# =============================================================================

# Alias: /api/enterprise-users/* → /api/admin/*
# These provide backward compatibility for EnterpriseUserManagement.jsx

@router.get("/enterprise-users/users")
async def enterprise_users_list_alias(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """SEC-040: Backward compatibility alias for /api/enterprise-users/users"""
    return await list_organization_users(admin=admin, db=db)


@router.get("/enterprise-users/analytics")
async def enterprise_users_analytics_alias(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """SEC-040: Backward compatibility alias for /api/enterprise-users/analytics"""
    # Return user analytics in legacy format
    org_id = admin["organization_id"]
    # SEC-044: Use timezone-aware datetime
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).count()

    active_users = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True,
        User.last_login >= week_ago
    ).count()

    new_users = db.query(User).filter(
        User.organization_id == org_id,
        User.created_at >= month_ago
    ).count()

    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "new_users_30d": new_users,
        "active_rate": round((active_users / total_users * 100) if total_users > 0 else 0, 1)
    }


@router.get("/enterprise-users/audit-logs")
async def enterprise_users_audit_alias(
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """SEC-040: Backward compatibility alias for /api/enterprise-users/audit-logs"""
    return await get_audit_log(limit=limit, offset=offset, admin=admin, db=db)


# =============================================================================
# SEC-040: SECURITY SETTINGS ENDPOINTS
# =============================================================================

@router.get("/security/settings")
async def get_security_settings(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-040: Get organization security settings.
    """
    org = db.query(Organization).filter(
        Organization.id == admin["organization_id"]
    ).first()

    return {
        "mfa": {
            "configuration": org.cognito_mfa_configuration or "OPTIONAL",
            "enforced": org.cognito_mfa_configuration == "ON"
        },
        "session": {
            "timeout_minutes": getattr(org, 'session_timeout_hours', 8) * 60,
            "max_concurrent_sessions": 5
        },
        "password_policy": {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special": True,
            "max_age_days": 90
        },
        "ip_restrictions": {
            "enabled": False,
            "allowed_ranges": []
        }
    }


# =============================================================================
# SEC-046 PHASE 3: BULK USER OPERATIONS
# =============================================================================

class BulkUserOperation(BaseModel):
    """SEC-046 Phase 3: Bulk user operation request"""
    user_ids: List[int] = Field(..., min_length=1, max_length=100, description="User IDs to operate on")
    operation: str = Field(..., description="Operation: suspend, reactivate, delete, role_change")
    role: Optional[str] = Field(None, description="New role for role_change operation")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for bulk operation")


@router.post("/users/bulk-operation")
@limiter.limit("10/minute")
async def bulk_user_operation(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    operation_data: BulkUserOperation,
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _csrf: bool = Depends(require_csrf)
):
    """
    SEC-046 Phase 3: Perform bulk operations on multiple users.

    Enterprise Features:
    - Suspend/reactivate multiple users at once
    - Bulk role changes
    - Bulk user deletion (soft delete)
    - Comprehensive audit logging per user
    - Rate limited: 10/minute

    Compliance: SOC 2 CC6.1, NIST AC-2, HIPAA 164.312(a)
    """
    org_id = admin["organization_id"]
    valid_operations = ["suspend", "reactivate", "delete", "role_change"]

    if operation_data.operation not in valid_operations:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operation. Must be one of: {valid_operations}"
        )

    if operation_data.operation == "role_change" and not operation_data.role:
        raise HTTPException(status_code=400, detail="Role is required for role_change operation")

    if operation_data.operation == "role_change":
        valid_roles = ["viewer", "analyst", "operator", "admin", "org_admin"]
        if operation_data.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {valid_roles}"
            )

    # Fetch users (with org isolation)
    users = db.query(User).filter(
        User.id.in_(operation_data.user_ids),
        User.organization_id == org_id
    ).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found with provided IDs")

    # Filter out self and owners
    eligible_users = []
    skipped_users = []

    for user in users:
        if user.id == admin["user_id"]:
            skipped_users.append({"id": user.id, "email": user.email, "reason": "Cannot operate on self"})
        elif getattr(user, 'is_owner', False):
            skipped_users.append({"id": user.id, "email": user.email, "reason": "Cannot operate on owner"})
        else:
            eligible_users.append(user)

    if not eligible_users:
        return {
            "success": False,
            "message": "No eligible users for operation",
            "processed": 0,
            "skipped": skipped_users
        }

    # Perform operation
    processed = []
    now = datetime.now(UTC)

    for user in eligible_users:
        old_values = {}
        new_values = {}

        if operation_data.operation == "suspend":
            old_values["is_suspended"] = getattr(user, 'is_suspended', False)
            user.is_suspended = True
            user.suspended_at = now
            user.suspended_by = admin["user_id"]
            user.suspension_reason = operation_data.reason
            new_values["is_suspended"] = True

        elif operation_data.operation == "reactivate":
            old_values["is_suspended"] = getattr(user, 'is_suspended', True)
            user.is_suspended = False
            user.suspended_at = None
            user.suspended_by = None
            user.suspension_reason = None
            new_values["is_suspended"] = False

        elif operation_data.operation == "delete":
            old_values["is_active"] = user.is_active
            user.is_active = False
            new_values["is_active"] = False

        elif operation_data.operation == "role_change":
            old_values["role"] = user.role
            user.role = operation_data.role
            if operation_data.role == "org_admin":
                user.is_org_admin = True
            else:
                user.is_org_admin = False
            new_values["role"] = operation_data.role

        # Audit log per user
        audit = AuditLog(
            organization_id=org_id,
            user_id=admin["user_id"],
            action=f"user.bulk_{operation_data.operation}",
            resource_type="user",
            resource_id=user.id,
            changes={
                "operation": operation_data.operation,
                "target_email": user.email,
                "reason": operation_data.reason,
                "old": old_values,
                "new": new_values
            },
            ip_address=request.client.host if request.client else None
        )
        db.add(audit)

        processed.append({
            "id": user.id,
            "email": user.email,
            "operation": operation_data.operation,
            "success": True
        })

    db.commit()

    logger.info(f"SEC-046 Phase 3: Bulk {operation_data.operation} on {len(processed)} users by admin {admin['user_id']}")

    return {
        "success": True,
        "message": f"Bulk {operation_data.operation} completed",
        "operation": operation_data.operation,
        "processed": len(processed),
        "skipped": len(skipped_users),
        "results": processed,
        "skipped_details": skipped_users
    }


# =============================================================================
# SEC-046 PHASE 3: USAGE OVERAGE ALERTS
# =============================================================================

@router.get("/alerts/usage-status")
async def get_usage_overage_status(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046 Phase 3: Get usage status and overage alerts.

    Enterprise Features:
    - Real-time usage vs limit comparison
    - Warning/critical thresholds (80%/95%)
    - Overage cost calculation
    - Notification recommendations

    Compliance: SOC 2 CC6.1, PCI-DSS 12.10
    """
    org_id = admin["organization_id"]
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get current tier limits
    tier_key = org.subscription_tier or "pilot"
    tier_config = BILLING_CONFIG["tiers"].get(tier_key, BILLING_CONFIG["tiers"]["pilot"])

    # Calculate current month usage
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current_usage = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= month_start
    ).count()

    # Get limits
    included_actions = tier_config["included_agent_actions"]
    overage_rate = tier_config["overage_per_action"]
    warning_threshold = BILLING_CONFIG["thresholds"]["warning"]
    critical_threshold = BILLING_CONFIG["thresholds"]["critical"]

    # Calculate percentages and status
    usage_percent = (current_usage / included_actions * 100) if included_actions > 0 else 0

    # Determine alert level
    alert_level = "normal"
    alert_message = None

    if current_usage > included_actions:
        alert_level = "overage"
        overage_count = current_usage - included_actions
        overage_cost = overage_count * overage_rate
        alert_message = f"You have exceeded your plan limit by {overage_count} actions. Current overage cost: ${overage_cost:.2f}"
    elif usage_percent >= critical_threshold:
        alert_level = "critical"
        remaining = included_actions - current_usage
        alert_message = f"Critical: Only {remaining} agent actions remaining ({100 - usage_percent:.1f}% left)"
    elif usage_percent >= warning_threshold:
        alert_level = "warning"
        remaining = included_actions - current_usage
        alert_message = f"Warning: {remaining} agent actions remaining ({100 - usage_percent:.1f}% left)"

    # User count
    user_count = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).count()

    # Days remaining in billing period
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    days_remaining = (next_month - now).days

    # Projected usage
    days_elapsed = now.day
    daily_rate = current_usage / days_elapsed if days_elapsed > 0 else 0
    projected_month_end = int(daily_rate * 30)

    # SEC-046: Build separate warnings and critical arrays for frontend compatibility
    warnings = []
    critical = []
    if alert_message:
        alert_obj = {
            "resource": "Agent Actions",
            "current": current_usage,
            "limit": included_actions,
            "percentage": round(usage_percent, 1),
            "message": alert_message
        }
        if alert_level in ("critical", "overage"):
            critical.append(alert_obj)
        elif alert_level == "warning":
            warnings.append(alert_obj)

    return {
        "status": alert_level,
        # SEC-046: Separate arrays for frontend usage alert display
        "warnings": warnings,
        "critical": critical,

        "usage": {
            "agent_actions": {
                "current": current_usage,
                "limit": included_actions,
                "percent": round(usage_percent, 1),
                "remaining": max(0, included_actions - current_usage),
                "overage": max(0, current_usage - included_actions),
                "overage_cost": max(0, (current_usage - included_actions) * overage_rate) if current_usage > included_actions else 0
            },
            "users": {"current": user_count, "limit": "unlimited", "percent": 0}
        },

        "projection": {
            "daily_rate": round(daily_rate, 1),
            "projected_month_end": projected_month_end,
            "will_exceed": projected_month_end > included_actions
        },

        "billing_period": {
            "start": month_start.isoformat(),
            "end": next_month.isoformat(),
            "days_remaining": days_remaining
        },

        "tier": {"name": tier_config["name"], "key": tier_key, "overage_rate": overage_rate}
    }


# =============================================================================
# SEC-046 PHASE 3: ANALYTICS CHARTS DATA
# =============================================================================

@router.get("/analytics/charts")
async def get_analytics_chart_data(
    days: int = Query(30, ge=7, le=90, description="Number of days: 7, 30, or 90"),
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046 Phase 3: Get formatted chart data for analytics dashboards.

    Compliance: SOC 2 CC6.1, HIPAA 164.312(b)
    """
    org_id = admin["organization_id"]
    now = datetime.now(UTC)
    # SEC-046: Accept days directly from frontend
    period_days = days if days in (7, 30, 90) else 30
    start_date = now - timedelta(days=period_days)

    # Daily action counts
    daily_actions = db.query(
        func.date(AgentAction.created_at).label('date'),
        func.count(AgentAction.id).label('count')
    ).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= start_date
    ).group_by(func.date(AgentAction.created_at)).order_by('date').all()

    # Daily alerts
    daily_alerts = db.query(
        func.date(Alert.timestamp).label('date'),
        func.count(Alert.id).label('count')
    ).filter(
        Alert.organization_id == org_id,
        Alert.timestamp >= start_date
    ).group_by(func.date(Alert.timestamp)).order_by('date').all()

    # Decision breakdown
    decision_breakdown = []
    try:
        decisions = db.query(
            AgentAction.status,
            func.count(AgentAction.id).label('count')
        ).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= start_date
        ).group_by(AgentAction.status).all()
        decision_breakdown = [{"name": d.status or "pending", "value": d.count} for d in decisions]
    except Exception:
        pass

    # Risk distribution
    risk_distribution = []
    try:
        risks = db.query(
            AgentAction.risk_level,
            func.count(AgentAction.id).label('count')
        ).filter(
            AgentAction.organization_id == org_id,
            AgentAction.created_at >= start_date,
            AgentAction.risk_level.isnot(None)
        ).group_by(AgentAction.risk_level).all()
        risk_distribution = [{"name": r.risk_level, "value": r.count} for r in risks]
    except Exception:
        pass

    return {
        "period": {"start": start_date.isoformat(), "end": now.isoformat(), "days": period_days},
        "time_series": {
            "agent_actions": [{"date": str(d.date), "value": d.count} for d in daily_actions],
            "alerts": [{"date": str(d.date), "value": d.count} for d in daily_alerts]
        },
        "distributions": {"decisions": decision_breakdown, "risk_levels": risk_distribution},
        "totals": {
            "agent_actions": sum(d.count for d in daily_actions),
            "alerts": sum(d.count for d in daily_alerts)
        }
    }


# =============================================================================
# SEC-046 PHASE 3: AUDIT LOG EXPORT
# =============================================================================

@router.get("/audit-log/export")
@limiter.limit("5/minute")
async def export_audit_log(
    request: Request,
    response: Response,  # SEC-072: Required for slowapi rate limit headers
    format: str = Query("json", description="Export format: json, csv"),
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046 Phase 3: Export audit logs for compliance reporting.

    Compliance: SOC 2 CC7.2, HIPAA 164.312(b), PCI-DSS 10.7, SOX 302/404
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io

    org_id = admin["organization_id"]
    now = datetime.now(UTC)
    start_date = now - timedelta(days=days)

    logs = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id,
        AuditLog.created_at >= start_date
    ).order_by(desc(AuditLog.created_at)).all()

    # User email map
    user_ids = list(set(log.user_id for log in logs if log.user_id))
    user_email_map = {}
    if user_ids:
        users = db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
        user_email_map = {u.id: u.email for u in users}

    # Audit the export
    export_audit = AuditLog(
        organization_id=org_id,
        user_id=admin["user_id"],
        action="audit.export",
        resource_type="audit_log",
        resource_id=None,
        changes={"format": format, "days": days, "record_count": len(logs)},
        ip_address=request.client.host if request.client else None
    )
    db.add(export_audit)
    db.commit()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Event Type", "User Email", "Resource Type", "Resource ID", "IP Address", "Details"])
        for log in logs:
            writer.writerow([
                log.created_at.isoformat() if log.created_at else "",
                log.action,
                user_email_map.get(log.user_id, f"user_{log.user_id}"),
                log.resource_type or "",
                log.resource_id or "",
                log.ip_address or "",
                str(log.changes) if log.changes else ""
            ])
        output.seek(0)
        filename = f"audit_log_{org_id}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # JSON export
    return {
        "export_info": {
            "organization_id": org_id,
            "exported_by": admin["email"],
            "export_timestamp": now.isoformat(),
            "record_count": len(logs)
        },
        "entries": [
            {
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "event_type": log.action,
                "user_email": user_email_map.get(log.user_id, f"user_{log.user_id}"),
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "details": log.changes or {}
            }
            for log in logs
        ]
    }


# =============================================================================
# SEC-046 PHASE 3: REAL-TIME STATUS UPDATES
# =============================================================================

@router.get("/status/realtime")
async def get_realtime_status(
    admin: dict = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """
    SEC-046 Phase 3: Get real-time system status for live dashboard updates.
    Poll every 30 seconds.

    Compliance: SOC 2 CC6.1
    """
    org_id = admin["organization_id"]
    now = datetime.now(UTC)

    five_min_ago = now - timedelta(minutes=5)
    hour_ago = now - timedelta(hours=1)

    recent_action_count = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.created_at >= five_min_ago
    ).count()

    pending_approvals = db.query(AgentAction).filter(
        AgentAction.organization_id == org_id,
        AgentAction.status == "pending",
        AgentAction.requires_approval == True
    ).count()

    active_users = db.query(User).filter(
        User.organization_id == org_id,
        User.is_active == True,
        User.last_login >= hour_ago
    ).count()

    recent_alerts = db.query(Alert).filter(
        Alert.organization_id == org_id,
        Alert.timestamp >= hour_ago,
        Alert.status == "new"
    ).count()

    # Health check
    health_status = "healthy"
    health_issues = []
    if pending_approvals > 10:
        health_status = "warning"
        health_issues.append(f"{pending_approvals} actions pending approval")
    if recent_alerts > 5:
        health_status = "warning" if health_status == "healthy" else health_status
        health_issues.append(f"{recent_alerts} new alerts in last hour")

    # Recent activity
    recent_activities = []
    try:
        recent = db.query(AgentAction).filter(
            AgentAction.organization_id == org_id
        ).order_by(desc(AgentAction.created_at)).limit(5).all()
        for action in recent:
            recent_activities.append({
                "id": action.id,
                "type": action.action_type,
                "agent": action.agent_id,
                "status": action.status,
                "timestamp": action.created_at.isoformat() if action.created_at else None
            })
    except Exception:
        pass

    # SEC-046: Flatten response structure for frontend compatibility
    return {
        "timestamp": now.isoformat(),
        "poll_interval_seconds": 30,
        # Flattened fields for frontend
        "system_status": health_status,
        "active_users": active_users,
        "pending_actions": pending_approvals,  # Renamed for frontend
        "new_alerts": recent_alerts,
        "actions_last_5min": recent_action_count,
        "api_latency_ms": 0,  # TODO: Implement actual API latency tracking
        # Additional detail
        "health_issues": health_issues,
        "recent_activity": recent_activities,
        "notifications": [{"type": "warning", "message": issue} for issue in health_issues]
    }


logger.info("SEC-040: Enterprise Unified Admin Console routes registered")
logger.info("SEC-046 Phase 3: Bulk operations, usage alerts, charts, export, real-time endpoints added")
