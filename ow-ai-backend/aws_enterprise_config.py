# aws_enterprise_config.py
"""
AWS Enterprise Configuration Manager

Production-ready configuration management for AWS-deployed applications
with Parameter Store, Secrets Manager, and environment variable fallbacks.

Author: Enterprise Security Team
Version: 2.0.0 
Security Level: Enterprise
Compliance: SOX, PCI-DSS, HIPAA, GDPR
Target: Pilot Phase Deployment
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger("enterprise.aws.config")

class AWSSecretSource(str, Enum):
    """AWS secret storage locations"""
    PARAMETER_STORE = "parameter_store"  # For non-sensitive config
    SECRETS_MANAGER = "secrets_manager"  # For sensitive secrets
    ENVIRONMENT_VARS = "environment_vars" # ECS environment variables
    ECS_TASK_METADATA = "ecs_metadata"   # ECS task metadata

@dataclass
class AWSSecret:
    """AWS secret configuration"""
    name: str
    source: AWSSecretSource
    parameter_name: Optional[str] = None
    secret_arn: Optional[str] = None
    required: bool = True
    default_value: Optional[str] = None

class AWSEnterpriseConfig:
    """
    Enterprise configuration manager for AWS deployments.
    
    Handles secrets from AWS Parameter Store, Secrets Manager,
    and ECS environment variables with proper fallback chains.
    """
    
    def __init__(self):
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.app_name = "owkai-pilot"
        
        # Initialize AWS clients with error handling
        self._ssm_client = None
        self._secrets_client = None
        self._initialize_aws_clients()
        
        # Secret definitions for your application
        self.secret_definitions = self._define_secrets()
        
        # Load and validate all configuration
        self.config = self._load_configuration()
        self._validate_configuration()
        
        logger.info(f"AWS Enterprise Configuration loaded for {self.environment}")

    def _initialize_aws_clients(self):
        """Initialize AWS clients with proper error handling"""
        try:
            # Parameter Store client
            self._ssm_client = boto3.client('ssm', region_name=self.region)
            
            # Secrets Manager client
            self._secrets_client = boto3.client('secretsmanager', region_name=self.region)
            
            # Test connectivity
            self._ssm_client.describe_parameters(MaxResults=1)
            logger.info("AWS clients initialized successfully")
            
        except NoCredentialsError:
            logger.warning("AWS credentials not available - using environment variables only")
            self._ssm_client = None
            self._secrets_client = None
            
        except ClientError as e:
            logger.warning(f"AWS service access limited: {e} - falling back to environment variables")
            if "Parameter Store" in str(e):
                self._ssm_client = None
            if "Secrets Manager" in str(e):
                self._secrets_client = None

    def _define_secrets(self) -> Dict[str, AWSSecret]:
        """Define all secrets needed by the application"""
        return {
            # Critical application secrets (Secrets Manager)
            "SECRET_KEY": AWSSecret(
                name="SECRET_KEY",
                source=AWSSecretSource.SECRETS_MANAGER,
                secret_arn=f"arn:aws:secretsmanager:{self.region}:*:secret:{self.app_name}/jwt-secret-key",
                required=True
            ),
            "DATABASE_URL": AWSSecret(
                name="DATABASE_URL", 
                source=AWSSecretSource.ENVIRONMENT_VARS,  # Injected by ECS from RDS
                required=True
            ),
            "OPENAI_API_KEY": AWSSecret(
                name="OPENAI_API_KEY",
                source=AWSSecretSource.SECRETS_MANAGER,
                secret_arn=f"arn:aws:secretsmanager:{self.region}:*:secret:{self.app_name}/openai-api-key",
                required=True
            ),
            
            # Application configuration (Parameter Store)
            "ALGORITHM": AWSSecret(
                name="ALGORITHM",
                source=AWSSecretSource.PARAMETER_STORE,
                parameter_name=f"/{self.app_name}/{self.environment}/algorithm",
                required=True,
                default_value="HS256"
            ),
            "ACCESS_TOKEN_EXPIRE_MINUTES": AWSSecret(
                name="ACCESS_TOKEN_EXPIRE_MINUTES",
                source=AWSSecretSource.PARAMETER_STORE,
                parameter_name=f"/{self.app_name}/{self.environment}/access-token-expire",
                required=False,
                default_value="30"
            ),
            "REFRESH_TOKEN_EXPIRE_DAYS": AWSSecret(
                name="REFRESH_TOKEN_EXPIRE_DAYS",
                source=AWSSecretSource.PARAMETER_STORE,
                parameter_name=f"/{self.app_name}/{self.environment}/refresh-token-expire",
                required=False,
                default_value="7"
            ),
            
            # Environment configuration
            "ALLOWED_ORIGINS": AWSSecret(
                name="ALLOWED_ORIGINS",
                source=AWSSecretSource.PARAMETER_STORE,
                parameter_name=f"/{self.app_name}/{self.environment}/allowed-origins",
                required=True,
                default_value="https://pilot.owkai.app"
            ),
            "LOG_LEVEL": AWSSecret(
                name="LOG_LEVEL",
                source=AWSSecretSource.PARAMETER_STORE,
                parameter_name=f"/{self.app_name}/{self.environment}/log-level",
                required=False,
                default_value="INFO"
            ),
            
            # Optional integrations
            "SENTRY_DSN": AWSSecret(
                name="SENTRY_DSN",
                source=AWSSecretSource.SECRETS_MANAGER,
                secret_arn=f"arn:aws:secretsmanager:{self.region}:*:secret:{self.app_name}/sentry-dsn",
                required=False
            ),
            "DATADOG_API_KEY": AWSSecret(
                name="DATADOG_API_KEY", 
                source=AWSSecretSource.SECRETS_MANAGER,
                secret_arn=f"arn:aws:secretsmanager:{self.region}:*:secret:{self.app_name}/datadog-api-key",
                required=False
            )
        }

    def _load_configuration(self) -> Dict[str, Any]:
        """Load all configuration values from AWS sources"""
        config = {}
        
        for secret_name, secret_def in self.secret_definitions.items():
            value = self._get_secret_value(secret_def)
            if value is not None:
                config[secret_name] = value
            elif secret_def.required:
                logger.error(f"Required secret {secret_name} not found")
            else:
                logger.info(f"Optional secret {secret_name} not configured")
        
        # Add computed configuration
        config.update(self._get_computed_config(config))
        
        return config

    def _get_secret_value(self, secret_def: AWSSecret) -> Optional[str]:
        """Get secret value from the appropriate AWS source"""
        
        # First, always try environment variables (highest priority)
        env_value = os.getenv(secret_def.name)
        if env_value:
            logger.debug(f"Secret {secret_def.name} loaded from environment")
            return env_value
        
        # Then try the defined AWS source
        if secret_def.source == AWSSecretSource.SECRETS_MANAGER:
            return self._get_from_secrets_manager(secret_def)
        elif secret_def.source == AWSSecretSource.PARAMETER_STORE:
            return self._get_from_parameter_store(secret_def)
        elif secret_def.source == AWSSecretSource.ECS_TASK_METADATA:
            return self._get_from_ecs_metadata(secret_def)
        
        # Finally, use default value if available
        if secret_def.default_value:
            logger.info(f"Using default value for {secret_def.name}")
            return secret_def.default_value
        
        return None

    def _get_from_secrets_manager(self, secret_def: AWSSecret) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager"""
        if not self._secrets_client:
            return None
            
        try:
            # Try both ARN and name-based lookups
            secret_ids = []
            if secret_def.secret_arn:
                secret_ids.append(secret_def.secret_arn)
            secret_ids.extend([
                f"{self.app_name}/{secret_def.name}",
                f"{self.app_name}/{self.environment}/{secret_def.name}",
                secret_def.name
            ])
            
            for secret_id in secret_ids:
                try:
                    response = self._secrets_client.get_secret_value(SecretId=secret_id)
                    logger.debug(f"Secret {secret_def.name} loaded from Secrets Manager: {secret_id}")
                    return response['SecretString']
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        logger.warning(f"Error accessing secret {secret_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Secrets Manager error for {secret_def.name}: {e}")
        
        return None

    def _get_from_parameter_store(self, secret_def: AWSSecret) -> Optional[str]:
        """Retrieve parameter from AWS Systems Manager Parameter Store"""
        if not self._ssm_client:
            return None
            
        try:
            # Try multiple parameter name patterns
            parameter_names = []
            if secret_def.parameter_name:
                parameter_names.append(secret_def.parameter_name)
            parameter_names.extend([
                f"/{self.app_name}/{self.environment}/{secret_def.name.lower()}",
                f"/{self.app_name}/{secret_def.name.lower()}",
                f"/owkai/{secret_def.name.lower()}"
            ])
            
            for param_name in parameter_names:
                try:
                    response = self._ssm_client.get_parameter(
                        Name=param_name,
                        WithDecryption=True
                    )
                    logger.debug(f"Parameter {secret_def.name} loaded from Parameter Store: {param_name}")
                    return response['Parameter']['Value']
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ParameterNotFound':
                        logger.warning(f"Error accessing parameter {param_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Parameter Store error for {secret_def.name}: {e}")
        
        return None

    def _get_from_ecs_metadata(self, secret_def: AWSSecret) -> Optional[str]:
        """Retrieve configuration from ECS task metadata"""
        try:
            metadata_uri = os.getenv('ECS_CONTAINER_METADATA_URI_V4')
            if metadata_uri:
                # Implementation for ECS metadata retrieval
                logger.debug(f"ECS metadata available for {secret_def.name}")
                # This would make HTTP calls to the metadata endpoint
                pass
        except Exception as e:
            logger.warning(f"ECS metadata error for {secret_def.name}: {e}")
        
        return None

    def _get_computed_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate computed configuration values"""
        computed = {}
        
        # Parse ALLOWED_ORIGINS into list
        if 'ALLOWED_ORIGINS' in config:
            origins = config['ALLOWED_ORIGINS']
            if isinstance(origins, str):
                computed['ALLOWED_ORIGINS_LIST'] = [
                    origin.strip() for origin in origins.split(',')
                ]
            else:
                computed['ALLOWED_ORIGINS_LIST'] = origins
        
        # Convert string integers to integers
        for key in ['ACCESS_TOKEN_EXPIRE_MINUTES', 'REFRESH_TOKEN_EXPIRE_DAYS']:
            if key in config and isinstance(config[key], str):
                try:
                    computed[key] = int(config[key])
                except ValueError:
                    logger.warning(f"Invalid integer value for {key}: {config[key]}")
        
        # Add deployment metadata
        computed['DEPLOYMENT_INFO'] = {
            'platform': 'AWS',
            'region': self.region,
            'environment': self.environment,
            'app_name': self.app_name,
            'config_version': '2.0.0'
        }
        
        return computed

    def _validate_configuration(self):
        """Validate that all required configuration is present"""
        missing_secrets = []
        
        for secret_name, secret_def in self.secret_definitions.items():
            if secret_def.required and secret_name not in self.config:
                missing_secrets.append(secret_name)
        
        if missing_secrets:
            error_msg = "CRITICAL CONFIGURATION ERRORS:\n"
            error_msg += "The following required secrets are missing:\n"
            
            for secret in missing_secrets:
                secret_def = self.secret_definitions[secret]
                error_msg += f"- {secret} (source: {secret_def.source.value})\n"
                
                # Provide AWS-specific setup instructions
                if secret_def.source == AWSSecretSource.SECRETS_MANAGER:
                    if secret_def.secret_arn:
                        error_msg += f"  AWS CLI: aws secretsmanager create-secret --name {self.app_name}/{secret} --secret-string 'YOUR_VALUE'\n"
                elif secret_def.source == AWSSecretSource.PARAMETER_STORE:
                    if secret_def.parameter_name:
                        error_msg += f"  AWS CLI: aws ssm put-parameter --name '{secret_def.parameter_name}' --value 'YOUR_VALUE' --type SecureString\n"
                elif secret_def.source == AWSSecretSource.ENVIRONMENT_VARS:
                    error_msg += f"  ECS Task Definition: Add {secret} to environment variables\n"
            
            error_msg += "\nFOR PILOT DEPLOYMENT:\n"
            error_msg += f"1. Set ECS environment variables in task definition\n"
            error_msg += f"2. Create AWS Secrets Manager secrets for sensitive data\n"
            error_msg += f"3. Create AWS Parameter Store parameters for configuration\n"
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All required configuration validated successfully")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value (for sensitive data)"""
        value = self.config.get(key)
        if value and key in ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']:
            # Don't log sensitive values
            return value
        return value

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'

    def get_cors_origins(self) -> List[str]:
        """Get CORS allowed origins as list"""
        return self.get('ALLOWED_ORIGINS_LIST', ['https://pilot.owkai.app'])

    def get_database_url(self) -> str:
        """Get database connection URL"""
        url = self.get_secret('DATABASE_URL')
        if not url:
            raise ValueError("DATABASE_URL not configured")
        return url

# Global configuration instance
config = None

def get_config() -> AWSEnterpriseConfig:
    """Get global configuration instance"""
    global config
    if config is None:
        config = AWSEnterpriseConfig()
    return config

# Backwards compatibility exports
def get_secret(key: str) -> Optional[str]:
    """Get secret value (backwards compatible)"""
    return get_config().get_secret(key)

# Configuration exports for your existing code
_config = get_config()
SECRET_KEY = _config.get_secret('SECRET_KEY')
DATABASE_URL = _config.get_secret('DATABASE_URL') 
OPENAI_API_KEY = _config.get_secret('OPENAI_API_KEY')
ALGORITHM = _config.get('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = _config.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30)
REFRESH_TOKEN_EXPIRE_DAYS = _config.get('REFRESH_TOKEN_EXPIRE_DAYS', 7)
ALLOWED_ORIGINS = _config.get_cors_origins()

logger.info("AWS Enterprise Configuration initialized")
logger.info(f"Environment: {_config.environment}")
logger.info(f"Region: {_config.region}")
logger.info(f"CORS Origins: {len(ALLOWED_ORIGINS)} configured")
logger.info("All secrets managed via AWS services")
