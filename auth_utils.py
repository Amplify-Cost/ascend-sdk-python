# auth_utils.py 
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt  
from datetime import datetime, timedelta, UTC
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import logging
import hashlib 

logger = logging.getLogger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with SHA-256 + bcrypt (fixes 72-byte limit)"""
    sha_digest = hashlib.sha256(password.encode('utf-8')).hexdigest()
    hashed = pwd_context.hash(sha_digest)
    logger.info("Password hashed successfully (SHA-256+bcrypt)")
    return hashed


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token(refresh_token: str):
    """Decode and validate refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password - supports both legacy and new hashes"""
    import hashlib
    
    # Try new method first (SHA-256 + bcrypt)
    sha_digest = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    try:
        if pwd_context.verify(sha_digest, hashed_password):
            logger.info("Password verification: SUCCESS (new method)")
            return True
    except:
        pass
    
    # Fallback: Try legacy method (direct bcrypt) for old users
    try:
        if pwd_context.verify(plain_password, hashed_password):
            logger.info("Password verification: SUCCESS (legacy method)")
            logger.warning("User needs password rehash - using legacy bcrypt")
            return True
    except:
        pass
    
    logger.info("Password verification: FAILED")
    return False

def decode_access_token(token: str):
    """Decode access token - used internally only"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        
        if payload.get("type") and payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid access token")
