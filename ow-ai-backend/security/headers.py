"""
Enterprise Security Headers Middleware

OWASP-compliant security headers for banking-level protection.
Implements defense-in-depth against:
- Clickjacking (X-Frame-Options)
- XSS (X-XSS-Protection, CSP)
- MIME sniffing (X-Content-Type-Options)
- Protocol downgrade (Strict-Transport-Security)
- Information leakage (X-Powered-By removal, Referrer-Policy)

Engineer: OW-KAI Enterprise Security
Date: 2025-11-24
Compliance: SOC 2, PCI-DSS, HIPAA
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Environment detection
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enterprise security headers middleware.

    Adds OWASP-recommended security headers to all responses.
    Headers are configured based on environment (production vs development).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # === CLICKJACKING PROTECTION ===
        # DENY: Never allow framing (most secure for banking apps)
        response.headers["X-Frame-Options"] = "DENY"

        # === XSS PROTECTION ===
        # Modern CSP makes this mostly redundant, but defense-in-depth
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # === MIME SNIFFING PROTECTION ===
        # Prevent browsers from MIME-sniffing responses
        response.headers["X-Content-Type-Options"] = "nosniff"

        # === CONTENT SECURITY POLICY ===
        # Strict CSP for API responses (no inline scripts/styles needed)
        csp_directives = [
            "default-src 'none'",  # Block everything by default
            "frame-ancestors 'none'",  # Additional clickjacking protection
            "base-uri 'self'",  # Prevent base tag hijacking
            "form-action 'self'",  # Restrict form submissions
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # === TRANSPORT SECURITY (HSTS) ===
        # Only set in production with HTTPS
        if IS_PRODUCTION:
            # max-age=2 years, include subdomains, preload eligible
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # === REFERRER POLICY ===
        # Don't leak URLs in referrer header
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # === PERMISSIONS POLICY ===
        # Disable unnecessary browser features
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # === REMOVE SERVER FINGERPRINTING ===
        # Don't reveal server technology
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        # === CACHE CONTROL FOR SENSITIVE DATA ===
        # API responses should not be cached by default
        if "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # === CROSS-ORIGIN POLICIES ===
        # Prevent cross-origin information leakage
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response


def get_cors_origins() -> list:
    """
    Get CORS origins from environment or use secure defaults.

    Production: Only allow explicitly configured origins
    Development: Allow localhost variants

    Returns:
        List of allowed origin strings
    """
    # Check environment variable first (comma-separated)
    env_origins = os.getenv("ALLOWED_ORIGINS", "")

    if env_origins:
        # Parse environment variable
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        # Use defaults based on environment
        if IS_PRODUCTION:
            origins = [
                "https://pilot.owkai.app",
                "https://app.owkai.app",
            ]
        else:
            origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:5174",
                "http://localhost:5175",
                "http://localhost:4173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]

    return origins
