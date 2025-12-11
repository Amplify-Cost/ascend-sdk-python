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

# =============================================================================
# SEC-087: Enterprise SameSite=Lax (Datadog/Wiz/Splunk standard)
# =============================================================================
# ASCEND sends notifications (Slack, Teams, email) with direct links to the
# dashboard. SameSite=Strict breaks UX when users click notification links
# because the browser won't send the session cookie on cross-site navigation.
#
# CSRF protection is enforced via X-CSRF-Token header validation (double-submit
# cookie pattern), NOT via SameSite attribute. This is the enterprise standard
# used by Datadog, Wiz, Splunk, and other security platforms.
#
# Security layers:
# 1. HttpOnly=True: Prevents XSS from reading cookies
# 2. Secure=True: HTTPS-only transmission in production
# 3. SameSite=Lax: Allows top-level navigation (notification links)
# 4. X-CSRF-Token: Header validation for state-changing requests
# =============================================================================
COOKIE_SAMESITE = "Lax"  # Enterprise standard for notification-driven platforms

# =============================================================================
# BEARER TOKEN: DISABLED - Cookie-only authentication
# =============================================================================
# Enterprise security requires HttpOnly cookie authentication only.
# Bearer tokens in browsers are vulnerable to XSS token theft.
# API-to-API calls should use API keys, not bearer tokens.
# =============================================================================
ALLOW_BEARER_FOR_MIGRATION = False  # DISABLED - Use cookies only

logger.info(f"Cookie Security: Environment={ENVIRONMENT}, Secure={COOKIE_SECURE}, SameSite={COOKIE_SAMESITE}")
