"""
Enterprise Rate Limiting Configuration
Prevents brute force attacks on authentication endpoints

COMPLIANCE:
- SOC 2 CC6.1: Logical Access Controls
- ISO 27001 A.9.4.3: Password Management
- OWASP ASVS 2.3.1: Rate Limiting
- NIST SP 800-63B 5.2.5: Throttling

Engineer: OW-KAI Enterprise Security Team
Date: 2025-11-24
Security Level: Banking/Financial Services Grade
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import os

logger = logging.getLogger(__name__)

# =============================================================================
# ENTERPRISE BANKING-LEVEL RATE LIMITING CONFIGURATION
# =============================================================================
# These limits are per IP address per time window
# CRITICAL: Authentication endpoints have strict limits to prevent brute force
# =============================================================================

RATE_LIMITS = {
    # Authentication - STRICT limits (brute force protection)
    "auth_login": os.getenv("RATE_LIMIT_LOGIN", "5/minute"),           # Login attempts
    "auth_refresh": os.getenv("RATE_LIMIT_REFRESH", "10/minute"),      # Token refresh
    "auth_csrf": os.getenv("RATE_LIMIT_CSRF", "20/minute"),            # CSRF token generation

    # Password operations - VERY STRICT (credential stuffing protection)
    "auth_password_change": os.getenv("RATE_LIMIT_REDACTED-CREDENTIAL_CHANGE", "3/minute"),   # Password change
    "auth_password_reset": os.getenv("RATE_LIMIT_REDACTED-CREDENTIAL_RESET", "3/minute"),     # Forgot password
    "auth_password_verify": os.getenv("RATE_LIMIT_REDACTED-CREDENTIAL_VERIFY", "5/minute"),   # Password verification

    # MFA operations - STRICT (OTP guessing protection)
    "auth_mfa_setup": os.getenv("RATE_LIMIT_MFA_SETUP", "5/minute"),    # MFA setup
    "auth_mfa_verify": os.getenv("RATE_LIMIT_MFA_VERIFY", "10/minute"), # MFA verification

    # User enumeration protection - STRICT
    "auth_user_lookup": os.getenv("RATE_LIMIT_USER_LOOKUP", "10/minute"),  # User existence check

    # Account operations - MODERATE
    "auth_register": os.getenv("RATE_LIMIT_REGISTER", "3/minute"),     # Registration
    "auth_logout": os.getenv("RATE_LIMIT_LOGOUT", "30/minute"),        # Logout

    # API operations - STANDARD
    "api_read": os.getenv("RATE_LIMIT_API_READ", "100/minute"),        # Read operations
    "api_write": os.getenv("RATE_LIMIT_API_WRITE", "30/minute"),       # Write operations

    # Default fallback
    "default": os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
}

# =============================================================================
# ENTERPRISE: IP-based blocking for repeated violations
# =============================================================================

VIOLATION_THRESHOLDS = {
    "soft_block_threshold": 10,    # Number of rate limit hits before soft block
    "soft_block_duration": 300,    # 5 minutes soft block
    "hard_block_threshold": 25,    # Number of rate limit hits before hard block
    "hard_block_duration": 3600,   # 1 hour hard block
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
