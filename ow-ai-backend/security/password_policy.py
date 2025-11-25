# security/password_policy.py
# =============================================================================
# ENTERPRISE BANKING-LEVEL REDACTED-CREDENTIAL POLICY
# =============================================================================
# Engineer: OW-KAI Enterprise Security Team
# Date: 2025-11-24
# Security Level: Banking/Financial Services Grade
#
# COMPLIANCE:
# - NIST SP 800-63B: Digital Identity Guidelines
# - PCI-DSS 8.2.3: Password Complexity
# - SOX Section 404: Access Controls
# - HIPAA § 164.312(d): Password Management
# =============================================================================

import re
import os
import logging
from typing import Tuple, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("enterprise.password_policy")

# =============================================================================
# REDACTED-CREDENTIAL POLICY CONFIGURATION (Environment-driven)
# =============================================================================

@dataclass
class PasswordPolicyConfig:
    """Enterprise password policy configuration"""
    min_length: int = int(os.getenv("REDACTED-CREDENTIAL_MIN_LENGTH", "12"))
    max_length: int = int(os.getenv("REDACTED-CREDENTIAL_MAX_LENGTH", "128"))
    require_uppercase: bool = os.getenv("REDACTED-CREDENTIAL_REQUIRE_UPPERCASE", "true").lower() == "true"
    require_lowercase: bool = os.getenv("REDACTED-CREDENTIAL_REQUIRE_LOWERCASE", "true").lower() == "true"
    require_numbers: bool = os.getenv("REDACTED-CREDENTIAL_REQUIRE_NUMBERS", "true").lower() == "true"
    require_special: bool = os.getenv("REDACTED-CREDENTIAL_REQUIRE_SPECIAL", "true").lower() == "true"
    min_unique_chars: int = int(os.getenv("REDACTED-CREDENTIAL_MIN_UNIQUE_CHARS", "8"))
    max_consecutive_chars: int = int(os.getenv("REDACTED-CREDENTIAL_MAX_CONSECUTIVE_CHARS", "3"))

    # Common password blacklist
    check_common_passwords: bool = True

    # Password history (prevent reuse)
    password_history_count: int = int(os.getenv("REDACTED-CREDENTIAL_HISTORY_COUNT", "12"))

# Global policy instance
POLICY = PasswordPolicyConfig()

# =============================================================================
# COMMON REDACTED-CREDENTIALS BLACKLIST (Top 100 most common)
# =============================================================================

COMMON_REDACTED-CREDENTIALS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "shadow", "123123", "654321", "superman", "qazwsx",
    "michael", "football", "password1", "password123", "welcome", "welcome1",
    "admin", "admin123", "root", "toor", "pass", "test", "guest", "master123",
    "changeme", "121212", "000000", "access", "passw0rd", "passw0rd!", "p@ssw0rd",
    "p@ssword", "p@ssword1", "password!", "password!1", "qwerty123", "qwertyuiop",
    "asdfghjkl", "zxcvbnm", "1q2w3e4r", "1qaz2wsx", "login", "starwars",
    "princess", "rockyou", "solo", "abc", "mypass", "mypassword", "1234",
    "12345", "123456789", "1234567890", "password12", "password1234", "passw0rd123",
    "letmein123", "welcome123", "login123", "admin1234", "root123", "toor123",
    # Banking-specific common passwords
    "bank", "banking", "money", "finance", "secure", "security", "enterprise",
    "corporate", "business", "company", "owkai", "owai", "pilot"
}

# =============================================================================
# REDACTED-CREDENTIAL VALIDATION FUNCTIONS
# =============================================================================

def validate_password_complexity(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against enterprise banking-level security requirements.

    Returns:
        Tuple of (is_valid, list_of_errors)

    COMPLIANCE:
    - NIST SP 800-63B Section 5.1.1.2
    - PCI-DSS Requirement 8.2.3
    """
    errors: List[str] = []

    if not password:
        return False, ["Password is required"]

    # Length checks
    if len(password) < POLICY.min_length:
        errors.append(f"Password must be at least {POLICY.min_length} characters")

    if len(password) > POLICY.max_length:
        errors.append(f"Password must not exceed {POLICY.max_length} characters")

    # Character class requirements
    if POLICY.require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if POLICY.require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if POLICY.require_numbers and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if POLICY.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*)")

    # Unique character check
    unique_chars = len(set(password))
    if unique_chars < POLICY.min_unique_chars:
        errors.append(f"Password must contain at least {POLICY.min_unique_chars} unique characters")

    # Consecutive character check (e.g., "aaa" or "111")
    if POLICY.max_consecutive_chars > 0:
        pattern = r'(.)\1{' + str(POLICY.max_consecutive_chars) + ',}'
        if re.search(pattern, password):
            errors.append(f"Password cannot contain more than {POLICY.max_consecutive_chars} consecutive identical characters")

    # Sequential character check (e.g., "abc" or "123")
    if _has_sequential_chars(password, 4):
        errors.append("Password cannot contain 4+ sequential characters (e.g., 'abcd', '1234')")

    # Common password check
    if POLICY.check_common_passwords:
        if password.lower() in COMMON_REDACTED-CREDENTIALS:
            errors.append("Password is too common and easily guessable")

        # Check if password contains common patterns
        for common in COMMON_REDACTED-CREDENTIALS:
            if len(common) >= 4 and common in password.lower():
                errors.append(f"Password contains common pattern: '{common}'")
                break

    # Keyboard pattern check (e.g., "qwerty", "asdf")
    keyboard_patterns = ["qwerty", "asdfgh", "zxcvbn", "qazwsx", "123456", "098765"]
    for pattern in keyboard_patterns:
        if pattern in password.lower():
            errors.append(f"Password contains keyboard pattern: '{pattern}'")
            break

    is_valid = len(errors) == 0

    if is_valid:
        logger.info("✅ Password complexity validation passed")
    else:
        logger.warning(f"❌ Password complexity validation failed: {len(errors)} issues")

    return is_valid, errors


def _has_sequential_chars(password: str, min_length: int = 4) -> bool:
    """Check for sequential characters like 'abcd' or '1234'"""
    password_lower = password.lower()

    # Check alphabetic sequences
    for i in range(len(password_lower) - min_length + 1):
        substring = password_lower[i:i + min_length]
        # Check ascending
        if all(ord(substring[j]) + 1 == ord(substring[j + 1]) for j in range(len(substring) - 1)):
            return True
        # Check descending
        if all(ord(substring[j]) - 1 == ord(substring[j + 1]) for j in range(len(substring) - 1)):
            return True

    return False


def get_password_strength(password: str) -> dict:
    """
    Calculate password strength score for UI feedback.

    Returns:
        dict with score (0-100), level (weak/fair/good/strong), and feedback
    """
    if not password:
        return {"score": 0, "level": "none", "feedback": "Enter a password"}

    score = 0
    feedback = []

    # Length scoring (up to 30 points)
    if len(password) >= 8:
        score += 10
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10

    # Character class scoring (up to 40 points)
    if re.search(r'[a-z]', password):
        score += 10
    if re.search(r'[A-Z]', password):
        score += 10
    if re.search(r'\d', password):
        score += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 10

    # Unique characters scoring (up to 20 points)
    unique_ratio = len(set(password)) / len(password)
    score += int(unique_ratio * 20)

    # Entropy bonus (up to 10 points)
    if len(set(password)) >= 10:
        score += 5
    if len(password) >= 20:
        score += 5

    # Deductions
    if password.lower() in COMMON_REDACTED-CREDENTIALS:
        score = max(0, score - 50)
        feedback.append("Common password detected")

    if re.search(r'(.)\1{3,}', password):
        score = max(0, score - 20)
        feedback.append("Too many repeated characters")

    # Determine level
    if score >= 80:
        level = "strong"
    elif score >= 60:
        level = "good"
    elif score >= 40:
        level = "fair"
    else:
        level = "weak"

    return {
        "score": min(100, score),
        "level": level,
        "feedback": feedback or ["Password strength acceptable"],
        "meets_enterprise_policy": score >= 60
    }


def generate_password_policy_message() -> str:
    """Generate human-readable password policy for error messages"""
    requirements = [
        f"At least {POLICY.min_length} characters long",
    ]

    if POLICY.require_uppercase:
        requirements.append("Contains at least one uppercase letter (A-Z)")
    if POLICY.require_lowercase:
        requirements.append("Contains at least one lowercase letter (a-z)")
    if POLICY.require_numbers:
        requirements.append("Contains at least one number (0-9)")
    if POLICY.require_special:
        requirements.append("Contains at least one special character (!@#$%^&*)")

    requirements.append(f"At least {POLICY.min_unique_chars} unique characters")
    requirements.append("No common passwords or keyboard patterns")

    return "Password must meet the following requirements:\n• " + "\n• ".join(requirements)


# Export policy for external use
__all__ = [
    "validate_password_complexity",
    "get_password_strength",
    "generate_password_policy_message",
    "POLICY",
    "PasswordPolicyConfig"
]
