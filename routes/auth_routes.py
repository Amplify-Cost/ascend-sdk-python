# auth_routes.py - Enterprise Authentication with Dual Format Support (SEC-006)
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response, Form
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, UTC
from typing import Optional
import logging
from passlib.context import CryptContext
from pydantic import BaseModel
from auth_utils import verify_password
from auth_utils import hash_password
from secrets import token_urlsafe

from database import get_db
from models import User
from schemas import UserCreate, LoginInput, TokenResponse
from token_utils import create_access_token, create_refresh_token, decode_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from dependencies import get_current_user, require_csrf  # ✅ FIX: Import require_csrf

# Cookie/CSRF constants centralized in security.cookies
from security.cookies import (
    SESSION_COOKIE_NAME,        # typically "access_token"
    CSRF_COOKIE_NAME,           # "owai_csrf"
    CSRF_HEADER_NAME,           # "X-CSRF-Token"
    COOKIE_SAMESITE,            # "None" or "Lax"/"Strict"
    COOKIE_SECURE,              # bool
    COOKIE_HTTPONLY             # bool (True for session)
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Existing cookie defaults, respected in dev/prod
COOKIE_CONFIG = {
    "secure": True,       # HTTPS only in prod
    "httponly": True,     # HttpOnly for session cookie
    "samesite": "strict", # overridden to "lax" in dev below
    "path": "/",
    "domain": None,
}

def get_cookie_config(request: Request) -> dict:
    """Derive cookie config per environment (dev vs prod)."""
    config = COOKIE_CONFIG.copy()
    # In dev (localhost), allow insecure and relax SameSite so your SPA works.
    if request.url.hostname in {"localhost", "127.0.0.1"}:
        config["secure"] = False
        config["samesite"] = "lax"
    return config

def detect_auth_preference(request: Request) -> str:
    """
    🏢 ENTERPRISE: Smart authentication mode detection

    Priority order:
    1. Explicit header (X-Auth-Mode: cookie/token) - Highest priority
    2. User-Agent detection (browsers use cookies, APIs use tokens)
    3. Default to token for unknown clients

    This approach:
    - Automatically selects cookie mode for web browsers (secure, HttpOnly)
    - Automatically selects token mode for API clients (stateless)
    - Allows explicit override via X-Auth-Mode header
    - Follows industry best practices (Auth0, AWS Cognito, Google)
    """
    # 1. Check for explicit preference header
    mode = (request.headers.get("X-Auth-Mode") or "").lower()
    if mode in {"cookie", "cookies"}:
        logger.debug("🔐 Auth mode: cookie (explicit header)")
        return "cookie"
    if mode in {"token", "bearer"}:
        logger.debug("🔐 Auth mode: token (explicit header)")
        return "token"

    # 2. Auto-detect from User-Agent (browsers vs API clients)
    user_agent = (request.headers.get("User-Agent") or "").lower()

    # Common browser User-Agent keywords
    browser_keywords = [
        "mozilla",      # Firefox, Chrome, Safari, Edge
        "chrome",       # Google Chrome
        "safari",       # Safari
        "firefox",      # Firefox
        "edge",         # Microsoft Edge
        "opera",        # Opera
        "msie",         # Internet Explorer (legacy)
        "trident"       # IE 11+
    ]

    # If User-Agent contains browser keywords, use cookie mode
    if any(keyword in user_agent for keyword in browser_keywords):
        logger.debug(f"🔐 Auth mode: cookie (detected browser: {user_agent[:50]}...)")
        return "cookie"

    # 3. Default to token for API clients, mobile apps, unknown clients
    logger.debug(f"🔐 Auth mode: token (API client or unknown: {user_agent[:50]}...)")
    return "token"

def _set_csrf_cookie(response: Response, request: Request) -> str:
    """
    Issue a non-HttpOnly CSRF cookie for double-submit protection.
    The frontend will echo this value in the X-CSRF-Token header
    for any POST/PUT/PATCH/DELETE request.
    """
    csrf = token_urlsafe(32)
    cookie_cfg = get_cookie_config(request)
    # CSRF cookie is NOT HttpOnly (frontend must read it)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf,
        httponly=False,
        secure=cookie_cfg.get("secure", True),
        samesite=cookie_cfg.get("samesite", "lax"),
        path="/",
        max_age=60 * 30,  # 30 minutes
    )
    return csrf

@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """User registration with dual auth support + CSRF issuance for cookie mode."""
    try:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        password_hash = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password=password_hash,
            role="user",
            is_active=True,
            created_at=datetime.now(UTC)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # JWTs
        access_token = create_access_token({
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "type": "access"
        })
        refresh_token = create_refresh_token({
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "type": "refresh"
        })

        auth_mode = detect_auth_preference(request)
        if auth_mode == "cookie":
            cfg = get_cookie_config(request)

            # Set session (HttpOnly) cookie for access token
            response.set_cookie(
                key=SESSION_COOKIE_NAME,  # typically "access_token"
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,           # enforce HttpOnly on session
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            # Set refresh token cookie (NOT HttpOnly is okay, but safer as HttpOnly too)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,                      # make refresh HttpOnly in enterprise
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )

            # Issue CSRF cookie for double-submit protection
            _set_csrf_cookie(response, request)

            logger.info(f"✅ User registered with cookie auth: {new_user.email}")
            return TokenResponse(  # keep schema: empty tokens in cookie mode
                access_token="",
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        # Legacy token mode (no cookies)
        logger.info(f"✅ User registered with token auth: {new_user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")

@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Enterprise login endpoint with dual format support.

    Supports TWO authentication formats:
    1. JSON: {"email": "user@example.com", "password": "password"}
    2. OAuth2 Form-data: username=user@example.com&password=password

    Returns JWT tokens in either:
    - Bearer token format (response body)
    - Cookie-based format (HttpOnly cookies)

    Security Features:
    - Rate limiting: 5 requests/minute
    - Security event logging
    - CSRF protection for cookie mode
    - Input validation
    """
    try:
        content_type = request.headers.get("content-type", "").lower()

        # Determine which format was used and extract credentials
        if "application/x-www-form-urlencoded" in content_type:
            # OAuth2 form-data format (uses 'username' field)
            form = await request.form()
            email = form.get("username")  # OAuth2 spec uses 'username' but we treat it as email
            password = form.get("password")
            auth_format = "form-data"

            if not email or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both username and password required for OAuth2 form-data format"
                )

            logger.info(f"🔐 Login attempt (OAuth2 form-data): {email}")
        elif "application/json" in content_type:
            # JSON format (uses 'email' field)
            try:
                body = await request.json()
                email = body.get("email")
                password = body.get("password")
                auth_format = "json"

                if not email or not password:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Both email and password required for JSON format"
                    )

                logger.info(f"🔐 Login attempt (JSON): {email}")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {str(e)}"
                )
        else:
            # Neither format provided
            logger.warning("❌ Login attempt with unsupported content-type")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login credentials required. Send either JSON {\"email\":\"...\",\"password\":\"...\"} or form-data username=...&password=..."
            )

        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"❌ Failed login attempt ({auth_format}): {email} - user not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # ============================================================================
        # PHASE 2 RBAC: ACCOUNT LOCKOUT PROTECTION (CVSS 7.2 - HIGH)
        # ============================================================================
        # Check if account is locked
        if user.is_locked and user.locked_until:
            # Check if lockout period has expired (auto-unlock after 30 minutes)
            if datetime.now(UTC) < user.locked_until.replace(tzinfo=UTC):
                remaining_minutes = int((user.locked_until.replace(tzinfo=UTC) - datetime.now(UTC)).total_seconds() / 60)
                logger.warning(f"🔒 Account locked: {email} (unlock in {remaining_minutes} minutes)")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is locked due to multiple failed login attempts. Please try again in {remaining_minutes} minutes or contact an administrator."
                )
            else:
                # Auto-unlock expired lockout
                logger.info(f"🔓 Auto-unlocking account: {email} (lockout period expired)")
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()

        # Verify password
        if not verify_password(password, user.password):
            # INCREMENT FAILED LOGIN ATTEMPTS (PHASE 2 RBAC)
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
                db.commit()
                logger.warning(f"🔒 Account locked after 5 failed attempts: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account has been locked due to multiple failed login attempts. Please contact an administrator or try again in 30 minutes."
                )
            else:
                db.commit()
                attempts_remaining = 5 - user.failed_login_attempts
                logger.warning(f"❌ Failed login attempt ({auth_format}): {email} ({attempts_remaining} attempts remaining)")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid email or password. {attempts_remaining} attempts remaining before account lockout."
                )

        # ============================================================================
        # PHASE 2 RBAC: PASSWORD EXPIRATION (CVSS 5.8 - MEDIUM)
        # ============================================================================
        # Check password age (90-day expiration policy)
        if user.password_last_changed:
            password_age_days = (datetime.now(UTC) - user.password_last_changed.replace(tzinfo=UTC)).days

            # Block login if password expired (>90 days)
            if password_age_days >= 90:
                logger.warning(f"⏰ Password expired for {email} ({password_age_days} days old)")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "password_expired",
                        "message": "Your password has expired. Please reset your password to continue.",
                        "password_age_days": password_age_days,
                        "requires_password_change": True
                    }
                )

            # Warn if password expiring soon (80-89 days)
            elif password_age_days >= 80:
                days_until_expiration = 90 - password_age_days
                logger.info(f"⚠️ Password expiring soon for {email} ({days_until_expiration} days remaining)")
                # Continue with login but include warning in response

        # Check if admin forced password change (PHASE 2 RBAC)
        if user.force_password_change:
            logger.info(f"🔑 Force password change required for {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "password_change_required",
                    "message": "Administrator has reset your password. You must change it before logging in.",
                    "requires_password_change": True
                }
            )

        # Check account status
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

        # SUCCESSFUL LOGIN - Reset failed attempts counter (PHASE 2 RBAC)
        user.failed_login_attempts = 0
        user.last_login = datetime.now(UTC)
        db.commit()

        access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access"
        })
        refresh_token = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh"
        })

        auth_mode = detect_auth_preference(request)
        if auth_mode == "cookie":
            cfg = get_cookie_config(request)

            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )

            _set_csrf_cookie(response, request)

            logger.info(f"✅ Cookie-based login ({auth_format}): {user.email}")
            return TokenResponse(
                access_token="",
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        # Legacy token mode
        logger.info(f"✅ Token-based login ({auth_format}): {user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    _=Depends(require_csrf)  # ✅ FIX: Now properly imported
):
    """Logout: clear session/refresh and CSRF cookies."""
    try:
        cfg = get_cookie_config(request)
        # Expire immediately
        expire_now = {**cfg, "max_age": 0}

        response.set_cookie(key=SESSION_COOKIE_NAME, value="", **expire_now)
        response.set_cookie(key="refresh_token", value="", **expire_now)
        response.set_cookie(key=CSRF_COOKIE_NAME, value="", httponly=False, **expire_now)

        logger.info(f"✅ User logged out: {current_user.get('email')}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return {"message": "Logout completed"}

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access/refresh tokens; for cookie mode, also keep CSRF fresh."""
    try:
        # Try cookie refresh first
        refresh_tok = request.cookies.get("refresh_token")
        auth_mode = "cookie" if refresh_tok else "token"

        if not refresh_tok:
            # Legacy: read from body
            body = await request.json()
            refresh_tok = (body or {}).get("refresh_token")

        if not refresh_tok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

        payload = decode_token(refresh_tok)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        new_access = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access"
        })
        new_refresh = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh"
        })

        if auth_mode == "cookie":
            cfg = get_cookie_config(request)
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=new_access,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            # Also rotate CSRF so client has a fresh token
            _set_csrf_cookie(response, request)
            return TokenResponse(access_token="", refresh_token="", token_type="cookie", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        # Legacy/bearer mode
        return TokenResponse(access_token=new_access, refresh_token=new_refresh, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed")

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Return current user for UI session checks."""
    try:
        return {
            "id": current_user.get("user_id") or current_user.get("sub"),
            "email": current_user.get("email"),
            "role": current_user.get("role"),
            "auth_method": current_user.get("auth_method", "cookie"),
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=401, detail="Unable to retrieve user information")

@router.get("/csrf", tags=["auth"])
def get_csrf(response: Response, request: Request):
    """Issue/refresh CSRF cookie and return its value."""
    csrf = _set_csrf_cookie(response, request)
    return {"csrf": csrf}

# ============================================================================
# PHASE 2 RBAC: PASSWORD CHANGE ENDPOINT
# ============================================================================

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    🔑 PHASE 2 RBAC: User password change endpoint

    Security Features:
    - Verifies current password is correct
    - Validates new password complexity (enterprise standards)
    - Ensures new password != current password
    - Updates password_last_changed timestamp
    - Clears force_password_change flag
    - Logs to audit trail

    Compliance:
    - NIST SP 800-63B: Password change requirements
    - PCI-DSS 3.2.1: Password history (new != current)
    - SOX: User password management
    - HIPAA: Password security controls

    Enterprise Standards:
    - Minimum 12 characters (14 for admin)
    - Complexity requirements (upper, lower, number, special)
    - No sequential/repeated characters
    - Not in common password list
    """
    try:
        logger.info(f"🔑 Password change requested by user: {current_user.get('email')}")

        # Get user with current password
        user_query = text("""
            SELECT id, email, password, role
            FROM users
            WHERE id = :user_id
        """)
        user = db.execute(user_query, {"user_id": current_user.get("user_id")}).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify current password
        from auth_utils import verify_password, hash_password, validate_password_strength

        if not verify_password(password_data.current_password, user.password):
            logger.warning(f"❌ Failed password change attempt for {user.email} - incorrect current password")
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        # Validate new password strength
        is_admin = user.role == "admin"
        validation_result = validate_password_strength(password_data.new_password, is_admin=is_admin)

        if not validation_result["valid"]:
            logger.warning(f"❌ Password validation failed for {user.email}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "New password does not meet complexity requirements",
                    "errors": validation_result["errors"],
                    "strength_score": validation_result["strength_score"]
                }
            )

        # Ensure new password != current password (PCI-DSS requirement)
        if verify_password(password_data.new_password, user.password):
            logger.warning(f"❌ New password same as current password for {user.email}")
            raise HTTPException(
                status_code=400,
                detail="New password must be different from current password"
            )

        # Hash new password
        new_password_hash = hash_password(password_data.new_password)

        # Update password with PHASE 2 columns
        update_query = text("""
            UPDATE users
            SET password = :password,
                password_last_changed = CURRENT_TIMESTAMP,
                force_password_change = FALSE
            WHERE id = :user_id
        """)

        db.execute(update_query, {
            "password": new_password_hash,
            "user_id": user.id
        })
        db.commit()

        # Log audit action
        try:
            from routes.enterprise_user_management_routes import log_audit_action
            await log_audit_action(
                db=db,
                user_email=user.email,
                action="PASSWORD_CHANGE",
                target=user.email,
                details=f"User {user.email} changed their password",
                ip_address=str(request.client.host) if request else "unknown",
                risk_level="Medium"
            )
        except Exception as e:
            logger.warning(f"⚠️ Audit logging failed (non-critical): {e}")

        logger.info(f"✅ Password changed successfully for {user.email}")

        return {
            "message": "✅ Password changed successfully",
            "user_email": user.email,
            "password_strength_score": validation_result["strength_score"],
            "security_note": "Password will expire in 90 days",
            "force_password_change": False
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")
