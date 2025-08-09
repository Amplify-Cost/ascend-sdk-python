# auth.py - Enhanced with Enterprise Features
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
from config import SECRET_KEY, ALGORITHM
from datetime import timedelta, datetime, UTC
from token_utils import create_access_token, decode_token, create_refresh_token
from dependencies import get_current_user
from pydantic import BaseModel
import logging

# Enterprise setup
router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

@router.post("/register", response_model=TokenResponse)
async def register_user(data: UserRegister, db: Session = Depends(get_db)):
    """Enterprise user registration"""
    try:
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        # Enterprise password hashing
        hashed_password = pwd_context.hash(data.password)
        new_user = User(
            email=data.email, 
            password=hashed_password,  # ✅ CORRECT FIELD NAME
            role="user",  # Enterprise security: backend assigns role
            is_active=True,
            created_at=datetime.now(UTC)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Enterprise token generation
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
        
        logger.info(f"✅ Enterprise user registered: {new_user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
        
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/token", response_model=TokenResponse)
async def login_user(data: UserLogin, db: Session = Depends(get_db)):
    """Enterprise user login"""
    try:
        user = db.query(User).filter(User.email == data.email).first()
        
        # ✅ CORRECT FIELD NAME: user.password
        if not user or not pwd_context.verify(data.password, user.password):
            logger.warning(f"❌ Failed login attempt: {data.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if user is active
        if hasattr(user, 'is_active') and not user.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated")

        # Update last login if field exists
        if hasattr(user, 'last_login'):
            user.last_login = datetime.now(UTC)
            db.commit()

        # Enterprise token generation
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
        
        logger.info(f"✅ Enterprise login successful: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current enterprise user information"""
    try:
        return {
            "id": current_user["user_id"],
            "email": current_user["email"], 
            "role": current_user["role"],
            "auth_method": current_user.get("auth_method", "token"),
            "enterprise_user": True
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=401, detail="Unable to retrieve user information")

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token_endpoint(request: dict, db: Session = Depends(get_db)):
    """Enterprise token refresh"""
    try:
        refresh_token = request.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token required")
        
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        if hasattr(user, 'is_active') and not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive")
        
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
        
        logger.info(f"✅ Token refreshed for: {user.email}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=30 * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(status_code=401, detail="Token refresh failed")

@router.post("/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Enterprise logout"""
    try:
        logger.info(f"✅ Enterprise logout: {current_user.get('email')}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return {"message": "Logout completed"}

@router.post("/request-reset")
async def request_password_reset(data: UserLogin, db: Session = Depends(get_db)):
    """Enterprise password reset request"""
    try:
        user = db.query(User).filter(User.email == data.email).first()
        if not user:
            # Don't reveal if user exists (security)
            return {"message": "If the email exists, a reset link has been sent"}

        reset_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "type": "reset"}, 
            expires_delta=timedelta(minutes=15)
        )
        
        logger.info(f"✅ Password reset requested: {user.email}")
        
        return {
            "reset_token": reset_token, 
            "message": "Password reset token generated"
        }
        
    except Exception as e:
        logger.error(f"❌ Password reset request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset request failed")

@router.post("/reset-password")
async def reset_password(request: dict, db: Session = Depends(get_db)):
    """Enterprise password reset"""
    try:
        token = request.get("token")
        new_password = request.get("new_password")

        if not token or not new_password:
            raise HTTPException(status_code=400, detail="Token and new password are required")

        payload = decode_token(token)
        if not payload or payload.get("type") != "reset":
            raise HTTPException(status_code=401, detail="Invalid or expired reset token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ CORRECT FIELD NAME: user.password
        user.password = pwd_context.hash(new_password)
        db.commit()
        
        logger.info(f"✅ Password reset completed: {user.email}")
        
        return {"message": "Password reset successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password reset error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")