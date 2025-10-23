"""
🏢 ENTERPRISE MIGRATION: Automation Playbooks System
Apply to: AWS RDS PostgreSQL (Dev + Production)
Author: Enterprise Security Team
Date: 2025-10-22
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file!")
    sys.exit(1)

def apply_migration():
    """Apply automation playbooks migration to database"""
    
    print("🏢 ENTERPRISE MIGRATION: Automation Playbooks System")
    print("=" * 70)
    
    # Extract host for display (hide password)
    db_host = DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'
    db_name = DATABASE_URL.split('/')[-1] if '/' in DATABASE_URL else 'unknown'
    print(f"📍 Target: {db_host}/{db_name}")
    print("")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            current_db, current_user = result.fetchone()
            print(f"✅ Connected: database='{current_db}' user='{current_user}'")
            print("")
        
        # Read migration SQL
        with open('migrations/add_automation_playbooks_20251022_103318.sql', 'r') as f:
            migration_sql = f.read()
        
        print("🔄 Applying migration...")
        print("")
        
        # Apply migration in transaction
        with engine.begin() as conn:
            # Split by comments and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        conn.execute(text(statement))
                        if 'CREATE TABLE' in statement.upper():
                            table_name = statement.split('TABLE')[1].split('(')[0].strip().split()[0]
                            print(f"  ✅ Created table: {table_name}")
                        elif 'CREATE INDEX' in statement.upper():
                            index_name = statement.split('INDEX')[1].split('ON')[0].strip()
                            print(f"  ✅ Created index: {index_name}")
                        elif 'INSERT INTO' in statement.upper():
                            print(f"  ✅ Inserted seed data")
                    except Exception as e:
                        # Skip if already exists
                        if 'already exists' in str(e).lower():
                            print(f"  ⚠️  Skipping (already exists)")
                        else:
                            raise
        
        print("")
        print("=" * 70)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY")
        print("")
        
        # Verify tables
        print("🔍 Verification:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('automation_playbooks', 'playbook_executions')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            for table in tables:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"  ✅ {table}: {count} rows")
        
        print("")
        print("=" * 70)
        return True
        
    except Exception as e:
        print("")
        print("=" * 70)
        print(f"❌ MIGRATION FAILED: {str(e)}")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
