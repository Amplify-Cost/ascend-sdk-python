# dependencies.py - Updated for dual authentication support (PHASE 1)
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
import logging
from typing import Optional

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # Don't auto-error for cookie fallback

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current authenticated user with dual auth support"""
    try:
        token = None
        auth_method = "unknown"
        
        # Try Bearer token first (legacy mode)
        if credentials and credentials.credentials:
            token = credentials.credentials
            auth_method = "bearer"
        
        # Fallback to cookie-based auth
        if not token:
            token = request.cookies.get("access_token")
            if token:
                auth_method = "cookie"
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as e:
            logger.error(f"JWT decode error ({auth_method}): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token type
        if payload.get("type") and payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token: user ID missing"
            )
        
        # Log successful authentication (enterprise audit)
        logger.info(f"✅ Authentication successful ({auth_method}): {email}")
        
        return {
            "user_id": int(user_id),
            "email": email,
            "role": role,
            "auth_method": auth_method  # Track auth method for analytics
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Token parsing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role with enterprise logging"""
    if current_user.get("role") != "admin":
        logger.warning(f"❌ Admin access denied for: {current_user.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    logger.info(f"✅ Admin access granted: {current_user.get('email')}")
    return current_user

def require_manager_or_admin(current_user: dict = Depends(get_current_user)):
    """Require manager or admin role"""
    allowed_roles = ["manager", "admin"]
    if current_user.get("role") not in allowed_roles:
        logger.warning(f"❌ Manager/Admin access denied for: {current_user.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    
    return current_user

# Legacy compatibility - remove in Phase 3
verify_token = get_current_user