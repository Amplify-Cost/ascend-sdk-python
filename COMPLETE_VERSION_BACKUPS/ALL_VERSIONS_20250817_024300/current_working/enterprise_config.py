import boto3
import os
import json
from typing import Optional
from botocore.exceptions import ClientError

class EnterpriseConfig:
    """Enterprise-grade configuration manager using AWS Secrets Manager"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        if self.environment == 'production':
            # Production: AWS Secrets Manager
            self.secrets_client = boto3.client(
                'secretsmanager',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.use_vault = True
            print("✅ Enterprise Config: Using AWS Secrets Manager")
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
        if self.use_vault:
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
                    print(f"❌ Secret not found: {secret_name}")
                elif error_code == 'InvalidRequestException':
                    print(f"❌ Invalid request for secret: {secret_name}")
                elif error_code == 'InvalidParameterException':
                    print(f"❌ Invalid parameter for secret: {secret_name}")
                else:
                    print(f"❌ Error retrieving secret {secret_name}: {e}")
                return None
            except Exception as e:
                print(f"❌ Unexpected error retrieving secret {secret_name}: {e}")
                return None
        else:
            # Development: use .env files
            return os.getenv(secret_name.upper().replace('-', '_'))
    
    def get_database_url(self) -> str:
        """Get complete database URL"""
        if self.use_vault:
            password = self.get_secret('database')
            host = os.getenv('DATABASE_HOST', 'localhost')
            username = os.getenv('DATABASE_USERNAME', 'postgres')
            database = os.getenv('DATABASE_NAME', 'owai')
            return f"postgresql://{username}:REDACTED-CREDENTIAL@{host}/{database}"
        else:
            return os.getenv('DATABASE_URL', 'postgresql://localhost/owai_dev')
    
    def test_connection(self) -> bool:
        """Test if we can connect to AWS Secrets Manager"""
        if not self.use_vault:
            return True  # No test needed for development
            
        try:
            # Try to list secrets to test connection
            self.secrets_client.list_secrets(MaxResults=1)
            print("✅ AWS Secrets Manager connection successful")
            return True
        except Exception as e:
            print(f"❌ AWS Secrets Manager connection failed: {e}")
            return False

# Create global instance
config = EnterpriseConfig()

# Test connection on import (only in production)
if config.environment == 'production':
    config.test_connection()