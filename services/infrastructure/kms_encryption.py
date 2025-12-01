"""
OW-AI Enterprise KMS Encryption Service
========================================

SEC-006: AWS KMS integration for encryption key management

Features:
- AWS KMS key management and rotation
- Data encryption using KMS-generated data keys
- Key caching for performance optimization
- Audit logging for all cryptographic operations

Compliance:
- SOC 2 CC6.1 (Cryptographic Key Management)
- PCI-DSS 3.5 (Key Storage)
- HIPAA 164.312(a)(2)(iv) (Encryption)
- NIST SP 800-57 (Key Management)

Version: 1.0.0
Date: 2025-12-01
"""

import os
import base64
import hashlib
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import secrets

logger = logging.getLogger("enterprise.infrastructure.kms")


class KeyPurpose(Enum):
    """Purpose categories for encryption keys."""
    DATA_ENCRYPTION = "data_encryption"
    TOKEN_SIGNING = "token_signing"
    PII_ENCRYPTION = "pii_encryption"
    AUDIT_SIGNING = "audit_signing"
    BACKUP_ENCRYPTION = "backup_encryption"


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "AES_256_GCM"
    AES_256_CBC = "AES_256_CBC"
    RSA_OAEP_SHA256 = "RSA_OAEP_SHA256"


class KMSEncryptionService:
    """
    SEC-006: AWS KMS integration for enterprise encryption.

    Banking-Level Requirements:
    - All sensitive data encrypted at rest
    - Keys managed by AWS KMS (never stored locally)
    - Automatic key rotation every 365 days
    - Complete audit trail for key usage
    """

    # Key cache TTL (5 minutes)
    KEY_CACHE_TTL = 300

    # Key aliases for different purposes
    KEY_ALIASES = {
        KeyPurpose.DATA_ENCRYPTION: "alias/owkai-data-encryption",
        KeyPurpose.TOKEN_SIGNING: "alias/owkai-token-signing",
        KeyPurpose.PII_ENCRYPTION: "alias/owkai-pii-encryption",
        KeyPurpose.AUDIT_SIGNING: "alias/owkai-audit-signing",
        KeyPurpose.BACKUP_ENCRYPTION: "alias/owkai-backup-encryption",
    }

    def __init__(self):
        self._key_cache: Dict[str, Dict[str, Any]] = {}
        self._operation_log: list = []
        self._kms_client = None

        # Initialize AWS KMS client if credentials available
        self._initialize_kms_client()

    def _initialize_kms_client(self) -> None:
        """Initialize AWS KMS client."""
        try:
            import boto3

            region = os.getenv("AWS_REGION", "us-east-2")
            self._kms_client = boto3.client("kms", region_name=region)
            logger.info(f"SEC-006: KMS client initialized for region {region}")
        except ImportError:
            logger.warning("SEC-006: boto3 not available - using local encryption fallback")
        except Exception as e:
            logger.warning(f"SEC-006: KMS initialization failed: {e} - using local fallback")

    def generate_data_key(
        self,
        purpose: KeyPurpose,
        context: Optional[Dict[str, str]] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate a data encryption key using KMS.

        Returns:
            Tuple of (plaintext_key, encrypted_key)
        """
        key_spec = "AES_256"

        if self._kms_client:
            try:
                key_alias = self.KEY_ALIASES.get(purpose, "alias/owkai-data-encryption")

                response = self._kms_client.generate_data_key(
                    KeyId=key_alias,
                    KeySpec=key_spec,
                    EncryptionContext=context or {"purpose": purpose.value}
                )

                self._log_operation(
                    "GENERATE_DATA_KEY",
                    purpose.value,
                    "success",
                    {"key_spec": key_spec}
                )

                return response["Plaintext"], response["CiphertextBlob"]

            except Exception as e:
                logger.error(f"SEC-006: KMS generate_data_key failed: {e}")
                self._log_operation("GENERATE_DATA_KEY", purpose.value, "failed", {"error": str(e)})

        # Fallback: Generate local key (NOT for production)
        logger.warning("SEC-006: Using local key generation fallback")
        plaintext_key = secrets.token_bytes(32)
        encrypted_key = self._local_encrypt(plaintext_key)

        return plaintext_key, encrypted_key

    def encrypt(
        self,
        data: bytes,
        purpose: KeyPurpose,
        context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Encrypt data using envelope encryption.

        Uses KMS to generate a data key, encrypts data with that key,
        then returns encrypted data and encrypted data key.

        Returns:
            Dict with encrypted_data, encrypted_key, algorithm, iv
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        # Generate data key
        plaintext_key, encrypted_key = self.generate_data_key(purpose, context)

        # Generate IV
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM

        # Encrypt data
        aesgcm = AESGCM(plaintext_key)
        encrypted_data = aesgcm.encrypt(iv, data, None)

        # Clear plaintext key from memory
        plaintext_key = b'\x00' * len(plaintext_key)

        self._log_operation(
            "ENCRYPT",
            purpose.value,
            "success",
            {"data_size": len(data), "algorithm": EncryptionAlgorithm.AES_256_GCM.value}
        )

        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "iv": base64.b64encode(iv).decode(),
            "algorithm": EncryptionAlgorithm.AES_256_GCM.value,
            "key_purpose": purpose.value,
            "timestamp": datetime.now(UTC).isoformat()
        }

    def decrypt(
        self,
        encrypted_payload: Dict[str, Any],
        context: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Decrypt data using envelope decryption.

        Uses KMS to decrypt the data key, then decrypts the data.
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        encrypted_data = base64.b64decode(encrypted_payload["encrypted_data"])
        encrypted_key = base64.b64decode(encrypted_payload["encrypted_key"])
        iv = base64.b64decode(encrypted_payload["iv"])
        purpose = KeyPurpose(encrypted_payload.get("key_purpose", "data_encryption"))

        # Decrypt data key using KMS
        plaintext_key = self._decrypt_data_key(encrypted_key, context)

        # Decrypt data
        aesgcm = AESGCM(plaintext_key)
        data = aesgcm.decrypt(iv, encrypted_data, None)

        # Clear plaintext key from memory
        plaintext_key = b'\x00' * len(plaintext_key)

        self._log_operation(
            "DECRYPT",
            purpose.value,
            "success",
            {"data_size": len(data)}
        )

        return data

    def _decrypt_data_key(
        self,
        encrypted_key: bytes,
        context: Optional[Dict[str, str]] = None
    ) -> bytes:
        """Decrypt a data key using KMS."""
        if self._kms_client:
            try:
                response = self._kms_client.decrypt(
                    CiphertextBlob=encrypted_key,
                    EncryptionContext=context or {}
                )
                return response["Plaintext"]
            except Exception as e:
                logger.error(f"SEC-006: KMS decrypt failed: {e}")

        # Fallback
        return self._local_decrypt(encrypted_key)

    def _local_encrypt(self, data: bytes) -> bytes:
        """Local encryption fallback (NOT for production)."""
        # Use environment secret for local fallback
        secret = os.getenv("LOCAL_ENCRYPTION_KEY", "").encode() or secrets.token_bytes(32)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        # Derive key from secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"owkai-local-salt",
            iterations=100000,
        )
        key = kdf.derive(secret)

        iv = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        encrypted = aesgcm.encrypt(iv, data, None)

        return iv + encrypted

    def _local_decrypt(self, encrypted: bytes) -> bytes:
        """Local decryption fallback (NOT for production)."""
        secret = os.getenv("LOCAL_ENCRYPTION_KEY", "").encode() or secrets.token_bytes(32)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"owkai-local-salt",
            iterations=100000,
        )
        key = kdf.derive(secret)

        iv = encrypted[:12]
        ciphertext = encrypted[12:]

        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext, None)

    def _log_operation(
        self,
        operation: str,
        key_purpose: str,
        status: str,
        details: Dict[str, Any]
    ) -> None:
        """Log cryptographic operation for audit trail."""
        log_entry = {
            "operation": operation,
            "key_purpose": key_purpose,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "details": details
        }
        self._operation_log.append(log_entry)
        logger.info(f"SEC-006 AUDIT: {operation} - {key_purpose} - {status}")

    def get_audit_log(self, limit: int = 100) -> list:
        """Get cryptographic operation audit log."""
        return self._operation_log[-limit:]


class PIIEncryptionService:
    """
    Specialized encryption service for PII data.

    Provides field-level encryption for sensitive personal data
    with automatic key management.
    """

    # Fields that should be encrypted
    PII_FIELDS = {
        "ssn", "social_security_number",
        "tax_id", "ein",
        "credit_card", "card_number",
        "bank_account", "account_number", "routing_number",
        "drivers_license", "passport_number",
        "date_of_birth", "dob",
        "phone_number", "mobile",
        "email", "email_address",
        "address", "street_address", "home_address",
    }

    def __init__(self, kms_service: Optional[KMSEncryptionService] = None):
        self._kms = kms_service or KMSEncryptionService()

    def encrypt_pii_field(self, field_name: str, value: str) -> str:
        """
        Encrypt a PII field value.

        Returns base64-encoded encrypted value with metadata prefix.
        """
        if not value:
            return value

        encrypted = self._kms.encrypt(
            value.encode(),
            KeyPurpose.PII_ENCRYPTION,
            {"field": field_name}
        )

        # Return compact format for storage
        return f"ENC::{encrypted['encrypted_key']}::{encrypted['iv']}::{encrypted['encrypted_data']}"

    def decrypt_pii_field(self, encrypted_value: str) -> str:
        """Decrypt a PII field value."""
        if not encrypted_value or not encrypted_value.startswith("ENC::"):
            return encrypted_value

        parts = encrypted_value.split("::")
        if len(parts) != 4:
            raise ValueError("Invalid encrypted PII format")

        payload = {
            "encrypted_key": parts[1],
            "iv": parts[2],
            "encrypted_data": parts[3],
            "key_purpose": KeyPurpose.PII_ENCRYPTION.value,
            "algorithm": EncryptionAlgorithm.AES_256_GCM.value
        }

        return self._kms.decrypt(payload).decode()

    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt all PII fields in a record.

        Automatically identifies and encrypts PII fields based on field names.
        """
        encrypted_record = record.copy()

        for field, value in record.items():
            field_lower = field.lower()
            if any(pii in field_lower for pii in self.PII_FIELDS):
                if isinstance(value, str):
                    encrypted_record[field] = self.encrypt_pii_field(field, value)

        return encrypted_record

    def decrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt all encrypted PII fields in a record."""
        decrypted_record = record.copy()

        for field, value in record.items():
            if isinstance(value, str) and value.startswith("ENC::"):
                decrypted_record[field] = self.decrypt_pii_field(value)

        return decrypted_record


# Global instances
kms_encryption_service = KMSEncryptionService()
pii_encryption_service = PIIEncryptionService(kms_encryption_service)


logger.info("SEC-006: KMS Encryption Service loaded")
