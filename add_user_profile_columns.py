import sys
from sqlalchemy import text, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def add_user_columns():
    """Add user profile columns"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS access_level VARCHAR(100) DEFAULT 'Level 1 - Read Only'
            """))
            conn.commit()
            print("✅ User profile columns added", flush=True)
    except Exception as e:
        print(f"⚠️ Error adding columns: {e}", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    add_user_columns()
