from sqlalchemy import text
from database import engine

def add_security_columns():
    with engine.connect() as conn:
        # Add columns with safe defaults
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Active'
        """))
        conn.commit()
        print("✅ Security columns added to users table")

if __name__ == "__main__":
    add_security_columns()
