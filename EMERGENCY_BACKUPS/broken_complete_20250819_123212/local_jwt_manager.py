import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging

logger = logging.getLogger(__name__)

class LocalJWTManager:
    def __init__(self, 
                 private_key_path: str = "jwt-keys/private.pem",
                 public_key_path: str = "jwt-keys/public.pem",
                 issuer: str = "http://localhost:8000",
                 audience: str = "ow-ai-api"):
        
        self.issuer = issuer
        self.audience = audience
        self._private_key = None
        self._public_key = None
        self._kid = "local-dev-key-1"
        
        # Load keys from local files
        self._load_local_keys(private_key_path, public_key_path)
    
    def _load_local_keys(self, private_key_path: str, public_key_path: str):
        """Load RSA keys from local files"""
        try:
            # Load private key
            with open(private_key_path, 'rb') as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            # Load public key
            with open(public_key_path, 'rb') as f:
                self._public_key = serialization.load_pem_public_key(f.read())
            
            logger.info("Successfully loaded RSA keys from local files")
            
        except Exception as e:
            logger.error(f"Failed to load keys from local files: {e}")
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
            "nbf": now
        }
        
        # Add key ID
        headers = {"kid": self._kid}
        
        try:
            # Convert private key to PEM format for PyJWT
            private_key_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Sign the token
            token = jwt.encode(
                payload,
                key=private_key_pem,
                algorithm="RS256",
                headers=headers
            )
            
            logger.info(f"Issued token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to sign token: {e}")
            raise

# Global instance for local development
local_jwt_manager = None

def get_jwt_manager():
    """Get the local JWT manager instance"""
    global local_jwt_manager
    if local_jwt_manager is None:
        local_jwt_manager = LocalJWTManager()
    return local_jwt_manager

def init_jwt_manager():
    """Initialize the local JWT manager"""
    global local_jwt_manager
    local_jwt_manager = LocalJWTManager()
    logger.info("Local JWT Manager initialized for development")
    return local_jwt_manager
