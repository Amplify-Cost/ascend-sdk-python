# routes/auth.py - ENTERPRISE-GRADE Authentication with Production Resilience
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
import jwt
import os
import logging
import json
from typing import Optional, Dict, Any
import traceback
from slowapi import Limiter
from slowapi.util import get_remote_address

# Enterprise Monitoring and Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# Enterprise Configuration
router = APIRouter(prefix="/auth", tags=["Enterprise Authentication"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

# Enterprise Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-enterprise-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Enterprise Cookie Configuration (for gradual rollout)
ENTERPRISE_COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,  # HTTPS only in production
    "samesite": "lax",
    "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    "path": "/",
    "domain": None
}

# Enterprise Feature Flags
ENTERPRISE_FEATURES = {
    "cookie_authentication": False,  # Disabled during emergency fix
    "enhanced_logging": True,
    "rate_limiting": True,
    "audit_trail": True,
    "graceful_degradation": True
}

class EnterpriseAuthError(Exception):
    """Enterprise-specific authentication error with context"""
    def __init__(self, message: str, error_code: str, context: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(self.message)

def enterprise_error_handler(func):
    """Enterprise decorator for comprehensive error handling and monitoring"""
    async def wrapper(*args, **kwargs):
        start_time = datetime.now(UTC)
        try:
            result = await func(*args, **kwargs)
            
            # Enterprise success logging
            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(f"✅ ENTERPRISE SUCCESS: {func.__name__} completed in {duration:.3f}s")
            
            return result
            
        except HTTPException:
            # Re-raise HTTP exceptions (expected errors)
            raise
        except EnterpriseAuthError as e:
            # Enterprise-specific errors
            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.error(f"🏢 ENTERPRISE ERROR: {func.__name__} failed in {duration:.3f}s - {e.error_code}: {e.message}")
            logger.error(f"🔍 ENTERPRISE CONTEXT: {e.context}")
            raise HTTPException(status_code=500, detail=f"Enterprise authentication error: {e.error_code}")
        except Exception as e:
            # Unexpected errors - enterprise resilience
            duration = (datetime.now(UTC) - start_time).total_seconds()
            error_trace = traceback.format_exc()
            logger.critical(f"🚨 ENTERPRISE CRITICAL: {func.__name__} unexpected failure in {duration:.3f}s")
            logger.critical(f"🚨 ERROR TRACE: {error_trace}")
            
            # Enterprise monitoring alert would go here
            # alert_enterprise_monitoring(func.__name__, str(e), error_trace)
            
            raise HTTPException(status_code=500, detail="Enterprise system temporarily unavailable")
    
    return wrapper

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Enterprise JWT token creation with enhanced security"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Enterprise token metadata
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "access",
            "iss": "ow-ai-enterprise",  # Enterprise issuer
            "aud": "ow-ai-platform",    # Enterprise audience
            "jti": f"{data.get('sub', 'unknown')}-{int(datetime.now(UTC).timestamp())}"  # Unique token ID
        })
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"🔐 ENTERPRISE: Access token created for user {data.get('email', 'unknown')}")
        
        return token
        
    except Exception as e:
        logger.error(f"🚨 ENTERPRISE TOKEN CREATION FAILED: {str(e)}")
        raise EnterpriseAuthError(
            "Token creation failed",
            "TOKEN_CREATION_ERROR",
            {"user_id": data.get("sub"), "error": str(e)}
        )

def create_refresh_token(data: dict) -> str:
    """Enterprise refresh token creation with extended security"""
    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
            "iss": "ow-ai-enterprise",
            "aud": "ow-ai-platform",
            "jti": f"refresh-{data.get('sub', 'unknown')}-{int(datetime.now(UTC).timestamp())}"
        })
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"🔐 ENTERPRISE: Refresh token created for user {data.get('email', 'unknown')}")
        
        return token
        
    except Exception as e:
        logger.error(f"🚨 ENTERPRISE REFRESH TOKEN CREATION FAILED: {str(e)}")
        raise EnterpriseAuthError(
            "Refresh token creation failed",
            "REFRESH_TOKEN_CREATION_ERROR",
            {"user_id": data.get("sub"), "error": str(e)}
        )

def validate_enterprise_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Enterprise token validation with comprehensive security checks"""
    try:
        if not token:
            raise EnterpriseAuthError("No token provided", "NO_TOKEN", {})
        
        # Decode with enterprise validation
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            audience="ow-ai-platform",
            issuer="ow-ai-enterprise"
        )
        
        # Enterprise type validation
        if payload.get("type") != expected_type:
            raise EnterpriseAuthError(
                f"Invalid token type: expected {expected_type}, got {payload.get('type')}",
                "INVALID_TOKEN_TYPE",
                {"expected": expected_type, "actual": payload.get("type")}
            )
        
        # Enterprise expiry validation
        if payload.get("exp", 0) < datetime.now(UTC).timestamp():
            raise EnterpriseAuthError(
                "Token expired",
                "TOKEN_EXPIRED",
                {"exp": payload.get("exp"), "now": datetime.now(UTC).timestamp()}
            )
        
        logger.debug(f"✅ ENTERPRISE: Token validated for user {payload.get('email', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        raise EnterpriseAuthError("Token expired", "TOKEN_EXPIRED", {})
    except jwt.InvalidTokenError as e:
        raise EnterpriseAuthError(f"Invalid token: {str(e)}", "INVALID_TOKEN", {"jwt_error": str(e)})
    except EnterpriseAuthError:
        raise
    except Exception as e:
        raise EnterpriseAuthError(f"Token validation failed: {str(e)}", "VALIDATION_ERROR", {"error": str(e)})

def parse_request_body_safely(request_body: bytes) -> Dict[str, Any]:
    """Enterprise-grade request body parsing with comprehensive error handling"""
    try:
        if not request_body:
            logger.warning("🔍 ENTERPRISE: Empty request body received")
            return {}
        
        # Decode bytes to string
        body_str = request_body.decode('utf-8')
        
        if not body_str.strip():
            logger.warning("🔍 ENTERPRISE: Whitespace-only request body")
            return {}
        
        # Parse JSON with enterprise error handling
        data = json.loads(body_str)
        
        logger.debug(f"✅ ENTERPRISE: Request body parsed successfully, keys: {list(data.keys())}")
        return data
        
    except UnicodeDecodeError as e:
        logger.error(f"🚨 ENTERPRISE: Unicode decode error: {str(e)}")
        raise EnterpriseAuthError("Invalid request encoding", "ENCODING_ERROR", {"error": str(e)})
    except json.JSONDecodeError as e:
        logger.error(f"🚨 ENTERPRISE: JSON decode error: {str(e)}")
        logger.error(f"🔍 ENTERPRISE: Raw body (first 200 chars): {request_body[:200]}")
        raise EnterpriseAuthError("Invalid JSON format", "JSON_PARSE_ERROR", {"error": str(e), "position": e.pos})
    except Exception as e:
        logger.error(f"🚨 ENTERPRISE: Unexpected parsing error: {str(e)}")
        raise EnterpriseAuthError("Request parsing failed", "PARSE_ERROR", {"error": str(e)})

@router.post("/token")
@enterprise_error_handler
@limiter.limit("5/minute" if ENTERPRISE_FEATURES["rate_limiting"] else "1000/minute")
async def enterprise_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """🏢 Enterprise login with comprehensive security and monitoring"""
    
    client_ip = get_remote_address(request)
    logger.info(f"🔐 ENTERPRISE LOGIN ATTEMPT: IP {client_ip}")
    
    try:
        # Enterprise request parsing
        request_body = await request.body()
        data = parse_request_body_safely(request_body)
        
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Enterprise input validation
        if not email or not password:
            logger.warning(f"🚨 ENTERPRISE: Invalid login attempt from {client_ip} - missing credentials")
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Enterprise user validation
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"🚨 ENTERPRISE: Login attempt for non-existent user: {email} from {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not pwd_context.verify(password, user.password):
            logger.warning(f"🚨 ENTERPRISE: Invalid password for user: {email} from {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Enterprise token creation
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "user_id": user.id
        }
        
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)
        
        # Enterprise audit logging
        logger.info(f"✅ ENTERPRISE LOGIN SUCCESS: {email} from {client_ip}")
        
        # Enterprise response with feature detection
        auth_mode = "token"  # Force token mode during emergency fix
        
        if ENTERPRISE_FEATURES["cookie_authentication"]:
            # Cookie mode (disabled during emergency)
            response.set_cookie(
                key="ow_ai_access_token",
                value=access_token,
                **ENTERPRISE_COOKIE_CONFIG
            )
            
            response.set_cookie(
                key="ow_ai_refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                path="/",
                domain=None
            )
            
            auth_mode = "cookie"
            logger.info(f"🍪 ENTERPRISE: Cookie authentication set for {email}")
        
        # Enterprise response format
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
            "auth_mode": auth_mode,
            "enterprise_features": {
                "cookie_support": ENTERPRISE_FEATURES["cookie_authentication"],
                "enhanced_security": True,
                "audit_logging": ENTERPRISE_FEATURES["audit_trail"]
            }
        }
        
    except HTTPException:
        raise
    except EnterpriseAuthError:
        raise
    except Exception as e:
        logger.critical(f"🚨 ENTERPRISE LOGIN CRITICAL ERROR: {str(e)}")
        raise

@router.get("/me")
@enterprise_error_handler
async def get_current_user_enterprise(
    request: Request, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """🏢 Enterprise user verification with multi-source authentication"""
    
    try:
        token = None
        auth_source = "unknown"
        
        # Enterprise multi-source token detection
        if ENTERPRISE_FEATURES["cookie_authentication"] and "ow_ai_access_token" in request.cookies:
            token = request.cookies["ow_ai_access_token"]
            auth_source = "cookie"
            logger.debug("🍪 ENTERPRISE: Using cookie authentication")
        elif credentials and credentials.credentials:
            token = credentials.credentials
            auth_source = "bearer"
            logger.debug("🎫 ENTERPRISE: Using bearer token authentication")
        
        if not token:
            logger.debug("🚨 ENTERPRISE: No authentication token found")
            raise HTTPException(status_code=401, detail="No authentication provided")
        
        # Enterprise token validation
        payload = validate_enterprise_token(token, "access")
        
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        if not user_id:
            raise EnterpriseAuthError("Invalid token payload", "INVALID_PAYLOAD", payload)
        
        # Enterprise user verification
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"🚨 ENTERPRISE: Token valid but user not found: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        logger.info(f"✅ ENTERPRISE AUTH SUCCESS: {email} via {auth_source}")
        
        return {
            "user_id": int(user_id),
            "email": email,
            "role": role,
            "auth_source": auth_source,
            "enterprise_validated": True,
            "token_metadata": {
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "token_id": payload.get("jti")
            }
        }
        
    except HTTPException:
        raise
    except EnterpriseAuthError:
        raise
    except Exception as e:
        logger.error(f"🚨 ENTERPRISE USER VERIFICATION ERROR: {str(e)}")
        raise

@router.post("/refresh-token")
@enterprise_error_handler
@limiter.limit("10/minute" if ENTERPRISE_FEATURES["rate_limiting"] else "1000/minute")
async def refresh_token_enterprise(request: Request, response: Response):
    """🏢 Enterprise token refresh with comprehensive error handling and monitoring"""
    
    client_ip = get_remote_address(request)
    logger.info(f"🔄 ENTERPRISE REFRESH ATTEMPT: IP {client_ip}")
    
    try:
        refresh_token = None
        auth_mode = "token"
        
        # Enterprise multi-source refresh token detection
        if ENTERPRISE_FEATURES["cookie_authentication"] and "ow_ai_refresh_token" in request.cookies:
            refresh_token = request.cookies["ow_ai_refresh_token"]
            auth_mode = "cookie"
            logger.debug("🍪 ENTERPRISE: Using cookie refresh token")
        else:
            # Parse request body for token-based refresh
            request_body = await request.body()
            data = parse_request_body_safely(request_body)
            refresh_token = data.get("refresh_token")
            logger.debug("🎫 ENTERPRISE: Using bearer refresh token")
        
        if not refresh_token:
            logger.warning(f"🚨 ENTERPRISE: No refresh token provided from {client_ip}")
            raise HTTPException(status_code=401, detail="No refresh token provided")
        
        # Enterprise refresh token validation
        payload = validate_enterprise_token(refresh_token, "refresh")
        
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"), 
            "role": payload.get("role"),
            "user_id": payload.get("user_id", payload.get("sub"))
        }
        
        # Enterprise new token creation
        new_access_token = create_access_token(data=user_data)
        
        logger.info(f"✅ ENTERPRISE REFRESH SUCCESS: {user_data.get('email')} from {client_ip}")
        
        # Enterprise response based on auth mode
        if auth_mode == "cookie" and ENTERPRISE_FEATURES["cookie_authentication"]:
            # Update cookie
            response.set_cookie(
                key="ow_ai_access_token",
                value=new_access_token,
                **ENTERPRISE_COOKIE_CONFIG
            )
            
            return {
                "success": True,
                "message": "🍪 Enterprise token refreshed via cookies",
                "auth_mode": "cookie",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        else:
            # Return new token for bearer auth
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "auth_mode": "token"
            }
        
    except HTTPException:
        raise
    except EnterpriseAuthError:
        raise
    except Exception as e:
        logger.critical(f"🚨 ENTERPRISE REFRESH CRITICAL ERROR: {str(e)}")
        raise

@router.post("/logout")
@enterprise_error_handler
async def enterprise_logout(request: Request, response: Response):
    """🏢 Enterprise logout with comprehensive session cleanup"""
    
    try:
        client_ip = get_remote_address(request)
        logger.info(f"🚪 ENTERPRISE LOGOUT: IP {client_ip}")
        
        # Enterprise cookie cleanup
        if ENTERPRISE_FEATURES["cookie_authentication"]:
            response.delete_cookie(
                key="ow_ai_access_token",
                path="/",
                domain=None,
                secure=True,
                httponly=True,
                samesite="lax"
            )
            
            response.delete_cookie(
                key="ow_ai_refresh_token", 
                path="/",
                domain=None,
                secure=True,
                httponly=True,
                samesite="lax"
            )
        
        logger.info(f"✅ ENTERPRISE LOGOUT SUCCESS: IP {client_ip}")
        
        return {
            "success": True,
            "message": "🏢 Enterprise logout successful",
            "cookies_cleared": ENTERPRISE_FEATURES["cookie_authentication"],
            "audit_logged": ENTERPRISE_FEATURES["audit_trail"]
        }
        
    except Exception as e:
        logger.error(f"🚨 ENTERPRISE LOGOUT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

# Enterprise health check endpoint
@router.get("/health")
async def enterprise_auth_health():
    """🏢 Enterprise authentication system health check"""
    return {
        "status": "healthy",
        "service": "enterprise-authentication",
        "features": ENTERPRISE_FEATURES,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0-enterprise"
    }