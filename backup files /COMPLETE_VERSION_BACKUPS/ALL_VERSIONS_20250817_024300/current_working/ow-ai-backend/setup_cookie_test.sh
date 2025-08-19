#!/bin/bash

# Cookie Authentication Test Setup Script
# Automatically sets up simplified local testing environment

set -e  # Exit on any error

echo "🍪 Setting up Cookie Authentication Test Environment..."
echo "=================================================="

# Navigate to backend directory
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

echo "📁 Current directory: $(pwd)"

# Step 1: Create Local JWT Manager
echo "🔧 Creating local JWT manager..."
cat > local_jwt_manager.py << 'EOF'
"""
Local JWT Manager for Testing Cookie Auth
Uses local keys instead of AWS
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

class LocalJWTManager:
    def __init__(self):
        self.secret_key = os.getenv("LOCAL_JWT_SECRET", "test_secret_key_for_cookie_auth_demo_only")
        self.algorithm = "HS256"  # Using HS256 for local testing simplicity
        self.issuer = "ow-ai-local-test"
        self.audience = "ow-ai-api"
    
    def issue_token(self, user_id: str, user_email: str, roles: list = None, expires_in_minutes: int = 60) -> str:
        """Issue a test JWT token"""
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)
        
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "email": user_email,
            "roles": roles or [],
            "iat": now,
            "exp": exp,
            "jti": f"{user_id}-{int(now.timestamp())}"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

# Global instance
local_jwt_manager = LocalJWTManager()

def get_jwt_manager():
    """Get JWT manager (local version for testing)"""
    return local_jwt_manager
EOF

echo "✅ Local JWT manager created"

# Step 2: Create Simple Dependencies
echo "🔧 Creating simple dependencies..."
# Backup original dependencies
if [ -f "dependencies.py" ]; then
    cp dependencies.py dependencies_backup_$(date +%Y%m%d_%H%M%S).py
    echo "📦 Backed up original dependencies.py"
fi

cat > dependencies_simple.py << 'EOF'
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
EOF

echo "✅ Simple dependencies created"

# Step 3: Create Simple Auth Routes
echo "🔧 Creating simple auth routes..."
cat > simple_auth_routes.py << 'EOF'
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
EOF

echo "✅ Simple auth routes created"

# Step 4: Backup and Update main.py
echo "🔧 Updating main.py..."
if [ -f "main.py" ]; then
    cp main.py main_backup_$(date +%Y%m%d_%H%M%S).py
    echo "📦 Backed up original main.py"
fi

# Create a simplified main.py for testing
cat > main_simple.py << 'EOF'
"""
Simplified main.py for cookie authentication testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import our simple components
from simple_auth_routes import router as auth_router
from local_jwt_manager import get_jwt_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cookie Auth Test",
    description="Testing cookie-based authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Cookie Auth Test Server", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "auth": "cookie-test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

echo "✅ Simplified main.py created"

# Step 5: Update .env file for local testing
echo "🔧 Updating .env file..."
if [ -f ".env" ]; then
    cp .env .env_backup_$(date +%Y%m%d_%H%M%S)
    echo "📦 Backed up original .env"
fi

# Add local JWT settings to .env
echo "" >> .env
echo "# Local JWT Testing" >> .env
echo "USE_LOCAL_JWT=true" >> .env
echo "LOCAL_JWT_SECRET=test_secret_key_for_cookie_auth_demo_only" >> .env

echo "✅ .env file updated"

# Step 6: Create test script
echo "🧪 Creating test script..."
cat > test_cookie_auth.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Cookie Authentication..."
echo "================================="

# Test 1: Health check
echo "Test 1: Health check"
curl -s http://localhost:8000/health
echo ""

# Test 2: Login and get cookie
echo "Test 2: Login (should set cookie)"
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  -c cookies.txt \
  -s | python -m json.tool
echo ""

# Test 3: Check if cookie was set
echo "Test 3: Cookie file contents"
cat cookies.txt
echo ""

# Test 4: Use cookie to access protected endpoint
echo "Test 4: Access /auth/me with cookie"
curl -s http://localhost:8000/auth/me -b cookies.txt | python -m json.tool
echo ""

# Test 5: Logout (clear cookie)
echo "Test 5: Logout (clear cookie)"
curl -X POST http://localhost:8000/auth/logout -b cookies.txt -c cookies.txt -s | python -m json.tool
echo ""

echo "✅ Cookie authentication tests completed!"
EOF

chmod +x test_cookie_auth.sh
echo "✅ Test script created and made executable"

# Step 7: Create startup script
echo "🚀 Creating startup script..."
cat > start_cookie_test.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Cookie Authentication Test Server..."
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "main_simple.py" ]; then
    echo "❌ main_simple.py not found. Run setup script first."
    exit 1
fi

# Start the server
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python main_simple.py
EOF

chmod +x start_cookie_test.sh
echo "✅ Startup script created"

# Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📁 Files created:"
echo "  • local_jwt_manager.py (Local JWT handling)"
echo "  • dependencies_simple.py (Simple auth dependencies)"
echo "  • simple_auth_routes.py (Test auth routes)"
echo "  • main_simple.py (Simplified main app)"
echo "  • test_cookie_auth.sh (Test script)"
echo "  • start_cookie_test.sh (Startup script)"
echo ""
echo "🚀 To start the test server:"
echo "  ./start_cookie_test.sh"
echo ""
echo "🧪 To test cookie authentication (in another terminal):"
echo "  ./test_cookie_auth.sh"
echo ""
echo "🌐 Or test in browser:"
echo "  http://localhost:8000/"
echo ""
echo "✅ Ready for cookie authentication testing!"
