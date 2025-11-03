#!/bin/bash

echo "🔧 Creating Enterprise Rate Limiting Module..."
echo ""

# Navigate to backend directory
cd ow-ai-backend || { echo "❌ Error: ow-ai-backend directory not found"; exit 1; }

# Create security directory if it doesn't exist
if [ ! -d "security" ]; then
    mkdir -p security
    echo "✅ Created security/ directory"
else
    echo "✅ security/ directory already exists"
fi

# Create __init__.py if it doesn't exist
if [ ! -f "security/__init__.py" ]; then
    touch security/__init__.py
    echo "✅ Created security/__init__.py"
fi

# Create rate_limiter.py
cat > security/rate_limiter.py << 'PYTHON_EOF'
"""
Enterprise Rate Limiting Configuration
Prevents brute force attacks on authentication endpoints
Compliant with: SOC2, ISO27001, OWASP ASVS
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Enterprise rate limiting configuration
# These limits are per IP address per time window

RATE_LIMITS = {
    "auth_login": "5/minute",      # Login endpoint - most restrictive
    "auth_refresh": "10/minute",   # Token refresh - moderate
    "auth_csrf": "20/minute",      # CSRF token generation - lenient
    "default": "60/minute"         # Default for non-auth endpoints
}

# Initialize the limiter with IP-based key function
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global fallback
    enabled=True,
    headers_enabled=True,  # Include rate limit headers in response
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors
    Returns user-friendly message without leaking security info
    """
    logger.warning(
        f"Rate limit exceeded for IP {request.client.host} on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later.",
            "retry_after": "60 seconds"
        },
        headers={
            "Retry-After": "60"
        }
    )
PYTHON_EOF

echo "✅ Created security/rate_limiter.py"
echo ""
echo "📊 File created successfully:"
ls -lh security/rate_limiter.py
echo ""
echo "📝 File contents preview (first 20 lines):"
head -20 security/rate_limiter.py
echo ""
echo "✅ Rate limiter module created successfully!"

