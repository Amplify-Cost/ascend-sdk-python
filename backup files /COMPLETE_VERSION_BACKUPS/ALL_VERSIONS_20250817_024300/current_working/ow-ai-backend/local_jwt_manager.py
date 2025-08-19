"""
Local JWT Manager for Testing Cookie Auth
Uses local keys instead of AWS
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

class LocalJWTManager:
    def __init__(self):
        self.secret_key = os.getenv("LOCAL_JWT_SECRET", "test_secret_key_for_cookie_auth_demo_only")
        self.algorithm = "HS256"  # Using HS256 for local testing simplicity
        self.issuer = "ow-ai-local-test"
        self.audience = "ow-ai-api"
    
    def issue_token(self, user_id: str, user_email: str, roles: list = None, expires_in_minutes: int = 60) -> str:
        """Issue a test JWT token"""
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
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

# Global instance
local_jwt_manager = LocalJWTManager()

def get_jwt_manager():
    """Get JWT manager (local version for testing)"""
    return local_jwt_manager
