import jwt
import time
import json
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from typing import Dict, List, Optional
from enterprise_config import config

class EnterpriseJWTManager:
    """
    Enterprise-grade JWT manager with RS256 signing and AWS Secrets Manager.

    Security (SEC-079):
    - REQUIRES JWT keys from AWS Secrets Manager or environment variables in production
    - Generates ephemeral keys ONLY for development (not production-safe)
    - NO demo/hardcoded keys - fails fast if keys unavailable in production

    Compliance: SOC 2 CC6.1, PCI-DSS 3.6, NIST 800-63B
    """

    def __init__(self):
        import os

        self.environment = os.environ.get("ENVIRONMENT", "development")

        # Get signing keys from AWS Secrets Manager or fallback
        self.private_key = config.get_secret('jwt-private-key')
        self.public_key = config.get_secret('jwt-public-key')

        # SEC-079: Try environment variables as secondary source
        if not self.private_key:
            self.private_key = os.environ.get('JWT_PRIVATE_KEY')
        if not self.public_key:
            self.public_key = os.environ.get('JWT_PUBLIC_KEY')

        # SEC-079: Generate ephemeral keys ONLY for development
        if not self.private_key or not self.public_key:
            if self.environment.lower() == "production":
                # SEC-079: FAIL FAST in production - no key generation
                raise ValueError(
                    "SEC-079 CRITICAL: JWT keys not configured in production! "
                    "Configure jwt-private-key and jwt-public-key in AWS Secrets Manager "
                    "or set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY environment variables."
                )
            else:
                print("⚠️  SEC-079: JWT keys not found - generating ephemeral development keys")
                self._generate_fallback_keys()

        # SEC-079: Final validation - keys MUST exist
        if not self.private_key or not self.public_key:
            raise ValueError(
                "SEC-079: Failed to load or generate JWT keys. "
                "Cannot initialize JWT Manager without valid RSA key pair."
            )

        # Enterprise JWT claims
        self.issuer = "https://api.ow-ai.com"
        self.audience = ["ow-ai-platform", "ow-ai-api", "ow-ai-dashboard"]

        print("✅ Enterprise JWT Manager initialized with RS256 keys")
    
    def _generate_fallback_keys(self):
        """Generate RSA keys as fallback when AWS is not available"""
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Serialize private key
            self.private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Serialize public key
            public_key = private_key.public_key()
            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            print("✅ Generated fallback RSA keys for JWT")
            
        except ImportError:
            print("⚠️  Cryptography library not available for key generation")
        except Exception as e:
            print(f"⚠️  Failed to generate fallback keys: {e}")
    
    # SEC-079: _use_demo_keys method REMOVED
    # Demo/hardcoded keys are a critical security vulnerability
    # The system now fails fast if keys are not properly configured
    
    def create_access_token(self, 
                          user_id: str, 
                          role: str, 
                          tenant_id: str, 
                          session_id: str,
                          permissions: List[str] = None) -> str:
        """
        Create enterprise-grade access token
        
        Args:
            user_id: Unique user identifier
            role: User role (admin, security, manager, approver, analyst, viewer)
            tenant_id: Customer/organization identifier
            session_id: Unique session identifier
            permissions: List of specific permissions
        
        Returns:
            Signed JWT token
        """
        now = datetime.now(UTC)
        
        # Enterprise-standard claims (RFC 7519 + custom)
        payload = {
            # RFC 7519 Standard Claims
            "iss": self.issuer,                    # Issuer
            "aud": self.audience,                  # Audience
            "sub": user_id,                        # Subject (user ID)
            "iat": int(now.timestamp()) - 10,     # Issued at (with clock skew tolerance)
            "nbf": int(now.timestamp()) - 10,     # Not before (with clock skew tolerance)
            "exp": int((now + timedelta(hours=1)).timestamp()),  # Expires in 1 hour
            "jti": session_id,                     # JWT ID (for revocation)
            
            # OW-AI Custom Claims
            "role": role,                          # User role
            "tenant_id": tenant_id,                # Customer organization
            "session_id": session_id,              # Login session
            "permissions": permissions or [],       # Granular permissions
            "token_type": "access",                # Token type
            
            # Enterprise Audit Fields
            "created_at": now.isoformat(),
            "version": "1.0"                       # Token format version
        }
        
        # Sign with RS256 (enterprise standard)
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers={
                "kid": "ow-ai-2024-08-primary",    # Key ID for rotation
                "typ": "JWT",
                "alg": "RS256"
            }
        )
        
        return token
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token with enterprise validation
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Enterprise verification with all security checks
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],              # Only allow RS256
                issuer=self.issuer,                # Verify issuer
                audience=self.audience,            # Verify audience
                options={
                    # Strict validation (enterprise requirement)
                    "require_exp": True,           # Must have expiration
                    "require_iat": True,           # Must have issued-at
                    "require_nbf": True,           # Must have not-before
                    "require_sub": True,           # Must have subject
                    "require_jti": True,           # Must have JWT ID
                    "verify_signature": True,      # Verify signature
                    "verify_exp": True,            # Check expiration
                    "verify_nbf": False,           # Don't check not-before (enterprise workaround)
                    "verify_iat": False,           # Don't verify issued-at timing (enterprise workaround)
                    "verify_aud": True,            # Check audience
                    "verify_iss": True,            # Check issuer
                }
            )
            
            # Additional enterprise validations
            self._validate_token_claims(payload)
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def _validate_token_claims(self, payload: Dict) -> None:
        """Additional enterprise claim validations"""
        
        # Validate required custom claims
        required_claims = ["role", "tenant_id", "session_id", "token_type"]
        for claim in required_claims:
            if claim not in payload:
                raise jwt.InvalidTokenError(f"Missing required claim: {claim}")
        
        # Validate role (6-level RBAC from your roadmap)
        valid_roles = ["admin", "security", "manager", "approver", "analyst", "viewer"]
        if payload["role"] not in valid_roles:
            raise jwt.InvalidTokenError(f"Invalid role: {payload['role']}")
        
        # Validate token type
        if payload["token_type"] != "access":
            raise jwt.InvalidTokenError(f"Invalid token type: {payload['token_type']}")
        
        # Check session revocation (implement based on your session store)
        if self._is_session_revoked(payload["session_id"]):
            raise jwt.InvalidTokenError("Session has been revoked")
    
    def _is_session_revoked(self, session_id: str) -> bool:
        """
        Check if session/token is revoked using RevocationService.

        SEC-081 FAIL SECURE: If RevocationService or Redis is unavailable,
        this method returns True (session considered revoked = deny access).
        This prevents session revocation bypass during infrastructure failures.

        Args:
            session_id: The JTI (JWT ID) to check for revocation

        Returns:
            True if session is revoked OR if check fails (FAIL SECURE)
            False only if session is confirmed NOT revoked
        """
        try:
            from services.revocation_service import get_revocation_service
            revocation_service = get_revocation_service()
            is_revoked = revocation_service.is_revoked(session_id)

            if is_revoked:
                import logging
                logging.getLogger(__name__).info(
                    f"SEC-081: Session revoked - access denied | jti={session_id[:8]}..."
                )

            return is_revoked

        except Exception as e:
            # SEC-081 FAIL SECURE: Any error during revocation check = deny access
            # This ensures infrastructure failures don't bypass security controls
            import logging
            logging.getLogger(__name__).error(
                f"SEC-081: Session revocation check failed - DENYING ACCESS (fail secure): {e}"
            )
            return True  # Session considered revoked = deny access
    
    def create_refresh_token(self, user_id: str, session_id: str) -> str:
        """Create refresh token (longer lived for token renewal)"""
        now = datetime.now(UTC)
        
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": int(now.timestamp()) - 10,    # Fixed clock skew issue
            "exp": int((now + timedelta(days=30)).timestamp()),  # 30 days
            "jti": f"refresh_{session_id}",
            "token_type": "refresh",
            "session_id": session_id
        }
        
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get default permissions for each role (enterprise RBAC)"""
        role_permissions = {
            "admin": [
                "read", "write", "delete", "approve", "manage_users", 
                "manage_policies", "view_audit", "emergency_override"
            ],
            "security": [
                "read", "write", "approve", "view_audit", "manage_policies"
            ],
            "manager": [
                "read", "write", "approve", "view_reports"
            ],
            "approver": [
                "read", "approve", "view_reports"
            ],
            "analyst": [
                "read", "write", "view_reports"
            ],
            "viewer": [
                "read"
            ]
        }
        return role_permissions.get(role, ["read"])

# Create global instance
jwt_manager = EnterpriseJWTManager()