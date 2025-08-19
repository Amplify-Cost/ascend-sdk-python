"""
Enterprise Authentication Endpoint Configuration
===============================================
Maps authentication endpoints for enterprise deployment
"""

from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnterpriseAuthConfig:
    """Configure enterprise authentication endpoints"""
    
    @staticmethod
    def map_legacy_endpoints(app: FastAPI):
        """Map legacy auth endpoints to new cookie-based system"""
        
        @app.middleware("http")
        async def auth_endpoint_mapper(request: Request, call_next):
            """Map old auth endpoints to new ones for backward compatibility"""
            
            # Map /auth/login to /auth/token for legacy compatibility
            if request.url.path == "/auth/login" and request.method == "POST":
                # Create new request to /auth/token
                logger.info("🔄 Mapping /auth/login to /auth/token for enterprise compatibility")
                # Modify the request path
                scope = request.scope.copy()
                scope["path"] = "/auth/token"
                request._url = request.url.replace(path="/auth/token")
            
            response = await call_next(request)
            
            # Add enterprise security headers
            if response.status_code == 200 and request.url.path.startswith("/auth/"):
                response.headers["X-Enterprise-Auth"] = "cookie-based"
                response.headers["X-CSRF-Protection"] = "enabled"
            
            return response
    
    @staticmethod
    def get_auth_endpoints() -> Dict[str, str]:
        """Get enterprise auth endpoint mapping"""
        return {
            "login": "/auth/token",
            "logout": "/auth/logout", 
            "me": "/auth/me",
            "refresh": "/auth/refresh",
            "health": "/health"
        }
