"""
Enterprise Environment Detection
===============================
Automatically detects Railway vs local environment and adjusts configuration
"""

import os
from typing import Dict, Any

class EnterpriseEnvironmentDetector:
    """Detects and configures enterprise environment settings"""
    
    @staticmethod
    def is_railway_environment() -> bool:
        """Check if running in Railway environment"""
        return bool(os.getenv('RAILWAY_ENVIRONMENT') or 
                   os.getenv('RAILWAY_PROJECT_ID') or
                   os.getenv('RAILWAY_SERVICE_ID'))
    
    @staticmethod
    def is_production_environment() -> bool:
        """Check if this is a production deployment"""
        env = os.getenv('ENVIRONMENT', 'development').lower()
        return env in ['production', 'prod'] or EnterpriseEnvironmentDetector.is_railway_environment()
    
    @staticmethod
    def get_database_url() -> str:
        """Get appropriate database URL for environment"""
        if EnterpriseEnvironmentDetector.is_railway_environment():
            return os.getenv('DATABASE_URL', '')
        else:
            # Local development - try Railway URL first, fallback to SQLite
            railway_url = os.getenv('DATABASE_URL', '')
            if railway_url and 'railway.internal' not in railway_url:
                return railway_url
            return os.getenv('LOCAL_DATABASE_URL', 'sqlite:///./enterprise_dev.db')
    
    @staticmethod
    def get_cookie_settings() -> Dict[str, Any]:
        """Get appropriate cookie settings for environment"""
        if EnterpriseEnvironmentDetector.is_production_environment():
            return {
                'secure': True,
                'samesite': 'strict',
                'domain': os.getenv('COOKIE_DOMAIN'),
                'httponly': True
            }
        else:
            return {
                'secure': False,
                'samesite': 'lax', 
                'domain': None,
                'httponly': True
            }
    
    @staticmethod
    def get_cors_origins() -> list:
        """Get CORS origins based on environment"""
        origins_str = os.getenv('ALLOWED_ORIGINS', '')
        origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
        
        # Always include local development origins in non-production
        if not EnterpriseEnvironmentDetector.is_production_environment():
            local_origins = ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000']
            for origin in local_origins:
                if origin not in origins:
                    origins.append(origin)
        
        return origins

# Global detector instance
env_detector = EnterpriseEnvironmentDetector()
