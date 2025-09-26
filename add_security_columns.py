from sqlalchemy import text
from database import engine
import logging

logger = logging.getLogger(__name__)

def add_security_columns():
    """Add security tracking columns to users table"""
    try:
        with engine.connect() as conn:
            # Add columns with safe defaults
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Active'
            """))
            conn.commit()
            logger.info("✅ Security columns added to users table")
            print("✅ Security columns added to users table")
    except Exception as e:
        logger.error(f"Failed to add security columns: {e}")
        print(f"⚠️ Security columns may already exist: {e}")

if __name__ == "__main__":
    add_security_columns()
