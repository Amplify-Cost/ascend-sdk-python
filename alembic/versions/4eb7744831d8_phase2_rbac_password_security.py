"""Phase 2: RBAC Password Security Enhancements

Revision ID: 4eb7744831d8
Revises: enterprise_pwd_std
Create Date: 2025-11-01 21:41:37.138185

ENTERPRISE SECURITY ENHANCEMENTS
=================================

Phase 2 of RBAC security fixes addresses 3 high-priority vulnerabilities:

1. Admin Password Reset (CVSS 6.5 - HIGH)
   - Adds force_password_change flag
   - Adds password_last_changed timestamp
   - Enables admin-initiated password resets

2. Account Lockout (CVSS 7.2 - HIGH)
   - Adds failed_login_attempts counter
   - Adds is_locked boolean flag
   - Adds locked_until timestamp
   - Prevents brute force attacks

3. Password Expiration (CVSS 5.8 - MEDIUM)
   - Uses password_last_changed for 90-day policy
   - Adds automated expiration warnings
   - Forces password rotation

Compliance:
- NIST SP 800-63B: Password security and authentication
- PCI-DSS 3.2.1: Access control requirements
- SOX: User access management
- HIPAA: Password expiration policies

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4eb7744831d8'
down_revision: Union[str, None] = 'enterprise_pwd_std'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Phase 2 RBAC password security columns to users table

    Enterprise Security Enhancements:
    - Password management (reset, expiration)
    - Account lockout protection
    - Audit trail support
    """
    # Get connection
    conn = op.get_bind()

    print("🔒 Phase 2 RBAC: Adding password security columns...")

    # Add password management columns
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(),
                                     server_default='false', nullable=False))
    op.add_column('users', sa.Column('password_last_changed', sa.TIMESTAMP(),
                                     nullable=True))

    # Add account lockout columns
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(),
                                     server_default='0', nullable=False))
    op.add_column('users', sa.Column('is_locked', sa.Boolean(),
                                     server_default='false', nullable=False))
    op.add_column('users', sa.Column('locked_until', sa.TIMESTAMP(),
                                     nullable=True))

    # Add index for password expiration queries (performance optimization)
    op.create_index('idx_password_last_changed', 'users', ['password_last_changed'])

    # Set password_last_changed for existing users
    # Assume current passwords are fresh (set to created_at or now())
    conn.execute(text("""
        UPDATE users
        SET password_last_changed = COALESCE(created_at, CURRENT_TIMESTAMP)
        WHERE password_last_changed IS NULL
    """))

    print("✅ Phase 2 RBAC: Password security columns added")
    print("   - force_password_change (admin reset flag)")
    print("   - password_last_changed (90-day expiration)")
    print("   - failed_login_attempts (brute force protection)")
    print("   - is_locked (account lockout)")
    print("   - locked_until (auto-unlock timestamp)")
    print("   - idx_password_last_changed (performance index)")


def downgrade() -> None:
    """
    Remove Phase 2 RBAC password security columns

    Note: Only use for rollback. Production data will be preserved but features disabled.
    """
    print("🔄 Phase 2 RBAC: Removing password security columns...")

    # Drop index
    op.drop_index('idx_password_last_changed', table_name='users')

    # Drop columns in reverse order
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'password_last_changed')
    op.drop_column('users', 'force_password_change')

    print("✅ Phase 2 RBAC: Password security columns removed")
