#!/usr/bin/env python3
"""
Railway Migration Script for Phase 2.1 Audit Tables
Runs database migration within Railway environment
"""
import os
import subprocess
import sys

def run_migration():
    """Run Alembic migration in Railway environment"""
    print("🚀 Running Phase 2.1 Database Migration on Railway...")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    try:
        # Set the database URL explicitly for Alembic
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found!")
            sys.exit(1)
            
        # Set environment for Alembic
        env = os.environ.copy()
        env['SQLALCHEMY_URL'] = database_url
        
        # Run the migration
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], env=env, capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
