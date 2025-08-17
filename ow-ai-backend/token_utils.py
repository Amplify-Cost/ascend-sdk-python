<<<<<<< HEAD
"""
Token utilities for RS256 JWT handling
IMPORTANT: This file replaces all HS256 JWT functionality
"""

from .jwt_manager import get_jwt_manager
from typing import Dict, Any

def create_access_token(user_id: str, user_email: str, roles: list = None, expires_in_minutes: int = 60) -> str:
    """Create access token using RS256
    
    REPLACES: All HS256 token creation functions
    """
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.issue_token(user_id, user_email, roles, expires_in_minutes)

def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify access token using RS256
    
    REPLACES: All HS256 token verification functions
    """
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.verify_token(token)

def create_refresh_token(user_id: str, user_email: str) -> str:
    """Create refresh token with longer expiration"""
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.issue_token(user_id, user_email, expires_in_minutes=60*24*7)  # 7 days

# Legacy function names for backward compatibility
def generate_token(*args, **kwargs):
    """Legacy wrapper - use create_access_token instead"""
    import warnings
    warnings.warn("generate_token is deprecated, use create_access_token", DeprecationWarning)
    return create_access_token(*args, **kwargs)

def decode_token(token: str) -> Dict[str, Any]:
    """Legacy wrapper - use verify_access_token instead"""
    import warnings
    warnings.warn("decode_token is deprecated, use verify_access_token", DeprecationWarning)
    return verify_access_token(token)
=======
# token_utils.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
>>>>>>> 894b585 (Initial commit: Enterprise JWT + AWS Secrets Manager implementation)
