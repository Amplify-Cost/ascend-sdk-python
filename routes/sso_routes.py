from auth_utils import hash_password
import secrets
import string


def generate_sso_temp_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(12))

"""
Enterprise SSO/OIDC Routes
Handles authentication with Okta, Azure AD, Google Workspace
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Optional
import logging
import secrets
import uuid
from datetime import datetime, timedelta, UTC

from database import get_db
from dependencies import get_current_user, require_admin, get_organization_filter
from enterprise_config import config
from jwt_manager import jwt_manager
from sso_manager import enterprise_sso
from rbac_manager import enterprise_rbac

router = APIRouter(prefix="/api/auth/sso", tags=["Enterprise SSO"])
logger = logging.getLogger(__name__)

# Store SSO state temporarily (in production, use Redis)
sso_state_store = {}

@router.get("/providers")
async def list_sso_providers():
    """List available SSO providers for frontend"""
    
    return {
        "providers": [
            {
                "id": "okta",
                "name": "Okta",
                "enabled": bool(config.get_secret("okta-client-id")),
                "icon": "okta"
            },
            {
                "id": "azure_ad", 
                "name": "Microsoft Azure AD",
                "enabled": bool(config.get_secret("azure-ad-client-id")),
                "icon": "microsoft"
            },
            {
                "id": "google",
                "name": "Google Workspace", 
                "enabled": bool(config.get_secret("google-client-id")),
                "icon": "google"
            }
        ],
        "enterprise_sso_enabled": True,
        "fallback_auth_enabled": config.environment != "production"
    }

@router.get("/login/{provider}")
async def initiate_sso_login(
    provider: str,
    request: Request,
    redirect_after_login: Optional[str] = None
):
    """Initiate SSO login flow"""
    
    try:
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state and redirect info
        sso_state_store[state] = {
            "provider": provider,
            "redirect_after_login": redirect_after_login or "/dashboard",
            "initiated_at": datetime.now(UTC).isoformat(),
            "ip_address": request.client.host
        }
        
        # Get redirect URI for this environment
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/auth/sso/callback/{provider}"
        
        # Get authorization URL from SSO provider
        authorization_url = enterprise_sso.get_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state
        )
        
        logger.info(f"🔐 SSO login initiated for {provider} with state {state[:8]}...")
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "provider": provider,
            "redirect_uri": redirect_uri
        }
        
    except Exception as e:
        logger.error(f"❌ SSO login initiation failed for {provider}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SSO login: {str(e)}"
        )

@router.get("/callback/{provider}")
async def handle_sso_callback(
    provider: str,
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle SSO callback and complete authentication"""
    
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"❌ SSO callback error for {provider}: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO authentication failed: {error}"
            )
        
        # Validate state parameter
        if not state or state not in sso_state_store:
            logger.error(f"❌ Invalid or missing state parameter: {state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SSO state parameter"
            )
        
        stored_state = sso_state_store.pop(state)  # Remove used state
        
        if stored_state["provider"] != provider:
            logger.error(f"❌ Provider mismatch: expected {stored_state['provider']}, got {provider}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSO provider mismatch"
            )
        
        # Exchange authorization code for tokens
        redirect_uri = f"{str(request.base_url).rstrip('/')}/auth/sso/callback/{provider}"
        token_data = enterprise_sso.exchange_code_for_token(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri
        )
        
        # Get user information from SSO provider
        access_token = token_data["access_token"]
        user_info = enterprise_sso.get_user_info(provider, access_token)
        
        # Get user groups for RBAC mapping
        user_groups = enterprise_sso.get_user_groups(
            provider=provider,
            access_token=access_token,
            user_id=user_info.get("sub") or user_info.get("id")
        )
        
        # Create enterprise user profile
        enterprise_profile = enterprise_sso.create_enterprise_user_profile(
            provider=provider,
            user_info=user_info,
            groups=user_groups
        )
        
        # 🏢 ENTERPRISE: Extract organization_id from SSO groups or email domain
        # Note: For SSO callback (public endpoint), we determine org from SSO metadata
        organization_id = enterprise_profile.get("organization_id")
        if not organization_id:
            # Try to map from email domain or SSO groups
            # For now, use default organization or create one
            logger.warning(f"⚠️ No organization_id in SSO profile for {enterprise_profile['email']}")

        # Create or update user in database with organization context
        user_record = await create_or_update_sso_user(db, enterprise_profile, organization_id)

        # Create enterprise JWT token with organization context
        session_id = str(uuid.uuid4())

        enterprise_token = jwt_manager.create_access_token(
            user_id=str(user_record["user_id"]),
            role=enterprise_profile["role"],
            tenant_id="main",  # Could be mapped from SSO
            session_id=session_id,
            permissions=list(enterprise_rbac.get_user_permissions(enterprise_profile["access_level"])),
            organization_id=organization_id  # 🏢 ENTERPRISE: Add org context to token
        )
        
        # Set secure cookie
        cookie_config = {
            "httponly": True,
            "secure": config.environment == "production",
            "samesite": "lax",
            "max_age": 3600  # 1 hour
        }
        
        response.set_cookie(
            key="ow_ai_token",
            value=enterprise_token,
            **cookie_config
        )
        
        # Audit log the SSO login
        await log_sso_audit_event(
            db=db,
            user_email=enterprise_profile["email"],
            action="sso_login_success",
            provider=provider,
            access_level=enterprise_profile["access_level"],
            ip_address=request.client.host,
            organization_id=organization_id  # 🏢 ENTERPRISE: Multi-tenant audit trail
        )

        logger.info(f"✅ SSO login successful for {enterprise_profile['email']} via {provider} [org_id={organization_id}]")

        # Redirect to original destination
        redirect_url = stored_state.get("redirect_after_login", "/dashboard")
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SSO callback handling failed: {str(e)}")

        # Audit log the failure
        try:
            await log_sso_audit_event(
                db=db,
                user_email="unknown",
                action="sso_login_failed",
                provider=provider,
                details=str(e),
                ip_address=request.client.host,
                organization_id=None  # Unknown org for failed login
            )
        except:
            pass  # Don't fail on audit logging
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO authentication failed: {str(e)}"
        )

@router.post("/logout")
async def sso_logout(
    request: Request,
    response: Response,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: int = Depends(get_organization_filter)
):
    """Logout from SSO session with multi-tenant audit trail"""

    try:
        # Clear the authentication cookie
        response.delete_cookie(
            key="ow_ai_token",
            httponly=True,
            secure=config.environment == "production",
            samesite="lax"
        )

        # Audit log the logout with organization context
        await log_sso_audit_event(
            db=db,
            user_email=current_user.get("email", "unknown"),
            action="sso_logout",
            provider=current_user.get("sso_provider", "unknown"),
            ip_address=request.client.host,
            organization_id=org_id  # 🏢 ENTERPRISE: Multi-tenant audit trail
        )

        logger.info(f"✅ SSO logout successful for {current_user.get('email', 'unknown')} [org_id={org_id}]")

        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"❌ SSO logout failed: {str(e)} [org_id={org_id}]")
        return {"message": "Logout completed with errors"}

@router.get("/user-profile")
async def get_sso_user_profile(
    current_user: Dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """Get current user's SSO profile and permissions"""

    try:
        # 🏢 ENTERPRISE: Verify organization context
        user_org_id = current_user.get("organization_id")
        if org_id is not None and user_org_id != org_id:
            logger.warning(f"⚠️ Organization mismatch for {current_user.get('email')}: token org_id={user_org_id}, filter org_id={org_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context mismatch"
            )

        role_summary = enterprise_rbac.get_role_summary(
            current_user.get("access_level", 0)
        )

        logger.info(f"✅ SSO user profile retrieved for {current_user.get('email')} [org_id={org_id}]")

        return {
            "user_info": {
                "email": current_user.get("email"),
                "first_name": current_user.get("first_name", ""),
                "last_name": current_user.get("last_name", ""),
                "department": current_user.get("department", ""),
                "sso_provider": current_user.get("sso_provider", ""),
                "login_method": "SSO",
                "mfa_enabled": current_user.get("mfa_enabled", True),
                "organization_id": org_id
            },
            "access_control": role_summary,
            "session_info": {
                "session_id": current_user.get("session_id"),
                "expires_at": current_user.get("exp"),
                "issued_at": current_user.get("iat")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get SSO user profile: {str(e)} [org_id={org_id}]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

# Helper functions

async def create_or_update_sso_user(db: Session, enterprise_profile: Dict, organization_id: int = None) -> Dict:
    """
    Create or update user from SSO profile with multi-tenant isolation

    Args:
        db: Database session
        enterprise_profile: SSO user profile data
        organization_id: Organization ID for multi-tenant isolation
    """

    try:
        email = enterprise_profile["email"]

        # 🏢 ENTERPRISE: Multi-tenant isolation - check if user exists in organization
        query_params = {"email": email}
        query = """
            SELECT user_id, email, access_level, organization_id
            FROM users
            WHERE email = :email
        """

        # 🏢 ENTERPRISE: Multi-tenant isolation
        if organization_id is not None:
            query += " AND organization_id = :organization_id"
            query_params["organization_id"] = organization_id

        existing_user = db.execute(text(query), query_params).fetchone()

        if existing_user:
            # Update existing user
            update_params = {
                "email": email,
                "first_name": enterprise_profile["first_name"],
                "last_name": enterprise_profile["last_name"],
                "access_level": enterprise_profile["access_level"],
                "department": enterprise_profile["department"],
                "mfa_enabled": enterprise_profile["mfa_enabled"],
                "status": enterprise_profile["status"],
                "last_login": datetime.now(UTC)
            }

            update_query = """
                UPDATE users SET
                    first_name = :first_name,
                    last_name = :last_name,
                    access_level = :access_level,
                    department = :department,
                    mfa_enabled = :mfa_enabled,
                    status = :status,
                    last_login = :last_login
                WHERE email = :email
            """

            # 🏢 ENTERPRISE: Multi-tenant isolation
            if organization_id is not None:
                update_query += " AND organization_id = :organization_id"
                update_params["organization_id"] = organization_id

            db.execute(text(update_query), update_params)

            user_id = existing_user[0]
            logger.info(f"✅ Updated existing SSO user: {email} [org_id={organization_id}]")

        else:
            # Create new user with organization context
            temp_password = generate_sso_temp_password()
            hashed_password = hash_password(temp_password)

            # Enterprise: Generate secure password for SSO users
            import secrets
            import string
            from auth_utils import hash_password

            def generate_enterprise_sso_password():
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                return "".join(secrets.choice(alphabet) for _ in range(14))

            temp_password = generate_enterprise_sso_password()
            hashed_password = hash_password(temp_password)

            insert_params = {
                "email": email,
                "password": hashed_password,
                "first_name": enterprise_profile["first_name"],
                "last_name": enterprise_profile["last_name"],
                "access_level": enterprise_profile["access_level"],
                "department": enterprise_profile["department"],
                "mfa_enabled": enterprise_profile["mfa_enabled"],
                "status": enterprise_profile["status"],
                "role": enterprise_profile["role"],
                "last_login": datetime.now(UTC),
                "created_at": datetime.now(UTC)
            }

            # 🏢 ENTERPRISE: Set organization_id for new users
            if organization_id is not None:
                insert_params["organization_id"] = organization_id
                insert_query = """
                    INSERT INTO users (
                        email, password, first_name, last_name, access_level, department,
                        mfa_enabled, status, role, last_login, created_at, organization_id
                    ) VALUES (
                        :email, :password, :first_name, :last_name, :access_level, :department,
                        :mfa_enabled, :status, :role, :last_login, :created_at, :organization_id
                    ) RETURNING user_id
                """
                logger.info(f"🏢 Enterprise SSO: Creating new user {email} with org_id={organization_id}")
            else:
                insert_query = """
                    INSERT INTO users (
                        email, password, first_name, last_name, access_level, department,
                        mfa_enabled, status, role, last_login, created_at
                    ) VALUES (
                        :email, :password, :first_name, :last_name, :access_level, :department,
                        :mfa_enabled, :status, :role, :last_login, :created_at
                    ) RETURNING user_id
                """
                logger.warning(f"⚠️ Enterprise SSO: Creating new user {email} without org_id (backward compatibility mode)")

            result = db.execute(text(insert_query), insert_params)

            user_id = result.fetchone()[0]
            logger.info(f"✅ Created new SSO user: {email} [org_id={organization_id}]")

        db.commit()

        return {
            "user_id": user_id,
            "email": email,
            "access_level": enterprise_profile["access_level"],
            "organization_id": organization_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create/update SSO user: {str(e)} [org_id={organization_id}]")
        raise

async def log_sso_audit_event(
    db: Session,
    user_email: str,
    action: str,
    provider: str = "",
    access_level: int = 0,
    details: str = "",
    ip_address: str = "",
    organization_id: int = None
):
    """
    Log SSO audit events with multi-tenant isolation

    Args:
        db: Database session
        user_email: User's email address
        action: Audit action type
        provider: SSO provider name
        access_level: User's access level
        details: Additional audit details
        ip_address: Client IP address
        organization_id: Organization ID for multi-tenant isolation
    """

    try:
        audit_params = {
            "user_email": user_email,
            "action": action,
            "target": f"SSO Provider: {provider}",
            "details": details or f"Access Level: {access_level}",
            "ip_address": ip_address,
            "timestamp": datetime.now(UTC)
        }

        # 🏢 ENTERPRISE: Multi-tenant isolation for audit logs
        if organization_id is not None:
            audit_params["organization_id"] = organization_id
            insert_query = """
                INSERT INTO user_audit_logs (
                    user_email, action, target, details, ip_address, timestamp, organization_id
                ) VALUES (
                    :user_email, :action, :target, :details, :ip_address, :timestamp, :organization_id
                )
            """
            logger.debug(f"🏢 Logging SSO audit event for {user_email} [org_id={organization_id}]")
        else:
            insert_query = """
                INSERT INTO user_audit_logs (
                    user_email, action, target, details, ip_address, timestamp
                ) VALUES (
                    :user_email, :action, :target, :details, :ip_address, :timestamp
                )
            """
            logger.debug(f"⚠️ Logging SSO audit event for {user_email} without org_id")

        db.execute(text(insert_query), audit_params)

        db.commit()

    except Exception as e:
        logger.warning(f"⚠️ Failed to log SSO audit event: {str(e)} [org_id={organization_id}]")
        # Don't fail the main operation for audit logging issues