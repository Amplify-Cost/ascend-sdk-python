"""
Authentication dependencies for RS256 JWT tokens
IMPORTANT: This replaces all HS256 authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt_manager import get_jwt_manager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Security scheme - only accepts Bearer tokens
security = HTTPBearer()

class TokenValidationError(Exception):
    """Custom exception for token validation errors"""
    pass

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and verify user from RS256 JWT token
    
    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Verifies token using RS256 public key
    3. Returns user information from token payload
    4. REJECTS any HS256 tokens
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    try:
        token = credentials.credentials
        
        # Verify token using JWT manager (RS256 only)
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(token)
        
        # Extract user information
        user_info = {
            "user_id": payload["sub"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "token_type": "access"
        }
        
        logger.info(f"Successfully authenticated user: {user_info['user_id']}")
        return user_info
        
    except Exception as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any] | None:
    """Optional authentication - returns None if no valid token"""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_roles(required_roles: list):
    """Create a dependency that requires specific roles
    
    Usage:
        admin_required = require_roles(["admin"])
        
        @app.get("/admin-only")
        async def admin_route(user: dict = Depends(admin_required)):
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user
    
    return role_checker

# Convenience role dependencies
require_admin = require_roles(["admin"])
require_user = require_roles(["user", "admin"])
require_moderator = require_roles(["moderator", "admin"])
