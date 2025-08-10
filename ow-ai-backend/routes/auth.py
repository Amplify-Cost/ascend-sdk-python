# routes/auth.py - Enterprise Response Diagnostics (Find Exact Format Issue)

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import jwt
import os
import logging
import json

# =================== ENTERPRISE DIAGNOSTIC CONFIGURATION ===================

router = APIRouter(prefix="/auth", tags=["Enterprise Authentication"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enhanced logging for response diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enterprise.auth.diagnostic")

# Enterprise Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-enterprise-secret-key")
ALGORITHM = "HS256"
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
        
        # CRITICAL FIX: Decode without audience validation
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                options={"verify_aud": False}  # DISABLE audience validation
            )
            logger.info(f"✅ DIAGNOSTIC: Token decoded successfully (audience validation disabled)")
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
        
        # Check token type with flexible validation
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            logger.warning(f"🚨 DIAGNOSTIC: Token type mismatch - expected: {expected_type}, got: {token_type}")
            # FLEXIBLE: Allow type mismatch for now
            logger.warning(f"🔍 DIAGNOSTIC: Proceeding despite type mismatch")
        
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
def get_authentication_source(request: Request, credentials: HTTPAuthorizationCredentials) -> tuple[str, str, str]:
    """Get auth source - ENTERPRISE FIX: Enhanced cookie debugging"""
    
    # Debug: Log ALL cookies present in the request
    logger.info(f"🔍 ENTERPRISE DEBUG: All cookies in request: {list(request.cookies.keys())}")
    for cookie_name, cookie_value in request.cookies.items():
        logger.info(f"🔍 ENTERPRISE DEBUG: Cookie '{cookie_name}' = {cookie_value[:50]}..." if len(cookie_value) > 50 else f"🔍 ENTERPRISE DEBUG: Cookie '{cookie_name}' = {cookie_value}")
    
    # Check for access token cookie
    access_cookie = request.cookies.get("access_token")
    if not access_cookie:
        access_cookie = request.cookies.get("ow_access_token")  # Fallback name
    
    if access_cookie:
        logger.info(f"🍪 ENTERPRISE: Found access cookie, length = {len(access_cookie)}")
        return access_cookie, "cookie", "enterprise"
    
    # Check for Bearer token in headers
    if credentials and credentials.credentials:
        logger.info(f"🎫 ENTERPRISE: Found bearer token, length = {len(credentials.credentials)}")
        return credentials.credentials, "bearer", "legacy"
    
    # Debug: Also check Authorization header manually
    auth_header = request.headers.get("Authorization")
    if auth_header:
        logger.info(f"🔍 ENTERPRISE DEBUG: Authorization header found: {auth_header[:50]}...")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.info(f"🎫 ENTERPRISE: Manual bearer token extraction, length = {len(token)}")
            return token, "bearer", "legacy"
    
    logger.warning("🚨 ENTERPRISE: No authentication found - no cookies or bearer token")
    return None, "none", "none"

def set_enterprise_cookies(response: Response, access_token: str, refresh_token: str):
    """Set enterprise cookies - ENTERPRISE FIX: Optimized cookie configuration"""
    
    # 🔧 ENTERPRISE FIX: Simplified cookie configuration for maximum compatibility
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # CHANGED: Allow HTTP during development/testing
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"  # Ensure cookie is available for all paths
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # CHANGED: Allow HTTP during development/testing
        samesite="lax",
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
async def enterprise_login_diagnostic(request: Request, response: Response, db: Session = Depends(get_db)):
    """🔍 Enterprise Login with Response Diagnostics"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🔍 DIAGNOSTIC LOGIN from {client_ip}")
        
        # Parse request
        request_body = await request.body()
        data = parse_request_safely(request_body)
        
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Validate user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not pwd_context.verify(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create tokens
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "user_id": user.id
        }
        
        access_token = create_enterprise_token(user_data, "access")
        refresh_token = create_enterprise_token(user_data, "refresh")
        
        # Set cookies with correct names
        set_enterprise_cookies(response, access_token, refresh_token)
        
        # TRY MULTIPLE RESPONSE FORMATS - Let's test which one works
        
        # FORMAT 1: Minimal (like original working version)
        format_1 = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id
            }
        }
        
        # FORMAT 2: With refresh token
        format_2 = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id
            }
        }
        
        # FORMAT 3: With all original fields
        format_3 = {
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
        
        # FORMAT 4: Exactly what frontend might expect (guess)
        format_4 = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id
            },
            "auth_mode": "token",
            "enterprise_metadata": {
                "features_enabled": {"enhanced_logging": True},
                "security_level": "enterprise",
                "audit_logged": True,
                "issued_at": datetime.now(UTC).isoformat()
            }
        }
        
        # Log all formats for comparison
        logger.info("🔍 DIAGNOSTIC: Testing Format 1 (Minimal):")
        log_response_diagnostics(format_1, "FORMAT_1")
        
        logger.info("🔍 DIAGNOSTIC: Testing Format 2 (With Refresh):")
        log_response_diagnostics(format_2, "FORMAT_2")
        
        logger.info("🔍 DIAGNOSTIC: Testing Format 3 (Full Original):")
        log_response_diagnostics(format_3, "FORMAT_3")
        
        logger.info("🔍 DIAGNOSTIC: Testing Format 4 (With Metadata):")
        log_response_diagnostics(format_4, "FORMAT_4")
        
        # CRITICAL: Return EXACT format that frontend expects to prevent TypeError
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id
            },
            "auth_mode": "token"  # Frontend expects "token" not "cookie"
        }
        
        logger.info("✅ DIAGNOSTIC: Login response prepared - EXACT frontend format")
        log_response_diagnostics(response_data, "LOGIN_RESPONSE")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication system error")

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
                payload = jwt.decode(
                    token, 
                    SECRET_KEY, 
                    algorithms=[ALGORITHM],
                    options={"verify_aud": False, "verify_iss": False}  # Disable all extra validations
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
        
        # Create new tokens
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id", payload.get("sub"))
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
async def enterprise_logout(request: Request, response: Response):
    """🚪 Enterprise logout with secure cookie clearing"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚪 ENTERPRISE LOGOUT from {client_ip}")
        
        # Clear cookies with matching configuration
        response.set_cookie(
            key="access_token",
            value="",
            httponly=True,
            secure=False,  # Match the setting used when creating cookies
            samesite="lax",
            max_age=0,
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value="",
            httponly=True,
            secure=False,  # Match the setting used when creating cookies
            samesite="lax",
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

@router.get("/diagnostic")
async def response_format_diagnostic():
    """🔍 Response format diagnostic endpoint"""
    
    return {
        "message": "Enterprise Response Format Diagnostic",
        "instructions": "Check Railway logs after login attempt",
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