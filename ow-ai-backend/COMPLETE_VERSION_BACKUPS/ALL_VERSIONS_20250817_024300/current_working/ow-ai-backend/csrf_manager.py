"""
Enterprise CSRF Protection Manager
Provides secure CSRF token generation and validation for cookie-based auth
"""

import secrets
import hmac
import hashlib
import time
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os

class CSRFManager:
    """Enterprise-grade CSRF protection for cookie authentication"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv("CSRF_SECRET_KEY", secrets.token_urlsafe(32))
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.token_lifetime = 3600  # 1 hour
    
    def generate_token(self, user_id: str = None) -> str:
        """Generate a secure CSRF token for the user session"""
        payload = {
            "user_id": user_id,
            "timestamp": int(time.time()),
            "nonce": secrets.token_urlsafe(16)
        }
        return self.serializer.dumps(payload)
    
    def validate_token(self, token: str, user_id: str = None) -> bool:
        """Validate CSRF token and ensure it matches the user session"""
        try:
            payload = self.serializer.loads(token, max_age=self.token_lifetime)
            
            # Verify user_id matches if provided
            if user_id and payload.get("user_id") != user_id:
                return False
            
            return True
        except (BadSignature, ValueError):
            return False
    
    def get_token_header_name(self) -> str:
        """Return the expected CSRF header name"""
        return "X-CSRF-Token"

# Global CSRF manager instance
csrf_manager = CSRFManager()
