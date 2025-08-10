# routes/auth.py - Enterprise 422 Diagnostic & Resolution System

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, Union
import jwt
import os
import logging
import json
import traceback

# =================== ENTERPRISE DEBUGGING CONFIGURATION ===================

# Enhanced logging for 422 diagnostics
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enterprise.auth.diagnostic")

# Enterprise Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-enterprise-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Enterprise Configuration
ENTERPRISE_FEATURES = {
    "diagnostic_mode": True,  # Enable detailed 422 debugging
    "enhanced_logging": True,
    "audit_trail": True,
    "request_body_logging": True,
    "validation_error_details": True
}

# =================== ENTERPRISE PYDANTIC MODELS ===================

class EnterpriseLoginRequest(BaseModel):
    """Enterprise login model with flexible validation for 422 debugging"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    
    class Config:
        # Enterprise debugging - allow extra fields
        extra = "allow"  # Changed from "ignore" to "allow" for debugging
        anystr_strip_whitespace = True
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    
    @validator('email', pre=True)
    def normalize_email(cls, v):
        """Enterprise email normalization"""
        if v:
            return str(v).strip().lower()
        return v

class EnterpriseRegistrationRequest(BaseModel):
    """Enterprise registration model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    role: Optional[str] = Field("user", description="User role (defaults to 'user')")
    
    class Config:
        extra = "allow"
        anystr_strip_whitespace = True

class EnterpriseRefreshRequest(BaseModel):
    """Enterprise refresh token model"""
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        extra = "allow"

# =================== ENTERPRISE EXCEPTION HANDLERS ===================

async def enterprise_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Enterprise 422 error handler with comprehensive diagnostics"""
    
    # Get request body for diagnostics
    request_body = ""
    try:
        request_body = (await request.body()).decode('utf-8')
    except Exception as e:
        logger.error(f"🚨 Could not read request body: {e}")
    
    # Enterprise diagnostic logging
    diagnostic_info = {
        "timestamp": datetime.now(UTC).isoformat(),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "raw_body": request_body,
        "validation_errors": exc.errors(),
        "client_ip": request.client.host if request.client else "unknown"
    }
    
    logger.error("🏢 ENTERPRISE 422 DIAGNOSTIC:")
    logger.error(f"🔍 Request Method: {request.method}")
    logger.error(f"🔍 Request URL: {request.url}")
    logger.error(f"🔍 Content-Type: {request.headers.get('content-type', 'NOT SET')}")
    logger.error(f"🔍 Raw Request Body: {request_body}")
    logger.error(f"🔍 Validation Errors: {exc.errors()}")
    logger.error(f"🔍 Expected Body Structure: {exc.body}")
    
    # Enterprise error response with diagnostic details
    error_response = {
        "error": "Enterprise Validation Error",
        "error_code": "ENTERPRISE_422_VALIDATION_FAILED",
        "message": "Request data validation failed",
        "timestamp": datetime.now(UTC).isoformat(),
        "validation_errors": exc.errors(),
    }
    
    # Include diagnostic info in development/debug mode
    if ENTERPRISE_FEATURES["diagnostic_mode"]:
        error_response["diagnostic_info"] = {
            "raw_request_body": request_body,
            "expected_format": "JSON with email and password fields",
            "content_type_header": request.headers.get('content-type'),
            "request_method": request.method,
            "url": str(request.url)
        }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )

# =================== FASTAPI ROUTER SETUP ===================

router = APIRouter(prefix="/auth", tags=["Enterprise Authentication"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Register the enterprise validation exception handler
from fastapi import FastAPI
app = FastAPI()
app.add_exception_handler(RequestValidationError, enterprise_validation_exception_handler)

# =================== ENTERPRISE UTILITY FUNCTIONS ===================

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
            "aud": "ow-ai-platform"
        })
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"✅ Enterprise {token_type} token created for user {data.get('email', 'unknown')}")
        return token
        
    except Exception as e:
        logger.error(f"🚨 Enterprise token creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def validate_enterprise_token(token: str) -> Dict[str, Any]:
    """Validate enterprise JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =================== ENTERPRISE ENDPOINTS ===================

@router.post("/token")
async def enterprise_login(
    request: Request,
    credentials: EnterpriseLoginRequest,  # Using Pydantic model for auto-validation
    db: Session = Depends(get_db)
):
    """🏢 Enterprise login with comprehensive 422 debugging"""
    
    try:
        # Enterprise logging
        logger.info(f"🏢 Enterprise login attempt for: {credentials.email}")
        logger.debug(f"🔍 Received credentials: email={credentials.email}, password_length={len(credentials.password)}")
        
        # Validate user exists
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            logger.warning(f"🚨 User not found: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Validate password
        if not pwd_context.verify(credentials.password, user.password):
            logger.warning(f"🚨 Invalid password for user: {credentials.email}")
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
        
        logger.info(f"✅ Enterprise login successful: {user.email}")
        
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
            "auth_mode": "token",
            "enterprise_metadata": {
                "security_level": "enterprise",
                "issued_at": datetime.now(UTC).isoformat(),
                "diagnostic_mode": ENTERPRISE_FEATURES["diagnostic_mode"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Enterprise login critical error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Enterprise authentication system error")

@router.post("/register")
async def enterprise_register(
    request: Request,
    user_data: EnterpriseRegistrationRequest,
    db: Session = Depends(get_db)
):
    """🏢 Enterprise registration with validation"""
    
    try:
        logger.info(f"🏢 Enterprise registration attempt for: {user_data.email}")
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password=hashed_password,
            role=user_data.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create tokens
        user_payload = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "user_id": new_user.id
        }
        
        access_token = create_enterprise_token(user_payload, "access")
        refresh_token = create_enterprise_token(user_payload, "refresh")
        
        logger.info(f"✅ Enterprise registration successful: {new_user.email}")
        
        return {
            "message": "Enterprise registration successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": new_user.email,
                "role": new_user.role,
                "user_id": new_user.id
            },
            "auth_mode": "token"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Enterprise registration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")

@router.get("/me")
async def get_current_user_enterprise(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """🏢 Enterprise user verification"""
    
    try:
        if not credentials or not credentials.credentials:
            logger.debug("🔍 No authentication credentials provided")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Validate token
        payload = validate_enterprise_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        logger.info(f"✅ Enterprise user verification successful: {user.email}")
        
        return {
            "user_id": int(user_id),
            "email": user.email,
            "role": user.role,
            "auth_source": "bearer",
            "enterprise_validated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Enterprise user verification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication validation failed")

@router.post("/refresh-token")
async def refresh_token_enterprise(
    request: Request,
    refresh_data: EnterpriseRefreshRequest
):
    """🏢 Enterprise token refresh"""
    
    try:
        logger.info("🏢 Enterprise token refresh attempt")
        
        # Validate refresh token
        payload = validate_enterprise_token(refresh_data.refresh_token)
        
        # Check if it's actually a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id", payload.get("sub"))
        }
        
        new_access_token = create_enterprise_token(user_data, "access")
        
        logger.info(f"✅ Enterprise token refresh successful for user: {user_data.get('email')}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "auth_mode": "token"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🚨 Enterprise token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token refresh failed")

@router.post("/logout")
async def enterprise_logout(request: Request):
    """🏢 Enterprise logout"""
    
    try:
        logger.info("🏢 Enterprise logout initiated")
        
        return {
            "success": True,
            "message": "Enterprise logout successful",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        logger.error(f"🚨 Enterprise logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

# =================== ENTERPRISE DIAGNOSTICS ENDPOINT ===================

@router.get("/diagnostic")
async def enterprise_diagnostic():
    """🏢 Enterprise authentication system diagnostics"""
    
    return {
        "status": "diagnostic_mode_active",
        "service": "enterprise-authentication-diagnostic",
        "features": ENTERPRISE_FEATURES,
        "timestamp": datetime.now(UTC).isoformat(),
        "pydantic_models": {
            "login": EnterpriseLoginRequest.schema(),
            "register": EnterpriseRegistrationRequest.schema(),
            "refresh": EnterpriseRefreshRequest.schema()
        },
        "expected_request_formats": {
            "login": {
                "method": "POST",
                "url": "/auth/token",
                "content_type": "application/json",
                "body_example": {
                    "email": "user@example.com",
                    "password": "securepassword123"
                }
            },
            "register": {
                "method": "POST", 
                "url": "/auth/register",
                "content_type": "application/json",
                "body_example": {
                    "email": "newuser@example.com",
                    "password": "securepassword123",
                    "role": "user"
                }
            }
        }
    }

@router.get("/health")
async def enterprise_auth_health():
    """🏢 Enterprise authentication health check"""
    
    return {
        "status": "healthy_diagnostic_mode",
        "service": "enterprise-authentication",
        "diagnostic_features": ENTERPRISE_FEATURES,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0-enterprise-diagnostic",
        "validation_status": "enhanced_422_debugging"
    }