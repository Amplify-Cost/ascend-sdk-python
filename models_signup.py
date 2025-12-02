"""
SEC-021: Enterprise Self-Service Signup Models
Banking-Level Security for Organization Registration

Implements:
- Email verification tokens with cryptographic security
- Signup attempt tracking for rate limiting
- Disposable email detection
- CAPTCHA verification tracking
- Trial period management
- Audit trail for compliance (SOC 2, GDPR)
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Index, UniqueConstraint, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime, timedelta
import secrets
import hashlib


class SignupStatus(str, enum.Enum):
    """SEC-021: Signup workflow states"""
    PENDING_VERIFICATION = "pending_verification"  # Email sent, awaiting click
    EMAIL_VERIFIED = "email_verified"              # Email confirmed
    PENDING_PAYMENT = "pending_payment"            # Trial or payment setup
    PENDING_APPROVAL = "pending_approval"          # Enterprise manual approval
    ACTIVE = "active"                              # Fully activated
    REJECTED = "rejected"                          # Manual rejection
    EXPIRED = "expired"                            # Verification token expired
    BLOCKED = "blocked"                            # Fraud detection blocked


class SignupRequest(Base):
    """
    SEC-021: Self-Service Signup Request

    Tracks the entire signup lifecycle from initial request to activation.
    Banking-level audit trail for compliance.
    """
    __tablename__ = "signup_requests"
    __table_args__ = (
        Index('ix_signup_requests_email', 'email'),
        Index('ix_signup_requests_status', 'status'),
        Index('ix_signup_requests_verification_token', 'verification_token_hash'),
        Index('ix_signup_requests_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Contact Information
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)

    # Organization Information
    organization_name = Column(String(255), nullable=False)
    organization_slug = Column(String(100), nullable=True)  # Generated on verification
    organization_size = Column(String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-500, 500+
    industry = Column(String(100), nullable=True)

    # Subscription & Trial
    requested_tier = Column(String(50), default="pilot")  # pilot, growth, enterprise, mega
    trial_days = Column(Integer, default=14)

    # Verification Token (SHA-256 hashed, never store plaintext)
    verification_token_hash = Column(String(64), nullable=True, index=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Status Tracking
    status = Column(String(50), default=SignupStatus.PENDING_VERIFICATION.value, index=True)
    status_changed_at = Column(DateTime, default=func.now())
    status_changed_reason = Column(Text, nullable=True)

    # Security & Fraud Detection
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    captcha_verified = Column(Boolean, default=False)
    captcha_score = Column(Integer, nullable=True)  # reCAPTCHA v3 score (0-100)

    # Fraud Detection Results
    is_disposable_email = Column(Boolean, default=False)
    email_domain_age_days = Column(Integer, nullable=True)
    fraud_score = Column(Integer, default=0)  # 0-100, higher = more suspicious
    fraud_flags = Column(JSON, default=list)  # List of triggered flags

    # Terms & Compliance
    terms_accepted = Column(Boolean, default=False)
    terms_accepted_at = Column(DateTime, nullable=True)
    terms_version = Column(String(20), nullable=True)  # e.g., "2025.1"
    privacy_accepted = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)

    # Referral Tracking
    referral_source = Column(String(100), nullable=True)  # organic, google, linkedin, referral
    referral_code = Column(String(50), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Result (after activation)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Audit Trail
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Email Resend Tracking
    # SEC-021 ENTERPRISE: server_default ensures DB-level default even for direct SQL
    verification_emails_sent = Column(Integer, default=0, server_default='0', nullable=False)
    last_verification_email_at = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        """
        SEC-021 ENTERPRISE: Initialize with explicit defaults for banking-level reliability.
        SQLAlchemy's default= only applies on INSERT, not Python object creation.
        """
        # Set Python-side defaults before parent init
        kwargs.setdefault('verification_emails_sent', 0)
        kwargs.setdefault('fraud_score', 0)
        kwargs.setdefault('fraud_flags', [])
        kwargs.setdefault('is_disposable_email', False)
        kwargs.setdefault('captcha_verified', False)
        kwargs.setdefault('terms_accepted', False)
        kwargs.setdefault('privacy_accepted', False)
        kwargs.setdefault('marketing_consent', False)
        kwargs.setdefault('trial_days', 14)
        super().__init__(**kwargs)

    def generate_verification_token(self) -> str:
        """
        SEC-021 ENTERPRISE: Generate cryptographically secure verification token.

        Security:
        - 256-bit entropy via secrets.token_urlsafe(32)
        - SHA-256 hash stored (never plaintext)
        - 24-hour expiration enforced
        - Audit trail via verification_emails_sent counter

        Returns:
            Plaintext token (to send in email) - NEVER log this value
        """
        token = secrets.token_urlsafe(32)  # 256-bit entropy
        self.verification_token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.verification_token_expires_at = datetime.utcnow() + timedelta(hours=24)

        # SEC-021 ENTERPRISE: Defense-in-depth - handle edge cases safely
        current_count = self.verification_emails_sent if self.verification_emails_sent is not None else 0
        self.verification_emails_sent = current_count + 1
        self.last_verification_email_at = datetime.utcnow()
        return token

    def verify_token(self, token: str) -> bool:
        """Verify a token against stored hash."""
        if not self.verification_token_hash:
            return False
        if datetime.utcnow() > self.verification_token_expires_at:
            return False
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return secrets.compare_digest(token_hash, self.verification_token_hash)


class SignupAttempt(Base):
    """
    SEC-021: Rate Limiting for Signup Attempts

    Tracks all signup attempts for rate limiting and fraud detection.
    """
    __tablename__ = "signup_attempts"
    __table_args__ = (
        Index('ix_signup_attempts_ip_address', 'ip_address'),
        Index('ix_signup_attempts_email_domain', 'email_domain'),
        Index('ix_signup_attempts_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Request Details
    email = Column(String(255), nullable=True)
    email_domain = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, default=False)
    failure_reason = Column(String(255), nullable=True)

    # Fraud Detection
    captcha_passed = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    # Timestamp
    created_at = Column(DateTime, default=func.now(), index=True)


class DisposableEmailDomain(Base):
    """
    SEC-021: Disposable Email Domain Blocklist

    Maintains list of known disposable/temporary email domains.
    """
    __tablename__ = "disposable_email_domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    added_at = Column(DateTime, default=func.now())
    added_by = Column(String(100), default="system")
    source = Column(String(100), nullable=True)  # Where we learned about this domain


class EmailVerificationAudit(Base):
    """
    SEC-021: Email Verification Audit Trail

    Complete audit of all verification attempts for compliance.
    """
    __tablename__ = "email_verification_audits"
    __table_args__ = (
        Index('ix_email_verification_audits_signup_id', 'signup_request_id'),
        Index('ix_email_verification_audits_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    signup_request_id = Column(Integer, ForeignKey("signup_requests.id"), nullable=False)

    event_type = Column(String(50), nullable=False)  # email_sent, link_clicked, verified, expired, resent
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    success = Column(Boolean, default=True)
    failure_reason = Column(Text, nullable=True)

    # SEC-021: Renamed from 'metadata' (SQLAlchemy reserved attribute)
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now(), index=True)


class AdminInvitation(Base):
    """
    SEC-021: Admin Invitation for Enterprise Signups

    When an enterprise customer signs up, they may invite additional admins
    before the organization is fully activated.
    """
    __tablename__ = "admin_invitations"
    __table_args__ = (
        Index('ix_admin_invitations_token_hash', 'invitation_token_hash'),
        Index('ix_admin_invitations_email', 'email'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Who is invited
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), default="admin")

    # Where they're invited to
    signup_request_id = Column(Integer, ForeignKey("signup_requests.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Invitation Token (SHA-256 hashed)
    invitation_token_hash = Column(String(64), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(50), default="pending")  # pending, accepted, expired, revoked
    accepted_at = Column(DateTime, nullable=True)

    # Who sent it
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_by_email = Column(String(255), nullable=True)  # For pre-activation invites

    # Result
    created_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def generate_invitation_token(self) -> str:
        """Generate secure invitation token."""
        token = secrets.token_urlsafe(32)
        self.invitation_token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.expires_at = datetime.utcnow() + timedelta(days=7)
        return token


class SubscriptionTier(Base):
    """
    SEC-021: Subscription Tier Configuration

    Defines available subscription tiers and their limits.
    """
    __tablename__ = "subscription_tiers"

    id = Column(Integer, primary_key=True, index=True)

    # Tier Identity
    name = Column(String(50), nullable=False, unique=True)  # pilot, growth, enterprise, mega
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Pricing
    price_monthly_cents = Column(Integer, default=0)
    price_yearly_cents = Column(Integer, default=0)
    stripe_price_id_monthly = Column(String(100), nullable=True)
    stripe_price_id_yearly = Column(String(100), nullable=True)

    # Limits
    included_users = Column(Integer, default=5)
    included_api_calls = Column(Integer, default=10000)
    included_mcp_servers = Column(Integer, default=3)
    included_agents = Column(Integer, default=10)

    # Features (JSON for flexibility)
    features = Column(JSON, default=dict)
    # Example: {"sso": false, "mfa": "optional", "audit_retention_days": 30}

    # Trial
    trial_days = Column(Integer, default=14)
    trial_features = Column(JSON, default=dict)  # Features available during trial

    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Show on pricing page
    sort_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
