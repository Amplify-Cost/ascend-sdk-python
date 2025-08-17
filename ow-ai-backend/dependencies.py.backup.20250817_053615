"""
Enterprise Cookie-Only Authentication Dependencies
Master Prompt Compliant: NO Bearer tokens, NO localStorage
"""

from fastapi import Request, HTTPException, status, Depends, Cookie, Form
from sqlalchemy.orm import Session
from database import get_db_session
from jwt_manager import get_jwt_manager
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

def get_db() -> Session:
    """Database dependency"""
    try:
        db = get_db_session()
        yield db
    finally:
        db.close()

async def get_current_user(request: Request) -> dict:
    """
    Enterprise Cookie-Only Authentication (Master Prompt Compliant)
    NO Bearer tokens allowed - pure cookie authentication only
    """
    try:
        # Get cookie value directly from request
        session_cookie = request.cookies.get("owai_session")
        
        if not session_cookie:
            logger.warning("No session cookie found")
            raise HTTPException(
                status_code=401,
                detail="Authentication required - no session cookie",
                headers={"WWW-Authenticate": "Cookie"}
            )
        
        # Decode the JWT from cookie
        jwt_manager = get_jwt_manager()
        payload = jwt_manager.verify_token(session_cookie)
        
        if not payload:
            logger.warning("Invalid session cookie")
            raise HTTPException(
                status_code=401,
                detail="Invalid session - please login again",
                headers={"WWW-Authenticate": "Cookie"}
            )
        
        # Log successful authentication
        logger.info(f"✅ Cookie authentication successful: {payload.get('email')}")
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "auth_method": "cookie_only"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cookie authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Cookie"}
        )

def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role with cookie authentication"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

def require_manager_or_admin(current_user: dict = Depends(get_current_user)):
    """Require manager or admin role with cookie authentication"""
    if current_user.get("role") not in ["manager", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or admin access required"
        )
    return current_user

def require_admin_with_db(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Require admin with database session"""
    return current_user, db

def require_manager_or_admin_with_db(
    current_user: dict = Depends(require_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Require manager/admin with database session"""
    return current_user, db

# Enterprise compliance
verify_token = get_current_user  # For compatibility

# Enterprise CSRF Protection Function - Master Prompt Compliant
async def require_csrf(request: Request, csrf_token: str = Form(...)):
    """
    Enterprise CSRF protection for state-changing requests
    Master Prompt compliant - part of cookie-only authentication
    """
    try:
        # Get CSRF token from cookie or session
        stored_csrf = request.cookies.get("csrf_token")
        
        if not stored_csrf:
            logger.warning("CSRF token missing from cookies")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required for this operation"
            )
        
        if stored_csrf != csrf_token:
            logger.warning("CSRF token mismatch")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
        
        return True
        
    except Exception as e:
        logger.error(f"CSRF validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed"
        )

# Export for imports
__all__ = ['get_current_user', 'require_csrf', 'get_db_session']
