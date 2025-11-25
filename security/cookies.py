# security/cookies.py
# =============================================================================
# ENTERPRISE BANKING-LEVEL COOKIE SECURITY CONFIGURATION
# =============================================================================
# Engineer: OW-KAI Enterprise Security Team
# Date: 2025-11-24
# Security Level: Banking/Financial Services Grade
#
# COMPLIANCE:
# - PCI-DSS 6.5.9: CSRF Protection
# - OWASP ASVS 3.1.3: Cookie Security
# - NIST SP 800-63B: Session Management
# - SOC 2 CC6.1: Logical Access Controls
# =============================================================================

import os
import logging

logger = logging.getLogger("enterprise.cookies")

# Cookie Names
SESSION_COOKIE_NAME = "owai_session"
CSRF_COOKIE_NAME = "owai_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

# =============================================================================
# ENTERPRISE SECURITY: Environment-based cookie configuration
# =============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"

# Cookie security settings based on environment
COOKIE_SECURE = IS_PRODUCTION  # True in production (HTTPS required)
COOKIE_HTTPONLY = True  # Always true - prevents XSS from accessing cookies

# ENTERPRISE BANKING-LEVEL: SameSite=Strict for maximum CSRF protection
# - "Strict": Cookie only sent for same-site requests (highest security)
# - "Lax": Cookie sent for same-site and top-level navigations
# We use "Strict" in production, "Lax" in development for localhost testing
COOKIE_SAMESITE = "Strict" if IS_PRODUCTION else "Lax"

# =============================================================================
# BEARER TOKEN: DISABLED - Cookie-only authentication
# =============================================================================
# Enterprise security requires HttpOnly cookie authentication only.
# Bearer tokens in browsers are vulnerable to XSS token theft.
# API-to-API calls should use API keys, not bearer tokens.
# =============================================================================
ALLOW_BEARER_FOR_MIGRATION = False  # DISABLED - Use cookies only

logger.info(f"Cookie Security: Environment={ENVIRONMENT}, Secure={COOKIE_SECURE}, SameSite={COOKIE_SAMESITE}")
