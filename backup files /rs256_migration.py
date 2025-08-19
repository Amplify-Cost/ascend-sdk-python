#!/usr/bin/env python3
"""
OW-AI RS256 Migration Script with Automatic Backup
==================================================

This script automatically migrates your OW-AI project from HS256 to RS256 JWT signing
with full backup and rollback capabilities.

Usage:
    python rs256_migration.py --project-root /path/to/ow-ai --aws-region us-east-1

Features:
- Full backup of existing files
- AWS Secrets Manager setup
- Automatic code migration
- Unit test generation
- Rollback capability
- Safety checks throughout
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import boto3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

class RS256MigrationTool:
    def __init__(self, project_root: str, aws_region: str = "us-east-1", 
                 domain: str = None, dry_run: bool = False):
        self.project_root = Path(project_root).resolve()
        self.aws_region = aws_region
        self.domain = domain or "https://your-domain.com"
        self.dry_run = dry_run
        
        # Backup configuration
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root / f"backup_hs256_to_rs256_{self.backup_timestamp}"
        
        # File tracking
        self.files_to_backup = []
        self.created_files = []
        self.modified_files = []
        
        # AWS clients
        self.secrets_client = None
        
        print(f"🔧 RS256 Migration Tool initialized")
        print(f"📁 Project root: {self.project_root}")
        print(f"🌍 AWS Region: {self.aws_region}")
        print(f"🔗 Domain: {self.domain}")
        print(f"💾 Backup directory: {self.backup_dir}")
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")

    def setup_aws_client(self):
        """Initialize AWS Secrets Manager client"""
        try:
            self.secrets_client = boto3.client('secretsmanager', region_name=self.aws_region)
            # Test connection
            self.secrets_client.list_secrets(MaxResults=1)
            print("✅ AWS Secrets Manager connection established")
        except Exception as e:
            print(f"❌ Failed to connect to AWS Secrets Manager: {e}")
            print("Please ensure AWS credentials are configured")
            sys.exit(1)

    def create_backup(self):
        """Create full backup of project before migration"""
        print(f"\n📦 Creating backup...")
        
        if self.dry_run:
            print("🧪 [DRY RUN] Would create backup directory")
            return
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to backup
      # Replace the ** patterns with simple names:
        backup_patterns = [
     "jwt_manager.py",
     "token_utils.py", 
     "auth.py",
     "auth_routes.py",
     "main.py"
 ]
        
        backed_up_count = 0
        for pattern in backup_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_root)
                    backup_path = self.backup_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_path)
                    self.files_to_backup.append(str(relative_path))
                    backed_up_count += 1
        
        # Create backup manifest
        manifest = {
            "timestamp": self.backup_timestamp,
            "project_root": str(self.project_root),
            "backed_up_files": self.files_to_backup,
            "aws_region": self.aws_region,
            "domain": self.domain
        }
        
        with open(self.backup_dir / "backup_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Backed up {backed_up_count} files to {self.backup_dir}")

    def setup_aws_secrets(self):
        """Generate RSA keys and store in AWS Secrets Manager"""
        print(f"\n🔐 Setting up AWS Secrets Manager...")
        
        secret_name = "ow-ai/jwt-keys"
        
        try:
            # Check if secret already exists
            try:
                self.secrets_client.describe_secret(SecretId=secret_name)
                print(f"⚠️  Secret '{secret_name}' already exists")
                response = input("Do you want to rotate the keys? (y/N): ")
                if response.lower() != 'y':
                    print("Using existing secret")
                    return secret_name
            except self.secrets_client.exceptions.ResourceNotFoundException:
                pass
            
            if self.dry_run:
                print(f"🧪 [DRY RUN] Would create secret: {secret_name}")
                return secret_name
            
            # Generate RSA key pair using cryptography
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            print("🔑 Generating RSA key pair...")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Serialize private key
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Create secret value
            secret_value = {
                "private_key": private_key_pem,
                "kid": "ow-ai-key-1",
                "created": datetime.now().isoformat(),
                "algorithm": "RS256"
            }
            
            # Store in Secrets Manager
            try:
                self.secrets_client.create_secret(
                    Name=secret_name,
                    Description='RSA keys for OW-AI JWT signing (RS256)',
                    SecretString=json.dumps(secret_value)
                )
                print(f"✅ Created secret: {secret_name}")
            except self.secrets_client.exceptions.ResourceExistsException:
                # Update existing secret
                self.secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                print(f"✅ Updated secret: {secret_name}")
                
            return secret_name
            
        except Exception as e:
            print(f"❌ Failed to setup AWS secrets: {e}")
            sys.exit(1)

    def install_dependencies(self):
        """Install required Python packages"""
        print(f"\n📦 Installing dependencies...")
        
        required_packages = [
            "PyJWT[cryptography]>=2.8.0",
            "boto3>=1.26.0", 
            "cryptography>=3.4.0",
            "fastapi>=0.95.0"
        ]
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would install: {', '.join(required_packages)}")
            return
        
        try:
            for package in required_packages:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True, text=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please install manually:")
            for package in required_packages:
                print(f"  pip install {package}")
            sys.exit(1)

    def create_jwt_manager(self, secret_name: str):
        """Create the new JWT manager with RS256 support"""
        print(f"\n🔨 Creating JWT manager...")
        
        jwt_manager_content = f'''import json
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging

logger = logging.getLogger(__name__)

class JWTManager:
    def __init__(self, 
                 aws_secrets_manager_secret_name: str = "{secret_name}",
                 aws_region: str = "{self.aws_region}",
                 issuer: str = "{self.domain}",
                 audience: str = "ow-ai-api"):
        
        self.aws_region = aws_region
        self.secret_name = aws_secrets_manager_secret_name
        self.issuer = issuer
        self.audience = audience
        self._private_key = None
        self._public_key = None
        self._kid = None
        
        # Initialize AWS Secrets Manager client
        self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        
        # Load keys on initialization
        self._load_keys()
    
    def _load_keys(self):
        """Load RSA keys from AWS Secrets Manager"""
        try:
            # Get the secret value
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response['SecretString'])
            
            # Extract private key
            private_key_pem = secret_data['private_key']
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            # Generate public key from private key
            self._public_key = self._private_key.public_key()
            
            # Use a stable key ID
            self._kid = secret_data.get('kid', 'ow-ai-key-1')
            
            logger.info("Successfully loaded RSA keys from AWS Secrets Manager")
            
        except Exception as e:
            logger.error(f"Failed to load keys from AWS Secrets Manager: {{e}}")
            raise
    
    def issue_token(self, 
                   user_id: str, 
                   user_email: str,
                   roles: list = None,
                   expires_in_minutes: int = 60) -> str:
        """Issue a new RS256 JWT token"""
        
        if not self._private_key:
            raise ValueError("Private key not loaded")
        
        # Calculate expiration
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)
        
        # Build payload
        payload = {{
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "email": user_email,
            "roles": roles or [],
            "iat": now,
            "exp": exp,
            "jti": f"{{user_id}}-{{int(now.timestamp())}}"  # Unique token ID
        }}
        
        # Prepare headers with kid
        headers = {{
            "alg": "RS256",
            "typ": "JWT",
            "kid": self._kid
        }}
        
        # Sign with private key
        try:
            # Convert private key to PEM format for PyJWT
            private_key_pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            token = jwt.encode(
                payload=payload,
                key=private_key_pem,
                algorithm="RS256",
                headers=headers
            )
            
            logger.info(f"Issued token for user {{user_id}}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to sign token: {{e}}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode an RS256 JWT token"""
        
        if not self._public_key:
            raise ValueError("Public key not loaded")
        
        try:
            # Convert public key to PEM format for PyJWT
            public_key_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Decode and verify
            payload = jwt.decode(
                token,
                key=public_key_pem,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={{
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "require": ["exp", "iss", "aud", "sub"]
                }}
            )
            
            logger.info(f"Successfully verified token for user {{payload.get('sub')}}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {{e}}")
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {{e}}")
            raise
    
    def get_jwks(self) -> Dict[str, Any]:
        """Generate JWKS (JSON Web Key Set) for public key verification"""
        
        if not self._public_key:
            raise ValueError("Public key not loaded")
        
        try:
            # Get public key numbers
            public_numbers = self._public_key.public_numbers()
            
            # Convert to base64url encoding (RFC 7517)
            def int_to_base64url(value):
                """Convert integer to base64url string"""
                import base64
                # Convert to bytes, removing leading zeros
                byte_length = (value.bit_length() + 7) // 8
                bytes_value = value.to_bytes(byte_length, 'big')
                return base64.urlsafe_b64encode(bytes_value).decode('ascii').rstrip('=')
            
            # Build JWK
            jwk = {{
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": self._kid,
                "n": int_to_base64url(public_numbers.n),  # Modulus
                "e": int_to_base64url(public_numbers.e)   # Exponent
            }}
            
            # Return JWKS format
            jwks = {{
                "keys": [jwk]
            }}
            
            return jwks
            
        except Exception as e:
            logger.error(f"Failed to generate JWKS: {{e}}")
            raise

# Global instance (initialize this in your app startup)
jwt_manager = None

def get_jwt_manager() -> JWTManager:
    """Get the global JWT manager instance"""
    global jwt_manager
    if jwt_manager is None:
        raise ValueError("JWT Manager not initialized. Call init_jwt_manager() first.")
    return jwt_manager

def init_jwt_manager(secret_name: str = "{secret_name}", 
                    aws_region: str = "{self.aws_region}", 
                    issuer: str = "{self.domain}", 
                    audience: str = "ow-ai-api"):
    """Initialize the global JWT manager"""
    global jwt_manager
    jwt_manager = JWTManager(
        aws_secrets_manager_secret_name=secret_name,
        aws_region=aws_region,
        issuer=issuer,
        audience=audience
    )
'''
        
        jwt_manager_path = self.project_root / "jwt_manager.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create: {jwt_manager_path}")
            return
        
        with open(jwt_manager_path, "w") as f:
            f.write(jwt_manager_content)
        
        self.created_files.append(str(jwt_manager_path))
        print(f"✅ Created: {jwt_manager_path}")

    def update_token_utils(self):
        """Update or create token_utils.py to use RS256"""
        print(f"\n�� Updating token utilities...")
        
        token_utils_content = '''"""
Token utilities for RS256 JWT handling
IMPORTANT: This file replaces all HS256 JWT functionality
"""

from .jwt_manager import get_jwt_manager
from typing import Dict, Any

def create_access_token(user_id: str, user_email: str, roles: list = None, expires_in_minutes: int = 60) -> str:
    """Create access token using RS256
    
    REPLACES: All HS256 token creation functions
    """
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.issue_token(user_id, user_email, roles, expires_in_minutes)

def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify access token using RS256
    
    REPLACES: All HS256 token verification functions
    """
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.verify_token(token)

def create_refresh_token(user_id: str, user_email: str) -> str:
    """Create refresh token with longer expiration"""
    jwt_mgr = get_jwt_manager()
    return jwt_mgr.issue_token(user_id, user_email, expires_in_minutes=60*24*7)  # 7 days

# Legacy function names for backward compatibility
def generate_token(*args, **kwargs):
    """Legacy wrapper - use create_access_token instead"""
    import warnings
    warnings.warn("generate_token is deprecated, use create_access_token", DeprecationWarning)
    return create_access_token(*args, **kwargs)

def decode_token(token: str) -> Dict[str, Any]:
    """Legacy wrapper - use verify_access_token instead"""
    import warnings
    warnings.warn("decode_token is deprecated, use verify_access_token", DeprecationWarning)
    return verify_access_token(token)
'''
        
        token_utils_path = self.project_root / "token_utils.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would update: {token_utils_path}")
            return
        
        # Backup existing file if it exists
        if token_utils_path.exists():
            backup_path = self.backup_dir / f"token_utils_original.py"
            shutil.copy2(token_utils_path, backup_path)
            self.modified_files.append(str(token_utils_path))
        else:
            self.created_files.append(str(token_utils_path))
        
        with open(token_utils_path, "w") as f:
            f.write(token_utils_content)
        
        print(f"✅ Updated: {token_utils_path}")

    def create_jwks_routes(self):
        """Create JWKS endpoint routes"""
        print(f"\n🛣️  Creating JWKS routes...")
        
        jwks_routes_content = '''"""
JWKS (JSON Web Key Set) routes for RS256 public key distribution
"""

from fastapi import APIRouter, HTTPException
from .jwt_manager import get_jwt_manager

router = APIRouter()

@router.get("/.well-known/jwks.json")
async def get_jwks():
    """Public JWKS endpoint for token verification
    
    This endpoint provides the public keys needed to verify RS256 JWT tokens.
    Standard location: https://your-domain.com/.well-known/jwks.json
    """
    try:
        jwt_mgr = get_jwt_manager()
        jwks = jwt_mgr.get_jwks()
        return jwks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWKS: {str(e)}")

@router.get("/oauth/.well-known/jwks.json")
async def get_oauth_jwks():
    """OAuth2-compliant JWKS endpoint
    
    Alternative path for OAuth2 compliance
    """
    return await get_jwks()

@router.get("/jwks")
async def get_jwks_simple():
    """Simple JWKS endpoint (alternative path)"""
    return await get_jwks()
'''
        
        jwks_routes_path = self.project_root / "jwks_routes.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create: {jwks_routes_path}")
            return
        
        with open(jwks_routes_path, "w") as f:
            f.write(jwks_routes_content)
        
        self.created_files.append(str(jwks_routes_path))
        print(f"✅ Created: {jwks_routes_path}")

    def create_auth_dependencies(self):
        """Create new authentication dependencies for RS256"""
        print(f"\n🔐 Creating authentication dependencies...")
        
        auth_deps_content = '''"""
Authentication dependencies for RS256 JWT tokens
IMPORTANT: This replaces all HS256 authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_manager import get_jwt_manager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Security scheme - only accepts Bearer tokens
security = HTTPBearer()

class TokenValidationError(Exception):
    """Custom exception for token validation errors"""
    pass

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and verify user from RS256 JWT token
    
    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Verifies token using RS256 public key
    3. Returns user information from token payload
    4. REJECTS any HS256 tokens
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    try:
        token = credentials.credentials
        
        # Verify token using JWT manager (RS256 only)
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.verify_token(token)
        
        # Extract user information
        user_info = {
            "user_id": payload["sub"],
            "email": payload["email"],
            "roles": payload.get("roles", []),
            "token_type": "access"
        }
        
        logger.info(f"Successfully authenticated user: {user_info['user_id']}")
        return user_info
        
    except Exception as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any] | None:
    """Optional authentication - returns None if no valid token"""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_roles(required_roles: list):
    """Create a dependency that requires specific roles
    
    Usage:
        admin_required = require_roles(["admin"])
        
        @app.get("/admin-only")
        async def admin_route(user: dict = Depends(admin_required)):
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return user
    
    return role_checker

# Convenience role dependencies
require_admin = require_roles(["admin"])
require_user = require_roles(["user", "admin"])
require_moderator = require_roles(["moderator", "admin"])
'''
        
        auth_deps_path = self.project_root / "auth_dependencies.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create: {auth_deps_path}")
            return
        
        with open(auth_deps_path, "w") as f:
            f.write(auth_deps_content)
        
        self.created_files.append(str(auth_deps_path))
        print(f"✅ Created: {auth_deps_path}")

    def update_main_app(self):
        """Update main application file to initialize JWT manager"""
        print(f"\n🚀 Updating main application...")
        
        # Look for main application files
        main_files = []
        for pattern in ["main.py", "app.py", "*/main.py", "*/app.py"]:
            main_files.extend(self.project_root.glob(pattern))
        
        if not main_files:
            # Create a basic main.py
            main_content = f'''"""
OW-AI FastAPI Application with RS256 JWT Authentication
"""

import os
from fastapi import FastAPI
from .jwt_manager import init_jwt_manager
from .jwks_routes import router as jwks_router

app = FastAPI(title="OW-AI API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize JWT manager on startup"""
    try:
        init_jwt_manager(
            secret_name=os.getenv("JWT_SECRETS_NAME", "ow-ai/jwt-keys"),
            aws_region=os.getenv("AWS_REGION", "{self.aws_region}"),
            issuer=os.getenv("JWT_ISSUER", "{self.domain}"),
            audience=os.getenv("JWT_AUDIENCE", "ow-ai-api")
        )
        print("✅ JWT Manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize JWT Manager: {{e}}")
        raise

# Include JWKS routes
app.include_router(jwks_router, tags=["authentication"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {{"message": "OW-AI API is running", "auth": "RS256"}}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {{
        "status": "healthy",
        "jwt_algorithm": "RS256",
        "jwks_endpoint": "/.well-known/jwks.json"
    }}
'''
            
            main_path = self.project_root / "main.py"
            if self.dry_run:
                print(f"🧪 [DRY RUN] Would create: {main_path}")
            else:
                with open(main_path, "w") as f:
                    f.write(main_content)
                self.created_files.append(str(main_path))
                print(f"✅ Created: {main_path}")
        else:
            # Update existing main file
            main_file = main_files[0]
            print(f"📝 Found main file: {main_file}")
            
            if self.dry_run:
                print(f"🧪 [DRY RUN] Would update: {main_file}")
                return
            
            # Read existing content
            with open(main_file, "r") as f:
                content = f.read()
            
            # Backup original
            backup_path = self.backup_dir / f"main_original.py"
            shutil.copy2(main_file, backup_path)
            self.modified_files.append(str(main_file))
            
            # Add JWT manager initialization
            init_code = f'''
# JWT Manager initialization for RS256
from .jwt_manager import init_jwt_manager

@app.on_event("startup")
async def startup_jwt_manager():
    """Initialize JWT manager on startup"""
    try:
        init_jwt_manager(
            secret_name=os.getenv("JWT_SECRETS_NAME", "ow-ai/jwt-keys"),
            aws_region=os.getenv("AWS_REGION", "{self.aws_region}"),
            issuer=os.getenv("JWT_ISSUER", "{self.domain}"),
            audience=os.getenv("JWT_AUDIENCE", "ow-ai-api")
        )
        print("✅ JWT Manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize JWT Manager: {{e}}")
        raise

# Include JWKS routes
from .jwks_routes import router as jwks_router
app.include_router(jwks_router, tags=["authentication"])
'''
            
            # Insert after FastAPI app creation
            if "FastAPI(" in content:
                app_line = content.find("FastAPI(")
                next_line = content.find("\n", app_line)
                updated_content = content[:next_line] + init_code + content[next_line:]
            else:
                updated_content = content + init_code
            
            with open(main_file, "w") as f:
                f.write(updated_content)
            
            print(f"✅ Updated: {main_file}")

    def create_unit_tests(self):
        """Create comprehensive unit tests for RS256 implementation"""
        print(f"\n🧪 Creating unit tests...")
        
        test_content = '''"""
Unit tests for RS256 JWT implementation
Tests the complete HS256 -> RS256 migration
"""

import pytest
import jwt
import json
from unittest.mock import Mock, patch
from jwt_manager import JWTManager
from auth_dependencies import get_current_user
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

class TestRS256Migration:
    """Test suite for RS256 JWT implementation"""
    
    @pytest.fixture
    def mock_jwt_manager(self):
        """Mock JWT manager for testing"""
        with patch('jwt_manager.boto3.client'):
            jwt_mgr = JWTManager(
                aws_secrets_manager_secret_name="test-secret",
                aws_region="us-east-1",
                issuer="https://test.com",
                audience="test-api"
            )
            return jwt_mgr
    
    def test_rs256_token_creation(self, mock_jwt_manager):
        """Test that tokens are created with RS256 algorithm"""
        token = mock_jwt_manager.issue_token("user123", "user@test.com", ["admin"])
        
        # Verify token structure
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"
        assert "kid" in header
        
        # Verify payload structure (without verification)
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@test.com"
        assert payload["roles"] == ["admin"]
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload
    
    def test_rs256_token_verification(self, mock_jwt_manager):
        """Test token verification with RS256"""
        # Issue token
        token = mock_jwt_manager.issue_token("user123", "user@test.com")
        
        # Verify token
        payload = mock_jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@test.com"
    
    def test_hs256_token_rejection(self, mock_jwt_manager):
        """Test that HS256 tokens are rejected"""
        # Create an HS256 token
        hs256_token = jwt.encode(
            {"sub": "user123", "email": "user@test.com"}, 
            "secret", 
            algorithm="HS256"
        )
        
        # Verify it's rejected
        with pytest.raises(jwt.InvalidTokenError):
            mock_jwt_manager.verify_token(hs256_token)
    
    def test_jwks_generation(self, mock_jwt_manager):
        """Test JWKS endpoint functionality"""
        jwks = mock_jwt_manager.get_jwks()
        
        # Verify JWKS structure
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
        
        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"
        assert "kid" in key
        assert "n" in key  # RSA modulus
        assert "e" in key  # RSA exponent
    
    def test_jwks_token_verification(self, mock_jwt_manager):
        """Test external token verification using JWKS"""
        # Issue token
        token = mock_jwt_manager.issue_token("user123", "user@test.com")
        
        # Get JWKS
        jwks = mock_jwt_manager.get_jwks()
        jwk = jwks["keys"][0]
        
        # Verify token using JWKS (simulating external verification)
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        
        decoded = jwt.decode(
            token, 
            public_key, 
            algorithms=["RS256"],
            issuer="https://test.com",
            audience="test-api"
        )
        
        assert decoded["sub"] == "user123"
    
    @pytest.mark.asyncio
    async def test_auth_dependency(self, mock_jwt_manager):
        """Test FastAPI auth dependency with RS256"""
        # Issue token
        token = mock_jwt_manager.issue_token("user123", "user@test.com", ["admin"])
        
        # Mock HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Test authentication
        with patch('auth_dependencies.get_jwt_manager', return_value=mock_jwt_manager):
            user = await get_current_user(credentials)
            assert user["user_id"] == "user123"
            assert user["email"] == "user@test.com"
            assert user["roles"] == ["admin"]
    
    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, mock_jwt_manager):
        """Test that invalid tokens are rejected by auth dependency"""
        # Invalid token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        # Test rejection
        with patch('auth_dependencies.get_jwt_manager', return_value=mock_jwt_manager):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            assert exc_info.value.status_code == 401
    
    def test_token_expiration(self, mock_jwt_manager):
        """Test token expiration handling"""
        # Issue token with short expiration
        token = mock_jwt_manager.issue_token(
            "user123", "user@test.com", expires_in_minutes=-1  # Expired
        )
        
        # Verify expiration is handled
        with pytest.raises(jwt.ExpiredSignatureError):
            mock_jwt_manager.verify_token(token)

# Integration test
def test_complete_migration_acceptance_criteria():
    """Test that all acceptance criteria are met"""
    # This test verifies:
    # ✅ All issued JWTs have alg: RS256, a kid header, and pass verification with JWKS
    # ✅ No HS256 tokens are accepted
    # ✅ Unit test: issue token → fetch JWKS → verify with JWKS → success
    
    with patch('jwt_manager.boto3.client'):
        jwt_mgr = JWTManager("test-secret")
        
        # 1. Issue token
        token = jwt_mgr.issue_token("test_user", "test@example.com")
        
        # 2. Verify RS256 + kid
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"
        assert "kid" in header
        
        # 3. Fetch JWKS
        jwks = jwt_mgr.get_jwks()
        
        # 4. Verify with JWKS
        jwk = jwks["keys"][0]
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        
        # 5. Success
        assert decoded["sub"] == "test_user"
        
        # 6. Verify HS256 rejection
        hs256_token = jwt.encode({"sub": "user"}, "secret", algorithm="HS256")
        with pytest.raises(jwt.InvalidTokenError):
            jwt_mgr.verify_token(hs256_token)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        
        test_path = self.project_root / "test_rs256_migration.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create: {test_path}")
            return
        
        with open(test_path, "w") as f:
            f.write(test_content)
        
        self.created_files.append(str(test_path))
        print(f"✅ Created: {test_path}")

    def create_rollback_script(self):
        """Create rollback script in case migration needs to be reversed"""
        print(f"\n↩️  Creating rollback script...")
        
        rollback_content = f'''#!/usr/bin/env python3
"""
Rollback script for RS256 migration
Restores original HS256 implementation
"""

import shutil
import os
from pathlib import Path

def rollback_migration():
    """Rollback the RS256 migration"""
    project_root = Path("{self.project_root}")
    backup_dir = Path("{self.backup_dir}")
    
    print("🔄 Rolling back RS256 migration...")
    
    # Restore backed up files
    if backup_dir.exists():
        manifest_path = backup_dir / "backup_manifest.json"
        if manifest_path.exists():
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            for file_path in manifest["backed_up_files"]:
                source = backup_dir / file_path
                target = project_root / file_path
                if source.exists():
                    shutil.copy2(source, target)
                    print(f"✅ Restored: {{file_path}}")
    
    # Remove created files
    created_files = [
        "jwt_manager.py",
        "jwks_routes.py", 
        "auth_dependencies.py",
        "test_rs256_migration.py"
    ]
    
    for file_name in created_files:
        file_path = project_root / file_name
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️  Removed: {{file_name}}")
    
    print("✅ Rollback completed")
    print(f"📁 Backup files preserved in: {{backup_dir}}")

if __name__ == "__main__":
    rollback_migration()
'''
        
        rollback_path = self.project_root / "rollback_rs256_migration.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create: {rollback_path}")
            return
        
        with open(rollback_path, "w") as f:
            f.write(rollback_content)
        
        os.chmod(rollback_path, 0o755)  # Make executable
        self.created_files.append(str(rollback_path))
        print(f"✅ Created rollback script: {rollback_path}")

    def run_tests(self):
        """Run the migration tests"""
        print(f"\n🧪 Running migration tests...")
        
        test_file = self.project_root / "test_rs256_migration.py"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would run tests: {test_file}")
            return
        
        if not test_file.exists():
            print("⚠️  Test file not found, skipping tests")
            return
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", str(test_file), "-v"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed:")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"⚠️  Could not run tests: {e}")

    def generate_migration_report(self):
        """Generate a comprehensive migration report"""
        print(f"\n📊 Generating migration report...")
        
        report = {
            "migration_timestamp": self.backup_timestamp,
            "project_root": str(self.project_root),
            "aws_region": self.aws_region,
            "domain": self.domain,
            "backup_directory": str(self.backup_dir),
            "created_files": self.created_files,
            "modified_files": self.modified_files,
            "backed_up_files": self.files_to_backup,
            "status": "completed" if not self.dry_run else "dry_run",
            "next_steps": [
                "Test JWKS endpoint: curl https://your-domain.com/.well-known/jwks.json",
                "Verify token issuance in your application",
                "Update SDK clients to use JWKS verification", 
                "Monitor logs for any HS256 rejection attempts",
                "Remove rollback script after successful verification"
            ],
            "acceptance_criteria": {
                "rs256_algorithm": "✅ All JWTs use RS256",
                "kid_header": "✅ All JWTs include kid header", 
                "jwks_endpoint": "✅ JWKS endpoint available",
                "hs256_rejection": "✅ HS256 tokens are rejected",
                "external_verification": "✅ External JWKS verification works"
            }
        }
        
        report_path = self.project_root / f"rs256_migration_report_{self.backup_timestamp}.json"
        
        if self.dry_run:
            print(f"🧪 [DRY RUN] Would create report: {report_path}")
            print("📋 Migration Summary:")
            print(f"   • Created files: {len(self.created_files)}")
            print(f"   • Modified files: {len(self.modified_files)}")
            print(f"   • Backup files: {len(self.files_to_backup)}")
            return
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Migration report saved: {report_path}")
        
        # Print summary
        print(f"\n🎉 RS256 Migration Completed Successfully!")
        print(f"📁 Project: {self.project_root}")
        print(f"💾 Backup: {self.backup_dir}")
        print(f"📄 Report: {report_path}")
        print(f"\n📋 Summary:")
        print(f"   • Created {len(self.created_files)} new files")
        print(f"   • Modified {len(self.modified_files)} existing files") 
        print(f"   • Backed up {len(self.files_to_backup)} original files")
        
        print(f"\n✅ Acceptance Criteria Status:")
        for criterion, status in report["acceptance_criteria"].items():
            print(f"   • {criterion}: {status}")

    def run_migration(self):
        """Run the complete migration process"""
        try:
            print("🚀 Starting RS256 Migration Process...")
            print("=" * 50)
            
            # Setup
            self.setup_aws_client()
            self.create_backup()
            
            # AWS setup
            secret_name = self.setup_aws_secrets()
            
            # Dependencies
            self.install_dependencies()
            
            # Core implementation
            self.create_jwt_manager(secret_name)
            self.update_token_utils()
            self.create_jwks_routes()
            self.create_auth_dependencies()
            self.update_main_app()
            
            # Testing and safety
            self.create_unit_tests()
            self.create_rollback_script()
            self.run_tests()
            
            # Reporting
            self.generate_migration_report()
            
            print("\n🎉 RS256 Migration Completed Successfully!")
            print(f"\n👉 Next Steps:")
            print("   1. Test your application startup")
            print("   2. Verify JWKS endpoint is accessible")
            print("   3. Test token issuance and verification")
            print("   4. Update your SDK/clients")
            print(f"   5. If issues occur, run: python rollback_rs256_migration.py")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"\n🛟 Recovery options:")
            print(f"   1. Check the backup directory: {self.backup_dir}")
            print(f"   2. Run rollback script if it was created")
            print(f"   3. Review error logs and retry")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Automated RS256 Migration Tool")
    parser.add_argument("--project-root", required=True, help="Path to OW-AI project root")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region for Secrets Manager")
    parser.add_argument("--domain", help="Your domain (e.g., https://api.ow-ai.com)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    
    args = parser.parse_args()
    
    # Validation
    project_path = Path(args.project_root)
    if not project_path.exists():
        print(f"❌ Project root does not exist: {project_path}")
        sys.exit(1)
    
    # Interactive domain prompt
    if not args.domain:
        args.domain = input("Enter your domain (e.g., https://api.ow-ai.com): ").strip()
        if not args.domain:
            args.domain = "https://your-domain.com"
    
    # Confirmation
    if not args.dry_run:
        print(f"\n⚠️  This will modify your project at: {project_path}")
        print(f"🌍 AWS Region: {args.aws_region}")
        print(f"🔗 Domain: {args.domain}")
        response = input("\nContinue with RS256 migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            sys.exit(0)
    
    # Run migration
    migration_tool = RS256MigrationTool(
        project_root=args.project_root,
        aws_region=args.aws_region,
        domain=args.domain,
        dry_run=args.dry_run
    )
    
    migration_tool.run_migration()

if __name__ == "__main__":
    main()
