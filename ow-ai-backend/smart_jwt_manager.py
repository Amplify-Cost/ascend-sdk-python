import os
import json
import boto3
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
import jwt
import logging

logger = logging.getLogger(__name__)

class SmartJWTManager:
    def __init__(self):
        self.issuer = "http://localhost:8000"
        self.audience = "ow-ai-api"
        self._private_key = None
        self._public_key = None
        self._kid = "ow-ai-key-1"
        self._load_keys()
    
    def _load_keys(self):
        """Load keys from AWS Secrets Manager or local files (environment-aware)"""
        
        # Check if we're in AWS environment
        is_aws_environment = (
            os.getenv('AWS_EXECUTION_ENV') or  # AWS Lambda/ECS
            os.getenv('AWS_REGION') or         # AWS environment
            os.getenv('ENVIRONMENT') == 'production'  # Explicit production flag
        )
        
        if is_aws_environment:
            logger.info("🚀 Production environment detected - using AWS Secrets Manager")
            self._load_from_aws()
        else:
            logger.info("💻 Development environment detected - using local JWT files")
            self._load_from_local_files()
    
    def _load_from_aws(self):
        """Load from AWS Secrets Manager (production)"""
        try:
            secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
            response = secrets_client.get_secret_value(SecretId='ow-ai/jwt-keys')
            secret_data = json.loads(response['SecretString'])
            
            private_key_pem = secret_data['private_key']
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'), password=None
            )
            self._public_key = self._private_key.public_key()
            self._kid = secret_data.get('kid', 'ow-ai-key-1')
            
            logger.info("✅ JWT keys loaded from AWS Secrets Manager")
        except Exception as e:
            logger.error(f"❌ Failed to load from AWS Secrets Manager: {e}")
            # Fallback to local files
            logger.info("🔄 Falling back to local files...")
            self._load_from_local_files()
    
    def _load_from_local_files(self):
        """Load from local files (development)"""
        try:
            with open("jwt-keys/private.pem", 'rb') as f:
                self._private_key = serialization.load_pem_private_key(f.read(), password=None)
            
            self._public_key = self._private_key.public_key()
            logger.info("✅ JWT keys loaded from local files")
        except Exception as e:
            logger.error(f"❌ Failed to load local JWT keys: {e}")
            raise
    
    def issue_token(self, user_id: str, user_email: str, roles: list = None, expires_in_minutes: int = 60) -> str:
        """Issue a new RS256 JWT token"""
        if not self._private_key:
            raise ValueError("Private key not loaded")
        
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)
        
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "email": user_email,
            "roles": roles or [],
            "iat": now,
            "exp": exp,
            "jti": f"{user_id}-{int(now.timestamp())}"
        }
        
        headers = {"alg": "RS256", "typ": "JWT", "kid": self._kid}
        
        try:
            private_key_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            token = jwt.encode(payload=payload, key=private_key_pem, algorithm="RS256", headers=headers)
            logger.info(f"Issued token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to sign token: {e}")
            raise
    
    def verify_token(self, token: str):
        """Verify and decode an RS256 JWT token"""
        if not self._public_key:
            raise ValueError("Public key not loaded")
        
        try:
            public_key_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            payload = jwt.decode(
                token, key=public_key_pem, algorithms=["RS256"],
                issuer=self.issuer, audience=self.audience,
                options={"verify_signature": True, "verify_exp": True, "verify_iss": True, "verify_aud": True}
            )
            
            logger.info(f"Successfully verified token for user {payload.get('sub')}")
            return payload
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise

# Global instance
jwt_manager = None

def get_jwt_manager():
    """Get the smart JWT manager instance"""
    global jwt_manager
    if jwt_manager is None:
        jwt_manager = SmartJWTManager()
    return jwt_manager

def init_jwt_manager(*args, **kwargs):
    """Initialize the smart JWT manager"""
    global jwt_manager
    jwt_manager = SmartJWTManager()
    logger.info("✅ Smart JWT Manager initialized")
    return jwt_manager
