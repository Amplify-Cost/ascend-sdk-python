# auth_routes.py - Updated for enterprise cookie sessions + CSRF (Phase 1, surgical)
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, UTC
import logging
from passlib.context import CryptContext
from auth_utils import verify_password
from auth_utils import hash_password
from secrets import token_urlsafe

from database import get_db
from models import User
from schemas import UserCreate, LoginInput, TokenResponse
from token_utils import create_access_token, create_refresh_token, decode_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from dependencies import get_current_user, require_csrf  # ✅ FIX: Import require_csrf

# Cookie/CSRF constants centralized in security.cookies
from security.cookies import (
    SESSION_COOKIE_NAME,        # typically "access_token"
    CSRF_COOKIE_NAME,           # "owai_csrf"
    CSRF_HEADER_NAME,           # "X-CSRF-Token"
    COOKIE_SAMESITE,            # "None" or "Lax"/"Strict"
    COOKIE_SECURE,              # bool
    COOKIE_HTTPONLY             # bool (True for session)
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Existing cookie defaults, respected in dev/prod
COOKIE_CONFIG = {
    "secure": True,       # HTTPS only in prod
    "httponly": True,     # HttpOnly for session cookie
    "samesite": "strict", # overridden to "lax" in dev below
    "path": "/",
    "domain": None,
}

def get_cookie_config(request: Request) -> dict:
    """Derive cookie config per environment (dev vs prod)."""
    config = COOKIE_CONFIG.copy()
    # In dev (localhost), allow insecure and relax SameSite so your SPA works.
    if request.url.hostname in {"localhost", "127.0.0.1"}:
        config["secure"] = False
        config["samesite"] = "lax"
    return config

def detect_auth_preference(request: Request) -> str:
    """
    Detect client preference (header-driven). Defaults to 'token'
    to avoid surprises; you can switch default to 'cookie' later.
    """
    mode = (request.headers.get("X-Auth-Mode") or "").lower()
    if mode in {"cookie", "cookies"}:
        return "cookie"
    return "token"

def _set_csrf_cookie(response: Response, request: Request) -> str:
    """
    Issue a non-HttpOnly CSRF cookie for double-submit protection.
    The frontend will echo this value in the X-CSRF-Token header
    for any POST/PUT/PATCH/DELETE request.
    """
    csrf = token_urlsafe(32)
    cookie_cfg = get_cookie_config(request)
    # CSRF cookie is NOT HttpOnly (frontend must read it)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf,
        httponly=False,
        secure=cookie_cfg.get("secure", True),
        samesite=cookie_cfg.get("samesite", "lax"),
        path="/",
        max_age=60 * 30,  # 30 minutes
    )
    return csrf

@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """User registration with dual auth support + CSRF issuance for cookie mode."""
    try:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        password_hash = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password=password_hash,
            role="user",
            is_active=True,
            created_at=datetime.now(UTC)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # JWTs
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

        auth_mode = detect_auth_preference(request)
        if auth_mode == "cookie":
            cfg = get_cookie_config(request)

            # Set session (HttpOnly) cookie for access token
            response.set_cookie(
                key=SESSION_COOKIE_NAME,  # typically "access_token"
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,           # enforce HttpOnly on session
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            # Set refresh token cookie (NOT HttpOnly is okay, but safer as HttpOnly too)
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,                      # make refresh HttpOnly in enterprise
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )

            # Issue CSRF cookie for double-submit protection
            _set_csrf_cookie(response, request)

            logger.info(f"✅ User registered with cookie auth: {new_user.email}")
            return TokenResponse(  # keep schema: empty tokens in cookie mode
                access_token="",
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        # Legacy token mode (no cookies)
        logger.info(f"✅ User registered with token auth: {new_user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")

@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginInput,
    db: Session = Depends(get_db)
):
    """Login with dual auth support + CSRF issuance for cookie mode."""
    try:
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.password):
            logger.warning(f"❌ Failed login attempt: {login_data.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

        user.last_login = datetime.now(UTC)
        db.commit()

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

        auth_mode = detect_auth_preference(request)
        if auth_mode == "cookie":
            cfg = get_cookie_config(request)

            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )

            _set_csrf_cookie(response, request)

            logger.info(f"✅ Cookie-based login: {user.email}")
            return TokenResponse(
                access_token="",
                refresh_token="",
                token_type="cookie",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        # Legacy token mode
        logger.info(f"✅ Token-based login: {user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    _=Depends(require_csrf)  # ✅ FIX: Now properly imported
):
    """Logout: clear session/refresh and CSRF cookies."""
    try:
        cfg = get_cookie_config(request)
        # Expire immediately
        expire_now = {**cfg, "max_age": 0}

        response.set_cookie(key=SESSION_COOKIE_NAME, value="", **expire_now)
        response.set_cookie(key="refresh_token", value="", **expire_now)
        response.set_cookie(key=CSRF_COOKIE_NAME, value="", httponly=False, **expire_now)

        logger.info(f"✅ User logged out: {current_user.get('email')}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return {"message": "Logout completed"}

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access/refresh tokens; for cookie mode, also keep CSRF fresh."""
    try:
        # Try cookie refresh first
        refresh_tok = request.cookies.get("refresh_token")
        auth_mode = "cookie" if refresh_tok else "token"

        if not refresh_tok:
            # Legacy: read from body
            body = await request.json()
            refresh_tok = (body or {}).get("refresh_token")

        if not refresh_tok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required")

        payload = decode_token(refresh_tok)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        new_access = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access"
        })
        new_refresh = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh"
        })

        if auth_mode == "cookie":
            cfg = get_cookie_config(request)
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=new_access,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=cfg["secure"],
                httponly=COOKIE_HTTPONLY,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                secure=cfg["secure"],
                httponly=True,
                samesite=cfg["samesite"],
                path=cfg["path"],
                domain=cfg["domain"],
            )
            # Also rotate CSRF so client has a fresh token
            _set_csrf_cookie(response, request)
            return TokenResponse(access_token="", refresh_token="", token_type="cookie", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        # Legacy/bearer mode
        return TokenResponse(access_token=new_access, refresh_token=new_refresh, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed")

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Return current user for UI session checks."""
    try:
        return {
            "id": current_user.get("user_id") or current_user.get("sub"),
            "email": current_user.get("email"),
            "role": current_user.get("role"),
            "auth_method": current_user.get("auth_method", "cookie"),
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=401, detail="Unable to retrieve user information")

@router.get("/csrf", tags=["auth"])
def get_csrf(response: Response, request: Request):
    """Issue/refresh CSRF cookie and return its value."""
    csrf = _set_csrf_cookie(response, request)
    return {"csrf": csrf}
