"""
SEC-BYOK-003: Envelope encryption service for BYOK/CMK support.

This service implements envelope encryption using customer-managed keys (CMK)
stored in the customer's AWS KMS account.

CRITICAL REQUIREMENTS:
1. FAIL SECURE: If CMK is unavailable or access denied, BLOCK all operations
2. AUDIT TRAIL: Log all encryption/decryption operations to byok_audit_log
3. DEFENSE IN DEPTH: Use encryption context for additional authentication
4. ZERO BREAKING CHANGES: Does not modify existing auth or data patterns

Architecture:
- Customer CMK (in customer's AWS account) encrypts DEK
- DEK (Data Encryption Key) encrypts actual data
- DEK is stored encrypted, decrypted on-demand via CMK
- If customer revokes CMK access, data becomes unreadable (by design)

Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP, NIST 800-53
"""

import os
import logging
import struct
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from services.encryption.byok_exceptions import (
    KeyAccessDenied,
    EncryptionError,
    DataAccessBlocked,
    KeyNotConfigured,
    KeyValidationFailed,
    DEKGenerationFailed,
)

logger = logging.getLogger(__name__)

# Encryption version byte for future compatibility
ENCRYPTION_VERSION_1 = 0x01

# Nonce size for AES-256-GCM (96 bits = 12 bytes)
NONCE_SIZE = 12

# AWS region for KMS operations
KMS_REGION = os.getenv("AWS_REGION", "us-east-2")


class BYOKEncryptionService:
    """
    Envelope encryption service for BYOK/CMK support.

    This service provides:
    - DEK generation using customer CMK
    - Data encryption/decryption with DEK
    - CMK validation and health checks
    - Automatic rotation detection (BYOK-011)

    FAIL SECURE: All operations block on CMK access issues when BYOK is configured.
    """

    def __init__(self, db_session=None):
        """
        Initialize the BYOK encryption service.

        Args:
            db_session: Optional database session for audit logging.
                        If not provided, audit logging is skipped.
        """
        self.kms_client = boto3.client("kms", region_name=KMS_REGION)
        self.db = db_session
        self._dek_cache: Dict[int, Tuple[bytes, datetime]] = {}  # org_id -> (dek, cached_at)
        self._cache_ttl_seconds = 300  # 5 minutes

    async def generate_dek(
        self,
        cmk_arn: str,
        org_id: int,
        cmk_key_version: Optional[str] = None
    ) -> Tuple[bytes, bytes, str]:
        """
        Generate a new Data Encryption Key (DEK) using customer's CMK.

        Args:
            cmk_arn: ARN of customer's CMK in their AWS account
            org_id: Organization ID for encryption context binding
            cmk_key_version: Optional CMK key version for tracking

        Returns:
            Tuple of (plaintext_dek, encrypted_dek, cmk_key_id)

        Raises:
            KeyAccessDenied: If CMK access is revoked
            DEKGenerationFailed: For any other KMS errors
        """
        try:
            # Encryption context binds the DEK to this specific tenant
            # This is enforced by the customer's key policy
            encryption_context = {
                "tenant_id": str(org_id),
                "service": "ascend",
                "purpose": "data_encryption",
            }

            response = self.kms_client.generate_data_key(
                KeyId=cmk_arn,
                KeySpec="AES_256",
                EncryptionContext=encryption_context,
            )

            plaintext_dek = response["Plaintext"]
            encrypted_dek = response["CiphertextBlob"]
            cmk_key_id = response.get("KeyId", "")

            await self._audit_log(
                org_id=org_id,
                operation="dek_generated",
                cmk_arn=cmk_arn,
                success=True,
                metadata={"cmk_key_id": cmk_key_id},
            )

            logger.info(f"BYOK-003: DEK generated for org {org_id}")
            return plaintext_dek, encrypted_dek, cmk_key_id

        except self.kms_client.exceptions.AccessDeniedException as e:
            # FAIL SECURE: Customer revoked access
            await self._audit_log(
                org_id=org_id,
                operation="dek_generated",
                cmk_arn=cmk_arn,
                success=False,
                error_message="Access denied - CMK access may be revoked",
            )
            logger.critical(f"BYOK-003: CMK access denied for org {org_id}: {e}")
            raise KeyAccessDenied(
                f"Encryption key access revoked for organization {org_id}"
            )

        except ClientError as e:
            # FAIL SECURE: Any KMS error blocks operation
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            await self._audit_log(
                org_id=org_id,
                operation="dek_generated",
                cmk_arn=cmk_arn,
                success=False,
                error_message=f"KMS error: {error_code}",
            )
            logger.error(f"BYOK-003: DEK generation failed for org {org_id}: {e}")
            raise DEKGenerationFailed(f"Unable to generate encryption key: {error_code}")

    async def decrypt_dek(
        self,
        cmk_arn: str,
        encrypted_dek: bytes,
        org_id: int
    ) -> bytes:
        """
        Decrypt a DEK using customer's CMK.

        Args:
            cmk_arn: ARN of customer's CMK
            encrypted_dek: The encrypted DEK blob
            org_id: Organization ID for encryption context

        Returns:
            Plaintext DEK bytes

        Raises:
            KeyAccessDenied: If CMK access is revoked
            EncryptionError: For decryption errors
        """
        try:
            encryption_context = {
                "tenant_id": str(org_id),
                "service": "ascend",
                "purpose": "data_encryption",
            }

            response = self.kms_client.decrypt(
                KeyId=cmk_arn,
                CiphertextBlob=encrypted_dek,
                EncryptionContext=encryption_context,
            )

            return response["Plaintext"]

        except self.kms_client.exceptions.AccessDeniedException:
            logger.critical(f"BYOK-003: CMK access denied during decrypt for org {org_id}")
            raise KeyAccessDenied(
                f"Encryption key access revoked for organization {org_id}"
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"BYOK-003: DEK decrypt failed for org {org_id}: {e}")
            raise EncryptionError(f"Unable to decrypt encryption key: {error_code}")

    async def encrypt(
        self,
        org_id: int,
        plaintext: bytes,
        byok_config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Encrypt data using tenant's BYOK configuration.

        If tenant has no BYOK configured, returns plaintext unchanged
        (platform default encryption handled at storage layer).

        FAIL SECURE: If BYOK is configured but CMK is unavailable,
        operation is BLOCKED.

        Args:
            org_id: Organization ID
            plaintext: Data to encrypt
            byok_config: Optional pre-fetched BYOK config

        Returns:
            Encrypted data package: [version:1][nonce:12][ciphertext:N]

        Raises:
            DataAccessBlocked: If BYOK configured but key not active
            KeyAccessDenied: If CMK access is revoked
            EncryptionError: For encryption errors
        """
        if byok_config is None:
            byok_config = await self._get_byok_config(org_id)

        if not byok_config:
            # No BYOK configured — return unchanged (platform handles default encryption)
            logger.debug(f"BYOK-003: No BYOK config for org {org_id}, skipping encryption")
            return plaintext

        # FAIL SECURE: Check status before attempting
        if byok_config["status"] != "active":
            await self._audit_log(
                org_id=org_id,
                operation="encrypt",
                cmk_arn=byok_config["cmk_arn"],
                success=False,
                error_message=f"Key status is {byok_config['status']}",
            )
            logger.warning(
                f"BYOK-003: BYOK status is {byok_config['status']} for org {org_id}"
            )
            raise DataAccessBlocked(
                f"Encryption key is not active (status: {byok_config['status']})"
            )

        try:
            # Get current DEK (cached or from DB)
            dek_plaintext = await self._get_current_dek(org_id, byok_config)

            # Encrypt data with DEK using AES-256-GCM
            nonce = os.urandom(NONCE_SIZE)
            aesgcm = AESGCM(dek_plaintext)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Package: [version:1][nonce:12][ciphertext:N]
            encrypted_package = struct.pack("B", ENCRYPTION_VERSION_1) + nonce + ciphertext

            await self._audit_log(
                org_id=org_id,
                operation="encrypt",
                cmk_arn=byok_config["cmk_arn"],
                success=True,
                metadata={"data_size": len(plaintext)},
            )

            return encrypted_package

        except (KeyAccessDenied, DataAccessBlocked):
            raise  # Re-raise security exceptions

        except Exception as e:
            await self._audit_log(
                org_id=org_id,
                operation="encrypt",
                cmk_arn=byok_config.get("cmk_arn"),
                success=False,
                error_message=str(e),
            )
            logger.error(f"BYOK-003: Encryption failed for org {org_id}: {e}")
            raise EncryptionError(f"Encryption failed: {e}")

    async def decrypt(
        self,
        org_id: int,
        encrypted_data: bytes,
        byok_config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Decrypt data using tenant's BYOK configuration.

        FAIL SECURE: If CMK access is revoked, data is UNREADABLE.

        Args:
            org_id: Organization ID
            encrypted_data: Encrypted data package
            byok_config: Optional pre-fetched BYOK config

        Returns:
            Decrypted plaintext

        Raises:
            DataAccessBlocked: If BYOK configured but key not active/revoked
            KeyAccessDenied: If CMK access is revoked
            EncryptionError: For decryption errors
        """
        if byok_config is None:
            byok_config = await self._get_byok_config(org_id)

        if not byok_config:
            # No BYOK configured — return unchanged
            logger.debug(f"BYOK-003: No BYOK config for org {org_id}, skipping decryption")
            return encrypted_data

        # FAIL SECURE: Check status before attempting
        if byok_config["status"] == "revoked":
            await self._audit_log(
                org_id=org_id,
                operation="access_denied",
                cmk_arn=byok_config["cmk_arn"],
                success=False,
                error_message="Key revoked by customer",
            )
            raise DataAccessBlocked("Encryption key has been revoked by customer")

        if byok_config["status"] != "active":
            await self._audit_log(
                org_id=org_id,
                operation="access_denied",
                cmk_arn=byok_config["cmk_arn"],
                success=False,
                error_message=f"Key status: {byok_config['status']}",
            )
            raise DataAccessBlocked(
                f"Encryption key is not active (status: {byok_config['status']})"
            )

        try:
            # Parse encrypted package
            if len(encrypted_data) < 1 + NONCE_SIZE + 16:  # version + nonce + min tag
                raise EncryptionError("Invalid encrypted data format")

            version = encrypted_data[0]
            if version != ENCRYPTION_VERSION_1:
                raise EncryptionError(f"Unsupported encryption version: {version}")

            nonce = encrypted_data[1 : 1 + NONCE_SIZE]
            ciphertext = encrypted_data[1 + NONCE_SIZE :]

            # Get DEK (will call KMS to decrypt it)
            dek_plaintext = await self._get_current_dek(org_id, byok_config)

            # Decrypt with DEK
            aesgcm = AESGCM(dek_plaintext)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            await self._audit_log(
                org_id=org_id,
                operation="decrypt",
                cmk_arn=byok_config["cmk_arn"],
                success=True,
            )

            return plaintext

        except (KeyAccessDenied, DataAccessBlocked):
            raise  # Re-raise security exceptions

        except Exception as e:
            await self._audit_log(
                org_id=org_id,
                operation="decrypt",
                cmk_arn=byok_config.get("cmk_arn"),
                success=False,
                error_message=str(e),
            )
            logger.error(f"BYOK-003: Decryption failed for org {org_id}: {e}")
            raise DataAccessBlocked(f"Unable to decrypt data: {e}")

    async def validate_cmk_access(
        self,
        cmk_arn: str,
        org_id: int
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate that ASCEND can access the customer's CMK.

        Used during:
        - Key registration (BYOK-004)
        - Periodic health checks (BYOK-005)
        - Rotation detection (BYOK-011)

        Args:
            cmk_arn: ARN of customer's CMK
            org_id: Organization ID for encryption context

        Returns:
            Tuple of (is_valid, cmk_key_id, error_message)
        """
        try:
            encryption_context = {
                "tenant_id": str(org_id),
                "service": "ascend",
                "purpose": "validation",
            }

            # Step 1: Describe the key to get metadata
            describe_response = self.kms_client.describe_key(KeyId=cmk_arn)
            cmk_key_id = describe_response["KeyMetadata"]["KeyId"]
            key_state = describe_response["KeyMetadata"]["KeyState"]

            if key_state != "Enabled":
                return False, cmk_key_id, f"Key is in {key_state} state"

            # Step 2: Try to generate a data key (validates encrypt permission)
            generate_response = self.kms_client.generate_data_key(
                KeyId=cmk_arn,
                KeySpec="AES_256",
                EncryptionContext=encryption_context,
            )

            # Step 3: Try to decrypt (validates decrypt permission)
            self.kms_client.decrypt(
                KeyId=cmk_arn,
                CiphertextBlob=generate_response["CiphertextBlob"],
                EncryptionContext=encryption_context,
            )

            await self._audit_log(
                org_id=org_id,
                operation="key_validated",
                cmk_arn=cmk_arn,
                success=True,
                metadata={"cmk_key_id": cmk_key_id},
            )

            logger.info(f"BYOK-003: CMK validated for org {org_id}")
            return True, cmk_key_id, None

        except self.kms_client.exceptions.AccessDeniedException as e:
            error_msg = "Access denied - check key policy"
            await self._audit_log(
                org_id=org_id,
                operation="key_validated",
                cmk_arn=cmk_arn,
                success=False,
                error_message=error_msg,
            )
            logger.warning(f"BYOK-003: CMK validation failed for org {org_id}: {e}")
            return False, None, error_msg

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = f"KMS error: {error_code}"
            await self._audit_log(
                org_id=org_id,
                operation="key_validated",
                cmk_arn=cmk_arn,
                success=False,
                error_message=error_msg,
            )
            logger.warning(f"BYOK-003: CMK validation failed for org {org_id}: {e}")
            return False, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            await self._audit_log(
                org_id=org_id,
                operation="key_validated",
                cmk_arn=cmk_arn,
                success=False,
                error_message=error_msg,
            )
            logger.error(f"BYOK-003: CMK validation error for org {org_id}: {e}")
            return False, None, error_msg

    async def get_cmk_key_version(self, cmk_arn: str) -> Optional[str]:
        """
        Get the current key version from CMK metadata.

        Used by BYOK-011 to detect automatic key rotation.

        Args:
            cmk_arn: ARN of customer's CMK

        Returns:
            Key ID string (changes when key is rotated), or None on error
        """
        try:
            response = self.kms_client.describe_key(KeyId=cmk_arn)
            return response["KeyMetadata"]["KeyId"]
        except Exception as e:
            logger.warning(f"BYOK-011: Failed to get CMK version: {e}")
            return None

    async def _get_byok_config(self, org_id: int) -> Optional[Dict[str, Any]]:
        """
        Get BYOK configuration for an organization.

        Returns None if BYOK is not configured for this organization.
        """
        if not self.db:
            return None

        result = await self.db.fetch_one(
            """
            SELECT cmk_arn, cmk_alias, status, status_reason,
                   last_validated_at, cmk_key_id, last_key_version
            FROM tenant_encryption_keys
            WHERE organization_id = $1
            """,
            org_id,
        )

        if not result:
            return None

        return dict(result)

    async def _get_current_dek(
        self,
        org_id: int,
        byok_config: Dict[str, Any]
    ) -> bytes:
        """
        Get the current DEK for an organization.

        Checks cache first, then database, then generates new if needed.

        Returns:
            Plaintext DEK bytes
        """
        # Check cache
        if org_id in self._dek_cache:
            cached_dek, cached_at = self._dek_cache[org_id]
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age < self._cache_ttl_seconds:
                return cached_dek

        # Get from database
        if self.db:
            result = await self.db.fetch_one(
                """
                SELECT encrypted_dek
                FROM encrypted_data_keys
                WHERE organization_id = $1 AND is_current = TRUE
                ORDER BY version DESC LIMIT 1
                """,
                org_id,
            )

            if result:
                # Decrypt DEK using CMK
                dek_plaintext = await self.decrypt_dek(
                    byok_config["cmk_arn"],
                    result["encrypted_dek"],
                    org_id,
                )
                # Cache it
                self._dek_cache[org_id] = (dek_plaintext, datetime.now(timezone.utc))
                return dek_plaintext

        # No DEK exists — generate new one
        dek_plaintext, dek_encrypted, cmk_key_id = await self.generate_dek(
            byok_config["cmk_arn"],
            org_id,
        )

        # Store encrypted DEK
        if self.db:
            await self.db.execute(
                """
                INSERT INTO encrypted_data_keys
                    (organization_id, encrypted_dek, encryption_context,
                     version, is_current, cmk_key_version)
                VALUES ($1, $2, $3, 1, TRUE, $4)
                ON CONFLICT (organization_id, version) DO NOTHING
                """,
                org_id,
                dek_encrypted,
                {"tenant_id": str(org_id), "service": "ascend"},
                cmk_key_id,
            )

        # Cache it
        self._dek_cache[org_id] = (dek_plaintext, datetime.now(timezone.utc))
        return dek_plaintext

    async def _audit_log(
        self,
        org_id: int,
        operation: str,
        cmk_arn: Optional[str],
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log BYOK operation to audit table.

        SEC Requirement: AUDIT TRAIL - all BYOK operations must be logged.
        """
        if not self.db:
            # Fallback to standard logging if no DB session
            log_level = logging.INFO if success else logging.WARNING
            logger.log(
                log_level,
                f"BYOK Audit: org={org_id} op={operation} success={success} "
                f"error={error_message} cmk={cmk_arn[:40] + '...' if cmk_arn else None}",
            )
            return

        try:
            await self.db.execute(
                """
                INSERT INTO byok_audit_log
                    (organization_id, operation, cmk_arn, success, error_message, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                org_id,
                operation,
                cmk_arn,
                success,
                error_message,
                metadata or {},
            )
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            logger.error(f"BYOK-003: Audit logging failed: {e}")

    def clear_dek_cache(self, org_id: Optional[int] = None) -> None:
        """
        Clear DEK cache for an organization or all organizations.

        Call this after key rotation to force re-fetch.
        """
        if org_id:
            self._dek_cache.pop(org_id, None)
        else:
            self._dek_cache.clear()
