#!/usr/bin/env python3
"""
EMERGENCY DATABASE SCHEMA FIX - CRITICAL PRODUCTION BLOCKER

This script fixes the missing database columns that are causing 500 errors:
- agent_actions.updated_at
- agent_actions.reviewed_at  
- users.status
- users.mfa_enabled
- users.login_attempts

Code reviewer identified these as critical blocking issues.
"""

import psycopg2
import os
import sys
from datetime import datetime

def connect_to_database():
    """Connect to the production database using Railway connection."""
    try:
        # Check environment variables first
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            # Try Railway public connection string
            DATABASE_URL = "postgresql://postgres:juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@junction.proxy.rlwy.net:19408/railway"
        
        print(f"🔗 Connecting to database: {DATABASE_URL.replace(':juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@', ':***@')}")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        print("✅ Database connection established")
        return conn
        
    except Exception as e:
        print(f"❌ CRITICAL: Database connection failed: {e}")
        print("💡 Trying fallback connection methods...")
        
        # Try alternative connections
        fallback_urls = [
            "postgresql://postgres:juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@monorail.proxy.rlwy.net:19408/railway",
            "postgresql://postgres:juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@viaduct.proxy.rlwy.net:19408/railway"
        ]
        
        for fallback_url in fallback_urls:
            try:
                print(f"🔄 Trying fallback: {fallback_url.replace(':juVnTTAwjcgEAkNPMTXoYVhcdqljgyHr@', ':***@')}")
                conn = psycopg2.connect(fallback_url)
                conn.autocommit = False
                print("✅ Database connection established via fallback")
                return conn
            except Exception as fe:
                print(f"   ❌ Fallback failed: {fe}")
                continue
        
        print("❌ All connection methods failed")
        sys.exit(1)

def check_current_schema(conn):
    """Check current database schema to understand what's missing."""
    print("\n🔍 Checking current database schema...")
    
    with conn.cursor() as cursor:
        # Check agent_actions columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'agent_actions' 
            ORDER BY column_name;
        """)
        
        agent_actions_columns = cursor.fetchall()
        print(f"📋 agent_actions table has {len(agent_actions_columns)} columns:")
        
        missing_agent_columns = []
        required_agent_columns = ['updated_at', 'reviewed_at']
        
        existing_columns = [col[0] for col in agent_actions_columns]
        for req_col in required_agent_columns:
            if req_col not in existing_columns:
                missing_agent_columns.append(req_col)
                print(f"   ❌ MISSING: {req_col}")
            else:
                print(f"   ✅ EXISTS: {req_col}")
        
        # Check users columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY column_name;
        """)
        
        users_columns = cursor.fetchall()
        print(f"\n📋 users table has {len(users_columns)} columns:")
        
        missing_user_columns = []
        required_user_columns = ['status', 'mfa_enabled', 'login_attempts']
        
        existing_user_columns = [col[0] for col in users_columns]
        for req_col in required_user_columns:
            if req_col not in existing_user_columns:
                missing_user_columns.append(req_col)
                print(f"   ❌ MISSING: {req_col}")
            else:
                print(f"   ✅ EXISTS: {req_col}")
        
        return missing_agent_columns, missing_user_columns

def apply_schema_fixes(conn, missing_agent_columns, missing_user_columns):
    """Apply the critical schema fixes."""
    print("\n🔧 Applying emergency schema fixes...")
    
    try:
        with conn.cursor() as cursor:
            
            # Fix agent_actions table
            if 'updated_at' in missing_agent_columns:
                print("   🔧 Adding agent_actions.updated_at column...")
                cursor.execute("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                """)
                
                print("   🔄 Updating existing records with updated_at...")
                cursor.execute("""
                    UPDATE agent_actions 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL;
                """)
                print("   ✅ agent_actions.updated_at added and populated")
            
            if 'reviewed_at' in missing_agent_columns:
                print("   🔧 Adding agent_actions.reviewed_at column...")
                cursor.execute("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
                """)
                print("   ✅ agent_actions.reviewed_at added")
            
            # Fix users table
            if 'status' in missing_user_columns:
                print("   🔧 Adding users.status column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN status VARCHAR(50) DEFAULT 'active';
                """)
                
                print("   🔄 Updating existing users with active status...")
                cursor.execute("""
                    UPDATE users 
                    SET status = 'active' 
                    WHERE status IS NULL;
                """)
                print("   ✅ users.status added and populated")
            
            if 'mfa_enabled' in missing_user_columns:
                print("   🔧 Adding users.mfa_enabled column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
                """)
                print("   ✅ users.mfa_enabled added")
            
            if 'login_attempts' in missing_user_columns:
                print("   🔧 Adding users.login_attempts column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN login_attempts INTEGER DEFAULT 0;
                """)
                print("   ✅ users.login_attempts added")
            
            # Create performance indexes
            print("   🔧 Creating performance indexes...")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_updated_at ON agent_actions(updated_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_reviewed_at ON agent_actions(reviewed_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_actions_status ON agent_actions(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);")
            
            print("   ✅ Performance indexes created")
            
            # Create trigger for automatic updated_at
            if 'updated_at' in missing_agent_columns:
                print("   🔧 Creating automatic updated_at trigger...")
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_agent_actions_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """)
                
                cursor.execute("DROP TRIGGER IF EXISTS trigger_agent_actions_updated_at ON agent_actions;")
                cursor.execute("""
                    CREATE TRIGGER trigger_agent_actions_updated_at
                        BEFORE UPDATE ON agent_actions
                        FOR EACH ROW
                        EXECUTE FUNCTION update_agent_actions_updated_at();
                """)
                print("   ✅ Automatic updated_at trigger created")
            
        conn.commit()
        print("\n✅ ALL SCHEMA FIXES APPLIED SUCCESSFULLY!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ CRITICAL: Schema fix failed: {e}")
        raise

def verify_fixes(conn):
    """Verify that the fixes are working."""
    print("\n🧪 Verifying schema fixes...")
    
    try:
        with conn.cursor() as cursor:
            # Test agent_actions queries that were failing
            print("   🧪 Testing agent_actions.updated_at query...")
            cursor.execute("SELECT COUNT(*) FROM agent_actions WHERE updated_at IS NOT NULL;")
            updated_at_count = cursor.fetchone()[0]
            print(f"   ✅ Found {updated_at_count} records with updated_at")
            
            print("   🧪 Testing agent_actions.reviewed_at availability...")
            cursor.execute("SELECT COUNT(*) FROM agent_actions;")
            total_count = cursor.fetchone()[0]
            print(f"   ✅ agent_actions table has {total_count} total records")
            
            # Test the performance metrics query that was failing
            print("   🧪 Testing performance metrics query (previously returned 500)...")
            cursor.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (COALESCE(reviewed_at, created_at) - created_at))/60) as avg_minutes
                FROM agent_actions 
                WHERE created_at IS NOT NULL;
            """)
            avg_result = cursor.fetchone()[0]
            print(f"   ✅ Performance metrics query works - avg time: {avg_result or 0:.2f} minutes")
            
            # Test users.status query that was failing
            print("   🧪 Testing users.status query...")
            cursor.execute("SELECT status, COUNT(*) FROM users GROUP BY status;")
            status_results = cursor.fetchall()
            for status, count in status_results:
                print(f"   ✅ Users with status '{status}': {count}")
            
        print("\n🎉 ALL VERIFICATIONS PASSED - API endpoints should now work!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise

def main():
    """Execute the emergency database schema fix."""
    print("🚨 EMERGENCY DATABASE SCHEMA FIX - CRITICAL PRODUCTION BLOCKER")
    print("=" * 70)
    print("Fixing missing columns that cause 500 errors in Authorization Center")
    print(f"🕒 Started at: {datetime.now().isoformat()}")
    print()
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Check what needs to be fixed
        missing_agent_columns, missing_user_columns = check_current_schema(conn)
        
        if not missing_agent_columns and not missing_user_columns:
            print("\n🎉 No missing columns found - database schema is correct!")
            return
        
        print(f"\n📋 SUMMARY OF REQUIRED FIXES:")
        print(f"   - Missing agent_actions columns: {missing_agent_columns}")
        print(f"   - Missing users columns: {missing_user_columns}")
        
        # Apply fixes
        apply_schema_fixes(conn, missing_agent_columns, missing_user_columns)
        
        # Verify fixes
        verify_fixes(conn)
        
        print(f"\n🏆 EMERGENCY FIX COMPLETED SUCCESSFULLY!")
        print(f"🕒 Completed at: {datetime.now().isoformat()}")
        print("\nThe following API endpoints should now work:")
        print("   ✅ /api/authorization/metrics/approval-performance")
        print("   ✅ /api/governance/unified-actions")
        print("   ✅ All Authorization Center endpoints")
        
    except Exception as e:
        print(f"\n❌ EMERGENCY FIX FAILED: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()