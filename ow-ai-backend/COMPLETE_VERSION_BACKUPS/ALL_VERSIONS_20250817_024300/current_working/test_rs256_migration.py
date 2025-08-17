"""
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
