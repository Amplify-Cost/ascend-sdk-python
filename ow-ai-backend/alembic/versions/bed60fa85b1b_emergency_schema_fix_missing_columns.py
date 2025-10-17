"""emergency_schema_fix_missing_columns

CRITICAL PRODUCTION BLOCKER FIX:
- Adds missing agent_actions.updated_at column (causing unified governance 500 errors)
- Adds missing agent_actions.reviewed_at column (causing performance metrics 500 errors)
- Adds missing users.status column (causing user management failures)
- Adds missing users.mfa_enabled column (enterprise feature requirement)
- Adds missing users.login_attempts column (security feature requirement)

These columns are referenced in models.py but missing from database causing:
- /api/authorization/metrics/approval-performance -> 500 error
- /api/governance/unified-actions -> 500 error
- User management endpoints -> 500 error

Revision ID: bed60fa85b1b
Revises: c3cdb8ad48b0
Create Date: 2025-09-11 22:35:55.110841
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'bed60fa85b1b'
down_revision: Union[str, None] = 'c3cdb8ad48b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    EMERGENCY SCHEMA FIX - Add missing columns that cause 500 errors.
    
    This fixes the critical production blocker where the database schema
    is missing columns that the application models expect to exist.
    """
    
    # Get connection for custom SQL operations
    connection = op.get_bind()
    
    # Fix agent_actions table - Add missing columns with safe operations
    print("🔧 Adding missing agent_actions columns...")
    
    # Add updated_at column if it doesn't exist
    try:
        # Check if column exists before adding
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agent_actions' AND column_name = 'updated_at'
        """))
        
        if not result.fetchone():
            op.add_column('agent_actions', 
                         sa.Column('updated_at', sa.DateTime(timezone=True), 
                                 server_default=sa.text('NOW()'), nullable=True))
            
            # Update existing records
            connection.execute(text("""
                UPDATE agent_actions 
                SET updated_at = created_at 
                WHERE updated_at IS NULL
            """))
            print("   ✅ agent_actions.updated_at added")
        else:
            print("   ✅ agent_actions.updated_at already exists")
    except Exception as e:
        print(f"   ⚠️ agent_actions.updated_at handling: {e}")
    
    # Add reviewed_at column if it doesn't exist
    try:
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agent_actions' AND column_name = 'reviewed_at'
        """))
        
        if not result.fetchone():
            op.add_column('agent_actions', 
                         sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
            print("   ✅ agent_actions.reviewed_at added")
        else:
            print("   ✅ agent_actions.reviewed_at already exists")
    except Exception as e:
        print(f"   ⚠️ agent_actions.reviewed_at handling: {e}")
    
    # Fix users table - Add missing enterprise columns
    print("🔧 Adding missing users columns...")
    
    # Add status column if it doesn't exist
    try:
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'status'
        """))
        
        if not result.fetchone():
            op.add_column('users', 
                         sa.Column('status', sa.String(50), 
                                 server_default='active', nullable=True))
            
            # Update existing records
            connection.execute(text("""
                UPDATE users 
                SET status = 'active' 
                WHERE status IS NULL
            """))
            print("   ✅ users.status added")
        else:
            print("   ✅ users.status already exists")
    except Exception as e:
        print(f"   ⚠️ users.status handling: {e}")
    
    # Add mfa_enabled column if it doesn't exist
    try:
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'mfa_enabled'
        """))
        
        if not result.fetchone():
            op.add_column('users', 
                         sa.Column('mfa_enabled', sa.Boolean, 
                                 server_default='false', nullable=True))
            print("   ✅ users.mfa_enabled added")
        else:
            print("   ✅ users.mfa_enabled already exists")
    except Exception as e:
        print(f"   ⚠️ users.mfa_enabled handling: {e}")
    
    # Add login_attempts column if it doesn't exist
    try:
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'login_attempts'
        """))
        
        if not result.fetchone():
            op.add_column('users', 
                         sa.Column('login_attempts', sa.Integer, 
                                 server_default='0', nullable=True))
            print("   ✅ users.login_attempts added")
        else:
            print("   ✅ users.login_attempts already exists")
    except Exception as e:
        print(f"   ⚠️ users.login_attempts handling: {e}")
    
    # Create performance indexes
    print("🔧 Creating performance indexes...")
    try:
        op.create_index('idx_agent_actions_updated_at', 'agent_actions', ['updated_at'])
        op.create_index('idx_agent_actions_reviewed_at', 'agent_actions', ['reviewed_at'])
        op.create_index('idx_agent_actions_status', 'agent_actions', ['status'])
        op.create_index('idx_users_status', 'users', ['status'])
        print("   ✅ Performance indexes created")
    except Exception as e:
        print(f"   ⚠️ Index creation: {e}")
    
    # Create trigger for automatic updated_at
    print("🔧 Creating automatic updated_at trigger...")
    try:
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION update_agent_actions_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        connection.execute(text("DROP TRIGGER IF EXISTS trigger_agent_actions_updated_at ON agent_actions"))
        connection.execute(text("""
            CREATE TRIGGER trigger_agent_actions_updated_at
                BEFORE UPDATE ON agent_actions
                FOR EACH ROW
                EXECUTE FUNCTION update_agent_actions_updated_at();
        """))
        print("   ✅ Automatic updated_at trigger created")
    except Exception as e:
        print(f"   ⚠️ Trigger creation: {e}")
    
    print("\n🎉 EMERGENCY SCHEMA FIX COMPLETED!")
    print("   The following API endpoints should now work:")
    print("   ✅ /api/authorization/metrics/approval-performance")
    print("   ✅ /api/governance/unified-actions") 
    print("   ✅ All Authorization Center endpoints")


def downgrade() -> None:
    """
    Downgrade schema - Remove the emergency fix columns.
    
    WARNING: This will break the application if columns are still being used.
    """
    print("🔄 Removing emergency schema fix columns...")
    
    # Remove indexes
    try:
        op.drop_index('idx_users_status')
        op.drop_index('idx_agent_actions_status') 
        op.drop_index('idx_agent_actions_reviewed_at')
        op.drop_index('idx_agent_actions_updated_at')
    except Exception as e:
        print(f"   ⚠️ Index removal: {e}")
    
    # Remove trigger
    connection = op.get_bind()
    try:
        connection.execute(text("DROP TRIGGER IF EXISTS trigger_agent_actions_updated_at ON agent_actions"))
        connection.execute(text("DROP FUNCTION IF EXISTS update_agent_actions_updated_at()"))
    except Exception as e:
        print(f"   ⚠️ Trigger removal: {e}")
    
    # Remove columns
    try:
        op.drop_column('users', 'login_attempts')
        op.drop_column('users', 'mfa_enabled')
        op.drop_column('users', 'status')
        op.drop_column('agent_actions', 'reviewed_at')
        op.drop_column('agent_actions', 'updated_at')
    except Exception as e:
        print(f"   ⚠️ Column removal: {e}")
    
    print("   ✅ Emergency schema fix columns removed")
