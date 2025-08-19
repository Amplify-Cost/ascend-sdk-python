"""
Enterprise Authentication Routes - Cookie-Based
Secure HTTP-only cookies + CSRF protection
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from database import get_db
from jwt_manager import get_jwt_manager
from csrf_manager import csrf_manager
from cookie_auth import reject_bearer_tokens

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(reject_bearer_tokens)])

@router.post("/login")
async def login_with_cookies(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Enterprise login with secure cookie authentication
    
    Security Features:
    - HTTP-only cookies prevent XSS
    - Secure flag requires HTTPS
    - SameSite protection
    - CSRF token generation
    """
    
    # Authenticate user (your existing logic)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    jwt_mgr = get_jwt_manager()
    access_token = jwt_mgr.issue_token(
        user_id=str(user.id),
        user_email=user.email,
        roles=user.roles,
        expires_in_minutes=60
    )
    
    # Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevents XSS access
        secure=True,    # HTTPS only (set to False for localhost testing)
        samesite="lax", # CSRF protection
        max_age=3600,   # 1 hour
        path="/"        # Available to all routes
    )
    
    # Generate CSRF token
    csrf_token = csrf_manager.generate_token(user_id=str(user.id))
    
    logger.info(f"Successful cookie login for user: {user.email}")
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "roles": user.roles
        },
        "csrf_token": csrf_token,  # Client needs this for state-changing requests
        "auth_method": "cookie"
    }

@router.post("/logout")
async def logout_with_cookies(response: Response):
    """
    Enterprise logout - clear secure cookies
    """
    
    # Clear the authentication cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    
    logger.info("User logged out - cookies cleared")
    
    return {"message": "Logout successful"}

@router.get("/csrf-token")
async def get_csrf_token(request: Request):
    """
    Get CSRF token for authenticated users
    Required for frontend state-changing operations
    """
    
    # Extract user from cookie (if authenticated)
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(access_token)
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
    
    # Generate fresh CSRF token
    csrf_token = csrf_manager.generate_token(user_id=user_id)
    
    return {"csrf_token": csrf_token}

@router.get("/me")
async def get_current_user_info(request: Request):
    """
    Get current user information from cookie authentication
    """
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(access_token)
        
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "auth_method": "cookie",
            "token_expires": payload.get("exp")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )

# Helper function (implement based on your existing user model)
def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user - implement based on your user model"""
    # TODO: Implement your existing user authentication logic
    pass
