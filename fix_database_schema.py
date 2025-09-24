#!/usr/bin/env python3
"""
Critical Database Schema Fix
============================================================================
Fixes missing columns that are causing 500 errors in production

Issues to Fix:
1. agent_actions.updated_at column does not exist
2. agent_actions.reviewed_at column does not exist  
3. users.status column does not exist

This script will:
- Add missing columns to existing tables
- Set proper defaults for existing data
- Ensure schema matches the models
"""

import os
import sys
from datetime import datetime, UTC
from sqlalchemy import create_engine, text, Column, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError

def get_database_url():
    """Get database URL from environment"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return None
    return db_url

def fix_agent_actions_table(engine):
    """Add missing columns to agent_actions table"""
    print("🔧 Fixing agent_actions table schema...")
    
    with engine.connect() as conn:
        # Check if updated_at column exists
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'agent_actions' 
                AND column_name = 'updated_at'
            """))
            if not result.fetchone():
                print("  ➕ Adding updated_at column...")
                conn.execute(text("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
                """))
                # Update existing records
                conn.execute(text("""
                    UPDATE agent_actions 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL
                """))
                print("  ✅ Updated existing records with created_at timestamp")
            else:
                print("  ✅ updated_at column already exists")
        
            # Check if reviewed_at column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'agent_actions' 
                AND column_name = 'reviewed_at'
            """))
            if not result.fetchone():
                print("  ➕ Adding reviewed_at column...")
                conn.execute(text("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN reviewed_at TIMESTAMP NULL
                """))
            else:
                print("  ✅ reviewed_at column already exists")
                
            conn.commit()
            print("✅ agent_actions table schema fixed")
            
        except Exception as e:
            print(f"❌ Error fixing agent_actions table: {e}")
            conn.rollback()
            return False
    
    return True

def fix_users_table(engine):
    """Add missing status column to users table"""
    print("🔧 Fixing users table schema...")
    
    with engine.connect() as conn:
        try:
            # Check if status column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'status'
            """))
            if not result.fetchone():
                print("  ➕ Adding status column...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN status VARCHAR(20) DEFAULT 'Active'
                """))
                # Update existing records
                conn.execute(text("""
                    UPDATE users 
                    SET status = CASE 
                        WHEN is_active = true THEN 'Active'
                        ELSE 'Inactive'
                    END
                    WHERE status IS NULL
                """))
                print("  ✅ Updated existing records with status based on is_active")
            else:
                print("  ✅ status column already exists")
                
            # Check if mfa_enabled column exists (referenced in enterprise routes)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'mfa_enabled'
            """))
            if not result.fetchone():
                print("  ➕ Adding mfa_enabled column...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE
                """))
            else:
                print("  ✅ mfa_enabled column already exists")
                
            # Check if login_attempts column exists  
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'login_attempts'
            """))
            if not result.fetchone():
                print("  ➕ Adding login_attempts column...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN login_attempts INTEGER DEFAULT 0
                """))
            else:
                print("  ✅ login_attempts column already exists")
                
            conn.commit()
            print("✅ users table schema fixed")
            
        except Exception as e:
            print(f"❌ Error fixing users table: {e}")
            conn.rollback()
            return False
    
    return True

def validate_schema_fix(engine):
    """Validate that all required columns now exist"""
    print("🔍 Validating schema fixes...")
    
    required_columns = [
        ('agent_actions', 'updated_at'),
        ('agent_actions', 'reviewed_at'),
        ('users', 'status'),
        ('users', 'mfa_enabled'),
        ('users', 'login_attempts')
    ]
    
    all_good = True
    with engine.connect() as conn:
        for table, column in required_columns:
            try:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name = '{column}'
                """))
                if result.fetchone():
                    print(f"  ✅ {table}.{column} exists")
                else:
                    print(f"  ❌ {table}.{column} still missing")
                    all_good = False
            except Exception as e:
                print(f"  ❌ Error checking {table}.{column}: {e}")
                all_good = False
    
    if all_good:
        print("✅ All schema fixes validated successfully")
    else:
        print("❌ Some schema fixes failed validation")
        
    return all_good

def main():
    print("🚑 CRITICAL DATABASE SCHEMA FIX")
    print("=" * 50)
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        sys.exit(1)
    
    try:
        # Create engine
        engine = create_engine(db_url)
        print(f"✅ Connected to database")
        
        # Fix schemas
        success = True
        
        if not fix_agent_actions_table(engine):
            success = False
            
        if not fix_users_table(engine):
            success = False
            
        if not validate_schema_fix(engine):
            success = False
            
        if success:
            print("\n🎉 ALL DATABASE SCHEMA FIXES COMPLETED SUCCESSFULLY!")
            print("The following 500 errors should now be resolved:")
            print("  - /api/authorization/metrics/approval-performance")
            print("  - /api/governance/unified-actions") 
            print("  - Enterprise user management routes")
            print("\n🔄 Restart the application to apply changes.")
        else:
            print("\n❌ SOME SCHEMA FIXES FAILED - MANUAL INTERVENTION REQUIRED")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()