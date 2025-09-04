"""
Enterprise Security Middleware
Rate limiting, request validation, audit logging
"""

from fastapi import Request, HTTPException, status
import time
import logging
from collections import defaultdict
from typing import Dict, List
import ipaddress
import json

logger = logging.getLogger(__name__)

class EnterpriseSecurityMiddleware:
    """Enterprise-grade security middleware for MCP operations"""
    
    def __init__(self):
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: set = set()
        
        # Security limits (configurable for different user tiers)
        self.rate_limits = {
            'default': 60,   # requests per minute
            'admin': 300,    # higher limits for admin users
            'enterprise': 600
        }
        
        self.max_request_size = 1024 * 1024  # 1MB
        self.suspicious_patterns = [
            'script', 'eval', 'exec', 'import', '__', 
            'subprocess', 'os.system', 'rm -rf', 'drop table'
        ]

    async def validate_request_security(self, request: Request, user_id: str, user_role: str = 'default'):
        """Comprehensive security validation for enterprise requests"""
        
        client_ip = self._get_client_ip(request)
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted request: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Rate limiting
        await self._check_rate_limit(user_id, user_role, client_ip)
        
        # Request size validation
        await self._validate_request_size(request)
        
        # Log security event
        logger.info("Enterprise security validation passed", extra={
            "user_id": user_id,
            "client_ip": client_ip,
            "endpoint": str(request.url.path),
            "method": request.method
        })

    async def _check_rate_limit(self, user_id: str, user_role: str, client_ip: str):
        """Rate limiting with role-based limits"""
        
        now = time.time()
        limit = self.rate_limits.get(user_role, self.rate_limits['default'])
        
        # Clean old requests (last minute)
        user_requests = self.request_counts[user_id]
        self.request_counts[user_id] = [req_time for req_time in user_requests 
                                       if now - req_time < 60]
        
        # Check rate limit
        if len(self.request_counts[user_id]) >= limit:
            logger.warning(f"Rate limit exceeded", extra={
                "user_id": user_id,
                "requests_count": len(self.request_counts[user_id]),
                "limit": limit,
                "client_ip": client_ip
            })
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute."
            )
        
        # Record request
        self.request_counts[user_id].append(now)

    async def _validate_request_size(self, request: Request):
        """Validate request size to prevent DoS attacks"""
        
        content_length = 0
        if hasattr(request, 'headers') and 'content-length' in request.headers:
            try:
                content_length = int(request.headers['content-length'])
            except (ValueError, TypeError):
                content_length = 0
        
        if content_length > self.max_request_size:
            logger.warning(f"Request size exceeded limit: {content_length} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request size exceeds maximum allowed limit"
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        
        # Check for forwarded IP (common in AWS ALB)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # Fallback to direct connection
        return getattr(request.client, 'host', 'unknown')

    async def validate_input_content(self, content: str, field_name: str):
        """Validate input content for suspicious patterns"""
        
        content_lower = content.lower()
        
        for pattern in self.suspicious_patterns:
            if pattern in content_lower:
                logger.warning(f"Suspicious pattern detected in {field_name}: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content in {field_name}"
                )

# Global middleware instance
enterprise_security = EnterpriseSecurityMiddleware()
