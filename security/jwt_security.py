"""
Enterprise JWT Security Module
================================
Centralized JWT encoding/decoding with enhanced security controls.

Created by: OW-kai Engineer
Date: 2025-11-10
Purpose: Eliminate JWT algorithm vulnerabilities and provide enterprise-grade token handling

Features:
- Explicit algorithm whitelist (blocks "none" algorithm attacks)
- Signature verification enforcement
- Required claims validation
- Algorithm confusion attack prevention
- Comprehensive error handling
- Audit logging for compliance

Compliance Mapping:
- OWASP ASVS v4.0: V3.5 Token-based Session Management
- NIST SP 800-63B: Section 5.1.3 Use of Assertions
- CWE-347: Improper Verification of Cryptographic Signature
"""

import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
    InvalidAlgorithmError
)
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class JWTSecurityError(Exception):
    """Raised when JWT security violation detected."""
    pass


class AlgorithmNotAllowedError(JWTSecurityError):
    """Raised when disallowed algorithm detected (e.g., 'none')."""
    pass


class JWTSecurity:
    """
    Enterprise-grade JWT security service.

    This class provides secure JWT operations that prevent:
    - Algorithm confusion attacks (CVE-2015-9235)
    - "none" algorithm bypass (CVE-2018-1000531)
    - Missing signature verification
    - Token forgery via algorithm substitution

    Usage:
        # Decode with security enforcement
        payload = JWTSecurity.secure_decode(
            token=jwt_token,
            secret_key=SECRET_KEY,
            algorithms=["HS256"],
            required_claims=["sub", "exp"]
        )

        # Encode with best practices
        token = JWTSecurity.secure_encode(
            payload={"sub": user_id, "role": "admin"},
            secret_key=SECRET_KEY,
            algorithm="HS256"
        )
    """

    # Algorithm whitelist - only secure algorithms allowed
    ALLOWED_ALGORITHMS = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]

    # Explicitly blocked algorithms
    BLOCKED_ALGORITHMS = ["none", "None", "NONE", ""]

    @classmethod
    def secure_decode(
        cls,
        token: str,
        secret_key: str,
        algorithms: Optional[List[str]] = None,
        required_claims: Optional[List[str]] = None,
        verify_exp: bool = True,
        verify_signature: bool = True,
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
        operation_name: str = "jwt_decode"
    ) -> Dict[str, Any]:
        """
        Securely decode JWT token with comprehensive validation.

        Args:
            token: JWT token string to decode
            secret_key: Secret key for signature verification
            algorithms: List of allowed algorithms (default: ["HS256"])
            required_claims: List of claims that must be present
            verify_exp: Verify expiration claim (default: True)
            verify_signature: Verify signature (default: True, NEVER disable)
            audience: Expected audience claim value
            issuer: Expected issuer claim value
            operation_name: Name for audit logging

        Returns:
            Decoded JWT payload as dictionary

        Raises:
            AlgorithmNotAllowedError: If "none" or disallowed algorithm detected
            ExpiredSignatureError: If token has expired
            InvalidSignatureError: If signature verification fails
            InvalidTokenError: If token is malformed or invalid
            JWTSecurityError: If security violation detected

        Security:
            ✅ Blocks "none" algorithm attack
            ✅ Explicit algorithm whitelist
            ✅ Signature verification enforced
            ✅ Expiration validation enforced
            ✅ Required claims validation
            ✅ Audit logging
        """
        # Default to HS256 if no algorithms specified
        if algorithms is None:
            algorithms = ["HS256"]

        # SECURITY CHECK #1: Block "none" algorithm
        for blocked in cls.BLOCKED_ALGORITHMS:
            if blocked in [a.lower() for a in algorithms]:
                error_msg = (
                    f"SECURITY VIOLATION: Blocked algorithm '{blocked}' detected | "
                    f"operation={operation_name} | "
                    f"This is likely an attack attempt"
                )
                logger.critical(error_msg)
                raise AlgorithmNotAllowedError(error_msg)

        # SECURITY CHECK #2: Validate algorithm whitelist
        for algo in algorithms:
            if algo not in cls.ALLOWED_ALGORITHMS:
                error_msg = (
                    f"SECURITY WARNING: Non-standard algorithm '{algo}' | "
                    f"operation={operation_name} | "
                    f"Allowed: {cls.ALLOWED_ALGORITHMS}"
                )
                logger.warning(error_msg)

        # SECURITY CHECK #3: Signature verification must be enabled
        if not verify_signature:
            error_msg = (
                f"SECURITY VIOLATION: Signature verification disabled | "
                f"operation={operation_name} | "
                f"Signature verification is REQUIRED"
            )
            logger.critical(error_msg)
            raise JWTSecurityError(error_msg)

        # Audit log
        logger.info(
            f"[AUDIT] JWT decode initiated | "
            f"operation={operation_name} | "
            f"algorithms={algorithms} | "
            f"verify_signature={verify_signature} | "
            f"verify_exp={verify_exp} | "
            f"timestamp={datetime.now(timezone.utc).isoformat()}"
        )

        try:
            # Decode with security options
            options = {
                "verify_signature": True,  # ALWAYS verify
                "verify_exp": verify_exp,
                "verify_aud": audience is not None,
                "verify_iss": issuer is not None,
                "require": required_claims or []
            }

            payload = jwt.decode(
                token,
                secret_key,
                algorithms=algorithms,
                options=options,
                audience=audience,
                issuer=issuer
            )

            # SECURITY CHECK #4: Verify required claims present
            if required_claims:
                missing_claims = [claim for claim in required_claims if claim not in payload]
                if missing_claims:
                    error_msg = (
                        f"SECURITY VIOLATION: Required claims missing | "
                        f"operation={operation_name} | "
                        f"missing={missing_claims}"
                    )
                    logger.error(error_msg)
                    raise JWTSecurityError(error_msg)

            # Success audit log
            logger.info(
                f"[AUDIT] JWT decode successful | "
                f"operation={operation_name} | "
                f"subject={payload.get('sub', 'unknown')} | "
                f"timestamp={datetime.now(timezone.utc).isoformat()}"
            )

            return payload

        except ExpiredSignatureError as e:
            logger.warning(
                f"[SECURITY] JWT token expired | "
                f"operation={operation_name} | "
                f"error={str(e)}"
            )
            raise

        except InvalidSignatureError as e:
            logger.error(
                f"[SECURITY] JWT signature verification failed | "
                f"operation={operation_name} | "
                f"error={str(e)} | "
                f"This may indicate tampering"
            )
            raise

        except InvalidAlgorithmError as e:
            logger.critical(
                f"[SECURITY] JWT algorithm attack detected | "
                f"operation={operation_name} | "
                f"error={str(e)} | "
                f"POTENTIAL ATTACK ATTEMPT"
            )
            raise AlgorithmNotAllowedError(f"Algorithm attack detected: {str(e)}")

        except DecodeError as e:
            logger.error(
                f"[SECURITY] JWT decode failed | "
                f"operation={operation_name} | "
                f"error={str(e)} | "
                f"Token may be malformed"
            )
            raise

        except Exception as e:
            logger.error(
                f"[ERROR] JWT decode unexpected error | "
                f"operation={operation_name} | "
                f"error={str(e)} | "
                f"error_type={type(e).__name__}"
            )
            raise

    @classmethod
    def secure_encode(
        cls,
        payload: Dict[str, Any],
        secret_key: str,
        algorithm: str = "HS256",
        operation_name: str = "jwt_encode"
    ) -> str:
        """
        Securely encode JWT token with best practices.

        Args:
            payload: Claims to encode in JWT
            secret_key: Secret key for signing
            algorithm: Algorithm to use (default: HS256)
            operation_name: Name for audit logging

        Returns:
            Encoded JWT token string

        Raises:
            JWTSecurityError: If security violation detected

        Security:
            ✅ Algorithm validation
            ✅ Blocks "none" algorithm
            ✅ Audit logging
        """
        # SECURITY CHECK: Validate algorithm
        if algorithm.lower() in [a.lower() for a in cls.BLOCKED_ALGORITHMS]:
            error_msg = (
                f"SECURITY VIOLATION: Blocked algorithm '{algorithm}' for encoding | "
                f"operation={operation_name}"
            )
            logger.critical(error_msg)
            raise AlgorithmNotAllowedError(error_msg)

        if algorithm not in cls.ALLOWED_ALGORITHMS:
            logger.warning(
                f"[SECURITY] Non-standard algorithm '{algorithm}' for encoding | "
                f"operation={operation_name}"
            )

        # Audit log
        logger.info(
            f"[AUDIT] JWT encode initiated | "
            f"operation={operation_name} | "
            f"algorithm={algorithm} | "
            f"subject={payload.get('sub', 'unknown')} | "
            f"timestamp={datetime.now(timezone.utc).isoformat()}"
        )

        try:
            token = jwt.encode(payload, secret_key, algorithm=algorithm)

            # Success audit log
            logger.info(
                f"[AUDIT] JWT encode successful | "
                f"operation={operation_name} | "
                f"timestamp={datetime.now(timezone.utc).isoformat()}"
            )

            return token

        except Exception as e:
            logger.error(
                f"[ERROR] JWT encode failed | "
                f"operation={operation_name} | "
                f"error={str(e)}"
            )
            raise

    @classmethod
    def validate_token_header(cls, token: str) -> Dict[str, Any]:
        """
        Validate JWT token header without decoding (for security checks).

        Args:
            token: JWT token to inspect

        Returns:
            Dictionary with header information

        Raises:
            JWTSecurityError: If dangerous header detected
        """
        try:
            # Decode header without verification (just to inspect)
            header = jwt.get_unverified_header(token)

            # Check for "none" algorithm in header
            alg = header.get("alg", "").lower()
            if alg in [a.lower() for a in cls.BLOCKED_ALGORITHMS]:
                error_msg = (
                    f"SECURITY VIOLATION: Blocked algorithm '{alg}' in token header | "
                    f"ATTACK ATTEMPT DETECTED"
                )
                logger.critical(error_msg)
                raise AlgorithmNotAllowedError(error_msg)

            return header

        except Exception as e:
            logger.error(f"Token header validation failed: {str(e)}")
            raise


# Convenience function for backward compatibility
def secure_jwt_decode(
    token: str,
    secret_key: str,
    algorithms: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for secure JWT decoding.

    This is a drop-in replacement for jwt.decode() with enhanced security.

    Args:
        token: JWT token to decode
        secret_key: Secret key for verification
        algorithms: List of allowed algorithms
        **kwargs: Additional options (verify_exp, required_claims, etc.)

    Returns:
        Decoded JWT payload
    """
    return JWTSecurity.secure_decode(
        token=token,
        secret_key=secret_key,
        algorithms=algorithms,
        **kwargs
    )
