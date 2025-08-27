import boto3
import os
import json
from typing import Optional
from botocore.exceptions import ClientError

class EnterpriseConfig:
    """Enterprise-grade configuration manager using AWS Secrets Manager"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.use_vault = False
        self.secrets_client = None
        
        # Initialize AWS Secrets Manager (works with ECS IAM roles)
        try:
            self.secrets_client = boto3.client(
                'secretsmanager',
                region_name=os.getenv('AWS_REGION', 'us-east-2')
            )
            # Test connection
            self.secrets_client.list_secrets(MaxResults=1)
            self.use_vault = True
            print("Enterprise Config: Using AWS Secrets Manager with IAM role")
        except Exception as e:
            print(f"AWS Secrets Manager not available: {e}")
            self.use_vault = False
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get secret from AWS Secrets Manager
        Args:
            secret_name: Name of the secret (e.g., 'jwt-private-key', 'jwt-public-key')
        Returns:
            Secret value as string or None if not found
        """
        if not self.use_vault or not self.secrets_client:
            print(f"Secrets Manager not available for {secret_name}")
            return None
        
        try:
            # Map secret names to full AWS paths
            secret_mapping = {
                'jwt-private-key': 'ow-ai/production/jwt-private-key',
                'jwt-public-key': 'ow-ai/production/jwt-public-key',
                'database': '/owkai/pilot/backend/DB_URL'
            }
            
            full_secret_name = secret_mapping.get(secret_name, secret_name)
            
            response = self.secrets_client.get_secret_value(SecretId=full_secret_name)
            return response['SecretString']
            
        except ClientError as e:
            print(f"Error retrieving secret {secret_name}: {e}")
            return None
    
    def get_database_url(self) -> str:
        """Get database URL with enterprise fallbacks"""
        if self.use_vault:
            db_url = self.get_secret('database')
            if db_url:
                return db_url
        
        # Fallback to environment variable
        return os.getenv('DATABASE_URL', 'postgresql://localhost/owkai_pilot')

# Create global instance
config = EnterpriseConfig()
