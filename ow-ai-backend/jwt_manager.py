<<<<<<< HEAD
import json
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging

logger = logging.getLogger(__name__)

class JWTManager:
    def __init__(self, 
                 aws_secrets_manager_secret_name: str = "ow-ai/jwt-keys",
                 aws_region: str = "us-east-1",
                 issuer: str = "http://localhost:8000",
                 audience: str = "ow-ai-api"):
        
        self.aws_region = aws_region
        self.secret_name = aws_secrets_manager_secret_name
        self.issuer = issuer
        self.audience = audience
        self._private_key = None
        self._public_key = None
        self._kid = None
        
        # Initialize AWS Secrets Manager client
        self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        
        # Load keys on initialization
        self._load_keys()
    
    def _load_keys(self):
        """Load RSA keys from AWS Secrets Manager"""
        try:
            # Get the secret value
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response['SecretString'])
            
            # Extract private key
            private_key_pem = secret_data['private_key']
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            # Generate public key from private key
            self._public_key = self._private_key.public_key()
            
            # Use a stable key ID
            self._kid = secret_data.get('kid', 'ow-ai-key-1')
            
            logger.info("Successfully loaded RSA keys from AWS Secrets Manager")
            
        except Exception as e:
            logger.error(f"Failed to load keys from AWS Secrets Manager: {e}")
            raise
    
    def issue_token(self, 
                   user_id: str, 
                   user_email: str,
                   roles: list = None,
                   expires_in_minutes: int = 60) -> str:
        """Issue a new RS256 JWT token"""
        
        if not self._private_key:
            raise ValueError("Private key not loaded")
        
        # Calculate expiration
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)
        
        # Build payload
=======
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
        # Get signing keys from AWS Secrets Manager
        self.private_key = config.get_secret('jwt-private-key')
        self.public_key = config.get_secret('jwt-public-key')
        
        if not self.private_key or not self.public_key:
            raise Exception("❌ JWT keys not found in AWS Secrets Manager")
        
        # Enterprise JWT claims
        self.issuer = "https://api.ow-ai.com"
        self.audience = ["ow-ai-platform", "ow-ai-api", "ow-ai-dashboard"]
        
        print("✅ Enterprise JWT Manager initialized with RS256 keys from AWS")
    
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
                    "verify_nbf": False,            # Check not-before
                    "verify_iat": False,            # Check issued-at
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
        
>>>>>>> 894b585 (Initial commit: Enterprise JWT + AWS Secrets Manager implementation)
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
<<<<<<< HEAD
            "email": user_email,
            "roles": roles or [],
            "iat": now,
            "exp": exp,
            "jti": f"{user_id}-{int(now.timestamp())}"  # Unique token ID
        }
        
        # Prepare headers with kid
        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": self._kid
        }
        
        # Sign with private key
        try:
            # Convert private key to PEM format for PyJWT
            private_key_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            token = jwt.encode(
                payload=payload,
                key=private_key_pem,
                algorithm="RS256",
                headers=headers
            )
            
            logger.info(f"Issued token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to sign token: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode an RS256 JWT token"""
        
        if not self._public_key:
            raise ValueError("Public key not loaded")
        
        try:
            # Convert public key to PEM format for PyJWT
            public_key_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Decode and verify
            payload = jwt.decode(
                token,
                key=public_key_pem,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "require": ["exp", "iss", "aud", "sub"]
                }
            )
            
            logger.info(f"Successfully verified token for user {payload.get('sub')}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise
    
    def get_jwks(self) -> Dict[str, Any]:
        """Generate JWKS (JSON Web Key Set) for public key verification"""
        
        if not self._public_key:
            raise ValueError("Public key not loaded")
        
        try:
            # Get public key numbers
            public_numbers = self._public_key.public_numbers()
            
            # Convert to base64url encoding (RFC 7517)
            def int_to_base64url(value):
                """Convert integer to base64url string"""
                import base64
                # Convert to bytes, removing leading zeros
                byte_length = (value.bit_length() + 7) // 8
                bytes_value = value.to_bytes(byte_length, 'big')
                return base64.urlsafe_b64encode(bytes_value).decode('ascii').rstrip('=')
            
            # Build JWK
            jwk = {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": self._kid,
                "n": int_to_base64url(public_numbers.n),  # Modulus
                "e": int_to_base64url(public_numbers.e)   # Exponent
            }
            
            # Return JWKS format
            jwks = {
                "keys": [jwk]
            }
            
            return jwks
            
        except Exception as e:
            logger.error(f"Failed to generate JWKS: {e}")
            raise

# Global instance (initialize this in your app startup)
jwt_manager = None

def get_jwt_manager() -> JWTManager:
    """Get the global JWT manager instance"""
    global jwt_manager
    if jwt_manager is None:
        raise ValueError("JWT Manager not initialized. Call init_jwt_manager() first.")
    return jwt_manager

def init_jwt_manager(secret_name: str = "ow-ai/jwt-keys", 
                    aws_region: str = "us-east-1", 
                    issuer: str = "http://localhost:8000", 
                    audience: str = "ow-ai-api"):
    """Initialize the global JWT manager"""
    global jwt_manager
    jwt_manager = JWTManager(
        aws_secrets_manager_secret_name=secret_name,
        aws_region=aws_region,
        issuer=issuer,
        audience=audience
    )
=======
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
>>>>>>> 894b585 (Initial commit: Enterprise JWT + AWS Secrets Manager implementation)
