"""SEC-021: Self-Service Signup Tables

Revision ID: 20251201_signup
Revises:
Create Date: 2025-12-01

Banking-Level Security Tables for:
- SignupRequest: Tracks signup lifecycle with fraud detection
- SignupAttempt: Rate limiting and security tracking
- DisposableEmailDomain: Fraud prevention blocklist
- EmailVerificationAudit: Complete audit trail
- AdminInvitation: Pre-activation team invitations
- SubscriptionTier: Tier configuration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20251201_signup'
down_revision = '08f9e6ba9d35'
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================================
    # SignupRequest - Main signup tracking table
    # ==========================================================================
    op.create_table(
        'signup_requests',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Contact Information
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),

        # Organization Information
        sa.Column('organization_name', sa.String(255), nullable=False),
        sa.Column('organization_slug', sa.String(100), nullable=True),
        sa.Column('organization_size', sa.String(50), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),

        # Subscription & Trial
        sa.Column('requested_tier', sa.String(50), default='pilot'),
        sa.Column('trial_days', sa.Integer(), default=14),

        # Verification Token (SHA-256 hashed)
        sa.Column('verification_token_hash', sa.String(64), nullable=True, index=True),
        sa.Column('verification_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),

        # Status Tracking
        sa.Column('status', sa.String(50), default='pending_verification', index=True),
        sa.Column('status_changed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('status_changed_reason', sa.Text(), nullable=True),

        # Security & Fraud Detection
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('captcha_verified', sa.Boolean(), default=False),
        sa.Column('captcha_score', sa.Integer(), nullable=True),

        # Fraud Detection Results
        sa.Column('is_disposable_email', sa.Boolean(), default=False),
        sa.Column('email_domain_age_days', sa.Integer(), nullable=True),
        sa.Column('fraud_score', sa.Integer(), default=0),
        sa.Column('fraud_flags', postgresql.JSON(), default=[]),

        # Terms & Compliance
        sa.Column('terms_accepted', sa.Boolean(), default=False),
        sa.Column('terms_accepted_at', sa.DateTime(), nullable=True),
        sa.Column('terms_version', sa.String(20), nullable=True),
        sa.Column('privacy_accepted', sa.Boolean(), default=False),
        sa.Column('marketing_consent', sa.Boolean(), default=False),

        # Referral Tracking
        sa.Column('referral_source', sa.String(100), nullable=True),
        sa.Column('referral_code', sa.String(50), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),

        # Result (after activation)
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),

        # Audit Trail
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Email Resend Tracking
        sa.Column('verification_emails_sent', sa.Integer(), default=0),
        sa.Column('last_verification_email_at', sa.DateTime(), nullable=True),
    )

    # ==========================================================================
    # SignupAttempt - Rate limiting and security
    # ==========================================================================
    op.create_table(
        'signup_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('email_domain', sa.String(255), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False, index=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('captcha_passed', sa.Boolean(), default=False),
        sa.Column('is_blocked', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
    )

    # ==========================================================================
    # DisposableEmailDomain - Fraud prevention blocklist
    # ==========================================================================
    op.create_table(
        'disposable_email_domains',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('domain', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('added_by', sa.String(100), default='system'),
        sa.Column('source', sa.String(100), nullable=True),
    )

    # Seed with common disposable email domains
    op.execute("""
        INSERT INTO disposable_email_domains (domain, added_by, source) VALUES
        ('tempmail.com', 'system', 'initial_seed'),
        ('throwaway.email', 'system', 'initial_seed'),
        ('guerrillamail.com', 'system', 'initial_seed'),
        ('mailinator.com', 'system', 'initial_seed'),
        ('temp-mail.org', 'system', 'initial_seed'),
        ('10minutemail.com', 'system', 'initial_seed'),
        ('fakeinbox.com', 'system', 'initial_seed'),
        ('trashmail.com', 'system', 'initial_seed'),
        ('yopmail.com', 'system', 'initial_seed'),
        ('getnada.com', 'system', 'initial_seed'),
        ('maildrop.cc', 'system', 'initial_seed'),
        ('dispostable.com', 'system', 'initial_seed'),
        ('sharklasers.com', 'system', 'initial_seed'),
        ('guerrillamailblock.com', 'system', 'initial_seed'),
        ('pokemail.net', 'system', 'initial_seed')
    """)

    # ==========================================================================
    # EmailVerificationAudit - Complete audit trail
    # ==========================================================================
    op.create_table(
        'email_verification_audits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('signup_request_id', sa.Integer(), sa.ForeignKey('signup_requests.id'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('event_metadata', postgresql.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
    )

    # ==========================================================================
    # AdminInvitation - Pre-activation team invitations
    # ==========================================================================
    op.create_table(
        'admin_invitations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('role', sa.String(50), default='admin'),
        sa.Column('signup_request_id', sa.Integer(), sa.ForeignKey('signup_requests.id'), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('invitation_token_hash', sa.String(64), nullable=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('invited_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('invited_by_email', sa.String(255), nullable=True),
        sa.Column('created_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ==========================================================================
    # SubscriptionTier - Tier configuration
    # ==========================================================================
    op.create_table(
        'subscription_tiers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly_cents', sa.Integer(), default=0),
        sa.Column('price_yearly_cents', sa.Integer(), default=0),
        sa.Column('stripe_price_id_monthly', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_yearly', sa.String(100), nullable=True),
        sa.Column('included_users', sa.Integer(), default=5),
        sa.Column('included_api_calls', sa.Integer(), default=10000),
        sa.Column('included_mcp_servers', sa.Integer(), default=3),
        sa.Column('included_agents', sa.Integer(), default=10),
        sa.Column('features', postgresql.JSON(), default={}),
        sa.Column('trial_days', sa.Integer(), default=14),
        sa.Column('trial_features', postgresql.JSON(), default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Seed subscription tiers
    op.execute("""
        INSERT INTO subscription_tiers (name, display_name, description, price_monthly_cents, price_yearly_cents, included_users, included_api_calls, included_mcp_servers, included_agents, trial_days, sort_order, features) VALUES
        ('pilot', 'Pilot', 'Perfect for trying out ASCEND', 0, 0, 5, 10000, 3, 10, 14, 1, '{"sso": false, "mfa": "optional", "audit_retention_days": 30}'),
        ('growth', 'Growth', 'For growing teams', 49900, 499000, 25, 100000, 10, 50, 14, 2, '{"sso": true, "mfa": "optional", "audit_retention_days": 90}'),
        ('enterprise', 'Enterprise', 'For large organizations', 199900, 1999000, 100, 500000, 50, 200, 14, 3, '{"sso": true, "mfa": "required", "audit_retention_days": 365}'),
        ('mega', 'Mega', 'For enterprises at scale', 499900, 4999000, 1000, 5000000, 200, 1000, 14, 4, '{"sso": true, "mfa": "required", "audit_retention_days": 2555, "dedicated_support": true}')
    """)


def downgrade():
    op.drop_table('subscription_tiers')
    op.drop_table('admin_invitations')
    op.drop_table('email_verification_audits')
    op.drop_table('disposable_email_domains')
    op.drop_table('signup_attempts')
    op.drop_table('signup_requests')
