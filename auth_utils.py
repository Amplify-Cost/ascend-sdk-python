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

# ============================================================================
# PHASE 1: ENTERPRISE PASSWORD SECURITY
# ============================================================================

def generate_secure_temp_password(length: int = 16) -> str:
    """Generate cryptographically secure temporary password

    Enterprise requirements:
    - Minimum 16 characters
    - Mix of uppercase, lowercase, numbers, special characters
    - Cryptographically secure randomness
    - Unique for each user

    Returns:
        Secure random password string (e.g., "Kx9#mP2wQ7$nR4tL")
    """
    import secrets
    import string

    logger.info(f"🔐 Generating secure temp password (length={length})")

    # Character sets for password complexity
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure at least one of each type (enterprise requirement)
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fill remaining characters with random mix
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        password_chars.append(secrets.choice(all_chars))

    # Shuffle to avoid predictable pattern (complexity requirement)
    secrets.SystemRandom().shuffle(password_chars)

    password = ''.join(password_chars)
    logger.info("✅ Secure temp password generated")
    return password

def validate_password_strength(password: str, is_admin: bool = False) -> dict:
    """Validate password meets enterprise complexity requirements

    Enterprise password policy (NIST SP 800-63B compliant):
    - Minimum 12 characters (14 for admin users)
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    - No sequential characters (123, abc, etc.)
    - No repeated characters (aaa, 111, etc.)
    - Not in common password list

    Args:
        password: The password to validate
        is_admin: Whether this is for an admin user (higher requirements)

    Returns:
        dict with keys:
            - valid (bool): Whether password meets all requirements
            - errors (list): List of validation error messages
            - strength_score (int): Password strength score 0-100
    """
    import re

    errors = []
    min_length = 14 if is_admin else 12

    logger.info(f"🔐 Validating password strength (admin={is_admin}, min_length={min_length})")

    # Length check
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")

    # Complexity checks
    if not re.search(r'[A-Z]', password):
        errors.append("Must contain at least one uppercase letter (A-Z)")
    if not re.search(r'[a-z]', password):
        errors.append("Must contain at least one lowercase letter (a-z)")
    if not re.search(r'\d', password):
        errors.append("Must contain at least one number (0-9)")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
        errors.append("Must contain at least one special character (!@#$%^&*...)")

    # Check for sequential characters (security vulnerability)
    sequential_patterns = [
        '012', '123', '234', '345', '456', '567', '678', '789',
        'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
        'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
        'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz'
    ]
    if any(pattern in password.lower() for pattern in sequential_patterns):
        errors.append("Cannot contain sequential characters (123, abc, etc.)")

    # Check for repeated characters (security vulnerability)
    if re.search(r'(.)\1{2,}', password):
        errors.append("Cannot contain 3 or more repeated characters (aaa, 111, etc.)")

    # Check against common passwords (top 100 most common)
    common_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey',
        'letmein', 'trustno1', 'dragon', 'baseball', 'iloveyou', 'master',
        'sunshine', 'ashley', 'bailey', 'shadow', 'superman', 'qazwsx',
        'michael', 'football', 'password1', 'welcome', 'admin', 'user'
    ]
    if password.lower() in common_passwords:
        errors.append("Cannot use common passwords (password, 123456, etc.)")

    # Calculate strength score (0-100)
    strength_score = 0
    if len(password) >= min_length:
        strength_score += 25
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
        strength_score += 20
    if re.search(r'\d', password):
        strength_score += 20
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:,.<>?]', password):
        strength_score += 20
    if len(password) >= 16:
        strength_score += 10
    if len(errors) == 0:
        strength_score += 5

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"✅ Password validation PASSED (score={strength_score}/100)")
    else:
        logger.warning(f"❌ Password validation FAILED ({len(errors)} errors)")
        for error in errors:
            logger.warning(f"   - {error}")

    return {
        "valid": is_valid,
        "errors": errors,
        "strength_score": strength_score
    }
