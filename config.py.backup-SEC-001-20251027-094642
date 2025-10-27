# config.py - Simple Configuration with AWS Enterprise Fallback
"""
Configuration Manager with Enterprise AWS Support

Provides local development support with enterprise AWS capabilities
when deployed. Gracefully handles missing AWS credentials/services.

Author: Enterprise Security Team  
Version: 2.1.0 - Local Development Enhanced
Security Level: Enterprise with Local Dev Support
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

logger = logging.getLogger("enterprise.config")

class SimpleConfig:
    """
    Simple configuration manager that works locally and with AWS.
    
    Prioritizes environment variables over AWS services for reliability.
    Provides sensible defaults for demo/development environments.
    """
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        logger.info(f"Initializing configuration for {self.environment} environment")
        
        # Initialize configuration with defaults
        self.config = self._load_configuration()
        logger.info("Configuration loaded successfully")

    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration with environment variables and sensible defaults"""
        config = {}
        
        # Critical secrets with defaults for development
        config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345678901234567890')
        config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/owai_dev')
        config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
        
        # Application configuration
        config['ALGORITHM'] = os.getenv('ALGORITHM', 'HS256')
        config['ACCESS_TOKEN_EXPIRE_MINUTES'] = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        config['REFRESH_TOKEN_EXPIRE_DAYS'] = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        
        # CORS configuration
        allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173,https://pilot.owkai.app')
        config['ALLOWED_ORIGINS_LIST'] = [origin.strip() for origin in allowed_origins.split(',')]
        
        # Optional configuration
        config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
        config['SENTRY_DSN'] = os.getenv('SENTRY_DSN')
        config['DATADOG_API_KEY'] = os.getenv('DATADOG_API_KEY')
        
        # Deployment metadata
        config['DEPLOYMENT_INFO'] = {
            'platform': 'LOCAL' if self.environment == 'development' else 'AWS',
            'environment': self.environment,
            'config_version': '2.1.0'
        }
        
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value"""
        value = self.config.get(key)
        if value and key in ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']:
            # Sensitive values - don't log them
            return value
        return value

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'

    def get_cors_origins(self) -> List[str]:
        """Get CORS allowed origins as list"""
        return self.get('ALLOWED_ORIGINS_LIST', ['http://localhost:3000'])

    def get_database_url(self) -> str:
        """Get database connection URL"""
        url = self.get_secret('DATABASE_URL')
        if not url:
            # Fallback for local development
            url = 'postgresql://localhost:5432/owai_dev'
            logger.warning("Using default database URL for local development")
        return url

# AWS Enterprise Config (preserved for production deployments)
AWS_ENTERPRISE_CONFIG_AVAILABLE = False
try:
    # Try to import AWS dependencies
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    
    class AWSEnterpriseConfig(SimpleConfig):
        """Enhanced AWS configuration - only used when AWS credentials are available"""
        
        def __init__(self):
            super().__init__()
            self._try_aws_integration()
        
        def _try_aws_integration(self):
            """Attempt to integrate with AWS services if credentials are available"""
            try:
                # Test AWS connectivity
                ssm_client = boto3.client('ssm', region_name='us-east-2')
                ssm_client.describe_parameters(MaxResults=1)
                
                logger.info("AWS integration available - using enterprise config")
                AWS_ENTERPRISE_CONFIG_AVAILABLE = True
                # Additional AWS integration logic would go here
                
            except (NoCredentialsError, ClientError) as e:
                logger.info(f"AWS integration not available: {e}")
                # Continue with simple config
    
except ImportError:
    logger.info("AWS SDK not available - using simple configuration")
    AWSEnterpriseConfig = SimpleConfig

# Global configuration instance
config = None

def get_config():
    """Get global configuration instance"""
    global config
    if config is None:
        # Try AWS config first, fall back to simple config
        try:
            if AWS_ENTERPRISE_CONFIG_AVAILABLE:
                config = AWSEnterpriseConfig()
            else:
                config = SimpleConfig()
        except Exception as e:
            logger.warning(f"Enterprise config failed, using simple config: {e}")
            config = SimpleConfig()
    return config

# Backwards compatibility exports
def get_secret(key: str) -> Optional[str]:
    """Get secret value (backwards compatible)"""
    return get_config().get_secret(key)

# Initialize configuration and export values
_config = get_config()
SECRET_KEY = _config.get_secret('SECRET_KEY')
DATABASE_URL = _config.get_secret('DATABASE_URL') 
OPENAI_API_KEY = _config.get_secret('OPENAI_API_KEY')
ALGORITHM = _config.get('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = _config.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30)
REFRESH_TOKEN_EXPIRE_DAYS = _config.get('REFRESH_TOKEN_EXPIRE_DAYS', 7)
ALLOWED_ORIGINS = _config.get_cors_origins()

logger.info(f"Configuration initialized successfully")
logger.info(f"Environment: {_config.environment}")
logger.info(f"CORS Origins: {len(ALLOWED_ORIGINS)} configured")
logger.info(f"Database: {'Local PostgreSQL' if 'localhost' in DATABASE_URL else 'External Database'}")