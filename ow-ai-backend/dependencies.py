# dependencies.py - Enterprise cookie sessions + CSRF (Phase 1, surgical)
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
import logging

from config import SECRET_KEY, ALGORITHM
from security.cookies import (
    SESSION_COOKIE_NAME,       # e.g., "access_token"
    CSRF_COOKIE_NAME,          # "owai_csrf"
    CSRF_HEADER_NAME,          # "X-CSRF-Token"
    # Feature flag: allow bearer during migration (set in security.cookies)
    ALLOW_BEARER_FOR_MIGRATION
)

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # do not auto-error: we support cookie fallback

def _decode_jwt(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Enterprise user extraction:
    1) Prefer cookie session (HttpOnly JWT in SESSION_COOKIE_NAME)
    2) Optionally allow Bearer token during migration (if flag enabled)
    """
    # 1) Cookie session
    cookie_jwt = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_jwt:
        try:
            payload = _decode_jwt(cookie_jwt)
            payload["auth_method"] = "cookie"
            request.state.auth = payload
            logger.info(f"✅ Authentication successful (cookie): {payload.get('email')}")
            return {
                "user_id": int(payload.get("sub")) if payload.get("sub") else None,
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "auth_method": "cookie",
                **payload
            }
        except JWTError as e:
            logger.error(f"JWT decode error (cookie): {str(e)}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    # 2) Migration fallback: Bearer
    if ALLOW_BEARER_FOR_MIGRATION:
        if credentials and credentials.credentials:
            try:
                payload = _decode_jwt(credentials.credentials)
                payload["auth_method"] = "bearer"
                request.state.auth = payload
                logger.info(f"✅ Authentication successful (bearer): {payload.get('email')}")
                return {
                    "user_id": int(payload.get("sub")) if payload.get("sub") else None,
                    "email": payload.get("email"),
                    "role": payload.get("role", "user"),
                    "auth_method": "bearer",
                    **payload
                }
            except JWTError as e:
                logger.error(f"JWT decode error (bearer): {str(e)}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    # Neither cookie nor allowed bearer present
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )

def require_csrf(request: Request):
    """
    Enforce CSRF double-submit for mutating methods when using cookies.
    Safe methods (GET/HEAD/OPTIONS) are not checked.
    """
    method = (request.method or "GET").upper()
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            raise HTTPException(status_code=403, detail="CSRF validation failed")
    return True

def require_admin(current_user: dict = Depends(get_current_user)):
    """Role guard: admin."""
    if current_user.get("role") != "admin":
        logger.warning(f"❌ Admin access denied for: {current_user.get('email')}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    logger.info(f"✅ Admin access granted: {current_user.get('email')}")
    return current_user

def require_manager_or_admin(current_user: dict = Depends(get_current_user)):
    """Role guard: manager or admin."""
    if current_user.get("role") not in {"manager", "admin"}:
        logger.warning(f"❌ Manager/Admin access denied for: {current_user.get('email')}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or Admin access required")
    return current_user

# Legacy alias for now (keeps existing imports working)
verify_token = get_current_user
