# auth_routes.py - FIXED IMPORTS
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models import User
from schemas import UserCreate, LoginInput, TokenResponse, TokenRefreshRequest
from auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token
    # ✅ REMOVED verify_token - it's now in dependencies.py
)
from dependencies import get_current_user  # ✅ ADD THIS IMPORT
from config import ACCESS_TOKEN_EXPIRE_MINUTES, LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Keep all your existing route functions exactly the same, just change:
# - Replace any `Depends(verify_token)` with `Depends(get_current_user)`
# - Replace any `verify_token(token)` calls with `get_current_user(credentials)`

@router.post("/register", response_model=TokenResponse)
@limiter.limit(REGISTER_RATE_LIMIT)
async def register_user(
    request: Request,
    data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            logger.warning(f"Registration attempt for existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        hashed_password = hash_password(data.password)
        new_user = User(
            email=data.email.lower(),
            password=hashed_password,
            role="user"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"New user registered: {data.email}")

        user_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role
        }
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/token", response_model=TokenResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login_user(
    request: Request,
    data: LoginInput,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    try:
        user = db.query(User).filter(User.email == data.email.lower()).first()
        if not user or not verify_password(data.password, user.password):
            logger.warning(f"Failed login attempt for: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        logger.info(f"Successful login: {data.email}")
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh-token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
    data: TokenRefreshRequest
):
    """Refresh access token using refresh token"""
    try:
        payload = decode_refresh_token(data.refresh_token)
        user_data = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
        new_access_token = create_access_token(user_data)
        new_refresh_token = create_refresh_token(user_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.post("/request-reset")
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    data: LoginInput,
    db: Session = Depends(get_db)
):
    """Request password reset token"""
    try:
        user = db.query(User).filter(User.email == data.email.lower()).first()
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {data.email}")
            return {"message": "If email exists, reset instructions have been sent"}

        reset_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "reset": True},
            expires_delta=timedelta(minutes=15)
        )
        logger.info(f"Password reset requested for: {data.email}")
        return {
            "message": "Reset token generated",
            "reset_token": reset_token
        }

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {"message": "If email exists, reset instructions have been sent"}

@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        data = await request.json()
        token = data.get("token")
        new_password = data.get("new_password")

        if not token or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token and new password are required"
            )

        # Use decode_access_token directly instead of verify_token
        from auth_utils import decode_access_token
        payload = decode_access_token(token)
        if not payload.get("reset"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset token"
            )

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.password = hash_password(new_password)
        db.commit()
        logger.info(f"Password reset successful for user: {user.email}")
        return {"message": "Password reset successful"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/update-profile")
@limiter.limit("5/minute")
async def update_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),  # ✅ CHANGED: Use get_current_user instead of verify_token
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email and not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or password required"
            )

        user = db.query(User).filter(User.id == int(current_user["user_id"])).first()  # ✅ CHANGED: Use user_id instead of sub
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if email and email.lower() != user.email:
            existing = db.query(User).filter(User.email == email.lower()).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = email.lower()

        if password:
            user.password = hash_password(password)

        db.commit()
        logger.info(f"Profile updated for user: {user.email}")
        return {"message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )