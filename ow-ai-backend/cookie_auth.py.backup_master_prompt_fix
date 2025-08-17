"""
Enterprise Cookie Authentication Middleware
Replaces Bearer token auth with secure HTTP-only cookies + CSRF protection
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security.utils import get_authorization_scheme_param
from jwt_manager import get_jwt_manager
from csrf_manager import csrf_manager
import logging

logger = logging.getLogger(__name__)

class CookieAuthenticationError(Exception):
    """Raised when cookie authentication fails"""
    pass

async def get_current_user_from_cookie(request: Request) -> dict:
    """
    Enterprise cookie-based authentication
    
    Security Features:
    - HTTP-only cookies prevent XSS token theft
    - CSRF token validation prevents CSRF attacks  
    - Secure cookie flags for HTTPS
    - SameSite protection
    """
    
    # Extract JWT from secure cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning("No access token cookie found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # Verify JWT token
    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(access_token)
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # Validate CSRF token for state-changing operations
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            logger.warning("Missing CSRF token for state-changing request")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required"
            )
        
        if not csrf_manager.validate_token(csrf_token, payload.get("sub")):
            logger.warning("Invalid CSRF token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
    
    # Extract user information
    user_info = {
        "user_id": payload["sub"],
        "email": payload["email"], 
        "roles": payload.get("roles", []),
        "auth_method": "cookie",
        "csrf_validated": request.method in ["POST", "PUT", "DELETE", "PATCH"]
    }
    
    logger.info(f"Cookie auth successful for user: {user_info['user_id']}")
    return user_info

async def reject_bearer_tokens(request: Request):
    """
    Reject Bearer tokens for enterprise cookie-only authentication
    But allow them for analytics and API endpoints after login
    """
    auth_header = request.headers.get("authorization", "")
    
    # Only reject Bearer tokens on auth-related endpoints
    auth_only_paths = [
        "/auth/token",
        "/auth/refresh-token",
        "/auth/logout"
    ]
    
    # Check if this is an auth-only path where we want cookie-only
    is_auth_only = any(request.url.path.startswith(path) for path in auth_only_paths)
    
    # Only reject Bearer tokens on auth endpoints, allow on analytics/API
    if auth_header.startswith("Bearer ") and is_auth_only:
        logger.warning(f"Rejected Bearer token attempt on auth endpoint from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Bearer tokens not allowed on auth endpoints. Use cookie authentication.",
            headers={"WWW-Authenticate": "Cookie"},
        )
