# config.py - Enterprise Edition (SECURE VERSION - NO REPO SECRETS)
"""
Enterprise Configuration Management with Railway Secrets Integration
CRITICAL: This version contains NO secrets in the repository
All secrets are injected via Railway environment variables
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Import enterprise secrets manager (optional - graceful fallback)
try:
    from enterprise_secrets.secrets_manager import get_secrets_manager, get_secret
    ENTERPRISE_SECRETS_AVAILABLE = True
except ImportError:
    ENTERPRISE_SECRETS_AVAILABLE = False
    print("ℹ️  Enterprise secrets manager optional - using Railway environment variables")

# Load environment variables ONLY for local development
# Railway automatically injects production secrets
if os.getenv("ENVIRONMENT") != "production":
    load_dotenv(".env.local")  # Use .env.local for development, never .env

logger = logging.getLogger(__name__)

class EnterpriseConfig:
    """Enterprise configuration with Railway secrets integration"""
    
    def __init__(self):
        self.secrets_manager = None
        
        # Initialize enterprise secrets manager (optional)
        if ENTERPRISE_SECRETS_AVAILABLE:
            try:
                self.secrets_manager = get_secrets_manager()
                logger.info("✅ Enterprise secrets manager initialized")
            except Exception as e:
                logger.info(f"ℹ️  Using Railway secrets (enterprise manager unavailable): {e}")
        
        # Load and validate all configuration
        self._load_configuration()
        self._validate_configuration()

    def _get_secret_secure(self, key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
        """
        Get secret from Railway environment variables with enterprise fallback
        SECURITY: Never stores secrets in repository
        """
        # Primary: Railway environment variables (production)
        value = os.getenv(key)
        if value:
            return value
        
        # Secondary: Enterprise secrets manager (if configured)
        if self.secrets_manager:
            try:
                value = self.secrets_manager.get_secret(key)
                if value:
                    return value
            except Exception as e:
                logger.debug(f"Enterprise secrets manager lookup failed for {key}: {e}")
        
        # Fallback: Default value
        if default is not None:
            return default
        
        # Error handling for required secrets
        if required:
            logger.error(f"❌ CRITICAL: Required secret {key} not found in Railway environment variables")
            logger.error("🔧 SOLUTION: Set secret in Railway: railway variables set {key}=<value>")
        
        return None

    def _load_configuration(self):
        """Load all configuration from Railway environment variables"""
        
        # ================== CRITICAL SECRETS ==================
        # These MUST be set in Railway environment variables
        
        # JWT Configuration - REQUIRED
        self.SECRET_KEY = self._get_secret_secure("SECRET_KEY", required=True)
        self.ALGORITHM = self._get_secret_secure("ALGORITHM", "HS256", required=False)
        
        # Database Configuration - REQUIRED  
        self.DATABASE_URL = self._get_secret_secure("DATABASE_URL", required=True)
        
        # External API Keys - REQUIRED
        self.OPENAI_API_KEY = self._get_secret_secure("OPENAI_API_KEY", required=True)
        
        # ================== ENTERPRISE SECRETS MANAGER ==================
        # Optional enterprise secrets manager configuration
        self.VAULT_URL = self._get_secret_secure("VAULT_URL", "http://localhost:8200", required=False)
        self.VAULT_TOKEN = self._get_secret_secure("VAULT_TOKEN", required=False)
        self.AWS_ACCESS_KEY_ID = self._get_secret_secure("AWS_ACCESS_KEY_ID", required=False)
        self.AWS_SECRET_ACCESS_KEY = self._get_secret_secure("AWS_SECRET_ACCESS_KEY", required=False)
        self.AZURE_VAULT_URL = self._get_secret_secure("AZURE_VAULT_URL", required=False)
        
        # ================== APPLICATION CONFIGURATION ==================
        # These can be environment variables or have safe defaults
        
        # Token Configuration
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # CORS Configuration - Railway Production URLs
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if allowed_origins_str:
            self.ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_str.split(",")]
        else:
            # Default Railway production origins (update these with your actual Railway URLs)
            self.ALLOWED_ORIGINS = [
                "https://passionate-elegance-production.up.railway.app",
                "https://owai-production.up.railway.app",
                "http://localhost:3000",  # Local development
                "http://localhost:5173"   # Vite dev server
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
        self.SECRET_PROVIDER = os.getenv("SECRET_PROVIDER", "railway_environment")
        self.SECRET_ROTATION_ENABLED = os.getenv("SECRET_ROTATION_ENABLED", "True").lower() == "true"
        
        # Compliance and Audit
        self.AUDIT_LOGGING_ENABLED = os.getenv("AUDIT_LOGGING_ENABLED", "True").lower() == "true"
        self.COMPLIANCE_MODE = os.getenv("COMPLIANCE_MODE", "SOC2").upper()
        
        # Security Headers
        self.SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "True").lower() == "true"
        
        # Monitoring and Observability (Optional)
        self.SENTRY_DSN = self._get_secret_secure("SENTRY_DSN", required=False)
        self.DATADOG_API_KEY = self._get_secret_secure("DATADOG_API_KEY", required=False)

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
                errors.append(f"   🔧 FIX: railway variables set {secret_name}=<your_value>")
            elif secret_name == "SECRET_KEY" and len(value) < 32:
                warnings.append(f"⚠️ {secret_name} should be at least 32 characters for production")
        
        # Environment-specific validation
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                warnings.append("⚠️ DEBUG mode enabled in production")
            
            if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
                warnings.append("⚠️ Access token expiration > 60 minutes in production")
            
            # Check for Railway production environment
            railway_env = os.getenv("RAILWAY_ENVIRONMENT")
            if railway_env:
                logger.info(f"✅ Railway environment detected: {railway_env}")
            else:
                warnings.append("⚠️ Railway environment not detected")
        
        # Report validation results
        if errors:
            error_msg = "❌ CRITICAL CONFIGURATION ERRORS:\n" + "\n".join(errors)
            error_msg += "\n\n🔧 QUICK FIX:\n"
            error_msg += "1. Install Railway CLI: npm install -g @railway/cli\n"
            error_msg += "2. Login: railway login\n"
            error_msg += "3. Set secrets: railway variables set SECRET_KEY=<new_secret_key>\n"
            error_msg += "4. Deploy: railway up"
            raise ValueError(error_msg)
        
        if warnings:
            for warning in warnings:
                logger.warning(warning)
        
        logger.info("✅ Enterprise configuration validation completed")

    def get_compliance_report(self) -> dict:
        """Generate compliance report for enterprise auditing"""
        # Check Railway environment
        railway_project = os.getenv("RAILWAY_PROJECT_ID")
        railway_env = os.getenv("RAILWAY_ENVIRONMENT")
        
        report = {
            "configuration_validated": True,
            "secrets_source": "railway_environment_variables",
            "repository_secrets": False,  # CRITICAL: No secrets in repo
            "enterprise_mode": self.ENTERPRISE_MODE,
            "secret_provider": self.SECRET_PROVIDER,
            "compliance_framework": self.COMPLIANCE_MODE,
            "audit_logging": self.AUDIT_LOGGING_ENABLED,
            "environment": self.ENVIRONMENT,
            "security_headers": self.SECURITY_HEADERS_ENABLED,
            "railway_integration": {
                "project_id": railway_project,
                "environment": railway_env,
                "secrets_managed": railway_project is not None
            },
            "security_score": self._calculate_security_score()
        }
        
        return report

    def _calculate_security_score(self) -> dict:
        """Calculate enterprise security score"""
        score = 100
        issues = []
        
        # Deduct for security issues
        if self.DEBUG and self.ENVIRONMENT == "production":
            score -= 20
            issues.append("Debug mode in production")
        
        if not self.SECURITY_HEADERS_ENABLED:
            score -= 10
            issues.append("Security headers disabled")
        
        if len(self.SECRET_KEY or "") < 32:
            score -= 15
            issues.append("Weak secret key")
        
        if not self.AUDIT_LOGGING_ENABLED:
            score -= 10
            issues.append("Audit logging disabled")
        
        return {
            "score": max(0, score),
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D",
            "issues": issues,
            "compliant": score >= 80
        }

    def rotate_secrets(self) -> dict:
        """Rotate secrets using enterprise secrets manager or Railway"""
        if not self.secrets_manager:
            return {
                "error": "Enterprise secrets manager not available",
                "solution": "Use Railway CLI: railway variables set SECRET_KEY=<new_value>"
            }
        
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

# Print secure configuration summary
print("🏢 OW-AI Enterprise Configuration Loaded (SECURE)")
print(f"✅ Environment: {config.ENVIRONMENT}")
print(f"✅ Enterprise Mode: {config.ENTERPRISE_MODE}")
print(f"✅ Secret Provider: {config.SECRET_PROVIDER}")
print(f"✅ Compliance Mode: {config.COMPLIANCE_MODE}")
print(f"✅ Allowed Origins: {len(config.ALLOWED_ORIGINS)} configured")
print(f"✅ Railway Integration: {'Active' if os.getenv('RAILWAY_PROJECT_ID') else 'Local Dev'}")
print("🔒 SECURITY: All secrets managed via Railway environment variables")

if config.ENVIRONMENT == "production":
    print("🔒 Production security validations passed")
    print("🛡️  NO SECRETS IN REPOSITORY - Enterprise compliant")
else:
    print("🛠️ Development mode - use .env.local for local secrets")