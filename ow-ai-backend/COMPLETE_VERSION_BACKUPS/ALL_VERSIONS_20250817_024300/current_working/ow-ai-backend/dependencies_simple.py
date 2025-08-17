"""
Simple dependencies for local cookie auth testing
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from local_jwt_manager import get_jwt_manager

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Simple auth for testing - checks cookies first, then Bearer tokens"""
    
    # Try cookie first
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            jwt_mgr = get_jwt_manager()
            payload = jwt_mgr.verify_token(access_token)
            logger.info(f"✅ Cookie auth successful: {payload.get('email')}")
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "auth_method": "cookie"
            }
        except Exception as e:
            logger.warning(f"Cookie auth failed: {e}")
    
    # Try Bearer token
    if credentials and credentials.credentials:
        try:
            jwt_mgr = get_jwt_manager()
            payload = jwt_mgr.verify_token(credentials.credentials)
            logger.info(f"✅ Bearer auth successful: {payload.get('email')}")
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "auth_method": "bearer"
            }
        except Exception as e:
            logger.warning(f"Bearer auth failed: {e}")
    
    # No valid auth found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

def require_admin(current_user: dict = Depends(get_current_user)):
    """Simple admin check"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return current_user

# Legacy alias
verify_token = get_current_user
