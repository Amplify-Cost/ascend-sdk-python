#!/usr/bin/env python3
"""
Database migration script for OW-AI Authorization System
Run this to create the authorization tables
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import DATABASE_URL, Base
    from models import PendingAgentAction
    print("✅ Successfully imported database modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you're running this from your project root directory")
    sys.exit(1)

def create_authorization_tables():
    """Create the authorization system tables"""
    try:
        print("🔄 Starting database migration for Authorization System...")
        print(f"Database URL: {DATABASE_URL[:50]}...")
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        print("🔄 Testing database connection...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Create the new table
        print("🔄 Creating PendingAgentAction table...")
        PendingAgentAction.__table__.create(engine, checkfirst=True)
        print("✅ PendingAgentAction table created successfully!")
        
        # Verify table was created
        print("🔄 Verifying table creation...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'pending_agent_actions'
            """))
            if result.fetchone():
                print("✅ Table verification successful!")
            else:
                print("❌ Table verification failed!")
                return False
        
        # Add indexes for performance
        print("🔄 Adding database indexes for optimal performance...")
        with engine.connect() as conn:
            try:
                # Index on tenant_id for multi-tenant queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_tenant_id 
                    ON pending_agent_actions(tenant_id)
                """))
                
                # Index on authorization_status for filtering
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_status 
                    ON pending_agent_actions(authorization_status)
                """))
                
                # Index on expires_at for cleanup queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_expires_at 
                    ON pending_agent_actions(expires_at)
                """))
                
                # Index on ai_risk_score for sorting
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_risk_score 
                    ON pending_agent_actions(ai_risk_score)
                """))
                
                # Composite index for common queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pending_actions_tenant_status 
                    ON pending_agent_actions(tenant_id, authorization_status)
                """))
                
                conn.commit()
                print("✅ Database indexes created successfully!")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not create indexes: {e}")
                print("This is not critical - the system will still work")
        
        # Also add tenant_id to existing tables if needed
        print("🔄 Updating existing tables for multi-tenancy...")
        with engine.connect() as conn:
            try:
                # Add tenant_id to agent_actions if it doesn't exist
                conn.execute(text("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR DEFAULT 'default'
                """))
                
                # Add tenant_id to alerts if it doesn't exist
                conn.execute(text("""
                    ALTER TABLE alerts 
                    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR DEFAULT 'default'
                """))
                
                conn.commit()
                print("✅ Existing tables updated for multi-tenancy!")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not update existing tables: {e}")
                print("This might be normal if columns already exist")
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 60)
        print("📋 NEXT STEPS:")
        print("1. Deploy your updated code to Railway")
        print("2. Navigate to the 'Authorization Center' tab in your dashboard")
        print("3. Test the system by creating a high-risk authorization request")
        print("4. Verify the approval/denial workflow works correctly")
        print("")
        print("🔗 Test endpoint:")
        print("   POST /agent-control/request-authorization")
        print("")
        print("🖥️  Dashboard:")
        print("   Click 'Authorization Center' in your app sidebar")
        print("=" * 60)
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False

def rollback_migration():
    """Rollback the migration (drop the authorization table)"""
    try:
        print("🔄 Rolling back authorization system migration...")
        engine = create_engine(DATABASE_URL)
        
        # Drop the table and indexes
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS pending_agent_actions CASCADE"))
            conn.commit()
        
        print("✅ Migration rolled back successfully!")
        print("⚠️  Note: This only removes the authorization table.")
        print("   Your existing agent_actions and alerts tables remain unchanged.")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

def check_migration_status():
    """Check if migration has already been applied"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_name = 'pending_agent_actions'
            """))
            count = result.fetchone()[0]
            
            if count > 0:
                print("✅ Authorization system migration already applied")
                
                # Check table structure
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'pending_agent_actions'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print(f"📊 Table structure ({len(columns)} columns):")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   • {col[0]:<20} {col[1]:<15} {nullable}")
                
                # Check if there are any pending actions
                result = conn.execute(text("""
                    SELECT COUNT(*) as pending_count
                    FROM pending_agent_actions 
                    WHERE authorization_status = 'pending'
                """))
                pending_count = result.fetchone()[0]
                
                if pending_count > 0:
                    print(f"⏳ Found {pending_count} pending authorization(s) requiring human review")
                else:
                    print("✅ No pending authorizations at this time")
                
                return True
            else:
                print("❌ Authorization system migration not applied")
                print("   Run without arguments to apply the migration")
                return False
                
    except Exception as e:
        print(f"❌ Could not check migration status: {e}")
        return False

if __name__ == "__main__":
    print("🔒 OW-AI Authorization System Database Migration")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            check_migration_status()
        elif command == "rollback":
            print("⚠️  This will remove the authorization system table!")
            confirm = input("Are you sure you want to rollback? (type 'yes' to confirm): ")
            if confirm.lower() == "yes":
                rollback_migration()
            else:
                print("❌ Rollback cancelled")
        elif command == "help":
            print("Available commands:")
            print("  python migrate_authorization.py          - Run migration")
            print("  python migrate_authorization.py status   - Check migration status")
            print("  python migrate_authorization.py rollback - Rollback migration")
            print("  python migrate_authorization.py help     - Show this help")
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python migrate_authorization.py help' for available commands")
    else:
        # Default: run migration
        if check_migration_status():
            print("\n💡 Migration already applied. Available options:")
            print("   • Use 'status' to check details")
            print("   • Use 'rollback' to undo (if needed)")
            print("   • Deploy your updated code to start using the authorization system")
        else:
            print("\n🚀 Starting migration...")
            success = create_authorization_tables()
            if not success:
                print("\n❌ Migration failed!")
                sys.exit(1)
            else:
                print("\n✅ Ready to deploy! Your authorization system is now set up.")