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
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
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
