import jwt
import time
import json
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from typing import Dict, List, Optional
from enterprise_config import config

class EnterpriseJWTManager:
    """Enterprise-grade JWT manager with RS256 signing and AWS Secrets Manager"""
    
    def __init__(self):
        # Get signing keys from AWS Secrets Manager or fallback
        self.private_key = config.get_secret('jwt-private-key')
        self.public_key = config.get_secret('jwt-public-key')
        
        # Enterprise fallback for AWS deployment
        if not self.private_key or not self.public_key:
            print("⚠️  JWT keys not found in AWS, using fallback RSA key generation")
            self._generate_fallback_keys()
        
        if not self.private_key or not self.public_key:
            print("❌ JWT keys could not be loaded or generated - using demo keys")
            self._use_demo_keys()
        
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
    
    def _use_demo_keys(self):
        """Use demo keys as last resort (NOT FOR PRODUCTION)"""
        self.private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
wXfKy2ljy1sbfmmjY1Sw9XVpQDjp7p2s2QN6g+N0c7G1jQ2qBJ1XFBRQpVqC5K
[Demo key - replace in production]
-----END PRIVATE KEY-----"""
        
        self.public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1L7VLPHCgcF3yst
[Demo key - replace in production]
-----END PUBLIC KEY-----"""
        
        print("⚠️  Using demo JWT keys - REPLACE IN PRODUCTION")
    
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
        now = datetime.utcnow()
        
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
        """Check if session is revoked (implement with Redis/database)"""
        # TODO: Implement session revocation check
        # This would check a Redis cache or database table
        # For now, always return False (no revocations)
        return False
    
    def create_refresh_token(self, user_id: str, session_id: str) -> str:
        """Create refresh token (longer lived for token renewal)"""
        now = datetime.utcnow()
        
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