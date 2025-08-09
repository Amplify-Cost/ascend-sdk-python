# auth_routes.py - Updated for dual authentication support (PHASE 1)
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta, UTC
import logging

from database import get_db
from models import User
from schemas import UserCreate, LoginInput, TokenResponse
from token_utils import create_access_token, create_refresh_token, decode_token
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from dependencies import get_current_user
from passlib.context import CryptContext

# Setup
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Enterprise cookie configuration
COOKIE_CONFIG = {
    "secure": True,      # HTTPS only in production
    "httponly": True,    # Prevent XSS access
    "samesite": "strict", # CSRF protection
    "path": "/",         # Available site-wide
    "domain": None,      # Auto-detect domain
}

def get_cookie_config(request: Request) -> dict:
    """Get cookie configuration based on environment"""
    config = COOKIE_CONFIG.copy()
    
    # Development adjustments
    if request.url.hostname in ["localhost", "127.0.0.1"]:
        config["secure"] = False  # Allow HTTP in development
        config["samesite"] = "lax"  # Less strict for development
    
    return config

def detect_auth_preference(request: Request) -> str:
    """Detect if client wants cookie-based or token-based auth"""
    # Check for cookie preference header
    auth_mode = request.headers.get("X-Auth-Mode", "").lower()
    if auth_mode in ["cookie", "cookies"]:
        return "cookie"
    
    # Check if modern browser (supports cookies well)
    user_agent = request.headers.get("User-Agent", "").lower()
    if any(browser in user_agent for browser in ["chrome", "firefox", "safari", "edge"]):
        # For now, default to token mode for compatibility
        # Later we'll switch this to "cookie" as default
        return "token"
    
    return "token"

@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Enterprise user registration with dual auth support"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user (role assigned by backend only)
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            role="user",  # Default role - enterprise security
            is_active=True,
            created_at=datetime.now(UTC)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate tokens
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
        
        # Detect authentication preference
        auth_mode = detect_auth_preference(request)
        
        if auth_mode == "cookie":
            # Set secure cookies
            cookie_config = get_cookie_config(request)
            
            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                **cookie_config
            )
            
            response.set_cookie(
                key="refresh_token", 
                value=refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                **cookie_config
            )
            
            logger.info(f"✅ User registered with cookie auth: {new_user.email}")
            
            # Return minimal response for cookie mode
            return TokenResponse(
                access_token="",  # Empty for cookie mode
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        else:
            # Legacy token mode
            logger.info(f"✅ User registered with token auth: {new_user.email}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginInput,
    db: Session = Depends(get_db)
):
    """Enterprise login with dual authentication support"""
    try:
        # Authenticate user
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not pwd_context.verify(login_data.password, user.hashed_password):
            logger.warning(f"❌ Failed login attempt: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated"
            )
        
        # Update last login
        user.last_login = datetime.now(UTC)
        db.commit()
        
        # Generate tokens
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
        
        # Detect authentication preference
        auth_mode = detect_auth_preference(request)
        
        if auth_mode == "cookie":
            # Set secure cookies
            cookie_config = get_cookie_config(request)
            
            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                **cookie_config
            )
            
            response.set_cookie(
                key="refresh_token",
                value=refresh_token, 
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                **cookie_config
            )
            
            logger.info(f"✅ Cookie-based login: {user.email}")
            
            # Return minimal response for cookie mode
            return TokenResponse(
                access_token="",  # Empty for cookie mode
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        else:
            # Legacy token mode
            logger.info(f"✅ Token-based login: {user.email}")
            
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """Enterprise logout with cookie clearing"""
    try:
        # Clear cookies
        cookie_config = get_cookie_config(request)
        cookie_config.update({"max_age": 0})  # Expire immediately
        
        response.set_cookie(key="access_token", value="", **cookie_config)
        response.set_cookie(key="refresh_token", value="", **cookie_config)
        
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
    """Refresh tokens with dual auth support"""
    try:
        # Try to get refresh token from cookie first, then fallback to body
        refresh_token = request.cookies.get("refresh_token")
        auth_mode = "cookie"
        
        if not refresh_token:
            # Fallback to legacy body-based refresh
            body = await request.json()
            refresh_token = body.get("refresh_token")
            auth_mode = "token"
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required"
            )
        
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        new_access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access"
        })
        
        new_refresh_token = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh"
        })
        
        if auth_mode == "cookie":
            # Update cookies
            cookie_config = get_cookie_config(request)
            
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                **cookie_config
            )
            
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                **cookie_config
            )
            
            return TokenResponse(
                access_token="",  # Empty for cookie mode
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        else:
            # Legacy token mode
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )