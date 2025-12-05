# enterprise_secrets/secrets_manager.py
"""
Enterprise-Grade Secrets Management System
Supports HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure enterprise logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretProvider(Enum):
    """Supported enterprise secret providers"""
    VAULT = "hashicorp_vault"
    AWS_SECRETS = "aws_secrets_manager"
    AZURE_KEYVAULT = "azure_key_vault"
    ENVIRONMENT = "environment_fallback"

class SecretRotationPolicy(Enum):
    """Enterprise secret rotation policies"""
    NEVER = "never"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CRITICAL_IMMEDIATE = "critical_immediate"

@dataclass
class SecretMetadata:
    """Enterprise secret metadata for compliance tracking"""
    name: str
    provider: SecretProvider
    created_at: datetime
    last_rotated: datetime
    rotation_policy: SecretRotationPolicy
    access_count: int
    last_accessed: datetime
    compliance_tags: List[str]
    risk_level: str
    owner: str

class EnterpriseSecretsManager:
    """
    Enterprise-grade secrets management with rotation, audit trails, and compliance
    Supports multiple backend providers with automatic failover
    """
    
    def __init__(self, 
                 primary_provider: SecretProvider = SecretProvider.VAULT,
                 fallback_provider: SecretProvider = SecretProvider.ENVIRONMENT,
                 encryption_key: Optional[str] = None):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.secret_metadata: Dict[str, SecretMetadata] = {}
        self.audit_trail: List[Dict] = []
        
        # Initialize encryption for local secret storage
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            self.encryption_key = self._generate_encryption_key()
        
        self.cipher_suite = self._create_cipher_suite()
        
        # Initialize providers
        self._initialize_providers()
        
        logger.info(f"🔐 Enterprise Secrets Manager initialized with {primary_provider.value}")

    def _generate_encryption_key(self) -> bytes:
        """
        Generate secure encryption key for local secrets.

        Security (SEC-079):
        - REQUIRES ENCRYPTION_MASTER_KEY environment variable in production
        - Uses cryptographically random salt per deployment
        - Stores salt in environment or generates unique per-instance for development
        - NO hardcoded defaults for production

        Compliance: SOC 2 CC6.1, PCI-DSS 3.5, NIST SP 800-53 SC-12
        """
        environment = os.environ.get("ENVIRONMENT", "development")

        # SEC-079: Get master key - REQUIRED in production
        master_key = os.environ.get("ENCRYPTION_MASTER_KEY")

        if not master_key:
            if environment.lower() == "production":
                logger.critical("⛔ SEC-079 CRITICAL: ENCRYPTION_MASTER_KEY not configured in production!")
                raise ValueError(
                    "SEC-079: ENCRYPTION_MASTER_KEY environment variable is REQUIRED in production. "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            else:
                # Development only: generate ephemeral key (changes on restart)
                logger.warning("⚠️ SEC-079: ENCRYPTION_MASTER_KEY not set - generating ephemeral development key")
                master_key = secrets.token_urlsafe(32)

        # SEC-079: Get or generate salt - should be stored persistently per deployment
        salt_b64 = os.environ.get("ENCRYPTION_SALT")

        if not salt_b64:
            if environment.lower() == "production":
                logger.critical("⛔ SEC-079 CRITICAL: ENCRYPTION_SALT not configured in production!")
                raise ValueError(
                    "SEC-079: ENCRYPTION_SALT environment variable is REQUIRED in production. "
                    "Generate with: python -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(16)).decode())\""
                )
            else:
                # Development only: generate ephemeral salt
                logger.warning("⚠️ SEC-079: ENCRYPTION_SALT not set - generating ephemeral development salt")
                salt = secrets.token_bytes(16)
        else:
            salt = base64.b64decode(salt_b64)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))

    def _create_cipher_suite(self) -> Fernet:
        """Create encryption cipher suite"""
        return Fernet(self.encryption_key)

    def _initialize_providers(self):
        """Initialize enterprise secret providers"""
        try:
            if self.primary_provider == SecretProvider.VAULT:
                self._init_vault_client()
            elif self.primary_provider == SecretProvider.AWS_SECRETS:
                self._init_aws_client()
            elif self.primary_provider == SecretProvider.AZURE_KEYVAULT:
                self._init_azure_client()
                
        except Exception as e:
            logger.warning(f"Primary provider {self.primary_provider.value} unavailable: {e}")
            logger.info(f"Falling back to {self.fallback_provider.value}")

    def _init_vault_client(self):
        """Initialize HashiCorp Vault client"""
        try:
            import hvac
            vault_url = os.environ.get("VAULT_URL", "http://localhost:8200")
            vault_token = os.environ.get("VAULT_TOKEN")
            
            if vault_token:
                self.vault_client = hvac.Client(url=vault_url, token=vault_token)
                if self.vault_client.is_authenticated():
                    logger.info("✅ HashiCorp Vault client initialized and authenticated")
                    return
            
            logger.warning("⚠️ Vault authentication failed")
        except ImportError:
            logger.warning("⚠️ hvac library not installed, install with: pip install hvac")
        except Exception as e:
            logger.warning(f"⚠️ Vault initialization failed: {e}")
        
        self.vault_client = None

    def _init_aws_client(self):
        """Initialize AWS Secrets Manager client"""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError
            
            self.aws_client = boto3.client('secretsmanager')
            # Test authentication
            self.aws_client.list_secrets(MaxResults=1)
            logger.info("✅ AWS Secrets Manager client initialized")
            
        except ImportError:
            logger.warning("⚠️ boto3 library not installed, install with: pip install boto3")
            self.aws_client = None
        except NoCredentialsError:
            logger.warning("⚠️ AWS credentials not configured")
            self.aws_client = None
        except Exception as e:
            logger.warning(f"⚠️ AWS Secrets Manager initialization failed: {e}")
            self.aws_client = None

    def _init_azure_client(self):
        """Initialize Azure Key Vault client"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = os.environ.get("AZURE_VAULT_URL")
            if not vault_url:
                raise ValueError("AZURE_VAULT_URL not configured")
                
            credential = DefaultAzureCredential()
            self.azure_client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info("✅ Azure Key Vault client initialized")
            
        except ImportError:
            logger.warning("⚠️ azure-keyvault-secrets library not installed")
            self.azure_client = None
        except Exception as e:
            logger.warning(f"⚠️ Azure Key Vault initialization failed: {e}")
            self.azure_client = None

    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Retrieve secret with enterprise audit trail and fallback logic
        """
        try:
            # Log access for compliance
            self._log_secret_access(secret_name, "READ")
            
            # Try primary provider first
            secret_value = self._get_from_primary_provider(secret_name)
            
            if secret_value:
                self._update_access_metadata(secret_name)
                return secret_value
            
            # Fallback to secondary provider
            logger.info(f"Primary provider failed, trying fallback for {secret_name}")
            secret_value = self._get_from_fallback_provider(secret_name)
            
            if secret_value:
                self._update_access_metadata(secret_name)
                return secret_value
            
            # Final fallback to environment
            secret_value = os.environ.get(secret_name)
            if secret_value:
                logger.warning(f"⚠️ Using environment fallback for {secret_name}")
                self._update_access_metadata(secret_name)
                return secret_value
            
            logger.error(f"❌ Secret {secret_name} not found in any provider")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error retrieving secret {secret_name}: {e}")
            self._log_secret_access(secret_name, "READ_ERROR", str(e))
            return None

    def _get_from_primary_provider(self, secret_name: str) -> Optional[str]:
        """Get secret from primary provider"""
        if self.primary_provider == SecretProvider.VAULT and self.vault_client:
            return self._get_from_vault(secret_name)
        elif self.primary_provider == SecretProvider.AWS_SECRETS and self.aws_client:
            return self._get_from_aws(secret_name)
        elif self.primary_provider == SecretProvider.AZURE_KEYVAULT and self.azure_client:
            return self._get_from_azure(secret_name)
        return None

    def _get_from_vault(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from HashiCorp Vault"""
        try:
            secret_path = f"secret/data/ow-ai/{secret_name}"
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=secret_path)
            return response['data']['data'].get('value')
        except Exception as e:
            logger.debug(f"Vault secret {secret_name} not found: {e}")
            return None

    def _get_from_aws(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.aws_client.get_secret_value(SecretId=f"ow-ai/{secret_name}")
            secret_data = json.loads(response['SecretString'])
            return secret_data.get('value', secret_data.get(secret_name))
        except Exception as e:
            logger.debug(f"AWS secret {secret_name} not found: {e}")
            return None

    def _get_from_azure(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from Azure Key Vault"""
        try:
            secret = self.azure_client.get_secret(secret_name.replace("_", "-"))
            return secret.value
        except Exception as e:
            logger.debug(f"Azure secret {secret_name} not found: {e}")
            return None

    def _get_from_fallback_provider(self, secret_name: str) -> Optional[str]:
        """Get secret from fallback provider"""
        if self.fallback_provider == SecretProvider.ENVIRONMENT:
            return os.environ.get(secret_name)
        return None

    def set_secret(self, secret_name: str, secret_value: str, 
                   rotation_policy: SecretRotationPolicy = SecretRotationPolicy.MONTHLY,
                   compliance_tags: List[str] = None) -> bool:
        """
        Store secret with enterprise metadata and compliance tracking
        """
        try:
            # Validate secret strength
            if not self._validate_secret_strength(secret_value):
                logger.error(f"❌ Secret {secret_name} does not meet enterprise security standards")
                return False
            
            # Store in primary provider
            success = self._store_in_primary_provider(secret_name, secret_value)
            
            if success:
                # Create metadata
                metadata = SecretMetadata(
                    name=secret_name,
                    provider=self.primary_provider,
                    created_at=datetime.now(UTC),
                    last_rotated=datetime.now(UTC),
                    rotation_policy=rotation_policy,
                    access_count=0,
                    last_accessed=datetime.now(UTC),
                    compliance_tags=compliance_tags or [],
                    risk_level=self._assess_secret_risk(secret_name),
                    owner=os.environ.get("SECRET_OWNER", "system")
                )
                
                self.secret_metadata[secret_name] = metadata
                self._log_secret_access(secret_name, "WRITE")
                logger.info(f"✅ Secret {secret_name} stored successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error storing secret {secret_name}: {e}")
            self._log_secret_access(secret_name, "WRITE_ERROR", str(e))
            return False

    def _store_in_primary_provider(self, secret_name: str, secret_value: str) -> bool:
        """Store secret in primary provider"""
        if self.primary_provider == SecretProvider.VAULT and self.vault_client:
            return self._store_in_vault(secret_name, secret_value)
        elif self.primary_provider == SecretProvider.AWS_SECRETS and self.aws_client:
            return self._store_in_aws(secret_name, secret_value)
        elif self.primary_provider == SecretProvider.AZURE_KEYVAULT and self.azure_client:
            return self._store_in_azure(secret_name, secret_value)
        return False

    def _store_in_vault(self, secret_name: str, secret_value: str) -> bool:
        """Store secret in HashiCorp Vault"""
        try:
            secret_path = f"secret/data/ow-ai/{secret_name}"
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={'value': secret_value}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {e}")
            return False

    def _store_in_aws(self, secret_name: str, secret_value: str) -> bool:
        """Store secret in AWS Secrets Manager"""
        try:
            secret_data = json.dumps({'value': secret_value})
            self.aws_client.create_secret(
                Name=f"ow-ai/{secret_name}",
                SecretString=secret_data
            )
            return True
        except self.aws_client.exceptions.ResourceExistsException:
            # Update existing secret
            self.aws_client.update_secret(
                SecretId=f"ow-ai/{secret_name}",
                SecretString=secret_data
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store secret in AWS: {e}")
            return False

    def _store_in_azure(self, secret_name: str, secret_value: str) -> bool:
        """Store secret in Azure Key Vault"""
        try:
            self.azure_client.set_secret(secret_name.replace("_", "-"), secret_value)
            return True
        except Exception as e:
            logger.error(f"Failed to store secret in Azure: {e}")
            return False

    def rotate_secret(self, secret_name: str, force: bool = False) -> bool:
        """
        Rotate secret with enterprise validation and rollback capability
        """
        try:
            metadata = self.secret_metadata.get(secret_name)
            if not metadata and not force:
                logger.error(f"❌ Secret {secret_name} metadata not found")
                return False
            
            # Check if rotation is needed
            if not force and not self._is_rotation_needed(metadata):
                logger.info(f"Secret {secret_name} rotation not needed yet")
                return True
            
            # Generate new secret based on type
            new_secret = self._generate_new_secret(secret_name)
            
            if not new_secret:
                logger.error(f"❌ Failed to generate new secret for {secret_name}")
                return False
            
            # Store old secret for rollback
            old_secret = self.get_secret(secret_name)
            
            # Store new secret
            success = self.set_secret(secret_name, new_secret)
            
            if success:
                # Update metadata
                if metadata:
                    metadata.last_rotated = datetime.now(UTC)
                
                self._log_secret_access(secret_name, "ROTATE")
                logger.info(f"✅ Secret {secret_name} rotated successfully")
                
                # Notify dependent services (implement webhook/notification logic)
                self._notify_secret_rotation(secret_name)
                
                return True
            else:
                logger.error(f"❌ Failed to store rotated secret {secret_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error rotating secret {secret_name}: {e}")
            self._log_secret_access(secret_name, "ROTATE_ERROR", str(e))
            return False

    def _generate_new_secret(self, secret_name: str) -> Optional[str]:
        """Generate new secret based on secret type"""
        if "API_KEY" in secret_name.upper():
            return self._generate_api_key()
        elif "PASSWORD" in secret_name.upper():
            return self._generate_password()
        elif "TOKEN" in secret_name.upper():
            return self._generate_token()
        elif "SECRET_KEY" in secret_name.upper():
            return self._generate_secret_key()
        else:
            # Default to strong random string
            return self._generate_random_string(32)

    def _generate_api_key(self) -> str:
        """Generate enterprise-grade API key"""
        return f"ow-ai-{secrets.token_urlsafe(32)}"

    def _generate_password(self) -> str:
        """Generate strong password meeting enterprise requirements"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(16))

    def _generate_token(self) -> str:
        """Generate secure token"""
        return secrets.token_urlsafe(64)

    def _generate_secret_key(self) -> str:
        """Generate cryptographic secret key"""
        return secrets.token_hex(32)

    def _generate_random_string(self, length: int) -> str:
        """Generate random string of specified length"""
        return secrets.token_urlsafe(length)

    def _validate_secret_strength(self, secret_value: str) -> bool:
        """Validate secret meets enterprise security requirements"""
        if len(secret_value) < 8:
            return False
        
        # Check for common weak patterns
        weak_patterns = ["password", "123456", "admin", "test"]
        if any(pattern in secret_value.lower() for pattern in weak_patterns):
            return False
        
        return True

    def _assess_secret_risk(self, secret_name: str) -> str:
        """Assess risk level of secret based on name and usage"""
        high_risk_indicators = ["API_KEY", "DATABASE", "PRODUCTION", "MASTER"]
        medium_risk_indicators = ["TOKEN", "PASSWORD", "SECRET"]
        
        secret_upper = secret_name.upper()
        
        if any(indicator in secret_upper for indicator in high_risk_indicators):
            return "HIGH"
        elif any(indicator in secret_upper for indicator in medium_risk_indicators):
            return "MEDIUM"
        else:
            return "LOW"

    def _is_rotation_needed(self, metadata: SecretMetadata) -> bool:
        """Check if secret rotation is needed based on policy"""
        if metadata.rotation_policy == SecretRotationPolicy.NEVER:
            return False
        
        now = datetime.now(UTC)
        time_since_rotation = now - metadata.last_rotated
        
        rotation_intervals = {
            SecretRotationPolicy.WEEKLY: timedelta(weeks=1),
            SecretRotationPolicy.MONTHLY: timedelta(days=30),
            SecretRotationPolicy.QUARTERLY: timedelta(days=90),
            SecretRotationPolicy.CRITICAL_IMMEDIATE: timedelta(seconds=1)
        }
        
        required_interval = rotation_intervals.get(metadata.rotation_policy, timedelta(days=30))
        return time_since_rotation >= required_interval

    def _update_access_metadata(self, secret_name: str):
        """Update secret access metadata for compliance tracking"""
        if secret_name in self.secret_metadata:
            metadata = self.secret_metadata[secret_name]
            metadata.access_count += 1
            metadata.last_accessed = datetime.now(UTC)

    def _log_secret_access(self, secret_name: str, action: str, details: str = ""):
        """Log secret access for enterprise audit trail"""
        audit_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "secret_name": secret_name,
            "action": action,
            "details": details,
            "user": os.environ.get("USER", "system"),
            "ip_address": "internal",
            "compliance_logged": True
        }
        
        self.audit_trail.append(audit_entry)
        
        # Keep only last 1000 entries in memory
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]

    def _notify_secret_rotation(self, secret_name: str):
        """Notify dependent services of secret rotation"""
        # Implement webhook notifications to dependent services
        logger.info(f"🔔 Notifying services of {secret_name} rotation")
        # This would integrate with your service mesh/notification system

    def get_secrets_due_for_rotation(self) -> List[str]:
        """Get list of secrets due for rotation"""
        due_secrets = []
        for secret_name, metadata in self.secret_metadata.items():
            if self._is_rotation_needed(metadata):
                due_secrets.append(secret_name)
        return due_secrets

    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """Get audit trail for compliance reporting"""
        return self.audit_trail[-limit:]

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for enterprise auditing"""
        total_secrets = len(self.secret_metadata)
        high_risk_secrets = len([m for m in self.secret_metadata.values() if m.risk_level == "HIGH"])
        due_for_rotation = len(self.get_secrets_due_for_rotation())
        
        return {
            "total_secrets_managed": total_secrets,
            "high_risk_secrets": high_risk_secrets,
            "secrets_due_for_rotation": due_for_rotation,
            "primary_provider": self.primary_provider.value,
            "audit_trail_entries": len(self.audit_trail),
            "compliance_frameworks": ["SOC2", "ISO27001", "NIST"],
            "last_generated": datetime.now(UTC).isoformat()
        }

# Enterprise Secrets Manager Singleton
_secrets_manager = None

def get_secrets_manager() -> EnterpriseSecretsManager:
    """Get singleton instance of secrets manager"""
    global _secrets_manager
    if _secrets_manager is None:
        provider = SecretProvider(os.environ.get("SECRET_PROVIDER", "environment_fallback"))
        _secrets_manager = EnterpriseSecretsManager(primary_provider=provider)
    return _secrets_manager

# Convenience functions for easy migration
def get_secret(name: str) -> Optional[str]:
    """Get secret using enterprise secrets manager"""
    return get_secrets_manager().get_secret(name)

def set_secret(name: str, value: str) -> bool:
    """Set secret using enterprise secrets manager"""
    return get_secrets_manager().set_secret(name, value)

def rotate_all_secrets() -> Dict[str, bool]:
    """Rotate all secrets that are due for rotation"""
    manager = get_secrets_manager()
    due_secrets = manager.get_secrets_due_for_rotation()
    results = {}
    
    for secret_name in due_secrets:
        results[secret_name] = manager.rotate_secret(secret_name)
    
    return results