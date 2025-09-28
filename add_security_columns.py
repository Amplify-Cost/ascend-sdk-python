import sys
import time
from sqlalchemy import text, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def add_security_columns():
    """Add security tracking columns to users table"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Active',
                ADD COLUMN IF NOT EXISTS department VARCHAR(100) DEFAULT 'Engineering'
            """))
            conn.commit()
            print("✅ Security columns added to users table", flush=True)
    except Exception as e:
        print(f"⚠️ Error adding security columns: {e}", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    add_security_columns()
