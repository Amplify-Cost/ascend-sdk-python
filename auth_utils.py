# auth_utils.py 
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt  
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import logging
import hashlib 

logger = logging.getLogger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash password with SHA-256 + bcrypt (fixes 72-byte limit)
    
    Process:
    1. SHA-256 converts any length password to fixed 64-char string
    2. Bcrypt hashes that 64-char string (always under 72-byte limit)
    
    Why: Bcrypt limit is 72 bytes, SHA-256 output is always 64 chars
    """
    # Step 1: SHA-256 pre-hash (handles unlimited length)
    sha_digest = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    # Step 2: Bcrypt the digest (adds salt + adaptive cost)
    hashed = pwd_context.hash(sha_digest)
    
    logger.info("✅ Password hashed successfully (SHA-256+bcrypt)")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash (applies same SHA-256 step)
    
    Why: Must convert plain password to SHA-256 first, then compare
    """
    # Apply same SHA-256 pre-hash
    sha_digest = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    
    # Verify against bcrypt hash
    is_valid = pwd_context.verify(sha_digest, hashed_password)
    
    logger.info(f"🔐 Password verification: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
    return is_valid

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token(refresh_token: str):
    """Decode and validate refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# Simple token decode function (no dependencies to avoid circular imports)
def decode_access_token(token: str):
    """Decode access token - used internally only"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type if present
        if payload.get("type") and payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")