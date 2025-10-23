"""
Core Configuration Management
Centralizes all environment variables and settings
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Application
    APP_NAME: str = "OW-AI Enterprise Backend"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./owai.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AWS (for production)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-2")
    AWS_SECRET_NAME: str = os.getenv("AWS_SECRET_NAME", "")
    USE_AWS_SECRETS: bool = os.getenv("USE_AWS_SECRETS", "false").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://pilot.owkai.app",
        "https://*.owkai.app"
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()
