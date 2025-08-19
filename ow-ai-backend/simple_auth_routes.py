"""
Simple auth routes for testing cookie authentication
"""

from fastapi import APIRouter, HTTPException, Response, Request, Form
from local_jwt_manager import get_jwt_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def test_login(
    response: Response, 
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Simple test login that sets cookies"""
    
    # For testing, accept any login
    test_user = {
        "user_id": "test_123",
        "email": f"{username}@example.com",
        "role": "admin"
    }
    
    # Create JWT token
    jwt_mgr = get_jwt_manager()
    access_token = jwt_mgr.issue_token(
        user_id=test_user["user_id"],
        user_email=test_user["email"],
        roles=[test_user["role"]]
    )
    
    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # False for localhost testing
        samesite="lax",
        max_age=3600,
        path="/"
    )
    
    logger.info("✅ Test login successful - cookie set")
    
    return {
        "message": "Login successful",
        "user": test_user,
        "auth_method": "cookie",
        "access_token": access_token  # Also return for testing
    }

@router.post("/token")
async def test_login_json(response: Response, request: Request):
    """Alternative login endpoint for JSON requests"""
    
    body = await request.json()
    username = body.get("username", "test")
    password = body.get("password", "test")
    
    # For testing, accept any login
    test_user = {
        "user_id": "test_123",
        "email": f"{username}@example.com",
        "role": "admin"
    }
    
    # Create JWT token
    jwt_mgr = get_jwt_manager()
    access_token = jwt_mgr.issue_token(
        user_id=test_user["user_id"],
        user_email=test_user["email"],
        roles=[test_user["role"]]
    )
    
    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600,
        path="/"
    )
    
    logger.info("✅ Test login successful (JSON) - cookie set")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": test_user,
        "auth_method": "cookie"
    }

@router.get("/me")
async def get_user_info(request: Request):
    """Test endpoint to check if cookie auth works"""
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No cookie found")
    
    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(access_token)
        
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "auth_method": "cookie",
            "message": "Cookie authentication working!"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid cookie: {e}")

@router.post("/logout")
async def logout(response: Response):
    """Clear cookies"""
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0,
        path="/"
    )
    
    return {"message": "Logged out - cookie cleared"}

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Auth routes are working!", "status": "ok"}
