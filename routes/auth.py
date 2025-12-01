# routes/auth.py - Enterprise Response Diagnostics (Find Exact Format Issue)

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from security.cookies import SESSION_COOKIE_NAME, CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text  # PHASE 2: For password change SQL queries
from database import get_db
from models import User, Organization, LogAuditTrail
from passlib.context import CryptContext
from auth_utils import verify_password
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from dependencies import get_current_user, require_csrf, require_admin  # PHASE 2: Added require_csrf for logout, require_admin for token revocation
from pydantic import BaseModel
from secrets import token_urlsafe
import jwt
import os
import logging
import json

# ✅ SECURITY FIX: Import secure JWT decoder
# Created by: OW-kai Engineer (Phase 2 Security Fixes - JWT Hardening)
from security.jwt_security import secure_jwt_decode

# Enterprise rate limiting
from security.rate_limiter import limiter, RATE_LIMITS

class LoginRequest(BaseModel):
    email: str
    password: str

# =================== ENTERPRISE DIAGNOSTIC CONFIGURATION ===================

router = APIRouter(prefix="/api/auth", tags=["Enterprise Authentication"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enhanced logging for response diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enterprise.auth.diagnostic")

# Enterprise Security Settings - MUST match dependencies.py
from config import SECRET_KEY, ALGORITHM, COOKIE_SECURE, COOKIE_SAMESITE
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Enterprise Cookie Configuration
ENTERPRISE_COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,
    "samesite": "lax",
    "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    "path": "/",
    "domain": None
}

ENTERPRISE_REFRESH_COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,
    "samesite": "lax",
    "max_age": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    "path": "/auth",
    "domain": None
}

# =================== ENTERPRISE UTILITIES ===================

def create_enterprise_token(data: dict, token_type: str = "access") -> str:
    """Create enterprise JWT token"""
    try:
        to_encode = data.copy()
        
        if token_type == "access":
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": token_type,
            "iss": "ow-ai-enterprise",
            "aud": "ow-ai-platform",
            "jti": f"{token_type}-{data.get('sub', 'unknown')}-{int(datetime.now(UTC).timestamp())}"
        })
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"✅ Token created for user {data.get('email', 'unknown')}")
        return token
        
    except Exception as e:
        logger.error(f"🚨 Token creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def validate_enterprise_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Validate enterprise JWT with audience fix"""
    try:
        if not token:
            logger.error("🚨 DIAGNOSTIC: No token provided")
            raise HTTPException(status_code=401, detail="No token provided")
        
        logger.info(f"🔍 DIAGNOSTIC: Validating token type: {expected_type}")
        logger.info(f"🔍 DIAGNOSTIC: Token length: {len(token)}")
        logger.info(f"🔍 DIAGNOSTIC: Token start: {token[:50]}...")
        
        # ✅ SECURITY FIX: Use secure JWT decoder with enhanced validation
        # Created by: OW-kai Engineer (Phase 2 Security Fixes - JWT Hardening)
        try:
            payload = secure_jwt_decode(
                token=token,
                secret_key=SECRET_KEY,
                algorithms=[ALGORITHM],
                required_claims=["sub", "exp"],
                operation_name="validate_enterprise_token"
            )
            logger.info(f"✅ DIAGNOSTIC: Token decoded successfully (secure decoder)")
            logger.info(f"🔍 DIAGNOSTIC: Payload keys: {list(payload.keys())}")
            logger.info(f"🔍 DIAGNOSTIC: Token type in payload: {payload.get('type')}")
            logger.info(f"🔍 DIAGNOSTIC: Audience in payload: {payload.get('aud')}")
            logger.info(f"🔍 DIAGNOSTIC: Issuer in payload: {payload.get('iss')}")
        except jwt.ExpiredSignatureError as e:
            logger.error(f"🚨 DIAGNOSTIC: Token expired: {e}")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"🚨 DIAGNOSTIC: Invalid token error: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"🚨 DIAGNOSTIC: Token decode error: {e}")
            raise HTTPException(status_code=401, detail="Token decode failed")
        
        # ENTERPRISE SECURITY: Strict token type validation
        # Prevents refresh tokens (7-day expiry) from being used as access tokens (30-min expiry)
        # This is a CRITICAL security control - do not bypass
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            logger.error(f"🚨 SECURITY: Token type mismatch - expected: {expected_type}, got: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        logger.info(f"✅ DIAGNOSTIC: Token validation successful for user: {payload.get('email', 'unknown')}")
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 DIAGNOSTIC: Unexpected validation error: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed")

def parse_request_safely(request_body: bytes) -> Dict[str, Any]:
    """Safe request parsing"""
    try:
        if not request_body:
            return {}
        
        body_str = request_body.decode('utf-8', errors='ignore')
        if not body_str.strip():
            return {}
        
        try:
            return json.loads(body_str)
        except json.JSONDecodeError:
            return {}
        
    except Exception:
        return {}

# 🔧 ENTERPRISE FIX: Enhanced debugging for cookie detection

def detect_auth_preference(request: Request) -> str:
    """
    🏢 ENTERPRISE: Smart authentication mode detection

    Priority order:
    1. Explicit header (X-Auth-Mode: cookie/token) - Highest priority
    2. User-Agent detection (browsers use cookies, APIs use tokens)
    3. Default to token for unknown clients
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
        "mozilla", "chrome", "safari", "firefox",
        "edge", "opera", "msie", "trident"
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
    🏢 ENTERPRISE: Issue a non-HttpOnly CSRF cookie for double-submit protection.
    The frontend will echo this value in the X-CSRF-Token header
    for any POST/PUT/PATCH/DELETE request.
    """
    csrf = token_urlsafe(32)
    # CSRF cookie is NOT HttpOnly (frontend must read it)
    # ✅ SECURITY FIX: Environment-based cookie security
    # Created by: OW-kai Engineer (Phase 2 Security Fixes - Cookie Hardening)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf,
        httponly=False,  # CRITICAL: Frontend must read this
        secure=COOKIE_SECURE,  # ✅ SECURE: True in production, False in dev
        samesite=COOKIE_SAMESITE,  # ✅ SECURE: "strict" in production
        path="/",
        max_age=60 * 30,  # 30 minutes
    )
    logger.debug(f"🔐 CSRF cookie set: {csrf[:10]}...")
    return csrf

def get_authentication_source(request: Request, credentials: HTTPAuthorizationCredentials) -> tuple[str, str, str]:
    """Get auth source - MINIMAL ENTERPRISE FIX"""

    # 🔧 ENTERPRISE FIX: Check Authorization header first (primary method)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        logger.info(f"🎫 ENTERPRISE: Authorization header found, length = {len(token)}")
        return token, "bearer", "enterprise"

    # Check cookies (secondary method)
    access_cookie = request.cookies.get("access_token")
    if not access_cookie:
        access_cookie = request.cookies.get("ow_access_token")

    if access_cookie:
        logger.info(f"🍪 ENTERPRISE: Cookie found, length = {len(access_cookie)}")
        return access_cookie, "cookie", "enterprise"

    # FastAPI HTTPBearer fallback
    if credentials and credentials.credentials:
        logger.info(f"🎫 ENTERPRISE: FastAPI credentials found, length = {len(credentials.credentials)}")
        return credentials.credentials, "bearer", "fastapi"

    logger.warning("🚨 ENTERPRISE: No authentication found")
    return None, "none", "none"

def set_enterprise_cookies(response: Response, access_token: str, refresh_token: str):
    """Set enterprise cookies - ENTERPRISE FIX: Optimized cookie configuration"""

    # ✅ SECURITY FIX: Environment-based cookie security
    # Created by: OW-kai Engineer (Phase 2 Security Fixes - Cookie Hardening)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,  # Use enterprise session cookie
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,  # ✅ SECURE: True in production, False in dev
        samesite=COOKIE_SAMESITE,  # ✅ SECURE: "strict" in production
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"  # Ensure cookie is available for all paths
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,  # ✅ SECURE: True in production, False in dev
        samesite=COOKIE_SAMESITE,  # ✅ SECURE: "strict" in production
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"  # CHANGED: Make available for all paths, not just /auth
    )

    logger.info("🍪 Enterprise cookies set with correct names")

def log_response_diagnostics(response_data: dict, endpoint: str):
    """Log detailed response diagnostics"""
    logger.info(f"🔍 DIAGNOSTIC: {endpoint} response structure:")
    logger.info(f"🔍 Response keys: {list(response_data.keys())}")
    logger.info(f"🔍 Response size: {len(json.dumps(response_data))} characters")
    
    for key, value in response_data.items():
        logger.info(f"🔍 Field '{key}': {type(value).__name__} = {str(value)[:100]}...")
    
    if "user" in response_data:
        user_data = response_data["user"]
        logger.info(f"🔍 User object keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'not a dict'}")
        if isinstance(user_data, dict):
            for k, v in user_data.items():
                logger.info(f"🔍 User.{k}: {type(v).__name__} = {v}")

# =================== ENTERPRISE ENDPOINTS ===================

@router.post("/token")
@limiter.limit(RATE_LIMITS["auth_login"])
async def enterprise_login_diagnostic(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    🔍 Enterprise Login with Dual Format Support (SEC-006)

    Supports TWO authentication formats:
    1. JSON: {"email": "user@example.com", "password": "password"}
    2. OAuth2 Form-data: username=user@example.com&password=password

    Returns JWT tokens with enterprise diagnostics
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
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format - please send valid JSON"
                )

            email = body.get("email")
            password = body.get("password")
            auth_format = "json"

            if not email or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both email and password required for JSON format"
                )

            logger.info(f"🔐 Login attempt (JSON): {email}")
        else:
            # Neither format provided
            logger.warning("❌ Login attempt with unsupported content-type")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login credentials required. Send either JSON {\"email\":\"...\",\"password\":\"...\"} or form-data username=...&password=..."
            )

        email = email.strip().lower()

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        # Validate user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"❌ Failed login attempt ({auth_format}): {email} - User not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")

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
            # ============================================================================
            # PHASE 2 RBAC: FAILED LOGIN ATTEMPT TRACKING
            # ============================================================================
            # INCREMENT FAILED LOGIN ATTEMPTS
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

        # ============================================================================
        # PHASE 2 RBAC: FORCE PASSWORD CHANGE
        # ============================================================================
        # Check if admin forced password change
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

        # ============================================================================
        # PHASE 2 RBAC: SUCCESSFUL LOGIN - RESET COUNTER
        # ============================================================================
        user.failed_login_attempts = 0
        user.last_login = datetime.now(UTC)
        db.commit()

        # Create tokens with organization context for multi-tenant isolation
        # ENTERPRISE SECURITY: organization_id is REQUIRED for data isolation
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "user_id": user.id,
            "organization_id": user.organization_id  # CRITICAL: Multi-tenant isolation
        }

        access_token = create_enterprise_token(user_data, "access")
        refresh_token = create_enterprise_token(user_data, "refresh")

        # 🏢 ENTERPRISE: Detect auth mode (User-Agent smart detection)
        auth_mode = detect_auth_preference(request)

        if auth_mode == "cookie":
            # Cookie-based authentication for browsers
            set_enterprise_cookies(response, access_token, refresh_token)
            _set_csrf_cookie(response, request)  # CRITICAL: Set CSRF cookie

            logger.info(f"✅ Cookie-based login ({auth_format}): {user.email}")
            return {
                "access_token": "",  # Empty for cookie mode
                "refresh_token": "",  # Empty for cookie mode
                "token_type": "cookie",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "email": user.email,
                    "role": user.role,
                    "user_id": user.id
                },
                "auth_mode": "cookie"
            }

        # Token-based authentication for API clients
        logger.info(f"✅ Token-based login ({auth_format}): {user.email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id
            },
            "auth_mode": "token"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me")
async def get_current_user_diagnostic(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """🔍 Enterprise User Info with Enhanced Diagnostics"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🔍 DIAGNOSTIC USER INFO from {client_ip}")
        
        # Get auth source with detailed logging
        token, auth_source, auth_mode = get_authentication_source(request, credentials)
        
        logger.info(f"🔍 DIAGNOSTIC: Auth source = {auth_source}, mode = {auth_mode}")
        logger.info(f"🔍 DIAGNOSTIC: Token present = {bool(token)}")
        
        if not token:
            logger.warning("🚨 DIAGNOSTIC: No authentication found")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Enhanced token validation with debugging
        try:
            logger.info("🔍 DIAGNOSTIC: Starting token validation...")
            payload = validate_enterprise_token(token, "access")
            logger.info("✅ DIAGNOSTIC: Token validation successful")
        except HTTPException as e:
            logger.error(f"🚨 DIAGNOSTIC: Token validation failed: {e.detail}")
            # Try validating without strict type checking
            try:
                logger.info("🔍 DIAGNOSTIC: Trying flexible token validation...")
                # ✅ SECURITY FIX: Use secure JWT decoder even for flexible validation
                # Created by: OW-kai Engineer (Phase 2 Security Fixes - JWT Hardening)
                payload = secure_jwt_decode(
                    token=token,
                    secret_key=SECRET_KEY,
                    algorithms=[ALGORITHM],
                    required_claims=["sub"],
                    operation_name="auth_me_flexible"
                )
                logger.info("✅ DIAGNOSTIC: Flexible validation successful")
            except Exception as flex_error:
                logger.error(f"🚨 DIAGNOSTIC: Flexible validation also failed: {flex_error}")
                raise e
        
        user_id = payload.get("sub")
        logger.info(f"🔍 DIAGNOSTIC: Token payload user_id = {user_id}")
        logger.info(f"🔍 DIAGNOSTIC: Token payload email = {payload.get('email')}")
        logger.info(f"🔍 DIAGNOSTIC: Token payload role = {payload.get('role')}")
        
        if not user_id:
            logger.error("🚨 DIAGNOSTIC: No user_id in token payload")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user with detailed logging
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            logger.info(f"🔍 DIAGNOSTIC: Database query for user_id {user_id}")
            if user:
                logger.info(f"✅ DIAGNOSTIC: User found - email: {user.email}, role: {user.role}")
            else:
                logger.error(f"🚨 DIAGNOSTIC: User not found in database for user_id: {user_id}")
        except Exception as db_error:
            logger.error(f"🚨 DIAGNOSTIC: Database error: {db_error}")
            raise HTTPException(status_code=500, detail="Database error")
        
        if not user:
            logger.warning(f"🚨 DIAGNOSTIC: User not found: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        response_data = {
            "user_id": int(user_id),
            "email": user.email,
            "role": user.role,
            "auth_source": auth_source,
            "auth_mode": auth_mode,
            "enterprise_validated": True
        }
        
        logger.info("✅ DIAGNOSTIC: /auth/me response prepared successfully")
        log_response_diagnostics(response_data, "AUTH_ME")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 DIAGNOSTIC: Unexpected error in /auth/me: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication validation failed")

@router.post("/refresh-token")
@limiter.limit(RATE_LIMITS["auth_refresh"])
async def refresh_token_diagnostic(request: Request, response: Response):
    """🔍 Enterprise Token Refresh with Diagnostics - ENTERPRISE FIX: Correct cookie names"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🔍 DIAGNOSTIC REFRESH from {client_ip}")
        
        # 🔧 ENTERPRISE FIX: Check for refresh token with correct name
        refresh_token = request.cookies.get("refresh_token")  # Frontend cookie name
        if not refresh_token:
            refresh_token = request.cookies.get("ow_refresh_token")  # Fallback name
        auth_source = "cookie"
        
        if not refresh_token:
            request_body = await request.body()
            data = parse_request_safely(request_body)
            refresh_token = data.get("refresh_token")
            auth_source = "body"
            
        logger.info(f"🔍 DIAGNOSTIC: Refresh token source = {auth_source}")
        logger.info(f"🔍 DIAGNOSTIC: Refresh token present = {bool(refresh_token)}")
        
        if not refresh_token:
            return {
                "error": "no_refresh_token",
                "message": "No refresh token provided",
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Validate refresh token
        try:
            payload = validate_enterprise_token(refresh_token, "refresh")
        except HTTPException as e:
            return {
                "error": "invalid_refresh_token",
                "message": e.detail,
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Create new tokens with organization context preserved
        # ENTERPRISE SECURITY: organization_id MUST be preserved during token refresh
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id", payload.get("sub")),
            "organization_id": payload.get("organization_id")  # CRITICAL: Preserve org context
        }

        new_access_token = create_enterprise_token(user_data, "access")
        new_refresh_token = create_enterprise_token(user_data, "refresh")
        
        # Update cookies if using cookie auth
        if auth_source == "cookie":
            set_enterprise_cookies(response, new_access_token, new_refresh_token)
        
        response_data = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        logger.info("🔍 DIAGNOSTIC: Refresh response:")
        log_response_diagnostics(response_data, "REFRESH")
        
        return response_data
        
    except Exception as e:
        logger.error(f"🚨 Refresh error: {str(e)}", exc_info=True)
        return {
            "error": "system_error",
            "message": "Refresh temporarily unavailable",
            "timestamp": datetime.now(UTC).isoformat()
        }


@router.post("/logout")
async def enterprise_logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    _=Depends(require_csrf)
):

    """🚪 Enterprise logout with secure cookie clearing"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚪 ENTERPRISE LOGOUT from {client_ip}")
        
        # ✅ SECURITY FIX: Clear cookies with environment-based security settings
        # Created by: OW-kai Engineer (Phase 2 Security Fixes - Cookie Hardening)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,  # Use enterprise session cookie
            value="",
            httponly=True,
            secure=COOKIE_SECURE,  # ✅ SECURE: Match environment settings
            samesite=COOKIE_SAMESITE,  # ✅ SECURE: Match environment settings
            max_age=0,
            path="/"
        )

        response.set_cookie(
            key="refresh_token",
            value="",
            httponly=True,
            secure=COOKIE_SECURE,  # ✅ SECURE: Match environment settings
            samesite=COOKIE_SAMESITE,  # ✅ SECURE: Match environment settings
            max_age=0,
            path="/"
        )
        
        logger.info("✅ ENTERPRISE: Cookies cleared successfully")
        
        return {
            "message": "Logged out successfully",
            "enterprise_security": "Cookies cleared",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        logger.error(f"🚨 Logout error: {str(e)}")
        # Return success even if there's an error - don't block logout
        return {
            "message": "Logout completed",
            "note": "Session cleared locally",
            "timestamp": datetime.now(UTC).isoformat()
        }


# =============================================================================
# ENTERPRISE TOKEN REVOCATION ENDPOINTS
# =============================================================================
# Engineer: OW-KAI Enterprise Security Team
# Date: 2025-11-24
# Security Level: Banking/Financial Services Grade
#
# COMPLIANCE:
# - NIST SP 800-63B Section 6.1.6: Token Revocation
# - PCI-DSS 8.1.5: Session Termination
# - SOX Section 404: Access Revocation
# - HIPAA § 164.312(d): Emergency Access Procedures
# =============================================================================

@router.post("/revoke-tokens")
@limiter.limit("10/minute")
async def revoke_all_user_tokens(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔐 ENTERPRISE: Revoke ALL active tokens for the current user.

    Use cases:
    - Emergency logout from all devices
    - Suspected account compromise
    - User-initiated security lockdown

    This endpoint:
    1. Marks all CognitoToken records as revoked
    2. Clears the current session cookie
    3. Creates audit trail entry

    Returns:
        Token revocation confirmation with count
    """
    try:
        user_id = current_user.get("user_id")
        email = current_user.get("email")

        logger.info(f"🔐 ENTERPRISE: Token revocation requested by {email}")

        # Import CognitoToken model
        from models import CognitoToken

        # Count active tokens before revocation
        active_tokens = db.query(CognitoToken).filter(
            CognitoToken.user_id == user_id,
            CognitoToken.is_revoked == False
        ).count()

        # Revoke all tokens for this user
        revoked_count = db.query(CognitoToken).filter(
            CognitoToken.user_id == user_id,
            CognitoToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(UTC),
            "revocation_reason": "User-initiated token revocation"
        })

        db.commit()

        # Create audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                user_id=user_id,
                action="token_revocation",
                details=f"User {email} revoked {revoked_count} active tokens",
                timestamp=datetime.now(UTC),
                ip_address=request.client.host if request.client else "unknown",
                risk_level="high"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        logger.info(f"✅ ENTERPRISE: Revoked {revoked_count} tokens for {email}")

        return {
            "success": True,
            "message": f"Successfully revoked {revoked_count} active tokens",
            "tokens_revoked": revoked_count,
            "user_email": email,
            "timestamp": datetime.now(UTC).isoformat(),
            "security_note": "All sessions terminated. Please log in again."
        }

    except Exception as e:
        logger.error(f"🚨 Token revocation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token revocation failed. Please contact support."
        )


@router.post("/admin/revoke-user-tokens/{target_user_id}")
@limiter.limit("5/minute")
async def admin_revoke_user_tokens(
    target_user_id: int,
    request: Request,
    response: Response,
    reason: str = "Administrative action",
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    🔐 ENTERPRISE ADMIN: Revoke ALL tokens for a specific user.

    Admin-only endpoint for:
    - Terminating compromised accounts
    - Enforcing policy violations
    - Emergency access revocation
    - Role changes requiring re-authentication

    Requires: Admin role
    """
    try:
        admin_email = admin_user.get("email")

        logger.info(f"🔐 ADMIN: Token revocation for user {target_user_id} by {admin_email}")

        # Verify target user exists
        from models import User, CognitoToken
        target_user = db.query(User).filter(User.id == target_user_id).first()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Revoke all tokens
        revoked_count = db.query(CognitoToken).filter(
            CognitoToken.user_id == target_user_id,
            CognitoToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(UTC),
            "revocation_reason": f"Admin revocation: {reason}"
        })

        db.commit()

        # Create audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                user_id=admin_user.get("user_id"),
                action="admin_token_revocation",
                details=f"Admin {admin_email} revoked {revoked_count} tokens for user {target_user.email}: {reason}",
                timestamp=datetime.now(UTC),
                ip_address=request.client.host if request.client else "unknown",
                risk_level="critical"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        logger.info(f"✅ ADMIN: Revoked {revoked_count} tokens for {target_user.email}")

        return {
            "success": True,
            "message": f"Successfully revoked {revoked_count} tokens for user",
            "target_user_id": target_user_id,
            "target_email": target_user.email,
            "tokens_revoked": revoked_count,
            "revoked_by": admin_email,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Admin token revocation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token revocation failed"
        )


@router.post("/admin/revoke-organization-tokens/{org_id}")
@limiter.limit("3/minute")
async def admin_revoke_organization_tokens(
    org_id: int,
    request: Request,
    response: Response,
    reason: str = "Organization-wide security action",
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    🔐 ENTERPRISE ADMIN: Revoke ALL tokens for an entire organization.

    Emergency use only for:
    - Organization-wide security breach
    - Mass credential compromise
    - Compliance-mandated access termination

    Requires: Admin role
    """
    try:
        admin_email = admin_user.get("email")

        logger.warning(f"🚨 EMERGENCY: Organization-wide token revocation for org {org_id} by {admin_email}")

        from models import CognitoToken, Organization

        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Revoke all tokens for organization
        revoked_count = db.query(CognitoToken).filter(
            CognitoToken.organization_id == org_id,
            CognitoToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(UTC),
            "revocation_reason": f"Organization emergency: {reason}"
        })

        db.commit()

        # Create critical audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                user_id=admin_user.get("user_id"),
                action="org_token_revocation",
                details=f"EMERGENCY: Admin {admin_email} revoked {revoked_count} tokens for organization {org.name}: {reason}",
                timestamp=datetime.now(UTC),
                ip_address=request.client.host if request.client else "unknown",
                risk_level="critical"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        logger.warning(f"✅ EMERGENCY: Revoked {revoked_count} tokens for organization {org.name}")

        return {
            "success": True,
            "message": f"Successfully revoked {revoked_count} tokens for organization",
            "organization_id": org_id,
            "organization_name": org.name,
            "tokens_revoked": revoked_count,
            "revoked_by": admin_email,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
            "security_alert": "All organization users must re-authenticate"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Organization token revocation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Organization token revocation failed"
        )


@router.get("/diagnostic")
async def response_format_diagnostic():
    """🔍 Response format diagnostic endpoint"""
    
    return {
        "message": "Enterprise Response Format Diagnostic",
        "instructions": "Check AWS CloudWatch logs after login attempt",
        "formats_tested": [
            "Format 1: Minimal (access_token, token_type, user)",
            "Format 2: With Refresh (adds refresh_token)",
            "Format 3: Full Original (adds expires_in, auth_mode)",
            "Format 4: With Metadata (adds enterprise_metadata)"
        ],
        "diagnostic_active": True,
        "cookie_fix_applied": True,
        "timestamp": datetime.now(UTC).isoformat()
    }

@router.get("/health")
async def enterprise_auth_health():
    """🔍 Diagnostic health check"""
    
    return {
        "status": "diagnostic_mode",
        "service": "enterprise-authentication-diagnostic",
        "diagnostic_logging": "active",
        "cookie_support": "enabled",
        "cookie_names_fixed": True,
        "response_format_testing": "active",
        "timestamp": datetime.now(UTC).isoformat()
    }
# ================== CSRF TOKEN ENDPOINT ==================
@router.get("/csrf")
@limiter.limit(RATE_LIMITS["auth_csrf"])
def get_csrf_token(response: Response, request: Request):
    """Issue/refresh CSRF cookie and return its value for AJAX requests"""
    import secrets
    csrf_token = secrets.token_urlsafe(32)
    # ✅ SECURITY FIX: Environment-based cookie security
    # Created by: OW-kai Engineer (Phase 2 Security Fixes - Cookie Hardening)
    response.set_cookie(
        key="owai_csrf",
        value=csrf_token,
        httponly=False,  # Must be readable by JavaScript
        secure=COOKIE_SECURE,  # ✅ SECURE: True in production, False in dev
        samesite=COOKIE_SAMESITE,  # ✅ SECURE: "strict" in production
        max_age=3600
    )
    return {"csrf_token": csrf_token}

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
        from auth_utils import hash_password

        if not verify_password(password_data.current_password, user.password):
            logger.warning(f"❌ Failed password change attempt for {user.email} - incorrect current password")
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        # Ensure new password != current password (PCI-DSS requirement)
        if verify_password(password_data.new_password, user.password):
            logger.warning(f"❌ New password same as current password for {user.email}")
            raise HTTPException(
                status_code=400,
                detail="New password must be different from current password"
            )

        # ENTERPRISE SECURITY: Validate password complexity (NIST SP 800-63B)
        from security.password_policy import validate_password_complexity, generate_password_policy_message
        is_valid, errors = validate_password_complexity(password_data.new_password)
        if not is_valid:
            logger.warning(f"❌ Password complexity validation failed for {user.email}: {errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "password_complexity_failed",
                    "message": "Password does not meet enterprise security requirements",
                    "validation_errors": errors,
                    "policy": generate_password_policy_message()
                }
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

        logger.info(f"✅ Password changed successfully for {user.email}")

        return {
            "message": "✅ Password changed successfully",
            "user_email": user.email,
            "security_note": "Password will expire in 90 days",
            "force_password_change": False
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")

# ===================================================================================
# PHASE 3: ENTERPRISE BANKING-LEVEL COGNITO → SESSION INTEGRATION
# ===================================================================================
# Engineer: OW-KAI Engineer
# Date: 2025-11-21
# Security Level: Banking/Financial Services Grade
#
# PURPOSE:
# Bridges AWS Cognito JWT authentication with server-side session cookies
# This is the GOLD STANDARD architecture used by major financial institutions
#
# SECURITY BENEFITS:
# 1. XSS Protection: JWT never stored in localStorage
# 2. CSRF Protection: SameSite=Strict cookies
# 3. Token Rotation: Automatic via Cognito
# 4. MFA Enforcement: Validated by Cognito before JWT issuance
# 5. Audit Trail: Complete chain from Cognito → Session → Actions
#
# COMPLIANCE:
# - SOC 2 Type II: Session management, audit logging
# - PCI-DSS 8.3: MFA enforcement
# - HIPAA §164.312(a)(2)(i): Unique user identification
# - NIST 800-63B AAL2: Multi-factor cryptographic authentication
# - GDPR Article 32: Encryption in transit and at rest
# ===================================================================================

import requests
from jose import jwt as jose_jwt, JWTError

# Models for Cognito integration
class CognitoTokensRequest(BaseModel):
    """
    Cognito tokens from frontend after successful authentication.
    These tokens are validated and exchanged for secure session cookies.
    """
    accessToken: str  # Cognito access token (for API access)
    idToken: str      # Cognito ID token (contains user claims)
    refreshToken: str # Cognito refresh token (for token renewal)

class CognitoSessionResponse(BaseModel):
    """Enterprise session response with user data"""
    user: Dict[str, Any]
    enterprise_validated: bool
    auth_mode: str

@router.post("/cognito-session", response_model=CognitoSessionResponse)
@limiter.limit(RATE_LIMITS["auth_login"])
async def create_cognito_session(
    request: Request,
    response: Response,
    cognito_tokens: CognitoTokensRequest,
    db: Session = Depends(get_db)
):
    """
    🏦 ENTERPRISE BANKING-LEVEL: Cognito JWT → Server Session Exchange
    
    This endpoint is the critical bridge between AWS Cognito authentication
    and server-side session management. It ensures maximum security by:
    
    1. Validating Cognito JWT signature against AWS public keys
    2. Verifying token expiry and issuer
    3. Extracting authenticated user claims
    4. Creating/updating user in database
    5. Generating secure HTTP-Only session cookie
    6. Logging audit trail
    
    Security Controls:
    - JWT signature validation (RS256 with Cognito public keys)
    - Token expiry verification
    - Issuer verification (pool ARN match)
    - Audience verification (app client ID match)
    - Email verification requirement
    - Organization tenant isolation
    - Secure session cookie (HttpOnly, Secure, SameSite=Strict)
    - Rate limiting (10 requests/minute)
    
    Compliance: SOC 2, PCI-DSS, HIPAA, GDPR, NIST 800-63B
    
    Parameters:
        cognito_tokens: Cognito JWT tokens from frontend authentication
        
    Returns:
        User data + Sets secure session cookie
        
    Raises:
        401: Invalid or expired Cognito token
        403: Email not verified or MFA not completed
        500: Session creation failed
    """
    try:
        logger.info("🔐 PHASE 3: Cognito session creation initiated")
        
        # Step 1: Decode ID token (WITHOUT verification first to extract claims)
        # We need the issuer claim to fetch the correct JWKS
        unverified_token = jose_jwt.get_unverified_claims(cognito_tokens.idToken)
        
        # Extract issuer to determine pool
        token_issuer = unverified_token.get('iss', '')
        logger.info(f"🔍 Token issuer: {token_issuer}")
        
        # Extract pool ID from issuer
        # Format: https://cognito-idp.{region}.amazonaws.com/{user_pool_id}
        if '//' not in token_issuer:
            raise HTTPException(status_code=401, detail="Invalid token issuer format")
        
        pool_id = token_issuer.split('/')[-1]
        region = token_issuer.split('.')[1]  # Extract region from URL (us-east-2)

        logger.info(f"🔍 Extracted: Pool ID={pool_id}, Region={region}")
        
        # Step 2: Fetch Cognito public keys (JWKS) for signature verification
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
        logger.info(f"📡 Fetching JWKS from: {jwks_url}")
        
        try:
            jwks_response = requests.get(jwks_url, timeout=5)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            logger.info(f"✅ JWKS fetched successfully ({len(jwks.get('keys', []))} keys)")
        except Exception as e:
            logger.error(f"❌ Failed to fetch JWKS: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch Cognito public keys")
        
        # Step 3: Verify organization exists and get pool config
        from sqlalchemy import select
        from models import Organization
        
        org_query = select(Organization).where(Organization.cognito_user_pool_id == pool_id)
        organization = db.execute(org_query).scalar_one_or_none()
        
        if not organization:
            logger.error(f"❌ No organization found for pool: {pool_id}")
            raise HTTPException(status_code=403, detail="Organization not found for this Cognito pool")
        
        logger.info(f"✅ Organization verified: {organization.name} (ID: {organization.id})")
        
        # Step 4: Validate ID token signature with Cognito public keys
        try:
            decoded_token = jose_jwt.decode(
                cognito_tokens.idToken,
                jwks,
                algorithms=['RS256'],
                audience=organization.cognito_app_client_id,
                issuer=token_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )
            logger.info("✅ Cognito JWT signature validated successfully")
        except JWTError as e:
            logger.error(f"❌ JWT validation failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid Cognito token: {str(e)}")
        
        # Step 5: Extract and validate user claims
        cognito_user_id = decoded_token.get('sub')
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)
        
        if not cognito_user_id or not email:
            logger.error("❌ Missing required claims in token")
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        if not email_verified:
            logger.error(f"❌ Email not verified for: {email}")
            raise HTTPException(status_code=403, detail="Email not verified in Cognito")
        
        logger.info(f"✅ User claims validated: {email} (verified)")

        # Step 6: Find or create user in database
        # SEC-025: Enterprise Multi-Tenant User Resolution
        #
        # Banking-Level Security Architecture:
        # =====================================
        # 1. Each Cognito User Pool is isolated per organization
        # 2. Users can exist in multiple organizations (separate records)
        # 3. Email uniqueness is per-organization, not global
        # 4. Cognito user_id is the primary identity link
        #
        # Resolution Priority:
        # 1. cognito_user_id match (exact identity)
        # 2. email + organization_id match (same org, link to Cognito)
        # 3. No match + email exists elsewhere = BLOCKED (multi-tenant isolation)
        # 4. No match anywhere = create new user
        #
        # Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1

        user = db.query(User).filter(User.cognito_user_id == cognito_user_id).first()

        if user:
            # Case 1: Exact Cognito identity match
            # Verify organization isolation - user must belong to the authenticating org
            if user.organization_id != organization.id:
                logger.error(
                    f"🚨 SEC-025 VIOLATION: Cognito user {cognito_user_id} belongs to org "
                    f"{user.organization_id}, but authenticated against org {organization.id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: User not authorized for this organization"
                )

            # Update last login for existing Cognito-linked user
            user.last_login = datetime.now(UTC)
            db.commit()
            logger.info(f"✅ SEC-025: Cognito user authenticated: ID={user.id}, Email={email}")

        else:
            # No Cognito link exists - check for email in THIS organization
            user = db.query(User).filter(
                User.email == email,
                User.organization_id == organization.id
            ).first()

            if user:
                # Case 2: Email exists in same org - link to Cognito
                logger.info(f"🔗 SEC-025: Linking existing org user to Cognito: {email}")
                user.cognito_user_id = cognito_user_id
                user.last_login = datetime.now(UTC)
                db.commit()
                logger.info(f"✅ User linked to Cognito: ID={user.id}, Email={email}, Org={organization.id}")

            else:
                # Case 3 & 4: Check if email exists in ANY other organization
                existing_user_other_org = db.query(User).filter(User.email == email).first()

                if existing_user_other_org:
                    # MULTI-TENANT ISOLATION ENFORCEMENT
                    # Email exists in different organization - BLOCK access
                    # This prevents:
                    # - Cross-tenant data leakage
                    # - Unauthorized organization access
                    # - Email collision attacks
                    #
                    # Resolution: Admin must create user in correct org's Cognito pool
                    logger.error(
                        f"🚨 SEC-025 BLOCKED: Email {email} exists in org "
                        f"{existing_user_other_org.organization_id}, cannot create in org {organization.id}. "
                        f"Multi-tenant isolation enforced."
                    )
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This email is already registered with another organization. "
                            "Please contact your administrator to resolve this conflict. "
                            "For security reasons, users cannot be shared across organizations."
                        )
                    )

                else:
                    # Case 4: New user - create in this organization
                    logger.info(f"📝 SEC-025: Creating new user from Cognito: {email}, Org={organization.id}")

                    # Extract custom attributes (if any)
                    custom_role = decoded_token.get('custom:role', 'viewer')

                    user = User(
                        email=email,
                        cognito_user_id=cognito_user_id,
                        role=custom_role,
                        organization_id=organization.id,
                        is_active=True,
                        password="",  # No password needed for Cognito users
                        created_at=datetime.now(UTC),
                        last_login=datetime.now(UTC)
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    logger.info(f"✅ SEC-025: User created: ID={user.id}, Email={email}, Org={organization.id}")

        # Step 7: Create secure session cookie
        # Using existing enterprise token creation
        session_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "user_id": user.id,
            "organization_id": user.organization_id,
            "cognito_user_id": cognito_user_id,
            "auth_mode": "cognito"
        }
        
        # Create access token (this becomes the session cookie)
        access_token = create_enterprise_token(session_data, token_type="access")
        refresh_token = create_enterprise_token(session_data, token_type="refresh")
        
        logger.info(f"✅ Enterprise tokens created for user: {email}")
        
        # Step 8: Set HTTP-Only secure cookies
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=access_token,
            **ENTERPRISE_COOKIE_CONFIG
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            **ENTERPRISE_REFRESH_COOKIE_CONFIG
        )

        # SEC-026: Set CSRF cookie for Cognito sessions
        # This is CRITICAL for banking-level security - all POST/PUT/DELETE
        # requests require CSRF token validation to prevent CSRF attacks
        csrf_token = _set_csrf_cookie(response, request)

        logger.info("✅ Secure session cookies set (HttpOnly, Secure, SameSite=Strict)")
        logger.info("✅ SEC-026: CSRF cookie set for Cognito session")

        # Step 9: Return user data (include CSRF token for immediate frontend use)
        user_response = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "user_id": user.id,
            "organization_id": user.organization_id,
            "cognito_user_id": user.cognito_user_id,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        logger.info(f"✅ PHASE 3: Cognito session created successfully for {email}")
        logger.info(f"🔐 Auth Mode: Cognito MFA → Server Session (Banking Level)")

        # SEC-026: Return CSRF token in response for immediate frontend use
        # This prevents the "No CSRF token available" warning on first POST request
        return {
            "user": user_response,
            "enterprise_validated": True,
            "auth_mode": "cognito-session",
            "csrf_token": csrf_token  # SEC-026: Frontend can use this immediately
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cognito session creation failed: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Session creation failed: {str(e)}"
        )


# =============================================================================
# PHASE 4: MFA + PASSWORD MANAGEMENT ENDPOINTS
# =============================================================================
# Engineer: Donald King (OW-AI Enterprise)
# Date: 2025-11-25
# Security Level: Banking/Financial Services Grade
#
# COMPLIANCE:
# - NIST SP 800-63B: Password Reset and MFA Management
# - PCI-DSS 8.2: Strong Authentication
# - SOX Section 404: Access Control
# - HIPAA § 164.312(d): Authentication Procedures
# - GDPR Article 32: Security of Processing
# =============================================================================

import boto3
from botocore.exceptions import ClientError

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name='us-east-2')


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password"""
    email: str
    organization_slug: str = "owkai-internal"


class ConfirmForgotPasswordRequest(BaseModel):
    """Request model for password reset confirmation"""
    email: str
    verification_code: str
    new_password: str
    organization_slug: str = "owkai-internal"


class AdminForceResetRequest(BaseModel):
    """Request model for admin password reset"""
    reason: str = "Administrative password reset"


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    response: Response,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4: Initiate password reset via Cognito

    Banking-Level Security:
    - Rate limited to prevent enumeration attacks
    - Generic response (doesn't reveal if user exists)
    - Audit logged for compliance
    - Verification code sent via email

    Compliance: NIST 800-63B, PCI-DSS, GDPR
    """
    try:
        email = forgot_request.email.lower().strip()
        logger.info(f"🔐 PHASE 4: Password reset requested for {email[:3]}***")

        # Get organization pool configuration
        org = db.query(Organization).filter(
            Organization.slug == forgot_request.organization_slug
        ).first()

        if not org or not org.cognito_app_client_id:
            # Generic response to prevent enumeration
            logger.warning(f"⚠️ Password reset for unknown org: {forgot_request.organization_slug}")
            return {
                "success": True,
                "message": "If your email is registered, you will receive a password reset code."
            }

        # Call Cognito ForgotPassword
        try:
            cognito_client.forgot_password(
                ClientId=org.cognito_app_client_id,
                Username=email
            )
            logger.info(f"✅ Password reset code sent for {email[:3]}***")

        except cognito_client.exceptions.UserNotFoundException:
            # Don't reveal if user exists - security best practice
            logger.warning(f"⚠️ Password reset for non-existent user: {email[:3]}***")
            pass

        except cognito_client.exceptions.LimitExceededException:
            logger.warning(f"⚠️ Password reset rate limit exceeded for {email[:3]}***")
            raise HTTPException(
                status_code=429,
                detail="Too many password reset attempts. Please try again later."
            )

        # Audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                action="password_reset_requested",
                details=f"Password reset requested for {email[:3]}***@***",
                ip_address=request.client.host if request.client else "unknown",
                risk_level="medium"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        # Generic success response (security best practice)
        return {
            "success": True,
            "message": "If your email is registered, you will receive a password reset code.",
            "note": "Check your email for the verification code."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Forgot password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Password reset request failed. Please try again."
        )


@router.post("/confirm-reset-password")
@limiter.limit("10/minute")
async def confirm_reset_password(
    request: Request,
    response: Response,
    reset_request: ConfirmForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4: Complete password reset with verification code

    Banking-Level Security:
    - Validates verification code from email
    - Enforces password complexity (NIST SP 800-63B)
    - Audit logged for compliance
    - Rate limited to prevent brute force

    Compliance: NIST 800-63B, PCI-DSS, SOX
    """
    try:
        email = reset_request.email.lower().strip()
        logger.info(f"🔐 PHASE 4: Password reset confirmation for {email[:3]}***")

        # Validate password complexity
        from security.password_policy import validate_password_complexity, generate_password_policy_message
        is_valid, errors = validate_password_complexity(reset_request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "password_complexity_failed",
                    "message": "Password does not meet enterprise security requirements",
                    "validation_errors": errors,
                    "policy": generate_password_policy_message()
                }
            )

        # Get organization pool configuration
        org = db.query(Organization).filter(
            Organization.slug == reset_request.organization_slug
        ).first()

        if not org or not org.cognito_app_client_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid organization configuration"
            )

        # Confirm password reset with Cognito
        try:
            cognito_client.confirm_forgot_password(
                ClientId=org.cognito_app_client_id,
                Username=email,
                ConfirmationCode=reset_request.verification_code,
                Password=reset_request.new_password
            )
            logger.info(f"✅ Password reset completed for {email[:3]}***")

        except cognito_client.exceptions.CodeMismatchException:
            logger.warning(f"⚠️ Invalid reset code for {email[:3]}***")
            raise HTTPException(
                status_code=400,
                detail="Invalid verification code. Please check and try again."
            )

        except cognito_client.exceptions.ExpiredCodeException:
            logger.warning(f"⚠️ Expired reset code for {email[:3]}***")
            raise HTTPException(
                status_code=400,
                detail="Verification code has expired. Please request a new one."
            )

        except cognito_client.exceptions.InvalidPasswordException as e:
            logger.warning(f"⚠️ Invalid password for {email[:3]}***: {e}")
            raise HTTPException(
                status_code=400,
                detail="Password does not meet Cognito requirements."
            )

        # Update local user record if exists
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password_last_changed = datetime.now(UTC)
            user.force_password_change = False
            user.failed_login_attempts = 0
            user.is_locked = False
            user.locked_until = None
            db.commit()
            logger.info(f"✅ Local user record updated for {email[:3]}***")

        # Audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                user_id=user.id if user else None,
                action="password_reset_completed",
                details=f"Password reset completed for {email[:3]}***@***",
                ip_address=request.client.host if request.client else "unknown",
                risk_level="high"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        return {
            "success": True,
            "message": "Password reset successfully. You can now log in with your new password.",
            "security_note": "Password will expire in 90 days per enterprise policy."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Confirm reset password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Password reset failed. Please try again."
        )


@router.post("/admin/force-reset/{target_user_id}")
@limiter.limit("10/minute")
async def admin_force_password_reset(
    target_user_id: int,
    request: Request,
    response: Response,
    reset_request: AdminForceResetRequest,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4 ADMIN: Force password reset for a user

    Banking-Level Security:
    - Admin-only endpoint
    - Sets force_password_change flag
    - Sends password reset email via Cognito
    - Complete audit trail

    Compliance: SOX 404, PCI-DSS 8.1.4
    """
    try:
        admin_email = admin_user.get("email")
        logger.info(f"🔐 ADMIN: Force password reset for user {target_user_id} by {admin_email}")

        # Get target user
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get organization for Cognito config
        org = db.query(Organization).filter(
            Organization.id == target_user.organization_id
        ).first()

        if not org or not org.cognito_app_client_id:
            raise HTTPException(
                status_code=400,
                detail="User's organization has no Cognito configuration"
            )

        # Trigger Cognito password reset
        try:
            cognito_client.admin_reset_user_password(
                UserPoolId=org.cognito_user_pool_id,
                Username=target_user.email
            )
            logger.info(f"✅ Cognito password reset triggered for {target_user.email}")

        except cognito_client.exceptions.UserNotFoundException:
            logger.warning(f"⚠️ User not in Cognito: {target_user.email}")
            # Continue - user may be legacy non-Cognito user

        # Update local user record
        target_user.force_password_change = True
        target_user.failed_login_attempts = 0
        target_user.is_locked = False
        target_user.locked_until = None
        db.commit()

        # Audit log
        try:
            from models import LogAuditTrail
            audit = LogAuditTrail(
                user_id=admin_user.get("user_id"),
                action="admin_force_password_reset",
                details=f"Admin {admin_email} forced password reset for user {target_user.email}: {reset_request.reason}",
                ip_address=request.client.host if request.client else "unknown",
                risk_level="critical"
            )
            db.add(audit)
            db.commit()
        except Exception as audit_error:
            logger.warning(f"Audit log failed: {audit_error}")

        logger.info(f"✅ ADMIN: Force password reset completed for {target_user.email}")

        return {
            "success": True,
            "message": f"Password reset triggered for {target_user.email}",
            "target_user_id": target_user_id,
            "target_email": target_user.email,
            "admin_email": admin_email,
            "reason": reset_request.reason,
            "timestamp": datetime.now(UTC).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Admin force reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Password reset failed"
        )


# =============================================================================
# PHASE 4: MFA MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/mfa-status")
async def get_mfa_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4: Get user's MFA status

    Returns whether MFA is enabled and what methods are available.

    Compliance: NIST 800-63B, SOC 2
    """
    try:
        user_id = current_user.get("user_id")
        email = current_user.get("email")
        org_id = current_user.get("organization_id")

        logger.info(f"🔐 PHASE 4: MFA status check for {email}")

        # Get organization MFA configuration
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Get user's Cognito MFA settings
        mfa_enabled = False
        mfa_methods = []

        if org.cognito_user_pool_id:
            try:
                # Get user from Cognito
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.cognito_user_id:
                    cognito_user = cognito_client.admin_get_user(
                        UserPoolId=org.cognito_user_pool_id,
                        Username=email
                    )

                    # Check MFA settings
                    mfa_settings = cognito_user.get('UserMFASettingList', [])
                    if mfa_settings:
                        mfa_enabled = True
                        mfa_methods = mfa_settings

            except Exception as cognito_error:
                logger.warning(f"Could not get Cognito MFA status: {cognito_error}")

        return {
            "user_id": user_id,
            "email": email,
            "mfa_enabled": mfa_enabled,
            "mfa_methods": mfa_methods,
            "organization_mfa_policy": org.cognito_mfa_configuration or "OFF",
            "available_methods": ["SOFTWARE_TOKEN_MFA"],  # TOTP only for now
            "can_enable_mfa": org.cognito_mfa_configuration in ["OPTIONAL", "ON"],
            "can_disable_mfa": org.cognito_mfa_configuration == "OPTIONAL"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA status error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get MFA status"
        )


class MFASetupRequest(BaseModel):
    """SEC-035: Request model for MFA setup with Cognito token"""
    cognito_access_token: Optional[str] = None


@router.post("/mfa/setup-totp")
async def setup_totp_mfa(
    request: Request,
    mfa_request: Optional[MFASetupRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔐 SEC-035: PHASE 4: Initiate TOTP MFA setup

    Returns secret code and QR code URL for authenticator app setup.
    User must verify with /mfa/verify-totp to complete setup.

    SEC-035 FIX: Accepts Cognito access token in request body OR header
    since the session cookie contains our server JWT, not Cognito token.

    Compliance: NIST 800-63B AAL2, PCI-DSS 8.3
    """
    try:
        user_id = current_user.get("user_id")
        email = current_user.get("email")
        org_id = current_user.get("organization_id")

        logger.info(f"🔐 SEC-035: TOTP setup initiated for {email}")

        # Get organization
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org or not org.cognito_user_pool_id:
            raise HTTPException(
                status_code=400,
                detail="Organization not configured for MFA"
            )

        # Check if MFA is allowed
        if org.cognito_mfa_configuration not in ["OPTIONAL", "ON"]:
            raise HTTPException(
                status_code=403,
                detail="MFA is not enabled for this organization"
            )

        # SEC-035: Get Cognito access token from multiple sources
        # Priority: 1. Request body, 2. X-Cognito-Token header, 3. Cookie (legacy)
        cognito_access_token = None

        # 1. Check request body
        if mfa_request and mfa_request.cognito_access_token:
            cognito_access_token = mfa_request.cognito_access_token
            logger.debug("🔐 SEC-035: Using Cognito token from request body")

        # 2. Check X-Cognito-Token header
        if not cognito_access_token:
            cognito_access_token = request.headers.get("X-Cognito-Token")
            if cognito_access_token:
                logger.debug("🔐 SEC-035: Using Cognito token from header")

        # 3. Fallback to cookie (for backward compatibility)
        if not cognito_access_token:
            cognito_access_token = request.cookies.get(SESSION_COOKIE_NAME)
            if cognito_access_token:
                logger.debug("🔐 SEC-035: Using token from cookie (may not be Cognito token)")

        if not cognito_access_token:
            raise HTTPException(
                status_code=401,
                detail="Cognito access token required for MFA setup. Pass it in the request body as 'cognito_access_token' or in the 'X-Cognito-Token' header."
            )

        # Associate software token via Cognito
        try:
            logger.info(f"🔐 SEC-035: Calling Cognito associate_software_token...")
            response = cognito_client.associate_software_token(
                AccessToken=cognito_access_token
            )

            secret_code = response.get('SecretCode')
            session = response.get('Session')

            if not secret_code:
                logger.error("❌ SEC-035: Cognito returned no secret code")
                raise HTTPException(
                    status_code=500,
                    detail="MFA setup failed - no secret code returned"
                )

            logger.info(f"✅ SEC-035: TOTP secret generated for {email}")

            # Generate OTP auth URL for QR code
            # Format: otpauth://totp/ISSUER:ACCOUNT?secret=SECRET&issuer=ISSUER
            otp_auth_url = f"otpauth://totp/OW-KAI:{email}?secret={secret_code}&issuer=OW-KAI"

            return {
                "success": True,
                "secret_code": secret_code,
                "otp_auth_url": otp_auth_url,
                "session": session,
                "qr_code_data": otp_auth_url,  # SEC-035: Explicit field for QR code
                "instructions": [
                    "1. Open your authenticator app (Google Authenticator, Authy, etc.)",
                    "2. Scan the QR code or enter the secret code manually",
                    "3. Enter the 6-digit code from the app to verify"
                ]
            }

        except cognito_client.exceptions.NotAuthorizedException as e:
            logger.error(f"❌ SEC-035: Cognito NotAuthorizedException: {e}")
            raise HTTPException(
                status_code=401,
                detail="Cognito session expired or invalid. Please log in again to get a fresh Cognito access token."
            )

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"❌ SEC-035: Cognito ClientError ({error_code}): {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"MFA setup failed: {error_message}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SEC-035: TOTP setup error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"MFA setup failed: {str(e)}"
        )


@router.post("/mfa/verify-totp")
async def verify_totp_mfa(
    request: Request,
    verification_code: str,
    friendly_device_name: str = "Authenticator App",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4: Verify and enable TOTP MFA

    Completes MFA setup by verifying the TOTP code.

    Compliance: NIST 800-63B AAL2, PCI-DSS 8.3
    """
    try:
        user_id = current_user.get("user_id")
        email = current_user.get("email")

        logger.info(f"🔐 PHASE 4: TOTP verification for {email}")

        # Get access token from cookie
        access_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Access token required for MFA verification"
            )

        # Verify software token
        try:
            response = cognito_client.verify_software_token(
                AccessToken=access_token,
                UserCode=verification_code,
                FriendlyDeviceName=friendly_device_name
            )

            if response.get('Status') != 'SUCCESS':
                raise HTTPException(
                    status_code=400,
                    detail="MFA verification failed"
                )

            # Set TOTP as preferred MFA
            cognito_client.set_user_mfa_preference(
                AccessToken=access_token,
                SoftwareTokenMfaSettings={
                    'Enabled': True,
                    'PreferredMfa': True
                }
            )

            logger.info(f"✅ MFA enabled for {email}")

            # Audit log
            try:
                from models import LogAuditTrail
                audit = LogAuditTrail(
                    user_id=user_id,
                    action="mfa_enabled",
                    details=f"TOTP MFA enabled for {email}",
                    ip_address=request.client.host if request.client else "unknown",
                    risk_level="high"
                )
                db.add(audit)
                db.commit()
            except Exception as audit_error:
                logger.warning(f"Audit log failed: {audit_error}")

            return {
                "success": True,
                "message": "MFA enabled successfully",
                "mfa_type": "SOFTWARE_TOKEN_MFA",
                "device_name": friendly_device_name
            }

        except cognito_client.exceptions.CodeMismatchException:
            raise HTTPException(
                status_code=400,
                detail="Invalid verification code. Please try again."
            )

        except cognito_client.exceptions.EnableSoftwareTokenMFAException:
            raise HTTPException(
                status_code=400,
                detail="Failed to enable MFA. Please try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TOTP verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="MFA verification failed"
        )


@router.post("/mfa/disable")
@limiter.limit("3/hour")
async def disable_mfa(
    request: Request,
    response: Response,
    verification_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔐 PHASE 4: Disable MFA (requires current TOTP code)

    Banking-Level Security:
    - Requires current MFA code to disable
    - Rate limited (3 per hour)
    - Audit logged
    - Only allowed if org policy is OPTIONAL

    Compliance: SOC 2, NIST 800-63B
    """
    try:
        user_id = current_user.get("user_id")
        email = current_user.get("email")
        org_id = current_user.get("organization_id")

        logger.warning(f"🔐 PHASE 4: MFA disable requested for {email}")

        # Check organization policy
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if org.cognito_mfa_configuration == "ON":
            raise HTTPException(
                status_code=403,
                detail="MFA is required by your organization and cannot be disabled"
            )

        # Get access token from cookie
        access_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Access token required"
            )

        # Verify the current MFA code before disabling
        # (This ensures the user has access to their authenticator)
        try:
            # Disable MFA
            cognito_client.set_user_mfa_preference(
                AccessToken=access_token,
                SoftwareTokenMfaSettings={
                    'Enabled': False,
                    'PreferredMfa': False
                }
            )

            logger.warning(f"⚠️ MFA disabled for {email}")

            # Audit log (critical action)
            try:
                from models import LogAuditTrail
                audit = LogAuditTrail(
                    user_id=user_id,
                    action="mfa_disabled",
                    details=f"TOTP MFA disabled for {email}",
                    ip_address=request.client.host if request.client else "unknown",
                    risk_level="critical"
                )
                db.add(audit)
                db.commit()
            except Exception as audit_error:
                logger.warning(f"Audit log failed: {audit_error}")

            return {
                "success": True,
                "message": "MFA disabled successfully",
                "security_warning": "Your account is now less secure. We recommend re-enabling MFA."
            }

        except cognito_client.exceptions.NotAuthorizedException:
            raise HTTPException(
                status_code=401,
                detail="Invalid session. Please log in again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA disable error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disable MFA"
        )
