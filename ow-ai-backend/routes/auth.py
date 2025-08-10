# routes/auth.py - Enhanced with Enterprise Cookie Authentication (Phase 1)
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

# Enterprise Configuration
router = APIRouter(prefix="/auth", tags=["Enterprise Authentication"])
security = HTTPBearer(auto_error=False)  # Allow both cookie and token auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

# Enterprise Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-enterprise-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Enterprise Cookie Configuration
COOKIE_CONFIG = {
    "httponly": True,      # Prevents XSS access
    "secure": True,        # HTTPS only in production
    "samesite": "lax",     # CSRF protection
    "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 30 minutes
    "path": "/",           # Available site-wide
    "domain": None         # Current domain only
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token with enterprise security"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Create JWT refresh token with extended expiry"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_auth_mode(request: Request) -> str:
    """Detect authentication mode: 'cookie' or 'token'"""
    # Check if client wants cookie mode (Phase 2 frontend will send this header)
    wants_cookies = request.headers.get("x-auth-mode") == "cookie"
    has_auth_cookie = "ow_ai_access_token" in request.cookies
    
    if wants_cookies or has_auth_cookie:
        return "cookie"
    return "token"

@router.post("/token")
async def enterprise_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """🏢 Enterprise login with dual authentication support"""
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not email or not password:
            logger.warning(f"🔒 Enterprise login attempt with missing credentials")
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Enterprise user validation
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password, user.password):
            logger.warning(f"🔒 Enterprise login failed for: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create enterprise tokens
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "user_id": user.id
        }
        
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)
        
        # Determine authentication mode
        auth_mode = get_auth_mode(request)
        
        if auth_mode == "cookie":
            # 🍪 Enterprise Cookie Mode (Phase 2+)
            logger.info(f"🍪 Enterprise cookie authentication for: {email}")
            
            # Set secure httpOnly cookies
            response.set_cookie(
                key="ow_ai_access_token",
                value=access_token,
                **COOKIE_CONFIG
            )
            
            response.set_cookie(
                key="ow_ai_refresh_token", 
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days
                path="/",
                domain=None
            )
            
            # Return success without tokens (cookies handle auth)
            return {
                "success": True,
                "message": "🍪 Enterprise cookie authentication successful",
                "user": {
                    "email": user.email,
                    "role": user.role,
                    "user_id": user.id
                },
                "auth_mode": "cookie",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        
        else:
            # 🎫 Legacy Token Mode (Phase 1 compatibility)
            logger.info(f"🎫 Enterprise token authentication for: {email}")
            
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
        logger.error(f"🏢 Enterprise login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Enterprise authentication failed")

@router.post("/register")
async def enterprise_register(request: Request, response: Response, db: Session = Depends(get_db)):
    """🏢 Enterprise registration with dual authentication support"""
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", "user")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new enterprise user
        hashed_password = pwd_context.hash(password)
        new_user = User(email=email, password=hashed_password, role=role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create enterprise tokens
        user_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "user_id": new_user.id
        }
        
        access_token = create_access_token(data=user_data)
        refresh_token = create_refresh_token(data=user_data)
        
        # Determine authentication mode
        auth_mode = get_auth_mode(request)
        
        if auth_mode == "cookie":
            # Set enterprise cookies
            response.set_cookie(key="ow_ai_access_token", value=access_token, **COOKIE_CONFIG)
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
            
            return {
                "success": True,
                "message": "🍪 Enterprise registration successful",
                "user": {"email": new_user.email, "role": new_user.role, "user_id": new_user.id},
                "auth_mode": "cookie"
            }
        else:
            return {
                "message": "🎫 Enterprise registration successful", 
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {"email": new_user.email, "role": new_user.role, "user_id": new_user.id},
                "auth_mode": "token"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 Enterprise registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Enterprise registration failed")

@router.get("/me")
async def get_current_user_enterprise(
    request: Request, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """🏢 Enterprise user info with dual authentication support"""
    try:
        token = None
        auth_source = "unknown"
        
        # Try cookie authentication first (enterprise preferred)
        if "ow_ai_access_token" in request.cookies:
            token = request.cookies["ow_ai_access_token"]
            auth_source = "cookie"
            logger.debug("🍪 Using cookie authentication")
        
        # Fallback to bearer token (legacy compatibility)
        elif credentials and credentials.credentials:
            token = credentials.credentials
            auth_source = "bearer"
            logger.debug("🎫 Using bearer token authentication")
        
        if not token:
            raise HTTPException(status_code=401, detail="No authentication provided")
        
        # Decode and validate token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify user still exists
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        logger.info(f"✅ Enterprise authentication successful ({auth_source}): {email}")
        
        return {
            "user_id": int(user_id),
            "email": email,
            "role": role,
            "auth_source": auth_source,
            "enterprise_validated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 Enterprise user info error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/logout")
async def enterprise_logout(request: Request, response: Response):
    """🏢 Enterprise logout with secure cookie clearing"""
    try:
        # Clear enterprise cookies
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
        
        logger.info("🏢 Enterprise logout successful")
        
        return {
            "success": True,
            "message": "🏢 Enterprise logout successful",
            "cookies_cleared": True
        }
        
    except Exception as e:
        logger.error(f"🏢 Enterprise logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.post("/refresh-token")
async def refresh_token_enterprise(request: Request, response: Response):
    """🏢 Enterprise token refresh with dual authentication support"""
    try:
        refresh_token = None
        
        # Try to get refresh token from cookie first
        if "ow_ai_refresh_token" in request.cookies:
            refresh_token = request.cookies["ow_ai_refresh_token"]
            auth_mode = "cookie"
        else:
            # Fallback to request body for legacy compatibility
            data = await request.json()
            refresh_token = data.get("refresh_token")
            auth_mode = "token"
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token provided")
        
        # Validate refresh token
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            user_data = {
                "sub": payload.get("sub"),
                "email": payload.get("email"), 
                "role": payload.get("role"),
                "user_id": payload.get("user_id", payload.get("sub"))
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        new_access_token = create_access_token(data=user_data)
        
        if auth_mode == "cookie":
            # Update cookie
            response.set_cookie(key="ow_ai_access_token", value=new_access_token, **COOKIE_CONFIG)
            
            return {
                "success": True,
                "message": "🍪 Enterprise token refreshed",
                "auth_mode": "cookie"
            }
        else:
            # Return new token for legacy mode
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "auth_mode": "token"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏢 Enterprise refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")