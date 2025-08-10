# routes/auth.py - Enterprise Loop Breaker (Bypass FastAPI Validation)

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

# =================== ENTERPRISE EMERGENCY CONFIGURATION ===================

router = APIRouter(prefix="/auth", tags=["Enterprise Authentication Emergency"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enhanced logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enterprise.auth.emergency")

# Enterprise Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-enterprise-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Enterprise Emergency Configuration
ENTERPRISE_FEATURES = {
    "emergency_mode": True,
    "bypass_validation": True,
    "infinite_loop_protection": True,
    "manual_request_parsing": True,
    "enhanced_logging": True
}

# =================== NO PYDANTIC MODELS - MANUAL PARSING ONLY ===================
# Completely bypass FastAPI validation to prevent 422 errors

def create_enterprise_token(data: dict, token_type: str = "access") -> str:
    """Create enterprise JWT token"""
    try:
        to_encode = data.copy()
        
        if token_type == "access":
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = datetime.now(UTC) + timedelta(days=7)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": token_type,
            "iss": "ow-ai-enterprise",
            "aud": "ow-ai-platform",
            "jti": f"{token_type}-{data.get('sub', 'unknown')}-{int(datetime.now(UTC).timestamp())}"
        })
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"✅ Emergency {token_type} token created for user {data.get('email', 'unknown')}")
        return token
        
    except Exception as e:
        logger.error(f"🚨 Emergency token creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def validate_enterprise_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Validate enterprise JWT token"""
    try:
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type if specified
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            logger.warning(f"🚨 Invalid token type: expected {expected_type}, got {token_type}")
            raise HTTPException(status_code=401, detail=f"Invalid token type")
        
        logger.debug(f"✅ Emergency token validated for user {payload.get('email', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("🚨 Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"🚨 Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Token validation error: {str(e)}")
        raise HTTPException(status_code=401, detail="Token validation failed")

async def emergency_parse_request(request: Request) -> Dict[str, Any]:
    """Emergency request parser that never fails"""
    try:
        # Log the request for debugging
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        content_type = request.headers.get("content-type", "none")
        
        logger.info(f"🚨 EMERGENCY REQUEST: {method} {url} from {client_ip} - Content-Type: {content_type}")
        
        # Get request body
        body = await request.body()
        logger.info(f"🔍 Raw body length: {len(body)} bytes")
        
        if not body:
            logger.info("🔍 Empty request body - returning empty dict")
            return {}
        
        body_str = body.decode('utf-8', errors='ignore')
        logger.info(f"🔍 Raw body content: {body_str[:200]}...")  # First 200 chars
        
        if not body_str.strip():
            logger.info("🔍 Whitespace-only body - returning empty dict")
            return {}
        
        # Try to parse JSON
        try:
            data = json.loads(body_str)
            logger.info(f"✅ Successfully parsed JSON with keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            logger.warning(f"🚨 JSON parse failed: {str(e)} - Returning empty dict")
            return {}
        
    except Exception as e:
        logger.error(f"🚨 Emergency parser critical error: {str(e)}")
        return {}

# =================== EMERGENCY ENDPOINTS - NO PYDANTIC VALIDATION ===================

@router.post("/token")
async def emergency_login(request: Request, db: Session = Depends(get_db)):
    """🚨 EMERGENCY LOGIN - No validation, manual parsing"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚨 EMERGENCY LOGIN ATTEMPT from {client_ip}")
        
        # Manual request parsing - never fails
        data = await emergency_parse_request(request)
        
        # Extract credentials with defaults
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        logger.info(f"🔍 Login data: email='{email}', password_provided={bool(password)}")
        
        if not email or not password:
            logger.warning(f"🚨 Missing credentials: email={bool(email)}, password={bool(password)}")
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Validate user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"🚨 User not found: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Validate password
        if not pwd_context.verify(password, user.password):
            logger.warning(f"🚨 Invalid password for user: {email}")
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
        
        logger.info(f"✅ EMERGENCY LOGIN SUCCESS: {user.email}")
        
        # Enterprise frontend compatibility - exact format expected
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "email": user.email,
                "role": user.role,
                "user_id": user.id,
                "id": user.id  # Frontend may expect 'id' field
            },
            "auth_mode": "token"
            # Removed emergency fields that might confuse frontend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 EMERGENCY LOGIN CRITICAL ERROR: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Emergency authentication system error")

@router.get("/me")
async def emergency_get_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """🚨 EMERGENCY USER INFO - No validation"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚨 EMERGENCY USER INFO REQUEST from {client_ip}")
        
        if not credentials or not credentials.credentials:
            logger.info("🔍 No authentication credentials provided")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Validate token
        payload = validate_enterprise_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"🚨 Token valid but user not found: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        logger.info(f"✅ EMERGENCY USER INFO SUCCESS: {user.email}")
        
        # Enterprise frontend compatibility - match expected format
        return {
            "user_id": int(user_id),
            "email": user.email,
            "role": user.role,
            "id": int(user_id),  # Frontend may expect 'id' field
            "auth_source": "bearer",
            "enterprise_validated": True
            # Removed emergency fields that might confuse frontend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 EMERGENCY USER INFO ERROR: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication validation failed")

@router.post("/refresh-token")
async def emergency_refresh_token(request: Request):
    """🚨 EMERGENCY REFRESH - LOOP BREAKER - Always returns JSON, never raises 422"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚨 EMERGENCY REFRESH REQUEST from {client_ip}")
        
        # CRITICAL: Always parse request safely - never fail with 422
        data = await emergency_parse_request(request)
        
        refresh_token = data.get("refresh_token", "")
        logger.info(f"🔍 Refresh token provided: {bool(refresh_token)}")
        
        if not refresh_token:
            logger.warning("🚨 No refresh token in request")
            # CRITICAL: Return JSON error, never raise HTTPException
            return {
                "error": "missing_refresh_token",
                "error_code": "EMERGENCY_MISSING_TOKEN",
                "message": "No refresh token provided in request",
                "emergency_mode": True,
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Try to validate refresh token
        try:
            payload = validate_enterprise_token(refresh_token, "refresh")
            logger.info(f"✅ Refresh token valid for user: {payload.get('email', 'unknown')}")
        except HTTPException as e:
            logger.warning(f"🚨 Invalid refresh token: {e.detail}")
            # CRITICAL: Return JSON error, never raise HTTPException
            return {
                "error": "invalid_refresh_token",
                "error_code": "EMERGENCY_INVALID_TOKEN",
                "message": f"Refresh token validation failed: {e.detail}",
                "emergency_mode": True,
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Create new access token
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id", payload.get("sub"))
        }
        
        try:
            new_access_token = create_enterprise_token(user_data, "access")
            logger.info(f"✅ EMERGENCY REFRESH SUCCESS for user: {user_data.get('email')}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "auth_mode": "token",
                "emergency_mode": True,
                "refreshed_at": datetime.now(UTC).isoformat()
            }
            
        except Exception as token_error:
            logger.error(f"🚨 Token creation failed: {str(token_error)}")
            # CRITICAL: Return JSON error, never raise HTTPException
            return {
                "error": "token_creation_failed",
                "error_code": "EMERGENCY_TOKEN_CREATION_ERROR",
                "message": "Could not create new access token",
                "emergency_mode": True,
                "timestamp": datetime.now(UTC).isoformat()
            }
        
    except Exception as e:
        logger.error(f"🚨 EMERGENCY REFRESH CRITICAL ERROR: {str(e)}", exc_info=True)
        # CRITICAL: ALWAYS return JSON, never raise exceptions
        return {
            "error": "system_error",
            "error_code": "EMERGENCY_SYSTEM_ERROR", 
            "message": "Emergency refresh system temporarily unavailable",
            "emergency_mode": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "details": str(e)
        }

@router.post("/logout")
async def emergency_logout(request: Request):
    """🚨 EMERGENCY LOGOUT - Always succeeds"""
    
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"🚨 EMERGENCY LOGOUT from {client_ip}")
        
        return {
            "success": True,
            "message": "Emergency logout successful",
            "emergency_mode": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        logger.error(f"🚨 Emergency logout error: {str(e)}")
        return {
            "success": False,
            "message": "Logout completed with warnings",
            "emergency_mode": True,
            "timestamp": datetime.now(UTC).isoformat()
        }

# =================== EMERGENCY DIAGNOSTICS ===================

@router.get("/emergency-status")
async def emergency_status():
    """🚨 Emergency system status - always works"""
    
    return {
        "status": "emergency_mode_active",
        "service": "enterprise-authentication-emergency",
        "features": ENTERPRISE_FEATURES,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "emergency-1.0.0",
        "validation_bypass": "active",
        "loop_protection": "maximum",
        "manual_parsing": "enabled"
    }

@router.get("/health")
async def emergency_health():
    """🚨 Emergency health check"""
    
    return {
        "status": "emergency_operational",
        "mode": "emergency_bypass_validation",
        "infinite_loop_protection": "active",
        "timestamp": datetime.now(UTC).isoformat(),
        "emergency_features": {
            "no_pydantic_validation": True,
            "manual_request_parsing": True,
            "guaranteed_json_responses": True,
            "loop_breaker_active": True
        }
    }