import boto3
import os
import json
from typing import Optional
from botocore.exceptions import ClientError

class EnterpriseConfig:
    """Enterprise-grade configuration manager using AWS Secrets Manager"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.use_vault = False
        self.secrets_client = None
        
        # Only initialize AWS in production if credentials are available
        if self.environment == 'production':
            try:
                # Check if AWS credentials are available
                aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                
                if aws_access_key and aws_secret_key:
                    self.secrets_client = boto3.client(
                        'secretsmanager',
                        region_name=os.getenv('AWS_REGION', 'us-east-1'),
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key
                    )
                    self.use_vault = True
                    print("✅ Enterprise Config: Using AWS Secrets Manager")
                else:
                    print("⚠️  Enterprise Config: AWS credentials not found, using fallback mode")
                    self.use_vault = False
                    
            except Exception as e:
                print(f"⚠️  Enterprise Config: AWS initialization failed ({str(e)}), using fallback mode")
                self.use_vault = False
        else:
            # Development: Local .env files only
            from dotenv import load_dotenv
            load_dotenv()
            self.use_vault = False
            print("⚠️  Development Config: Using .env files")
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret from AWS Secrets Manager (production) or .env (development)
        
        Args:
            secret_name: Name of the secret (e.g., 'database', 'jwt-private-key')
        
        Returns:
            Secret value or None if not found
        """
        if self.use_vault and self.secrets_client:
            try:
                # AWS Secrets Manager format: ow-ai/production/secret-name
                full_secret_name = f"ow-ai/production/{secret_name}"
                
                response = self.secrets_client.get_secret_value(SecretId=full_secret_name)
                
                # Parse the secret value
                secret_value = response['SecretString']
                
                # If it's JSON, extract the value
                try:
                    secret_dict = json.loads(secret_value)
                    # Return the first value if it's a dict
                    if isinstance(secret_dict, dict):
                        return list(secret_dict.values())[0]
                    return secret_value
                except json.JSONDecodeError:
                    return secret_value
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    print(f"⚠️  Secret not found: {secret_name}")
                else:
                    print(f"⚠️  Error retrieving secret {secret_name}: {e}")
                return None
            except Exception as e:
                print(f"⚠️  Unexpected error retrieving secret {secret_name}: {e}")
                return None
        else:
            # Fallback: use environment variables or .env files
            env_name = secret_name.upper().replace('-', '_')
            fallback_value = os.getenv(env_name)
            
            if fallback_value:
                return fallback_value
            
            # Enterprise fallback for Railway deployment
            if secret_name == 'jwt-private-key':
                return os.getenv('JWT_PRIVATE_KEY')
            elif secret_name == 'jwt-public-key':
                return os.getenv('JWT_PUBLIC_KEY')
            elif secret_name == 'database':
                return os.getenv('DATABASE_PASSWORD')
            elif secret_name == 'webhook-signing':
                return os.getenv('WEBHOOK_SECRET')
                
            return None
    
    def get_database_url(self) -> str:
        """Get complete database URL"""
        if self.use_vault:
            password = self.get_secret('database')
            host = os.getenv('DATABASE_HOST', 'localhost')
            username = os.getenv('DATABASE_USERNAME', 'postgres')
            database = os.getenv('DATABASE_NAME', 'owai')
            return f"postgresql://{username}:{password}@{host}/{database}"
        else:
            # Fallback to Railway DATABASE_URL or construct from parts
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                return database_url
            
            # Construct from individual parts
            password = self.get_secret('database') or os.getenv('DATABASE_PASSWORD', 'fallback_password')
            host = os.getenv('DATABASE_HOST', 'localhost')
            username = os.getenv('DATABASE_USERNAME', 'postgres')
            database = os.getenv('DATABASE_NAME', 'owai')
            return f"postgresql://{username}:{password}@{host}/{database}"
    
    def test_connection(self) -> bool:
        """Test if we can connect to AWS Secrets Manager"""
        if not self.use_vault or not self.secrets_client:
            print("⚠️  AWS Secrets Manager not configured - using fallback mode")
            return True  # Return True for fallback mode
            
        try:
            # Try to list secrets to test connection
            self.secrets_client.list_secrets(MaxResults=1)
            print("✅ AWS Secrets Manager connection successful")
            return True
        except Exception as e:
            print(f"⚠️  AWS Secrets Manager connection failed: {e}")
            return False

# Create global instance
config = EnterpriseConfig()

# Test connection on import (only in production)
if config.environment == 'production' and config.use_vault:
    config.test_connection()