"""
Organization Admin Routes - Enterprise User Management via AWS Cognito

This module provides organization administrators with secure user management
capabilities including:
- Inviting new users via AWS Cognito
- Listing organization users
- Removing users (with Cognito integration)
- Updating user roles and permissions
- Enforcing subscription tier limits

Security Features:
- Organization admin permission enforcement
- Input validation and sanitization
- Subscription tier limit enforcement
- Complete audit logging
- PostgreSQL RLS enforced multi-tenancy
- Token revocation on role changes

Engineer: Donald King (OW-AI Enterprise)
Created: 2025-11-20
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime
import bleach
import boto3
from botocore.exceptions import ClientError

from database import get_db
from models import User, Organization, CognitoToken, AuthAuditLog
from dependencies_cognito import require_org_admin, log_auth_event
from config import (
    COGNITO_USER_POOL_ID,
    COGNITO_APP_CLIENT_ID,
    AWS_REGION
)

router = APIRouter(
    prefix="/organizations",
    tags=["Organization Admin"]
)

# Initialize AWS Cognito client
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)


# ============================================================================
# PYDANTIC SCHEMAS - Enterprise Input Validation
# ============================================================================

class InviteUserRequest(BaseModel):
    """
    User invitation request with enterprise validation.

    Security:
    - Email validation via EmailStr
    - Role whitelist validation
    - XSS protection via bleach sanitization
    - Length limits on text fields
    """
    email: EmailStr
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_org_admin: bool = False

    @validator("role")
    def validate_role(cls, v):
        """Validate role against whitelist"""
        allowed_roles = ['user', 'admin', 'manager', 'viewer']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

    @validator("first_name", "last_name")
    def sanitize_name(cls, v):
        """Sanitize names to prevent XSS"""
        if v:
            # Remove all HTML tags, strip whitespace
            sanitized = bleach.clean(v, tags=[], strip=True).strip()
            if len(sanitized) > 100:
                raise ValueError("Name must be less than 100 characters")
            return sanitized
        return v

    @validator("is_org_admin")
    def validate_admin_flag(cls, v, values):
        """Only admins can create other admins"""
        if v and values.get('role') not in ['admin']:
            raise ValueError("Only admin role can have is_org_admin=true")
        return v


class UpdateUserRoleRequest(BaseModel):
    """User role update request"""
    role: str
    is_org_admin: Optional[bool] = None

    @validator("role")
    def validate_role(cls, v):
        allowed_roles = ['user', 'admin', 'manager', 'viewer']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    role: str
    is_org_admin: bool
    cognito_user_id: Optional[str]
    last_login: Optional[datetime]
    login_attempts: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# HELPER FUNCTIONS - Cognito Integration
# ============================================================================

async def check_subscription_user_limit(org: Organization, db: Session) -> bool:
    """
    Check if organization has reached user limit for their subscription tier.

    Returns:
        True if under limit, False if at/over limit
    """
    current_user_count = db.query(User).filter(
        User.organization_id == org.id,
        User.cognito_user_id.isnot(None)  # Only count active Cognito users
    ).count()

    # Subscription tier limits
    tier_limits = {
        'trial': 5,
        'startup': 10,
        'business': 50,
        'enterprise': 1000
    }

    limit = tier_limits.get(org.subscription_tier, 5)
    return current_user_count < limit


async def create_cognito_user(
    email: str,
    organization_id: int,
    organization_slug: str,
    role: str,
    is_org_admin: bool,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> str:
    """
    Create user in AWS Cognito with custom attributes.

    Args:
        email: User email (also used as username)
        organization_id: Organization ID
        organization_slug: Organization slug
        role: User role
        is_org_admin: Whether user is org admin
        first_name: Optional first name
        last_name: Optional last name

    Returns:
        Cognito user ID (sub)

    Raises:
        HTTPException: If Cognito user creation fails
    """
    try:
        # Prepare user attributes
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'email_verified', 'Value': 'true'},
            {'Name': 'custom:organization_id', 'Value': str(organization_id)},
            {'Name': 'custom:organization_slug', 'Value': organization_slug},
            {'Name': 'custom:role', 'Value': role},
            {'Name': 'custom:is_org_admin', 'Value': 'true' if is_org_admin else 'false'}
        ]

        if first_name:
            user_attributes.append({'Name': 'given_name', 'Value': first_name})
        if last_name:
            user_attributes.append({'Name': 'family_name', 'Value': last_name})

        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=user_attributes,
            DesiredDeliveryMediums=['EMAIL'],
            MessageAction='SUPPRESS'  # We'll send custom invitation email
        )

        # Extract Cognito user ID from response
        cognito_user_id = None
        for attr in response['User']['Attributes']:
            if attr['Name'] == 'sub':
                cognito_user_id = attr['Value']
                break

        if not cognito_user_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract Cognito user ID"
            )

        return cognito_user_id

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            raise HTTPException(
                status_code=400,
                detail=f"User with email {email} already exists"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Cognito user: {str(e)}"
            )


async def disable_cognito_user(cognito_user_id: str):
    """
    Disable user in AWS Cognito.

    Args:
        cognito_user_id: Cognito user ID (sub)
    """
    try:
        cognito_client.admin_disable_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=cognito_user_id
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable Cognito user: {str(e)}"
        )


async def update_cognito_user_attributes(
    cognito_user_id: str,
    role: str,
    is_org_admin: bool
):
    """
    Update user custom attributes in AWS Cognito.

    Args:
        cognito_user_id: Cognito user ID
        role: New role
        is_org_admin: New admin status
    """
    try:
        cognito_client.admin_update_user_attributes(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=cognito_user_id,
            UserAttributes=[
                {'Name': 'custom:role', 'Value': role},
                {'Name': 'custom:is_org_admin', 'Value': 'true' if is_org_admin else 'false'}
            ]
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update Cognito user: {str(e)}"
        )


async def revoke_all_user_tokens(user_id: int, reason: str, db: Session):
    """
    Revoke all tokens for a user (forces re-login).

    Args:
        user_id: Local database user ID
        reason: Revocation reason for audit
        db: Database session
    """
    tokens = db.query(CognitoToken).filter(
        CognitoToken.user_id == user_id,
        CognitoToken.is_revoked == False
    ).all()

    now = datetime.now()
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = now
        token.revocation_reason = reason

    db.commit()


# ============================================================================
# ORGANIZATION ADMIN ROUTES
# ============================================================================

@router.post("/{org_id}/users", response_model=UserResponse)
async def invite_user(
    org_id: int,
    request: InviteUserRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Invite new user to organization via AWS Cognito.

    Security:
    - Requires organization admin permissions
    - Validates current user is admin of THIS organization
    - Enforces subscription tier user limits
    - Input validation via Pydantic
    - Creates user in Cognito with custom attributes
    - Complete audit logging

    Flow:
    1. Validate org admin permission
    2. Check subscription user limit
    3. Create user in AWS Cognito
    4. Create user in local database
    5. Log invitation event
    6. Return user details

    Args:
        org_id: Organization ID
        request: User invitation details
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created user details
    """
    # Validate current user is admin of THIS organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="You can only invite users to your own organization"
        )

    # Get organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check subscription user limit
    if not await check_subscription_user_limit(org, db):
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached for {org.subscription_tier} tier. Please upgrade your subscription."
        )

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.email == request.email.lower(),
        User.organization_id == org_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists in this organization"
        )

    # Create user in AWS Cognito
    cognito_user_id = await create_cognito_user(
        email=request.email.lower(),
        organization_id=org.id,
        organization_slug=org.slug,
        role=request.role,
        is_org_admin=request.is_org_admin,
        first_name=request.first_name,
        last_name=request.last_name
    )

    # Create user in local database
    new_user = User(
        email=request.email.lower(),
        cognito_user_id=cognito_user_id,
        organization_id=org.id,
        role=request.role,
        is_org_admin=request.is_org_admin,
        login_attempts=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log invitation event
    log_auth_event(
        event_type="user_invited",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=org.id,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "invited_user_email": request.email,
            "invited_user_role": request.role,
            "invited_user_id": new_user.id
        },
        db=db
    )

    return new_user


@router.get("/{org_id}/users", response_model=List[UserResponse])
async def list_organization_users(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    List all users in organization.

    Security:
    - Requires organization admin permissions
    - PostgreSQL RLS enforces multi-tenancy isolation
    - Only returns users from current organization

    Args:
        org_id: Organization ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of users in organization
    """
    # Validate current user is admin of THIS organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view users from your own organization"
        )

    # Query users (RLS automatically filters by organization_id)
    users = db.query(User).filter(
        User.organization_id == org_id,
        User.cognito_user_id.isnot(None)  # Only active Cognito users
    ).order_by(User.created_at.desc()).all()

    return users


@router.delete("/{org_id}/users/{user_id}")
async def remove_user(
    org_id: int,
    user_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Remove user from organization.

    Security:
    - Requires organization admin permissions
    - Prevents self-removal
    - Disables user in Cognito
    - Revokes all user tokens
    - Complete audit logging

    Flow:
    1. Validate permissions
    2. Prevent self-removal
    3. Disable user in Cognito
    4. Revoke all tokens
    5. Mark user as inactive in database
    6. Log removal event

    Args:
        org_id: Organization ID
        user_id: User ID to remove
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # Validate current user is admin of THIS organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="You can only remove users from your own organization"
        )

    # Get user to remove
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == org_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-removal
    if user.id == current_user.get("user_id"):
        raise HTTPException(
            status_code=400,
            detail="You cannot remove yourself. Another admin must remove you."
        )

    # Disable user in AWS Cognito
    if user.cognito_user_id:
        await disable_cognito_user(user.cognito_user_id)

    # Revoke all user tokens (force logout)
    await revoke_all_user_tokens(
        user_id=user.id,
        reason=f"User removed by admin {current_user.get('email')}",
        db=db
    )

    # Mark user as inactive (soft delete)
    user.cognito_user_id = None  # Unlink from Cognito
    user.role = 'disabled'
    db.commit()

    # Log removal event
    log_auth_event(
        event_type="user_removed",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=org_id,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "removed_user_email": user.email,
            "removed_user_id": user.id
        },
        db=db
    )

    return {"message": f"User {user.email} removed successfully"}


@router.patch("/{org_id}/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    org_id: int,
    user_id: int,
    request: UpdateUserRoleRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Update user role and permissions.

    Security:
    - Requires organization admin permissions
    - Prevents self-demotion from admin
    - Updates role in Cognito custom attributes
    - Revokes existing tokens (forces re-login with new role)
    - Complete audit logging

    Flow:
    1. Validate permissions
    2. Prevent self-demotion
    3. Update role in Cognito
    4. Update role in database
    5. Revoke all tokens (force re-login)
    6. Log role change

    Args:
        org_id: Organization ID
        user_id: User ID to update
        request: New role details
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user details
    """
    # Validate current user is admin of THIS organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update users in your own organization"
        )

    # Get user to update
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == org_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-demotion from admin
    if user.id == current_user.get("user_id"):
        if request.is_org_admin == False or request.role not in ['admin']:
            raise HTTPException(
                status_code=400,
                detail="You cannot remove your own admin permissions. Another admin must do this."
            )

    # Update role in AWS Cognito
    if user.cognito_user_id:
        is_admin = request.is_org_admin if request.is_org_admin is not None else user.is_org_admin
        await update_cognito_user_attributes(
            cognito_user_id=user.cognito_user_id,
            role=request.role,
            is_org_admin=is_admin
        )

    # Update role in database
    old_role = user.role
    old_admin_status = user.is_org_admin
    user.role = request.role
    if request.is_org_admin is not None:
        user.is_org_admin = request.is_org_admin
    db.commit()
    db.refresh(user)

    # Revoke all existing tokens (force re-login with new role)
    await revoke_all_user_tokens(
        user_id=user.id,
        reason=f"Role changed from {old_role} to {request.role}",
        db=db
    )

    # Log role change
    log_auth_event(
        event_type="user_role_updated",
        success=True,
        user_id=current_user.get("user_id"),
        cognito_user_id=current_user.get("cognito_user_id"),
        organization_id=org_id,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
        metadata={
            "updated_user_email": user.email,
            "updated_user_id": user.id,
            "old_role": old_role,
            "new_role": request.role,
            "old_admin_status": old_admin_status,
            "new_admin_status": user.is_org_admin
        },
        db=db
    )

    return user


@router.get("/{org_id}/subscription-info")
async def get_subscription_info(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Get organization subscription information including user limits.

    Args:
        org_id: Organization ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Subscription details and usage
    """
    # Validate current user is admin of THIS organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own organization's subscription"
        )

    # Get organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Count active users
    active_users = db.query(User).filter(
        User.organization_id == org_id,
        User.cognito_user_id.isnot(None)
    ).count()

    # Subscription tier limits
    tier_limits = {
        'trial': 5,
        'startup': 10,
        'business': 50,
        'enterprise': 1000
    }

    limit = tier_limits.get(org.subscription_tier, 5)

    return {
        "organization_id": org.id,
        "organization_name": org.name,
        "subscription_tier": org.subscription_tier,
        "subscription_status": org.subscription_status,
        "user_limit": limit,
        "current_users": active_users,
        "available_slots": max(0, limit - active_users),
        "usage_percentage": round((active_users / limit) * 100, 2)
    }


# ============================================================================
# ORGANIZATION ADMIN ROUTES - Auto-detect org from JWT token (Enterprise UX)
# ============================================================================

@router.post("/users", response_model=UserResponse)
async def invite_user_auto_org(
    request: InviteUserRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Invite new user to organization (auto-detect org from JWT token).

    This is the enterprise-grade UX version that extracts organization_id
    from the JWT token custom claims, eliminating the need for clients to
    pass org_id in the URL path.

    Security:
    - Organization ID extracted from validated JWT token
    - All security validations same as /{org_id}/users endpoint
    - Complete audit logging

    Args:
        request: User invitation details
        db: Database session
        current_user: Current authenticated user (JWT validated)

    Returns:
        Created user details
    """
    # Extract organization ID from JWT token
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization ID not found in authentication token"
        )

    # Delegate to existing endpoint (reuse all security logic)
    return await invite_user(org_id, request, req, db, current_user)


@router.get("/users", response_model=List[UserResponse])
async def list_organization_users_auto_org(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    List all users in organization (auto-detect org from JWT token).

    Enterprise-grade UX: Organization ID extracted from JWT token.

    Security:
    - Organization ID extracted from validated JWT token
    - PostgreSQL RLS enforces multi-tenancy isolation
    - Only returns users from current organization

    Args:
        db: Database session
        current_user: Current authenticated user (JWT validated)

    Returns:
        List of users in organization
    """
    # Extract organization ID from JWT token
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization ID not found in authentication token"
        )

    # Delegate to existing endpoint
    return await list_organization_users(org_id, db, current_user)


@router.delete("/users/{user_id}")
async def remove_user_auto_org(
    user_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Remove user from organization (auto-detect org from JWT token).

    Enterprise-grade UX: Organization ID extracted from JWT token.

    Security:
    - Organization ID extracted from validated JWT token
    - All security validations same as /{org_id}/users/{user_id} endpoint
    - Complete audit logging

    Args:
        user_id: User ID to remove
        db: Database session
        current_user: Current authenticated user (JWT validated)

    Returns:
        Success message
    """
    # Extract organization ID from JWT token
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization ID not found in authentication token"
        )

    # Delegate to existing endpoint
    return await remove_user(org_id, user_id, req, db, current_user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role_auto_org(
    user_id: int,
    request: UpdateUserRoleRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Update user role and permissions (auto-detect org from JWT token).

    Enterprise-grade UX: Organization ID extracted from JWT token.

    Security:
    - Organization ID extracted from validated JWT token
    - All security validations same as /{org_id}/users/{user_id}/role endpoint
    - Complete audit logging

    Args:
        user_id: User ID to update
        request: New role details
        db: Database session
        current_user: Current authenticated user (JWT validated)

    Returns:
        Updated user details
    """
    # Extract organization ID from JWT token
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization ID not found in authentication token"
        )

    # Delegate to existing endpoint
    return await update_user_role(org_id, user_id, request, req, db, current_user)


@router.get("/subscription-info")
async def get_subscription_info_auto_org(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Get organization subscription information (auto-detect org from JWT token).

    Enterprise-grade UX: Organization ID extracted from JWT token.

    Args:
        db: Database session
        current_user: Current authenticated user (JWT validated)

    Returns:
        Subscription details and usage
    """
    # Extract organization ID from JWT token
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization ID not found in authentication token"
        )

    # Delegate to existing endpoint
    return await get_subscription_info(org_id, db, current_user)
