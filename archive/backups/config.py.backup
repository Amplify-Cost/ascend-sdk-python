# config.py - Enterprise Edition with Secrets Management
"""
Enterprise Configuration Management with Centralized Secrets
Supports HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Import enterprise secrets manager
try:
    from enterprise_secrets.secrets_manager import get_secrets_manager, get_secret
    ENTERPRISE_SECRETS_AVAILABLE = True
except ImportError:
    ENTERPRISE_SECRETS_AVAILABLE = False
    print("⚠️  Enterprise secrets manager not available, using environment fallback")

# Load environment variables for local development
load_dotenv()

logger = logging.getLogger(__name__)

class EnterpriseConfig:
    """Enterprise configuration with centralized secrets management"""
    
    def __init__(self):
        self.secrets_manager = None
        if ENTERPRISE_SECRETS_AVAILABLE:
            try:
                self.secrets_manager = get_secrets_manager()
                logger.info("✅ Enterprise secrets manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Secrets manager initialization failed: {e}")
        
        # Load and validate all configuration
        self._load_configuration()
        self._validate_configuration()

    def _get_secret_secure(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from enterprise secrets manager with fallback"""
        if self.secrets_manager:
            try:
                value = self.secrets_manager.get_secret(key)
                if value:
                    return value
            except Exception as e:
                logger.warning(f"Failed to get secret {key} from secrets manager: {e}")
        
        # Fallback to environment variable
        return os.getenv(key, default)

    def _load_configuration(self):
        """Load all configuration from secrets manager and environment"""
        
        # ================== CRITICAL SECRETS ==================
        # These should be stored in enterprise secrets manager
        
        # JWT Configuration
        self.SECRET_KEY = self._get_secret_secure("SECRET_KEY")
        self.ALGORITHM = "HS256"
        
        # Database Configuration
        self.DATABASE_URL = self._get_secret_secure("DATABASE_URL")
        
        # External API Keys
        self.OPENAI_API_KEY = self._get_secret_secure("OPENAI_API_KEY")
        
        # Enterprise Secrets Manager Configuration
        self.VAULT_URL = self._get_secret_secure("VAULT_URL", "http://localhost:8200")
        self.VAULT_TOKEN = self._get_secret_secure("VAULT_TOKEN")
        self.AWS_ACCESS_KEY_ID = self._get_secret_secure("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = self._get_secret_secure("AWS_SECRET_ACCESS_KEY")
        self.AZURE_VAULT_URL = self._get_secret_secure("AZURE_VAULT_URL")
        
        # ================== APPLICATION CONFIGURATION ==================
        # These can be environment variables
        
        # Token Configuration
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # CORS Configuration
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if allowed_origins_str:
            self.ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_str.split(",")]
        else:
            self.ALLOWED_ORIGINS = [
                "https://passionate-elegance-production.up.railway.app",
                "https://owai-production.up.railway.app",
                "http://localhost:3000",
                "http://localhost:5173"
            ]
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
        self.REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "3/minute")
        
        # Environment Configuration
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        
        # Enterprise Features
        self.ENTERPRISE_MODE = os.getenv("ENTERPRISE_MODE", "True").lower() == "true"
        self.SECRET_PROVIDER = os.getenv("SECRET_PROVIDER", "environment_fallback")
        self.SECRET_ROTATION_ENABLED = os.getenv("SECRET_ROTATION_ENABLED", "True").lower() == "true"
        
        # Compliance and Audit
        self.AUDIT_LOGGING_ENABLED = os.getenv("AUDIT_LOGGING_ENABLED", "True").lower() == "true"
        self.COMPLIANCE_MODE = os.getenv("COMPLIANCE_MODE", "SOC2").upper()
        
        # Security Headers
        self.SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "True").lower() == "true"
        
        # Monitoring and Observability  
        self.SENTRY_DSN = self._get_secret_secure("SENTRY_DSN")
        self.DATADOG_API_KEY = self._get_secret_secure("DATADOG_API_KEY")

    def _validate_configuration(self):
        """Validate critical configuration and secrets"""
        errors = []
        warnings = []
        
        # Critical secrets validation
        critical_secrets = {
            "SECRET_KEY": "JWT signing key for authentication",
            "DATABASE_URL": "PostgreSQL connection string",
            "OPENAI_API_KEY": "OpenAI API key for LLM features"
        }
        
        for secret_name, description in critical_secrets.items():
            value = getattr(self, secret_name, None)
            if not value:
                errors.append(f"❌ {secret_name} - {description}")
            elif secret_name == "SECRET_KEY" and len(value) < 32:
                warnings.append(f"⚠️ {secret_name} should be at least 32 characters for production")
        
        # Enterprise secrets validation
        if self.ENTERPRISE_MODE:
            if self.SECRET_PROVIDER != "environment_fallback":
                enterprise_secrets = {
                    "vault": ["VAULT_URL", "VAULT_TOKEN"],
                    "aws_secrets_manager": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                    "azure_key_vault": ["AZURE_VAULT_URL"]
                }
                
                provider_secrets = enterprise_secrets.get(self.SECRET_PROVIDER, [])
                for secret in provider_secrets:
                    if not getattr(self, secret, None):
                        warnings.append(f"⚠️ {secret} not configured for {self.SECRET_PROVIDER}")
        
        # Security validation
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                warnings.append("⚠️ DEBUG mode enabled in production")
            
            if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
                warnings.append("⚠️ Access token expiration > 60 minutes in production")
        
        # Report validation results
        if errors:
            error_msg = "Missing required configuration:\n" + "\n".join(errors)
            raise ValueError(error_msg)
        
        if warnings:
            for warning in warnings:
                logger.warning(warning)
        
        logger.info("✅ Enterprise configuration validation completed")

    def get_compliance_report(self) -> dict:
        """Generate compliance report for enterprise auditing"""
        report = {
            "configuration_validated": True,
            "secrets_manager_enabled": self.secrets_manager is not None,
            "enterprise_mode": self.ENTERPRISE_MODE,
            "secret_provider": self.SECRET_PROVIDER,
            "compliance_framework": self.COMPLIANCE_MODE,
            "audit_logging": self.AUDIT_LOGGING_ENABLED,
            "environment": self.ENVIRONMENT,
            "security_headers": self.SECURITY_HEADERS_ENABLED
        }
        
        if self.secrets_manager:
            try:
                secrets_report = self.secrets_manager.get_compliance_report()
                report.update({"secrets_compliance": secrets_report})
            except Exception as e:
                logger.warning(f"Failed to get secrets compliance report: {e}")
        
        return report

    def rotate_secrets(self) -> dict:
        """Rotate secrets using enterprise secrets manager"""
        if not self.secrets_manager:
            return {"error": "Secrets manager not available"}
        
        try:
            from enterprise_secrets.secrets_manager import rotate_all_secrets
            results = rotate_all_secrets()
            logger.info(f"✅ Secret rotation completed: {results}")
            return {"success": True, "rotated_secrets": results}
        except Exception as e:
            logger.error(f"❌ Secret rotation failed: {e}")
            return {"error": str(e)}

# Create global configuration instance
config = EnterpriseConfig()

# Export configuration values for backward compatibility
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
DATABASE_URL = config.DATABASE_URL
OPENAI_API_KEY = config.OPENAI_API_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = config.REFRESH_TOKEN_EXPIRE_DAYS
ALLOWED_ORIGINS = config.ALLOWED_ORIGINS
RATE_LIMIT_PER_MINUTE = config.RATE_LIMIT_PER_MINUTE
LOGIN_RATE_LIMIT = config.LOGIN_RATE_LIMIT
REGISTER_RATE_LIMIT = config.REGISTER_RATE_LIMIT

# Enterprise-specific exports
ENTERPRISE_MODE = config.ENTERPRISE_MODE
SECRET_PROVIDER = config.SECRET_PROVIDER
COMPLIANCE_MODE = config.COMPLIANCE_MODE
AUDIT_LOGGING_ENABLED = config.AUDIT_LOGGING_ENABLED

# Print configuration summary
print("🏢 OW-AI Enterprise Configuration Loaded")
print(f"✅ Environment: {config.ENVIRONMENT}")
print(f"✅ Enterprise Mode: {config.ENTERPRISE_MODE}")
print(f"✅ Secret Provider: {config.SECRET_PROVIDER}")
print(f"✅ Compliance Mode: {config.COMPLIANCE_MODE}")
print(f"✅ Allowed Origins: {len(config.ALLOWED_ORIGINS)} configured")
print(f"✅ Secrets Manager: {'Active' if config.secrets_manager else 'Fallback Mode'}")

if config.ENVIRONMENT == "production":
    print("🔒 Production security validations passed")
else:
    print("🛠️ Development mode active")